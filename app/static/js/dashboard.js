// Dashboard JavaScript
console.log('Dashboard.js carregado');

class DashboardManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.init();
            });
        }
    }

    async init() {
        console.log('DashboardManager.init() chamado');

        // Verificação simples: apenas verificar se há token
        const token = this.apiClient.getToken();
        if (!token) {
            console.log('Dashboard: Nenhum token encontrado, redirecionando para login');
            window.location.href = '/login';
            return;
        }

        // Verificar se o token ainda é válido
        try {
            await this.apiClient.get('/api/auth/me');
            console.log('Dashboard: Token válido, continuando...');
        } catch (error) {
            console.warn('Dashboard: Token inválido, redirecionando para login:', error.message);
            this.apiClient.clearStoredAuth();
            window.location.href = '/login';
            return;
        }

        // Token válido, continuar com inicialização normal
        this.setupEventListeners();
        await this.loadDashboardData();
        // Aplicar controle de acesso
        utils.hideElementsForNonAdmin(this.apiClient);
        utils.showUserInfo(this.apiClient);
    }

    async checkAuth() {
        if (this.isCheckingAuth) {
            console.log('Dashboard: CheckAuth já em andamento, pulando...');
            return; // Evitar múltiplas verificações
        }
        
        console.log('Dashboard: Verificando autenticação...');
        this.isCheckingAuth = true;
        try {
            const user = await this.apiClient.getCurrentUser();
            console.log('Dashboard: Usuário autenticado:', user);
            document.getElementById('user-info').textContent = `Olá, ${user.nome}`;
        } catch (error) {
            console.error('Dashboard: Erro ao verificar autenticação:', error);
            // Pequeno delay para evitar throttling
            setTimeout(() => {
                window.location.href = '/login';
            }, 100);
        } finally {
            this.isCheckingAuth = false;
        }
    }

    setupEventListeners() {
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        
        // Adicionar listener para redimensionamento da janela
        window.addEventListener('resize', () => {
            // Redimensionar gráficos após um pequeno delay
            setTimeout(() => {
                if (this.receitaChart) this.receitaChart.resize();
                if (this.statusImoveisChart) this.statusImoveisChart.resize();
            }, 100);
        });
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    async loadDashboardData() {
        try {
            // Carregar estatísticas
            await this.loadStats();

            // Carregar gráficos
            await this.loadCharts();

        } catch (error) {
            console.error('Erro ao carregar dados do dashboard:', error);
        }
    }

    async loadStats() {
        try {
            const stats = await this.apiClient.get('/api/dashboard/stats');

            document.getElementById('receita-mensal').textContent = `R$ ${stats.receita_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('receita-anual').textContent = `R$ ${stats.receita_anual.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('variacao-mensal').textContent = `${stats.variacao_mensal > 0 ? '+' : ''}${stats.variacao_mensal}%`;
            document.getElementById('imoveis-disponiveis').textContent = stats.imoveis_disponiveis;

        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
            // Mostrar valores padrão em caso de erro
            document.getElementById('receita-mensal').textContent = 'R$ 0,00';
            document.getElementById('receita-anual').textContent = 'R$ 0,00';
            document.getElementById('variacao-mensal').textContent = '0%';
            document.getElementById('imoveis-disponiveis').textContent = '0';
        }
    }

    async loadCharts() {
        try {
            const chartData = await this.apiClient.get('/api/dashboard/charts');

            // Renderizar gráfico de receita
            this.renderReceitaChart(chartData.receita_por_mes);
            
            // Renderizar gráfico de status dos imóveis
            this.renderStatusImoveisChart(chartData.status_imoveis);

        } catch (error) {
            console.error('Erro ao carregar gráficos:', error);
            // Renderizar gráficos vazios em caso de erro
            this.renderReceitaChart([]);
            this.renderStatusImoveisChart([]);
        }
    }

    renderReceitaChart(data) {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.error('Chart.js não está carregado');
            return;
        }

        const ctx = document.getElementById('receita-chart').getContext('2d');

        // Destruir gráfico anterior se existir
        if (this.receitaChart) {
            console.log('Destruindo gráfico de receita anterior');
            this.receitaChart.destroy();
        }

        // Verificar se o canvas está visível e tem dimensões
        const canvas = document.getElementById('receita-chart');
        if (!canvas || canvas.offsetHeight === 0) {
            console.warn('Canvas de receita não está pronto, tentando novamente em 100ms');
            setTimeout(() => this.renderReceitaChart(data), 100);
            return;
        }

        console.log('Renderizando gráfico de receita com dados:', data);

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.mes || 'N/A');
        const values = data.map(item => item.receita || 0);

        this.receitaChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Receita (R$)',
                    data: values,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true,
                    pointBackgroundColor: 'rgb(59, 130, 246)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Evolução da Receita Mensal',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return 'Receita: R$ ' + context.parsed.y.toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            },
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    renderStatusImoveisChart(data) {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.error('Chart.js não está carregado');
            return;
        }

        const ctx = document.getElementById('status-imoveis-chart').getContext('2d');

        // Destruir gráfico anterior se existir
        if (this.statusImoveisChart) {
            console.log('Destruindo gráfico de status anterior');
            this.statusImoveisChart.destroy();
        }

        // Verificar se o canvas está visível e tem dimensões
        const canvas = document.getElementById('status-imoveis-chart');
        if (!canvas || canvas.offsetHeight === 0) {
            console.warn('Canvas de status não está pronto, tentando novamente em 100ms');
            setTimeout(() => this.renderStatusImoveisChart(data), 100);
            return;
        }

        console.log('Renderizando gráfico de status com dados:', data);

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.status || 'N/A');
        const values = data.map(item => item.quantidade || 0);

        this.statusImoveisChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quantidade',
                    data: values,
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',  // Vermelho para Alugado
                        'rgba(34, 197, 94, 0.8)',  // Verde para Disponível
                        'rgba(251, 191, 36, 0.8)'  // Amarelo para Manutenção
                    ],
                    borderColor: [
                        'rgb(239, 68, 68)',
                        'rgb(34, 197, 94)',
                        'rgb(251, 191, 36)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                    barThickness: 60,
                    maxBarThickness: 80
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12,
                                weight: 'bold'
                            }
                        }
                    },
                    title: {
                        display: true,
                        text: 'Status dos Imóveis',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: 20
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + ' imóveis';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1,
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            font: {
                                size: 11,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }

}

// Inicializar quando o DOM estiver carregado
console.log('DOM carregado, inicializando dashboard...');
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded disparado');
    // Aguardar as bibliotecas externas serem carregadas
    const checkLibraries = () => {
        console.log('Verificando bibliotecas - Chart:', typeof Chart);
        if (typeof Chart !== 'undefined') {
            console.log('Bibliotecas carregadas, aguardando ApiClient...');
            // DashboardManager será inicializado quando apiReady for disparado
            new DashboardManager();
        } else {
            console.log('Aguardando bibliotecas carregarem...');
            setTimeout(checkLibraries, 100);
        }
    };
    checkLibraries();
});