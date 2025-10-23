// Dashboard JavaScript
console.log('Dashboard.js carregado');

class DashboardManager {
    constructor() {
        this.apiClient = new ApiClient();
        this.receitaChart = null;
        this.statusImoveisChart = null;
        this.tiposImoveisChart = null;
        this.receitaProprietariosChart = null;
        this.alugueisTable = null;
        this.isCheckingAuth = false; // Flag para evitar múltiplas verificações
        this.init();
    }

    async init() {
        console.log('DashboardManager.init() chamado');
        await this.tryAutoLogin();
        this.setupEventListeners();
        await this.loadDashboardData();
        // Aplicar controle de acesso
        utils.hideElementsForNonAdmin();
        utils.showUserInfo();
    }

    async tryAutoLogin() {
        console.log('Tentando login automático...');
        try {
            // Tentar login com credenciais de teste
            const formData = new FormData();
            formData.append('username', 'admin@example.com');
            formData.append('password', 'admin00');

            const response = await fetch('/auth/login', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                console.log('Login automático bem-sucedido');
                this.apiClient.setToken(data.access_token);
                // Obter informações do usuário
                await this.apiClient.getCurrentUser();
            } else {
                console.log('Login automático falhou, continuando sem autenticação');
            }
        } catch (error) {
            console.log('Erro no login automático:', error);
        }
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

        if (this.receitaChart) {
            this.receitaChart.destroy();
        }

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
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Receita Mensal'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            }
                        }
                    }
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

        if (this.statusImoveisChart) {
            this.statusImoveisChart.destroy();
        }

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
                    backgroundColor: 'rgb(16, 185, 129)',
                    borderColor: 'rgb(5, 150, 105)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Status dos Imóveis'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
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

        if (this.tiposImoveisChart) {
            this.tiposImoveisChart.destroy();
        }

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.tipo || 'N/A');
        const values = data.map(item => item.quantidade || 0);

        this.tiposImoveisChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Quantidade',
                    data: values,
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)',
                        'rgb(139, 92, 246)'
                    ],
                    borderColor: 'rgb(255, 255, 255)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Distribuição por Tipo de Imóvel'
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

        if (this.receitaProprietariosChart) {
            this.receitaProprietariosChart.destroy();
        }

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.proprietario || 'N/A');
        const values = data.map(item => item.receita_total || 0);

        this.receitaProprietariosChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Receita Total (R$)',
                    data: values,
                    backgroundColor: 'rgb(59, 130, 246)',
                    borderColor: 'rgb(37, 99, 235)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Receita por Proprietário'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return 'R$ ' + value.toLocaleString('pt-BR');
                            }
                        }
                    }
                }
            }
        });
    }

    async loadRecentRentals() {
        try {
            // Buscar aluguéis mensais recentes (últimos 10)
            const rentals = await this.apiClient.get('/api/alugueis/mensais/?limit=10');

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
                `Imóvel ${rental.id_imovel}`,
                `Proprietário ${rental.id_proprietario}`,
                `R$ ${(rental.valor_total || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                new Date(rental.data_referencia).toLocaleDateString('pt-BR'),
                rental.status || 'N/A'
            ]);

            this.alugueisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Imóvel', 'Proprietário', 'Valor', 'Data Referência', 'Status'],
                columns: [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            Handsontable.renderers.TextRenderer.apply(this, arguments);
                            if (value === 'recebido') {
                                td.style.backgroundColor = '#dcfce7';
                                td.style.color = '#166534';
                            } else if (value === 'pendente') {
                                td.style.backgroundColor = '#fef3c7';
                                td.style.color = '#92400e';
                            } else if (value === 'atrasado') {
                                td.style.backgroundColor = '#fef2f2';
                                td.style.color = '#dc2626';
                            }
                        }
                    }
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
            console.log('Bibliotecas carregadas, inicializando DashboardManager');
            new DashboardManager();
        } else {
            console.log('Aguardando bibliotecas carregarem...');
            setTimeout(checkLibraries, 100);
        }
    };
    checkLibraries();
});