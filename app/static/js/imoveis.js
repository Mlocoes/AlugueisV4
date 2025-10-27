// Imóveis JavaScript
class ImoveisManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.imoveisTable = null;
            this.currentImovel = null;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.imoveisTable = null;
                this.currentImovel = null;
                this.init();
            });
        }
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadImoveis();
        
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
        document.getElementById('add-imovel-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchImoveis());
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('imovel-form').addEventListener('submit', (e) => this.saveImovel(e));
        
        // Export functionality
        document.getElementById('export-btn').addEventListener('click', (e) => this.toggleExportDropdown(e));
        document.getElementById('export-excel').addEventListener('click', (e) => this.exportData(e, 'excel'));
        document.getElementById('export-csv').addEventListener('click', (e) => this.exportData(e, 'csv'));
        
        // Fechar dropdown ao clicar fora
        document.addEventListener('click', (e) => {
            const exportBtn = document.getElementById('export-btn');
            const exportDropdown = document.getElementById('export-dropdown');
            if (!exportBtn.contains(e.target) && !exportDropdown.contains(e.target)) {
                exportDropdown.classList.add('hidden');
            }
        });
        
        // Carregar filtros salvos
        this.loadSavedFilters();
        
        // Salvar filtros ao mudar
        document.getElementById('search-endereco').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-tipo').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-status').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-valor-min').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-valor-max').addEventListener('change', () => this.saveFilters());
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    async loadImoveis() {
        try {
            const imoveis = await this.apiClient.get('/api/imoveis/');

            const container = document.getElementById('imoveis-table');

            if (this.imoveisTable) {
                this.imoveisTable.destroy();
            }

            // Armazenar dados originais para referência
            this.imoveisData = imoveis;

            const data = imoveis.map(imovel => [
                imovel.id,
                imovel.nome,
                imovel.tipo,
                imovel.endereco,
                imovel.alugado ? 'alugado' : 'disponivel',
                imovel.valor_mercado || 0,
                'Ações'
            ]);

            const isAdmin = this.apiClient.isAdmin();

            this.imoveisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Nome', 'Tipo', 'Endereço', 'Status', 'Valor Mercado (R$)', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true }, // ID
                    { type: 'text', readOnly: !isAdmin }, // Nome
                    { 
                        type: 'dropdown',
                        source: ['Comercial', 'Residencial'],
                        readOnly: !isAdmin
                    }, // Tipo
                    { type: 'text', readOnly: !isAdmin }, // Endereço
                    {
                        type: 'dropdown',
                        source: ['disponivel', 'alugado'],
                        readOnly: !isAdmin,
                        renderer: function(instance, td, row, col, prop, value) {
                            Handsontable.renderers.DropdownRenderer.apply(this, arguments);
                            if (value === 'disponivel') {
                                td.style.backgroundColor = '#dcfce7';
                                td.style.color = '#166534';
                                td.textContent = 'Disponível';
                            } else if (value === 'alugado') {
                                td.style.backgroundColor = '#dbeafe';
                                td.style.color = '#1e40af';
                                td.textContent = 'Alugado';
                            }
                        }
                    }, // Status (alugado)
                    { 
                        type: 'numeric',
                        numericFormat: { pattern: '0,0.00' },
                        readOnly: !isAdmin
                    }, // Valor Mercado
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            const imovelId = instance.getDataAtRow(row)[0];
                            if (isAdmin) {
                                td.innerHTML = `
                                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="imoveisManager.deleteImovel(${imovelId})">
                                        <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                                        </svg>
                                    </button>
                                `;
                            } else {
                                td.innerHTML = '-';
                            }
                        }
                    } // Ações
                ],
                height: 500,
                readOnly: !isAdmin,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation',
                // Configuração de ordenação avançada
                columnSorting: {
                    sortEmptyCells: true,
                    initialConfig: this.loadSortConfig(),
                    headerAction: true,
                    indicator: true
                },
                afterChange: (changes, source) => {
                    if (source === 'edit' && isAdmin && changes) {
                        // Pequeno delay para permitir edição rápida sem salvar intermediário
                        setTimeout(() => {
                            this.handleCellChange(changes);
                        }, 300);
                    }
                },
                afterColumnSort: (currentSortConfig, destinationSortConfigs) => {
                    this.saveSortConfig(currentSortConfig);
                    this.updateSortIndicators(currentSortConfig);
                },
                cells: function(row, col) {
                    const cellProperties = {};
                    if (!isAdmin && col !== 0 && col !== 7) {
                        cellProperties.className = 'htDimmed';
                    }
                    return cellProperties;
                }
            });

        } catch (error) {
            console.error('Erro ao carregar imóveis:', error);
        }
    }

    async handleCellChange(changes) {
        if (!changes) return;

        for (const change of changes) {
            const [row, col, oldValue, newValue] = change;
            
            if (oldValue === newValue) continue;

            const rowData = this.imoveisTable.getDataAtRow(row);
            const imovelId = rowData[0];
            
            // Mapeamento de colunas para campos do backend
            const columnMap = {
                1: 'nome',        // Nome
                2: 'tipo',        // Tipo
                3: 'endereco',    // Endereço
                4: 'alugado',     // Status (mapeado para alugado)
                5: 'valor_mercado' // Valor Mercado
            };

            const fieldName = columnMap[col];
            if (!fieldName) continue;

            // VALIDAR DADOS ANTES DE ENVIAR
            const validationError = this.validateField(fieldName, newValue);
            if (validationError) {
                // Feedback visual: célula vermelha (erro de validação)
                const cell = this.imoveisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fee2e2';
                    cell.style.border = '2px solid #dc2626';
                }
                
                // Reverter valor imediatamente
                this.imoveisTable.setDataAtCell(row, col, oldValue, 'revert');
                
                // Mostrar erro
                utils.showAlert(validationError, 'error');
                continue;
            }

            // Encontrar o imóvel original
            const originalImovel = this.imoveisData.find(i => i.id === imovelId);
            if (!originalImovel) continue;

            // Preparar dados para atualização baseado no campo
            let updatedData = {};

            if (fieldName === 'nome') {
                updatedData.nome = rowData[1];
            } else if (fieldName === 'tipo') {
                updatedData.tipo = rowData[2];
            } else if (fieldName === 'endereco') {
                updatedData.endereco = rowData[3];
            } else if (fieldName === 'alugado') {
                // Mapear status para boolean alugado
                updatedData.alugado = rowData[4] === 'alugado';
            } else if (fieldName === 'valor_mercado') {
                updatedData.valor_mercado = parseFloat(rowData[5]) || 0;
            }

            try {
                // Verificar se o token ainda é válido
                await this.apiClient.ensureValidToken();

                // Feedback visual: célula amarela (salvando)
                const cell = this.imoveisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fef3c7';
                }

                // Salvar no backend
                await this.apiClient.put(`/api/imoveis/${imovelId}/`, updatedData);

                // Feedback visual: célula verde (sucesso)
                if (cell) {
                    cell.style.backgroundColor = '#dcfce7';
                    cell.style.border = '2px solid #16a34a';
                    cell.classList.add('cell-edited-success');
                    setTimeout(() => {
                        cell.style.backgroundColor = '';
                        cell.style.border = '';
                        cell.classList.remove('cell-edited-success');
                    }, 2000);
                }

                // Atualizar dados originais
                if (originalImovel) {
                    Object.assign(originalImovel, updatedData);
                }

                console.log(`✓ Imóvel ${imovelId} atualizado: ${fieldName} = ${newValue}`);

            } catch (error) {
                console.error('Erro ao atualizar imóvel:', error);
                
                // Feedback visual: célula vermelha (erro)
                const cell = this.imoveisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fee2e2';
                    cell.style.border = '2px solid #dc2626';
                    cell.classList.add('cell-edited-error');
                    setTimeout(() => {
                        cell.style.backgroundColor = '';
                        cell.style.border = '';
                        cell.classList.remove('cell-edited-error');
                    }, 3000);
                }

                // Reverter valor
                this.imoveisTable.setDataAtCell(row, col, oldValue, 'revert');

                utils.showAlert('Erro ao salvar alteração. Tente novamente.', 'error');
            }
        }
    }

    validateField(fieldName, value) {
        // Verificar se o valor é válido
        if (value === null || value === undefined) {
            return 'Valor não pode ser vazio.';
        }
        
        // Converter para string e trim para validação
        const strValue = String(value).trim();
        
        switch (fieldName) {
            case 'nome':
                if (strValue === '') {
                    return 'Nome do imóvel é obrigatório.';
                }
                if (strValue.length > 120) {
                    return 'Nome do imóvel deve ter no máximo 120 caracteres.';
                }
                break;
                
            case 'tipo':
                if (!strValue || !['Comercial', 'Residencial'].includes(strValue)) {
                    return 'Tipo deve ser "Comercial" ou "Residencial".';
                }
                break;
                
            case 'endereco':
                if (strValue === '') {
                    return 'Endereço do imóvel é obrigatório.';
                }
                break;
                
            case 'alugado':
                if (!strValue || !['disponivel', 'alugado'].includes(strValue)) {
                    return 'Status deve ser "disponivel" ou "alugado".';
                }
                break;
                
            case 'valor_mercado':
                const numValue = parseFloat(strValue);
                if (isNaN(numValue) || numValue < 0) {
                    return 'Valor de mercado deve ser um número positivo.';
                }
                if (numValue > 999999999.99) {
                    return 'Valor de mercado não pode exceder R$ 999.999.999,99.';
                }
                break;
        }
        return null; // Sem erro
    }

    async deleteImovel(imovelId) {
        if (!confirm('Tem certeza que deseja excluir este imóvel?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/imoveis/${imovelId}/`);
            utils.showAlert('Imóvel excluído com sucesso!', 'success');
            this.loadImoveis();
        } catch (error) {
            console.error('Erro ao excluir imóvel:', error);
            utils.showAlert('Erro ao excluir imóvel. Tente novamente.', 'error');
        }
    }

    showModal(imovel = null) {
        this.currentImovel = imovel;

        if (imovel) {
            // Editar imóvel
            document.getElementById('modal-title').textContent = 'Editar Imóvel';
            document.getElementById('save-btn').textContent = 'Salvar';
            document.getElementById('imovel-id').value = imovel.id;
            document.getElementById('nome').value = imovel.nome;
            document.getElementById('tipo').value = imovel.tipo;
            document.getElementById('endereco').value = imovel.endereco;
            document.getElementById('alugado').checked = imovel.alugado;
            document.getElementById('valor_mercado').value = imovel.valor_mercado;
        } else {
            // Novo imóvel
            document.getElementById('modal-title').textContent = 'Adicionar Novo Imóvel';
            document.getElementById('save-btn').textContent = 'Adicionar';
            document.getElementById('imovel-id').value = '';
            document.getElementById('nome').value = '';
            document.getElementById('tipo').value = 'Residencial';
            document.getElementById('endereco').value = '';
            document.getElementById('alugado').checked = false;
            document.getElementById('valor_mercado').value = '';
        }

        const modal = new bootstrap.Modal(document.getElementById('imovelModal'));
        modal.show();
    }

    hideModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('imovelModal'));
        if (modal) {
            modal.hide();
        }
    }

    async saveImovel(event) {
        event.preventDefault();

        const imovelId = document.getElementById('imovel-id').value;
        const nome = document.getElementById('nome').value;
        const tipo = document.getElementById('tipo').value;
        const endereco = document.getElementById('endereco').value;
        const alugado = document.getElementById('alugado').checked;
        const valor_mercado = parseFloat(document.getElementById('valor_mercado').value.replace(',', '.')) || 0;

        if (!nome || !tipo || !endereco) {
            return utils.showAlert('Por favor, preencha todos os campos obrigatórios.', 'error');
        }

        try {
            // Verificar se o token ainda é válido
            await this.apiClient.ensureValidToken();

            // Feedback visual: botão de salvar
            const saveButton = document.getElementById('save-btn');
            saveButton.classList.add('disabled');
            saveButton.innerHTML = 'Salvando...';

            let response;

            if (imovelId) {
                // Atualizar imóvel existente
                response = await this.apiClient.put(`/api/imoveis/${imovelId}/`, {
                    nome,
                    tipo,
                    endereco,
                    alugado,
                    valor_mercado
                });
            } else {
                // Adicionar novo imóvel
                response = await this.apiClient.post('/api/imoveis/', {
                    nome,
                    tipo,
                    endereco,
                    alugado,
                    valor_mercado
                });
            }

            this.hideModal();
            this.loadImoveis();

            utils.showAlert(`Imóvel ${imovelId ? 'atualizado' : 'adicionado'} com sucesso!`, 'success');
        } catch (error) {
            console.error('Erro ao salvar imóvel:', error);
            utils.showAlert('Erro ao salvar imóvel. Tente novamente.', 'error');
        } finally {
            const saveButton = document.getElementById('save-btn');
            saveButton.classList.remove('disabled');
            saveButton.innerHTML = imovelId ? 'Salvar' : 'Adicionar';
        }
    }

    async searchImoveis() {
        const endereco = document.getElementById('search-endereco').value.trim();
        const tipo = document.getElementById('filter-tipo').value;
        const status = document.getElementById('filter-status').value;
        const valorMin = parseFloat(document.getElementById('filter-valor-min').value) || 0;
        const valorMax = parseFloat(document.getElementById('filter-valor-max').value) || Infinity;

        let filteredImoveis = this.imoveisData;

        // Filtro por endereço
        if (endereco) {
            filteredImoveis = filteredImoveis.filter(imovel => 
                imovel.endereco.toLowerCase().includes(endereco.toLowerCase()) ||
                imovel.nome.toLowerCase().includes(endereco.toLowerCase())
            );
        }

        // Filtro por tipo
        if (tipo && tipo !== 'Todos') {
            filteredImoveis = filteredImoveis.filter(imovel => imovel.tipo === tipo);
        }

        // Filtro por status
        if (status && status !== 'Todos') {
            const isAlugado = status === 'alugado';
            filteredImoveis = filteredImoveis.filter(imovel => imovel.alugado === isAlugado);
        }

        // Filtro por valor
        if (valorMin > 0 || valorMax < Infinity) {
            filteredImoveis = filteredImoveis.filter(imovel => {
                const valor = imovel.valor_mercado || 0;
                return valor >= valorMin && valor <= valorMax;
            });
        }

        this.updateTable(filteredImoveis);
        
        // Mostrar contador de resultados
        const totalResults = filteredImoveis.length;
        const totalOriginal = this.imoveisData.length;
        utils.showAlert(`Encontrados ${totalResults} de ${totalOriginal} imóveis`, 'info');
    }

    clearFilters() {
        document.getElementById('search-endereco').value = '';
        document.getElementById('filter-tipo').value = 'Todos';
        document.getElementById('filter-status').value = 'Todos';
        document.getElementById('filter-valor-min').value = '';
        document.getElementById('filter-valor-max').value = '';

        // Verificar se os dados e tabela existem antes de atualizar
        if (this.imoveisData && this.imoveisTable) {
            this.updateTable(this.imoveisData);
            utils.showAlert(`Mostrando todos os ${this.imoveisData.length} imóveis`, 'info');
        } else {
            // Se não há dados ou tabela, recarregar tudo
            this.loadImoveis();
        }
    }

    updateTable(data) {
        if (!this.imoveisTable) {
            console.error('Tabela não inicializada. Tentando inicializar...');
            return;
        }

        this.imoveisTable.loadData(data.map(imovel => [
            imovel.id,
            imovel.nome,
            imovel.tipo,
            imovel.endereco,
            imovel.alugado ? 'alugado' : 'disponivel',
            imovel.valor_mercado || 0,
            'Ações'
        ]));
    }

    loadSavedFilters() {
        const savedFilters = JSON.parse(localStorage.getItem('imoveisFilters')) || {};

        document.getElementById('search-endereco').value = savedFilters.endereco || '';
        document.getElementById('filter-tipo').value = savedFilters.tipo || 'Todos';
        document.getElementById('filter-status').value = savedFilters.status || 'Todos';
        document.getElementById('filter-valor-min').value = savedFilters.valorMin || '';
        document.getElementById('filter-valor-max').value = savedFilters.valorMax || '';
    }

    saveFilters() {
        const endereco = document.getElementById('search-endereco').value.trim();
        const tipo = document.getElementById('filter-tipo').value;
        const status = document.getElementById('filter-status').value;
        const valorMin = document.getElementById('filter-valor-min').value.trim();
        const valorMax = document.getElementById('filter-valor-max').value.trim();

        const filters = {
            endereco: endereco || undefined,
            tipo: tipo !== 'Todos' ? tipo : undefined,
            status: status !== 'Todos' ? status : undefined,
            valorMin: valorMin || undefined,
            valorMax: valorMax || undefined
        };

        localStorage.setItem('imoveisFilters', JSON.stringify(filters));
    }

    toggleExportDropdown(e) {
        e.preventDefault();
        const dropdown = document.getElementById('export-dropdown');
        dropdown.classList.toggle('hidden');
    }

    async exportData(e, format) {
        e.preventDefault();
        
        // Fechar dropdown
        document.getElementById('export-dropdown').classList.add('hidden');
        
        try {
            // Obter filtros atuais
            const endereco = document.getElementById('search-endereco').value.trim();
            const tipo = document.getElementById('filter-tipo').value;
            const status = document.getElementById('filter-status').value;
            const valorMin = document.getElementById('filter-valor-min').value.trim();
            const valorMax = document.getElementById('filter-valor-max').value.trim();
            
            // Construir parâmetros da URL
            const params = new URLSearchParams();
            if (endereco) params.append('endereco', endereco);
            if (tipo && tipo !== 'Todos') params.append('tipo', tipo);
            if (status && status !== 'Todos') params.append('status', status);
            if (valorMin) params.append('valor_min', valorMin);
            if (valorMax) params.append('valor_max', valorMax);
            params.append('format', format);
            
            // Fazer download
            const url = `/api/imoveis/export?${params.toString()}`;
            const link = document.createElement('a');
            link.href = url;
            link.download = ''; // Deixar o servidor definir o nome
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            utils.showAlert(`Exportação ${format.toUpperCase()} iniciada com sucesso!`, 'success');
            
        } catch (error) {
            console.error('Erro na exportação:', error);
            utils.showAlert('Erro ao exportar dados', 'error');
        }
    }

    loadSortConfig() {
        try {
            const saved = localStorage.getItem('imoveis_sort_config');
            return saved ? JSON.parse(saved) : undefined;
        } catch (error) {
            console.error('Erro ao carregar configuração de ordenação:', error);
            return undefined;
        }
    }

    saveSortConfig(config) {
        try {
            if (config && config.length > 0) {
                localStorage.setItem('imoveis_sort_config', JSON.stringify(config));
            } else {
                localStorage.removeItem('imoveis_sort_config');
            }
        } catch (error) {
            console.error('Erro ao salvar configuração de ordenação:', error);
        }
    }

    updateSortIndicators(sortConfig) {
        if (!this.imoveisTable) return;

        // Remover indicadores anteriores
        const headers = this.imoveisTable.getColHeader();
        headers.forEach((header, index) => {
            const th = this.imoveisTable.getCell(-1, index);
            if (th) {
                th.classList.remove('sort-ascending', 'sort-descending', 'sort-active', 'sort-priority-1', 'sort-priority-2', 'sort-priority-3');
                th.title = header; // Reset tooltip
            }
        });

        // Adicionar indicadores para colunas ordenadas
        if (sortConfig && sortConfig.length > 0) {
            sortConfig.forEach((config, sortIndex) => {
                const th = this.imoveisTable.getCell(-1, config.column);
                if (th) {
                    const direction = config.sortOrder === 'asc' ? 'ascending' : 'descending';
                    th.classList.add('sort-active', `sort-${direction}`, `sort-priority-${sortIndex + 1}`);
                    
                    // Adicionar tooltip informativo
                    const sortNumber = sortConfig.length > 1 ? ` (${sortIndex + 1}ª prioridade)` : '';
                    const directionText = config.sortOrder === 'asc' ? 'crescente' : 'decrescente';
                    th.title = `${headers[config.column]} - Ordenado por ${directionText}${sortNumber}`;
                }
            });
        }
    }
}

const imoveisManager = new ImoveisManager();