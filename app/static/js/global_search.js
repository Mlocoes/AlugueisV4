// Busca Global - Sistema de Aluguéis
class GlobalSearchManager {
    constructor() {
        this.apiClient = null;
        this.searchTimeout = null;
        this.init();
    }

    async init() {
        // Aguardar API estar pronta
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.setupEventListeners();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.setupEventListeners();
            });
        }
    }

    setupEventListeners() {
        const searchInput = document.getElementById('global-search');
        const searchBtn = document.getElementById('global-search-btn');
        const resultsContainer = document.getElementById('global-search-results');

        if (searchInput && searchBtn) {
            // Event listener para input com debounce
            searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            // Event listener para botão de busca
            searchBtn.addEventListener('click', () => {
                this.performGlobalSearch(searchInput.value);
            });

            // Fechar resultados ao clicar fora
            document.addEventListener('click', (e) => {
                if (!searchInput.contains(e.target) && !resultsContainer.contains(e.target) && !searchBtn.contains(e.target)) {
                    this.hideResults();
                }
            });

            // Fechar resultados ao pressionar ESC
            searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.hideResults();
                    searchInput.blur();
                } else if (e.key === 'Enter') {
                    this.performGlobalSearch(searchInput.value);
                }
            });
        }
    }

    handleSearchInput(query) {
        // Limpar timeout anterior
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Se query for muito curta, esconder resultados
        if (query.length < 2) {
            this.hideResults();
            return;
        }

        // Debounce: esperar 300ms antes de buscar
        this.searchTimeout = setTimeout(() => {
            this.performGlobalSearch(query);
        }, 300);
    }

    async performGlobalSearch(query) {
        if (!query || query.length < 2) {
            this.hideResults();
            return;
        }

        try {
            // Mostrar loading
            this.showLoading();

            // Fazer busca em paralelo em todas as entidades
            const [imoveis, usuarios, alugueis, participacoes] = await Promise.allSettled([
                this.apiClient.get(`/api/imoveis/?q=${encodeURIComponent(query)}`),
                this.apiClient.get(`/api/usuarios/?q=${encodeURIComponent(query)}`),
                this.apiClient.get(`/api/alugueis/?q=${encodeURIComponent(query)}`),
                this.apiClient.get(`/api/participacoes/?q=${encodeURIComponent(query)}`)
            ]);

            // Processar resultados
            const results = {
                imoveis: imoveis.status === 'fulfilled' ? imoveis.value : [],
                usuarios: usuarios.status === 'fulfilled' ? usuarios.value : [],
                alugueis: alugueis.status === 'fulfilled' ? alugueis.value : [],
                participacoes: participacoes.status === 'fulfilled' ? participacoes.value : []
            };

            this.displayResults(results, query);

        } catch (error) {
            console.error('Erro na busca global:', error);
            this.showError('Erro ao realizar busca');
        }
    }

    showLoading() {
        const resultsContainer = document.getElementById('global-search-results');
        const content = document.getElementById('search-results-content');

        resultsContainer.classList.remove('hidden');
        content.innerHTML = `
            <div class="p-4 text-center text-gray-500">
                <i class="fas fa-spinner fa-spin mr-2"></i>
                Buscando...
            </div>
        `;
    }

    showError(message) {
        const resultsContainer = document.getElementById('global-search-results');
        const content = document.getElementById('search-results-content');

        resultsContainer.classList.remove('hidden');
        content.innerHTML = `
            <div class="p-4 text-center text-red-500">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                ${message}
            </div>
        `;
    }

    displayResults(results, query) {
        const resultsContainer = document.getElementById('global-search-results');
        const content = document.getElementById('search-results-content');

        // Calcular total de resultados
        const totalResults = results.imoveis.length + results.usuarios.length +
                           results.alugueis.length + results.participacoes.length;

        if (totalResults === 0) {
            content.innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    <i class="fas fa-search mr-2"></i>
                    Nenhum resultado encontrado para "${query}"
                </div>
            `;
        } else {
            let html = `<div class="p-2 border-b border-gray-200 bg-gray-50 text-sm font-medium text-gray-700">
                ${totalResults} resultado${totalResults !== 1 ? 's' : ''} encontrado${totalResults !== 1 ? 's' : ''}
            </div>`;

            // Imóveis
            if (results.imoveis.length > 0) {
                html += this.renderResultsSection('Imóveis', results.imoveis, 'imoveis', 'fas fa-building', (item) => ({
                    title: item.endereco || item.nome,
                    subtitle: `Tipo: ${item.tipo}, Status: ${item.status}`,
                    link: '/imoveis'
                }));
            }

            // Usuários (Proprietários)
            if (results.usuarios.length > 0) {
                html += this.renderResultsSection('Proprietários', results.usuarios, 'proprietarios', 'fas fa-user', (item) => ({
                    title: item.nome,
                    subtitle: `Email: ${item.email}`,
                    link: '/proprietarios'
                }));
            }

            // Aluguéis
            if (results.alugueis.length > 0) {
                html += this.renderResultsSection('Aluguéis', results.alugueis, 'aluguel', 'fas fa-file-contract', (item) => ({
                    title: `Aluguel - ${item.imovel?.endereco || 'Imóvel ' + item.id_imovel}`,
                    subtitle: `Valor: R$ ${item.valor_total?.toFixed(2) || 'N/A'}, Data: ${new Date(item.data_inicio).toLocaleDateString('pt-BR')}`,
                    link: '/aluguel'
                }));
            }

            // Participações
            if (results.participacoes.length > 0) {
                html += this.renderResultsSection('Participações', results.participacoes, 'participacoes', 'fas fa-percentage', (item) => ({
                    title: `Participação - ${item.imovel?.endereco || 'Imóvel ' + item.id_imovel}`,
                    subtitle: `${item.proprietario?.nome || 'Proprietário ' + item.id_proprietario} - ${item.participacao}%`,
                    link: '/participacoes'
                }));
            }

            content.innerHTML = html;
        }

        resultsContainer.classList.remove('hidden');
    }

    renderResultsSection(title, items, section, iconClass, formatter) {
        let html = `
            <div class="border-b border-gray-100 last:border-b-0">
                <div class="px-3 py-2 bg-gray-50 text-xs font-medium text-gray-600 uppercase tracking-wide flex items-center">
                    <i class="${iconClass} mr-2"></i>
                    ${title} (${items.length})
                </div>
        `;

        items.slice(0, 5).forEach(item => {
            const data = formatter(item);
            html += `
                <a href="${data.link}" class="block px-3 py-2 hover:bg-gray-50 border-b border-gray-50 last:border-b-0">
                    <div class="text-sm font-medium text-gray-900">${this.highlightText(data.title)}</div>
                    <div class="text-xs text-gray-500">${this.highlightText(data.subtitle)}</div>
                </a>
            `;
        });

        if (items.length > 5) {
            html += `
                <div class="px-3 py-2 text-xs text-blue-600 hover:text-blue-800 cursor-pointer">
                    + ${items.length - 5} mais resultados...
                </div>
            `;
        }

        html += `</div>`;
        return html;
    }

    highlightText(text) {
        // Esta função seria usada para destacar o termo de busca, mas por simplicidade retornamos o texto como está
        return text;
    }

    hideResults() {
        const resultsContainer = document.getElementById('global-search-results');
        if (resultsContainer) {
            resultsContainer.classList.add('hidden');
        }
    }
}

// Inicializar busca global quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    new GlobalSearchManager();
});