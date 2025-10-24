// Relatórios JavaScript
class RelatoriosManager {
    constructor() {
        this.apiClient = window.apiClient;
        this.init();
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        
        // Controle de acesso baseado em papel
        utils.hideElementsForNonAdmin();
        utils.showUserInfo();
    }

    async checkAuth() {
        try {
            await this.apiClient.getCurrentUser();
        } catch (error) {
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
                    await this.apiClient.getCurrentUser();
                } else {
                    console.log('Login automático falhou, redirecionando para login');
                    window.location.href = '/login';
                }
            } catch (loginError) {
                console.log('Erro no login automático, redirecionando para login');
                window.location.href = '/login';
            }
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

        if (!reportType) {
            alert('Selecione um tipo de relatório.');
            return;
        }

        try {
            let url = `/api/relatorios/${reportType}?`;
            const params = [];
            if (dateFrom) params.push(`data_inicio=${dateFrom}`);
            if (dateTo) params.push(`data_fim=${dateTo}`);
            url += params.join('&');

            const reportData = await this.apiClient.get(url);

            this.displayReport(reportData, reportType);
            this.updateSummaryStats(reportData.summary);

        } catch (error) {
            console.error('Erro ao gerar relatório:', error);
            alert('Erro ao gerar relatório. Tente novamente.');
        }
    }

    displayReport(data, reportType) {
        // Atualizar título do gráfico
        const chartTitle = document.getElementById('chart-title');
        const tableTitle = document.getElementById('table-title');

        switch (reportType) {
            case 'receitas':
                chartTitle.textContent = 'Receitas por Período';
                tableTitle.textContent = 'Receitas Detalhadas';
                break;
            case 'proprietarios':
                chartTitle.textContent = 'Receitas por Proprietário';
                tableTitle.textContent = 'Receitas por Proprietário';
                break;
            case 'imoveis':
                chartTitle.textContent = 'Performance de Imóveis';
                tableTitle.textContent = 'Dados de Imóveis';
                break;
            case 'alugueis':
                chartTitle.textContent = 'Aluguéis Ativos';
                tableTitle.textContent = 'Lista de Aluguéis';
                break;
            case 'inadimplencia':
                chartTitle.textContent = 'Taxa de Inadimplência';
                tableTitle.textContent = 'Aluguéis em Atraso';
                break;
        }

        // Criar gráfico
        this.createReportChart(data.chart, reportType);

        // Criar tabela
        this.createReportTable(data.table, reportType);
    }

    createReportChart(chartData, reportType) {
        const ctx = document.getElementById('report-chart').getContext('2d');

        if (this.reportChart) {
            this.reportChart.destroy();
        }

        let config = {};

        switch (reportType) {
            case 'receitas':
            case 'proprietarios':
                config = {
                    type: 'bar',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: 'Valor (R$)',
                            data: chartData.values,
                            backgroundColor: 'rgba(59, 130, 246, 0.8)',
                            borderColor: 'rgb(59, 130, 246)',
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

            case 'imoveis':
                config = {
                    type: 'doughnut',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            data: chartData.values,
                            backgroundColor: [
                                'rgb(59, 130, 246)',
                                'rgb(16, 185, 129)',
                                'rgb(245, 158, 11)',
                                'rgb(239, 68, 68)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right',
                            }
                        }
                    }
                };
                break;

            case 'alugueis':
            case 'inadimplencia':
                config = {
                    type: 'pie',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            data: chartData.values,
                            backgroundColor: [
                                'rgb(16, 185, 129)',
                                'rgb(239, 68, 68)',
                                'rgb(245, 158, 11)'
                            ]
                        }]
                    },
                    options: {
                        responsive: true
                    }
                };
                break;
        }

        this.reportChart = new Chart(ctx, config);
    }

    createReportTable(tableData, reportType) {
        const container = document.getElementById('report-table');

        if (this.reportTable) {
            this.reportTable.destroy();
        }

        let columns = [];
        let colHeaders = [];

        switch (reportType) {
            case 'receitas':
                colHeaders = ['Período', 'Receita Total', 'Número de Aluguéis'];
                columns = [
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    { type: 'text', readOnly: true }
                ];
                break;

            case 'proprietarios':
                colHeaders = ['Proprietário', 'Receita Total', 'Percentual'];
                columns = [
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
                            td.textContent = value + '%';
                        }
                    }
                ];
                break;

            case 'imoveis':
                colHeaders = ['Imóvel', 'Status', 'Valor Aluguel', 'Receita Total'];
                columns = [
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
                    }
                ];
                break;

            case 'alugueis':
                colHeaders = ['Imóvel', 'Inquilino', 'Valor', 'Status'];
                columns = [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            td.textContent = 'R$ ' + parseFloat(value).toLocaleString('pt-BR', { minimumFractionDigits: 2 });
                        }
                    },
                    { type: 'text', readOnly: true }
                ];
                break;

            case 'inadimplencia':
                colHeaders = ['Imóvel', 'Inquilino', 'Dias em Atraso', 'Valor Devido'];
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
                    }
                ];
                break;
        }

        this.reportTable = new Handsontable(container, {
            data: tableData,
            colHeaders: colHeaders,
            columns: columns,
            height: 300,
            readOnly: true,
            stretchH: 'all',
            licenseKey: 'non-commercial-and-evaluation'
        });
    }

    updateSummaryStats(summary) {
        document.getElementById('total-receitas').textContent = `R$ ${summary.total_receitas.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        document.getElementById('receitas-medias').textContent = `R$ ${summary.receitas_medias.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`;
        document.getElementById('taxa-ocupacao').textContent = `${summary.taxa_ocupacao}%`;
        document.getElementById('inadimplencia').textContent = `${summary.inadimplencia}%`;
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
}

// Instância global
let relatoriosManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    relatoriosManager = new RelatoriosManager();
});