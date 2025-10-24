/**
 * Sistema de Importação de Dados
 */

class ImportManager {
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
        try {
            await this.checkAuth();
            this.setupEventListeners();
            utils.showUserInfo(this.apiClient);
            
        } catch (error) {
            console.error('Erro na inicialização:', error);
            window.location.href = '/login';
        }
    }

    async checkAuth() {
        try {
            const user = await this.apiClient.getCurrentUser();
            
            // Verificar se é admin
            if (user.tipo !== 'administrador') {
                alert('Acesso negado. Apenas administradores podem importar dados.');
                window.location.href = '/dashboard';
                return;
            }
        } catch (error) {
            console.log('Usuário não autenticado, redirecionando para login');
            window.location.href = '/login';
        }
    }

    setupEventListeners() {
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        
        // Event listeners para mudança de arquivo
        document.getElementById('file-proprietarios').addEventListener('change', (e) => 
            this.onFileSelected(e, 'proprietarios'));
        document.getElementById('file-imoveis').addEventListener('change', (e) => 
            this.onFileSelected(e, 'imoveis'));
        document.getElementById('file-alugueis').addEventListener('change', (e) => 
            this.onFileSelected(e, 'alugueis'));
        document.getElementById('file-participacoes').addEventListener('change', (e) => 
            this.onFileSelected(e, 'participacoes'));
    }

    onFileSelected(event, type) {
        const file = event.target.files[0];
        if (file) {
            const resultDiv = document.getElementById(`result-${type}`);
            resultDiv.innerHTML = `
                <div class="text-sm text-blue-600 flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/>
                    </svg>
                    Arquivo selecionado: ${file.name}
                </div>
            `;
        }
    }

    async importData(type) {
        const fileInput = document.getElementById(`file-${type}`);
        const file = fileInput.files[0];
        const resultDiv = document.getElementById(`result-${type}`);

        if (!file) {
            this.showResult(resultDiv, 'error', 'Por favor, selecione um arquivo primeiro');
            return;
        }

        // Validar extensão
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
            this.showResult(resultDiv, 'error', 'Arquivo deve ser .xlsx ou .xls');
            return;
        }

        // Mostrar loading
        this.showResult(resultDiv, 'loading', 'Importando dados...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            // Usar ApiClient para garantir autenticação correta
            const result = await this.apiClient.request(`/api/importacao/${type}`, {
                method: 'POST',
                body: formData
            });

            if (result.success !== false) {
                this.showResult(resultDiv, 'success', result.message || 'Importação concluída', result);
                // Limpar input
                fileInput.value = '';
            } else {
                const errors = result.erros || [result.message || 'Erro desconhecido'];
                this.showResult(resultDiv, 'error', result.message || 'Erro ao importar', errors);
            }

        } catch (error) {
            console.error('Erro na importação:', error);
            this.showResult(resultDiv, 'error', 'Erro ao conectar com o servidor');
        }
    }

    showResult(container, type, message, details = null) {
        let html = '';
        
        if (type === 'loading') {
            html = `
                <div class="flex items-center text-blue-600">
                    <svg class="animate-spin h-5 w-5 mr-3" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    ${message}
                </div>
            `;
        } else if (type === 'success') {
            html = `
                <div class="bg-green-50 border border-green-200 rounded-md p-3">
                    <div class="flex items-center text-green-800">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        <span class="font-medium">${message}</span>
                    </div>
                    ${details ? `
                        <div class="mt-2 text-sm text-green-700">
                            <p>Importados: ${details.imported} de ${details.total}</p>
                        </div>
                    ` : ''}
                </div>
            `;
        } else if (type === 'error') {
            html = `
                <div class="bg-red-50 border border-red-200 rounded-md p-3">
                    <div class="flex items-center text-red-800">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                        </svg>
                        <span class="font-medium">${message}</span>
                    </div>
                    ${details && Array.isArray(details) && details.length > 0 ? `
                        <div class="mt-2 text-sm text-red-700">
                            <p class="font-medium mb-1">Erros encontrados:</p>
                            <ul class="list-disc list-inside space-y-1 max-h-40 overflow-y-auto">
                                ${details.map(error => `<li>${error}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        container.innerHTML = html;
    }

    async analyzeFile(type) {
        const fileInput = document.getElementById(`file-${type}`);
        const resultDiv = document.getElementById(`result-${type}`);
        
        if (!fileInput.files[0]) {
            this.showResult(resultDiv, 'error', 'Selecione um arquivo primeiro');
            return;
        }

        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        this.showResult(resultDiv, 'loading', 'Analisando arquivo...');

        try {
            // Usar ApiClient para garantir autenticação correta
            const result = await this.apiClient.request(`/api/importacao/analisar/${type}`, {
                method: 'POST',
                body: formData
            });

            // Se chegou aqui, a resposta foi bem-sucedida
            this.showAnalysisResult(resultDiv, result);

        } catch (error) {
            console.error('Erro na análise:', error);
            this.showResult(resultDiv, 'error', error.message || 'Erro ao analisar arquivo');
        }
    }

    showAnalysisResult(container, result) {
        try {
            let html = `
                <div class="bg-blue-50 border border-blue-200 rounded-md p-3">
                    <div class="flex items-center text-blue-800 mb-2">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" clip-rule="evenodd"/>
                        </svg>
                        <span class="font-medium">Análise do Arquivo</span>
                    </div>
                    <div class="text-sm text-blue-700">
                        <p><strong>Colunas encontradas:</strong> ${result.columns ? result.columns.join(', ') : 'Nenhuma coluna encontrada'}</p>
                        <p><strong>Total de linhas:</strong> ${result.total_rows || 0}</p>
                        <p><strong>Linhas de dados:</strong> ${result.data_rows || 0}</p>
                    </div>
            `;

            if (result.preview && Array.isArray(result.preview) && result.preview.length > 0) {
                html += `
                    <div class="mt-3">
                        <p class="text-sm font-medium text-blue-800 mb-2">Preview dos primeiros registros:</p>
                        <div class="overflow-x-auto">
                            <table class="min-w-full text-xs text-blue-700 border border-blue-300">
                                <thead class="bg-blue-100">
                                    <tr>
                                        ${(result.columns || []).map(col => `<th class="border border-blue-300 px-2 py-1">${col || ''}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.preview.map(row => `
                                        <tr>
                                            ${(result.columns || []).map(col => `<td class="border border-blue-300 px-2 py-1">${row[col] !== undefined ? row[col] : ''}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                `;
            }

            if (result.warnings && Array.isArray(result.warnings) && result.warnings.length > 0) {
                html += `
                    <div class="mt-3">
                        <p class="text-sm font-medium text-yellow-800 mb-1">Avisos:</p>
                        <ul class="text-xs text-yellow-700 list-disc list-inside">
                            ${result.warnings.map(w => `<li>${w || ''}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }

            html += `
                    </div>
                </div>
            `;

            container.innerHTML = html;
        } catch (error) {
            console.error('Erro ao mostrar resultado da análise:', error);
            container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-md p-3">
                    <div class="flex items-center text-red-800">
                        <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                        <span class="font-medium">Erro ao exibir resultado da análise</span>
                    </div>
                    <div class="mt-2 text-sm text-red-700">
                        ${error.message || 'Erro desconhecido'}
                    </div>
                </div>
            `;
        }
    }

    logout() {
        this.apiClient.logout();
        window.location.href = '/login';
    }
}

// Função global para importação (chamada pelos botões)
function importData(type) {
    if (window.importManager) {
        window.importManager.importData(type);
    }
}

// Função global para análise
window.analyzeFile = function(type) {
    window.importManager.analyzeFile(type);
};

// Inicializar
document.addEventListener('DOMContentLoaded', () => {
    window.importManager = new ImportManager();
});
