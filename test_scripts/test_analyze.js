// Teste simples da função analyzeFile
console.log('Testando analyzeFile...');

// Simular o ApiClient
class MockApiClient {
    async request(endpoint, options) {
        console.log('Fazendo requisição para:', endpoint);
        // Simular resposta bem-sucedida
        return {
            columns: ['Nome', 'Endereço', 'VALOR'],
            total_rows: 10,
            data_rows: 10,
            preview: [
                {Nome: 'Teste 1', Endereço: 'Rua 1', VALOR: 1.0},
                {Nome: 'Teste 2', Endereço: 'Rua 2', VALOR: 1.0}
            ],
            warnings: ['Aviso de teste']
        };
    }
}

// Simular ImportManager
class TestImportManager {
    constructor() {
        this.apiClient = new MockApiClient();
    }
    
    showAnalysisResult(container, result) {
        console.log('Resultado da análise:', result);
        console.log('Colunas:', result.columns);
        console.log('Linhas totais:', result.total_rows);
        console.log('Preview:', result.preview);
        if (result.warnings) {
            console.log('Avisos:', result.warnings);
        }
    }
    
    async analyzeFile(type) {
        console.log('Analisando arquivo do tipo:', type);
        
        try {
            const result = await this.apiClient.request(`/api/importacao/analisar/${type}`, {
                method: 'POST',
                body: new FormData()
            });
            
            this.showAnalysisResult(null, result);
            console.log('✅ Análise concluída com sucesso!');
            
        } catch (error) {
            console.error('❌ Erro na análise:', error);
        }
    }
}

// Executar teste
const manager = new TestImportManager();
manager.analyzeFile('participacoes');
