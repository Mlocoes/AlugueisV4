// Relatórios JavaScript
class RelatoriosManager {
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
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadFilterOptions();
        
        // Controle de acesso baseado em papel
        utils.hideElementsForNonAdmin(this.apiClient);
        utils.showUserInfo(this.apiClient);
    }

    async checkAuth() {
        try {
            await this.apiClient.getCurrentUser();
        } catch (error) {
            // Sempre redirecionar para a tela de login ao carregar a página quando não autenticado
            window.location.href = '/login';
            return;
        }
    }

    setupEventListeners() {
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        document.getElementById('generate-report-btn').addEventListener('click', () => this.generateReport());
        document.getElementById('export-pdf-btn').addEventListener('click', () => this.exportReport('pdf'));
        document.getElementById('export-excel-btn').addEventListener('click', () => this.exportReport('excel'));
        document.getElementById('export-csv-btn').addEventListener('click', () => this.exportReport('csv'));
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    async generateReport() {
        const reportType = document.getElementById('report-type').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;
        const proprietarioId = document.getElementById('filter-proprietario').value;
        const imovelId = document.getElementById('filter-imovel').value;
        const aliasId = document.getElementById('filter-alias').value;

        if (!reportType) {
            utils.showAlert('Selecione um tipo de relatório.', 'warning');
            return;
        }

        if (!dateFrom || !dateTo) {
            utils.showAlert('Selecione o período do relatório.', 'warning');
            return;
        }

        try {
            let url = `/api/relatorios/${reportType}?`;
            const params = [];
            params.push(`data_inicio=${dateFrom}`);
            params.push(`data_fim=${dateTo}`);
            
            if (proprietarioId) params.push(`id_proprietario=${proprietarioId}`);
            if (imovelId) params.push(`id_imovel=${imovelId}`);
            if (aliasId) params.push(`id_alias=${aliasId}`);
            
            url += params.join('&');

            const reportData = await this.apiClient.get(url);

            this.displayReport(reportData, reportType);

        } catch (error) {
            console.error('Erro ao gerar relatório:', error);
            utils.showAlert('Erro ao gerar relatório. Tente novamente.', 'error');
        }
    }

    displayReport(data, reportType) {
        // Atualizar título do gráfico
        const chartTitle = document.getElementById('chart-title');
        const tableTitle = document.getElementById('table-title');

        switch (reportType) {
            case 'receitas-periodo':
                chartTitle.textContent = 'Receitas por Período';
                tableTitle.textContent = 'Receitas Detalhadas';
                break;
            case 'receitas-proprietario':
                chartTitle.textContent = 'Receitas por Proprietário';
                tableTitle.textContent = 'Receitas por Proprietário';
                break;
            case 'performance-imoveis':
                chartTitle.textContent = 'Performance de Imóveis';
                tableTitle.textContent = 'Dados de Imóveis';
                break;
            case 'alugueis-ativos':
                chartTitle.textContent = 'Aluguéis Ativos';
                tableTitle.textContent = 'Lista de Aluguéis';
                break;
        }

        // Criar gráfico
        this.createReportChart(data.dados, reportType);

        // Criar tabela
        this.createReportTable(data.dados, reportType);

        // Atualizar estatísticas
        this.updateSummaryStats(data);
    }

    createReportChart(dados, reportType) {
        const ctx = document.getElementById('report-chart').getContext('2d');

        if (this.reportChart) {
            this.reportChart.destroy();
        }

        let config = {};

        switch (reportType) {
            case 'receitas-periodo':
                config = {
                    type: 'line',
                    data: {
                        labels: dados.map(d => d.periodo),
                        datasets: [{
                            label: 'Receitas (R$)',
                            data: dados.map(d => d.total_receitas),
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            borderColor: 'rgb(59, 130, 246)',
                            borderWidth: 2,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
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
                };
                break;

            case 'receitas-proprietario':
                config = {
                    type: 'bar',
                    data: {
                        labels: dados.map(d => d.nome),
                        datasets: [{
                            label: 'Receitas (R$)',
                            data: dados.map(d => d.total_receitas),
                            backgroundColor: 'rgba(16, 185, 129, 0.8)',
                            borderColor: 'rgb(16, 185, 129)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
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
                };
                break;

            case 'performance-imoveis':
                config = {
                    type: 'bar',
                    data: {
                        labels: dados.map(d => d.nome),
                        datasets: [{
                            label: 'Receita Total (R$)',
                            data: dados.map(d => d.receita_total),
                            backgroundColor: 'rgba(245, 158, 11, 0.8)',
                            borderColor: 'rgb(245, 158, 11)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
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
                };
                break;

            case 'alugueis-ativos':
                config = {
                    type: 'doughnut',
                    data: {
                        labels: ['Aluguéis Ativos'],
                        datasets: [{
                            data: [dados.length],
                            backgroundColor: ['rgb(59, 130, 246)']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom',
                            }
                        }
                    }
                };
                break;
        }

        this.reportChart = new Chart(ctx, config);
    }

    createReportTable(dados, reportType) {
        const container = document.getElementById('report-table');

        if (this.reportTable) {
            this.reportTable.destroy();
        }

        let columns = [];
        let colHeaders = [];

        switch (reportType) {
            case 'receitas-periodo':
                colHeaders = ['Período', 'Receita Total', 'Imóveis Ativos', 'Proprietários Ativos'];
                columns = [
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true }
                ];
                break;

            case 'receitas-proprietario':
                colHeaders = ['Proprietário', 'Receita Total', 'Imóveis', 'Taxa Média'];
                columns = [
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = parseFloat(value).toFixed(2) + '%';
                        }
                    }
                ];
                break;

            case 'performance-imoveis':
                colHeaders = ['Imóvel', 'Endereço', 'Tipo', 'Receita Total', 'Meses Alugado', 'Receita Média'];
                columns = [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    }
                ];
                break;

            case 'alugueis-ativos':
                colHeaders = ['ID', 'Imóvel', 'Proprietário', 'Valor Total', 'Valor Proprietário', 'Taxa Admin'];
                columns = [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = parseFloat(value).toFixed(2) + '%';
                        }
                    }
                ];
                break;
        }

        // Preparar dados para Handsontable
        const tableData = dados.map(item => {
            switch (reportType) {
                case 'receitas-periodo':
                    return [
                        item.periodo,
                        item.total_receitas,
                        item.imoveis_ativos,
                        item.proprietarios_ativos
                    ];
                case 'receitas-proprietario':
                    return [
                        item.nome,
                        item.total_receitas,
                        item.imoveis,
                        item.taxa_media
                    ];
                case 'performance-imoveis':
                    return [
                        item.nome,
                        item.endereco,
                        item.tipo,
                        item.receita_total,
                        item.meses_alugado,
                        item.receita_media_mensal
                    ];
                case 'alugueis-ativos':
                    return [
                        item.id,
                        item.imovel,
                        item.proprietario,
                        item.valor_total,
                        item.valor_proprietario,
                        item.taxa_administracao
                    ];
                default:
                    return [];
            }
        });

        this.reportTable = new Handsontable(container, {
            data: tableData,
            colHeaders: colHeaders,
            columns: columns,
            height: 400,
            readOnly: true,
            stretchH: 'all',
            licenseKey: 'non-commercial-and-evaluation'
        });
    }

    updateSummaryStats(data) {
        // Calcular estatísticas baseadas nos dados
        let totalReceitas = 0;
        let totalImoveis = 0;
        let totalProprietarios = 0;

        if (data.dados && data.dados.length > 0) {
            switch (data.filtros ? 'with_filtros' : 'without_filtros') {
                case 'with_filtros':
                    // Usar total_geral se disponível
                    totalReceitas = data.total_geral || data.dados.reduce((sum, item) => {
                        if (item.total_receitas) return sum + item.total_receitas;
                        if (item.receita_total) return sum + item.receita_total;
                        if (item.valor_total) return sum + item.valor_total;
                        return sum;
                    }, 0);
                    
                    totalImoveis = data.dados.reduce((sum, item) => sum + (item.imoveis_ativos || item.imoveis || 1), 0);
                    totalProprietarios = data.dados.reduce((sum, item) => sum + (item.proprietarios_ativos || 1), 0);
                    break;
                    
                default:
                    // Fallback para estrutura antiga
                    totalReceitas = data.dados.reduce((sum, item) => sum + (item.total_receitas || item.receita_total || 0), 0);
                    break;
            }
        }

        const receitasMedias = data.dados && data.dados.length > 0 ? totalReceitas / data.dados.length : 0;
        const taxaOcupacao = totalImoveis > 0 ? (totalImoveis / data.dados.length * 100) : 0;

        document.getElementById('total-receitas').textContent = `R$ ${totalReceitas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        document.getElementById('receitas-medias').textContent = `R$ ${receitasMedias.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        document.getElementById('taxa-ocupacao').textContent = `${taxaOcupacao.toFixed(1)}%`;
        document.getElementById('inadimplencia').textContent = `0%`; // Placeholder
    }

    async exportReport(format) {
        const reportType = document.getElementById('report-type').value;
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;

        if (!reportType) {
            alert('Gere um relatório primeiro.');
            return;
        }

        try {
            let url = `/api/relatorios/${reportType}/export/${format}?`;
            const params = [];
            if (dateFrom) params.push(`data_inicio=${dateFrom}`);
            if (dateTo) params.push(`data_fim=${dateTo}`);
            url += params.join('&');

            // Para exportações, vamos fazer o download
            const response = await this.apiClient.get(url, { responseType: 'blob' });

            // Criar link de download
            const blob = new Blob([response], {
                type: format === 'pdf' ? 'application/pdf' :
                      format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' :
                      'text/csv'
            });

            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `relatorio_${reportType}_${new Date().toISOString().split('T')[0]}.${format === 'excel' ? 'xlsx' : format}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            console.error('Erro ao exportar relatório:', error);
            alert('Erro ao exportar relatório. Tente novamente.');
        }
    }

    async loadFilterOptions() {
        try {
            // Carregar proprietários
            const proprietarios = await this.apiClient.get('/api/usuarios/');
            const proprietarioSelect = document.getElementById('filter-proprietario');
            proprietarioSelect.innerHTML = '<option value="">Todos</option>';
            proprietarios.forEach(prop => {
                const option = document.createElement('option');
                option.value = prop.id;
                option.textContent = `${prop.nome} ${prop.sobrenome || ''}`.trim();
                proprietarioSelect.appendChild(option);
            });

            // Carregar imóveis
            const imoveis = await this.apiClient.get('/api/imoveis/');
            const imovelSelect = document.getElementById('filter-imovel');
            imovelSelect.innerHTML = '<option value="">Todos</option>';
            imoveis.forEach(imovel => {
                const option = document.createElement('option');
                option.value = imovel.id;
                option.textContent = imovel.nome;
                imovelSelect.appendChild(option);
            });

            // Carregar aliases
            const aliases = await this.apiClient.get('/api/alias/');
            const aliasSelect = document.getElementById('filter-alias');
            aliasSelect.innerHTML = '<option value="">Todos</option>';
            aliases.forEach(alias => {
                const option = document.createElement('option');
                option.value = alias.id;
                option.textContent = alias.nome;
                aliasSelect.appendChild(option);
            });

        } catch (error) {
            console.error('Erro ao carregar opções dos filtros:', error);
        }
    }
}

// Instância global
let relatoriosManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    relatoriosManager = new RelatoriosManager();
});