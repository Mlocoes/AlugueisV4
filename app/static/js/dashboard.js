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
                if (this.tiposImoveisChart) this.tiposImoveisChart.resize();
                if (this.receitaProprietariosChart) this.receitaProprietariosChart.resize();
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

            // Carregar tabela de aluguéis recentes
            await this.loadRecentRentals();

        } catch (error) {
            console.error('Erro ao carregar dados do dashboard:', error);
        }
    }

    async loadStats() {
        try {
            const stats = await this.apiClient.get('/api/dashboard/stats');

            document.getElementById('total-imoveis').textContent = stats.total_imoveis;
            document.getElementById('receita-mensal').textContent = `R$ ${stats.receita_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('alugueis-ativos').textContent = stats.alugueis_ativos;
            document.getElementById('alugueis-vencidos').textContent = '0'; // TODO: implementar contagem de aluguéis vencidos

        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
            // Mostrar valores padrão em caso de erro
            document.getElementById('total-imoveis').textContent = '0';
            document.getElementById('receita-mensal').textContent = 'R$ 0,00';
            document.getElementById('alugueis-ativos').textContent = '0';
            document.getElementById('alugueis-vencidos').textContent = '0';
        }
    }

    async loadCharts() {
        try {
            const chartData = await this.apiClient.get('/api/dashboard/charts');

            // Renderizar gráfico de receita
            this.renderReceitaChart(chartData.receita_por_mes);
            
            // Renderizar gráfico de status dos imóveis
            this.renderStatusImoveisChart(chartData.status_imoveis);
            
            // Renderizar gráfico de distribuição por tipo
            this.renderTiposImoveisChart(chartData.distribuicao_tipos);
            
            // Renderizar gráfico de receita por proprietário
            this.renderReceitaProprietariosChart(chartData.receita_por_proprietario);

        } catch (error) {
            console.error('Erro ao carregar gráficos:', error);
            // Renderizar gráficos vazios em caso de erro
            this.renderReceitaChart([]);
            this.renderStatusImoveisChart([]);
            this.renderTiposImoveisChart([]);
            this.renderReceitaProprietariosChart([]);
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

    renderTiposImoveisChart(data) {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.error('Chart.js não está carregado');
            return;
        }

        const ctx = document.getElementById('tipos-imoveis-chart').getContext('2d');

        // Destruir gráfico anterior se existir
        if (this.tiposImoveisChart) {
            console.log('Destruindo gráfico de tipos anterior');
            this.tiposImoveisChart.destroy();
        }

        // Verificar se o canvas está visível e tem dimensões
        const canvas = document.getElementById('tipos-imoveis-chart');
        if (!canvas || canvas.offsetHeight === 0) {
            console.warn('Canvas de tipos não está pronto, tentando novamente em 100ms');
            setTimeout(() => this.renderTiposImoveisChart(data), 100);
            return;
        }

        console.log('Renderizando gráfico de tipos com dados:', data);

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.tipo || 'N/A');
        const values = data.map(item => item.quantidade || 0);

        this.tiposImoveisChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quantidade',
                    data: values,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)',
                        'rgba(6, 182, 212, 0.8)'
                    ],
                    borderColor: 'rgb(255, 255, 255)',
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverBorderColor: 'rgb(255, 255, 255)',
                    cutout: '60%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
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
                        text: 'Distribuição por Tipo de Imóvel',
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
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    renderReceitaProprietariosChart(data) {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.error('Chart.js não está carregado');
            return;
        }

        const ctx = document.getElementById('receita-proprietarios-chart').getContext('2d');

        // Destruir gráfico anterior se existir
        if (this.receitaProprietariosChart) {
            console.log('Destruindo gráfico de proprietários anterior');
            this.receitaProprietariosChart.destroy();
        }

        // Verificar se o canvas está visível e tem dimensões
        const canvas = document.getElementById('receita-proprietarios-chart');
        if (!canvas || canvas.offsetHeight === 0) {
            console.warn('Canvas de proprietários não está pronto, tentando novamente em 100ms');
            setTimeout(() => this.renderReceitaProprietariosChart(data), 100);
            return;
        }

        console.log('Renderizando gráfico de proprietários com dados:', data);

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.proprietario || 'N/A');
        const values = data.map(item => item.receita_total || 0);

        // Criar gradiente para as barras
        const gradient = ctx.createLinearGradient(0, 0, 400, 0);
        gradient.addColorStop(0, 'rgba(16, 185, 129, 0.8)');
        gradient.addColorStop(1, 'rgba(5, 150, 105, 0.8)');

        this.receitaProprietariosChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Receita Total (R$)',
                    data: values,
                    backgroundColor: gradient,
                    borderColor: 'rgb(5, 150, 105)',
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                }]
            },
            options: {
                indexAxis: 'y', // Gráfico horizontal
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false, // Ocultar legenda para economia de espaço
                    },
                    title: {
                        display: true,
                        text: 'Top 10 Proprietários por Receita',
                        font: {
                            size: 16,
                            weight: 'bold'
                        },
                        padding: {
                            top: 10,
                            bottom: 20
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        callbacks: {
                            label: function(context) {
                                return 'Receita: R$ ' + context.parsed.x.toLocaleString('pt-BR');
                            }
                        }
                    }
                },
                scales: {
                    x: {
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
                    y: {
                        ticks: {
                            font: {
                                size: 11
                            }
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                elements: {
                    bar: {
                        borderRadius: 6,
                    }
                }
            }
        });
    }

    async loadRecentRentals() {
        try {
            // Buscar aluguéis recentes via endpoint específico do dashboard
            const rentals = await this.apiClient.get('/api/dashboard/recent-rentals');

            const container = document.getElementById('alugueis-recentes-table');

            if (this.alugueisTable) {
                this.alugueisTable.destroy();
            }

            // Verificar se Handsontable está disponível
            if (typeof Handsontable === 'undefined') {
                console.error('Handsontable não está carregado');
                return;
            }

            const data = rentals.map(rental => [
                rental.id,
                rental.imovel,
                rental.proprietario,
                `R$ ${(rental.valor_total || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                rental.data_referencia,
                rental.status
            ]);

            this.alugueisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Imóvel', 'Proprietário', 'Valor Total', 'Data Ref.', 'Status'],
                columns: [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true }
                ],
                height: 300,
                readOnly: true,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation'
            });

        } catch (error) {
            console.error('Erro ao carregar aluguéis recentes:', error);
        }
    }
}

// Inicializar quando o DOM estiver carregado
console.log('DOM carregado, inicializando dashboard...');
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded disparado');
    // Aguardar as bibliotecas externas serem carregadas
    const checkLibraries = () => {
        console.log('Verificando bibliotecas - Chart:', typeof Chart, 'Handsontable:', typeof Handsontable);
        if (typeof Chart !== 'undefined' && typeof Handsontable !== 'undefined') {
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