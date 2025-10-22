// Dashboard JavaScript
console.log('Dashboard.js carregado');

class DashboardManager {
    constructor() {
        this.apiClient = new ApiClient();
        this.receitaChart = null;
        this.proprietariosChart = null;
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
            formData.append('username', 'admin');
            formData.append('password', '123');

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
            // Por enquanto, usar dados mock até implementar o backend
            const stats = {
                total_imoveis: 5,
                receita_mensal: 15000.00,
                alugueis_ativos: 3,
                alugueis_vencidos: 0
            };

            // const stats = await this.apiClient.get('/api/dashboard/stats');

            document.getElementById('total-imoveis').textContent = stats.total_imoveis;
            document.getElementById('receita-mensal').textContent = `R$ ${stats.receita_mensal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
            document.getElementById('alugueis-ativos').textContent = stats.alugueis_ativos;
            document.getElementById('alugueis-vencidos').textContent = stats.alugueis_vencidos;

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
            // Por enquanto, usar dados mock até implementar o backend
            const chartData = {
                receita_por_mes: [
                    { mes: 'Jan', receita: 12000 },
                    { mes: 'Fev', receita: 13500 },
                    { mes: 'Mar', receita: 11800 },
                    { mes: 'Abr', receita: 14200 },
                    { mes: 'Mai', receita: 13800 },
                    { mes: 'Jun', receita: 15600 }
                ],
                status_imoveis: [
                    { status: 'Alugado', quantidade: 3 },
                    { status: 'Disponível', quantidade: 2 },
                    { status: 'Manutenção', quantidade: 0 }
                ]
            };

            // const chartData = await this.apiClient.get('/api/dashboard/charts');

            this.renderReceitaChart(chartData.receita_por_mes);
            this.renderProprietariosChart(chartData.status_imoveis);

        } catch (error) {
            console.error('Erro ao carregar gráficos:', error);
            // Renderizar gráficos vazios em caso de erro
            this.renderReceitaChart([]);
            this.renderProprietariosChart([]);
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

    renderProprietariosChart(data) {
        // Verificar se Chart.js está disponível
        if (typeof Chart === 'undefined') {
            console.error('Chart.js não está carregado');
            return;
        }

        const ctx = document.getElementById('proprietarios-chart').getContext('2d');

        if (this.proprietariosChart) {
            this.proprietariosChart.destroy();
        }

        // Processar dados para o formato esperado pelo Chart.js
        const labels = data.map(item => item.status || 'N/A');
        const values = data.map(item => item.quantidade || 0);

        this.proprietariosChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 158, 11)',
                        'rgb(239, 68, 68)',
                        'rgb(139, 92, 246)'
                    ]
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
                        text: 'Distribuição por Proprietário'
                    }
                }
            }
        });
    }

    async loadRecentRentals() {
        try {
            // Por enquanto, usar dados mock até implementar o backend
            const rentals = [
                { id: 1, endereco: 'Rua A, 123', inquilino: 'João Silva', valor: 1500.00, data: '2024-01-15', status: 'Ativo' },
                { id: 2, endereco: 'Rua B, 456', inquilino: 'Maria Santos', valor: 1200.00, data: '2024-01-10', status: 'Ativo' },
                { id: 3, endereco: 'Rua C, 789', inquilino: 'Pedro Oliveira', valor: 1800.00, data: '2024-01-05', status: 'Ativo' }
            ];

            // const rentals = await this.apiClient.get('/api/alugueis?limit=10&order_by=data_criacao&order=desc');

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
                rental.endereco,
                rental.inquilino,
                `R$ ${rental.valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                new Date(rental.data).toLocaleDateString('pt-BR'),
                rental.status
            ]);

            this.alugueisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Imóvel', 'Inquilino', 'Valor', 'Data Início', 'Status'],
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
                            if (value === 'ativo') {
                                td.style.backgroundColor = '#dcfce7';
                                td.style.color = '#166534';
                            } else if (value === 'vencido') {
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