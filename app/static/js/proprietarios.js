// Proprietários JavaScript
class ProprietariosManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.proprietariosTable = null;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.proprietariosTable = null;
                this.init();
            });
        }
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadProprietarios();
        
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
        document.getElementById('add-proprietario-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchProprietarios());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('proprietario-form').addEventListener('submit', (e) => this.saveProprietario(e));
        
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
        
        // Event listeners para filtros
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        this.loadSavedFilters();
        document.getElementById('search-nome').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-status').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-data-criacao-de').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-data-criacao-ate').addEventListener('change', () => this.saveFilters());
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    async loadProprietarios() {
        try {
            const proprietarios = await this.apiClient.get('/api/usuarios/?role=proprietario');

            // Armazenar dados originais
            this.proprietariosData = proprietarios;

            const container = document.getElementById('proprietarios-table');

            if (this.proprietariosTable) {
                this.proprietariosTable.destroy();
            }

            const data = proprietarios.map(prop => [
                prop.id,
                prop.nome,
                prop.email,
                prop.telefone || '',
                prop.cpf_cnpj || '',
                prop.ativo,
                'Ações'
            ]);

            const isAdmin = this.apiClient.isAdmin();

            this.proprietariosTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Nome', 'Email', 'Telefone', 'CPF/CNPJ', 'Status', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true }, // ID
                    { type: 'text', readOnly: !isAdmin }, // Nome
                    { type: 'text', readOnly: !isAdmin }, // Email
                    { type: 'text', readOnly: !isAdmin }, // Telefone
                    { type: 'text', readOnly: !isAdmin }, // CPF/CNPJ
                    {
                        type: 'dropdown',
                        source: [true, false],
                        readOnly: !isAdmin,
                        renderer: function(instance, td, row, col, prop, value) {
                            Handsontable.renderers.DropdownRenderer.apply(this, arguments);
                            if (value === true || value === 'true') {
                                td.style.backgroundColor = '#dcfce7';
                                td.style.color = '#166534';
                                td.textContent = 'Ativo';
                            } else {
                                td.style.backgroundColor = '#fef2f2';
                                td.style.color = '#dc2626';
                                td.textContent = 'Inativo';
                            }
                        }
                    }, // Status
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            const proprietarioId = instance.getDataAtRow(row)[0];
                            if (isAdmin) {
                                td.innerHTML = `
                                    <button class="text-red-600 hover:text-red-800 text-sm" onclick="proprietariosManager.deleteProprietario(${proprietarioId})">
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
                    if (source === 'edit' && isAdmin) {
                        this.handleCellChange(changes);
                    }
                },
                afterColumnSort: (currentSortConfig, destinationSortConfigs) => {
                    this.saveSortConfig(currentSortConfig);
                },
                cells: function(row, col) {
                    const cellProperties = {};
                    if (!isAdmin && col !== 0 && col !== 6) {
                        cellProperties.className = 'htDimmed';
                    }
                    return cellProperties;
                }
            });

        } catch (error) {
            console.error('Erro ao carregar proprietários:', error);
        }
    }

    async handleCellChange(changes) {
        if (!changes) return;

        for (const change of changes) {
            const [row, col, oldValue, newValue] = change;
            
            if (oldValue === newValue) continue;

            const rowData = this.proprietariosTable.getDataAtRow(row);
            const proprietarioId = rowData[0];
            
            // Mapeamento de colunas
            const columnMap = {
                1: 'nome',
                2: 'email',
                3: 'telefone',
                4: 'cpf_cnpj',
                5: 'ativo'
            };

            const fieldName = columnMap[col];
            if (!fieldName) continue;

            // Encontrar o proprietário original
            const originalProprietario = this.proprietariosData.find(p => p.id === proprietarioId);
            if (!originalProprietario) continue;

            // Preparar dados para atualização
            const updatedData = {
                nome: rowData[1],
                email: rowData[2],
                telefone: rowData[3] || '',
                cpf_cnpj: rowData[4] || '',
                ativo: rowData[5] === true || rowData[5] === 'true',
                papel: originalProprietario.papel,
                // Preservar senha se não for alterada
                senha: originalProprietario.senha || 'sem_alteracao'
            };

            try {
                // Feedback visual: célula amarela (salvando)
                const cell = this.proprietariosTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fef3c7';
                }

                // Salvar no backend
                await this.apiClient.put(`/api/usuarios/${proprietarioId}/`, updatedData);

                // Feedback visual: célula verde (sucesso)
                if (cell) {
                    cell.style.backgroundColor = '#dcfce7';
                    setTimeout(() => {
                        cell.style.backgroundColor = '';
                    }, 2000);
                }

                // Atualizar dados originais
                Object.assign(originalProprietario, updatedData);

                console.log(`✓ Proprietário ${proprietarioId} atualizado: ${fieldName} = ${newValue}`);

            } catch (error) {
                console.error('Erro ao atualizar proprietário:', error);
                
                // Feedback visual: célula vermelha (erro)
                const cell = this.proprietariosTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fee2e2';
                }

                // Reverter valor
                this.proprietariosTable.setDataAtCell(row, col, oldValue, 'revert');

                utils.showAlert('Erro ao salvar alteração. Tente novamente.', 'error');
            }
        }
    }

    clearFilters() {
        // Limpar os campos de filtro
        document.getElementById('search-nome').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-data-criacao-de').value = '';
        document.getElementById('filter-data-criacao-ate').value = '';
        
        // Limpar localStorage
        localStorage.removeItem('proprietarios_filters');
        
        // Recarregar todos os dados
        this.loadProprietarios();
    }

    saveFilters() {
        const filters = {
            nome: document.getElementById('search-nome').value,
            status: document.getElementById('filter-status').value,
            dataCriacaoDe: document.getElementById('filter-data-criacao-de').value,
            dataCriacaoAte: document.getElementById('filter-data-criacao-ate').value
        };
        
        localStorage.setItem('proprietarios_filters', JSON.stringify(filters));
    }

    loadSavedFilters() {
        const saved = localStorage.getItem('proprietarios_filters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                
                if (filters.nome) {
                    document.getElementById('search-nome').value = filters.nome;
                }
                if (filters.status) {
                    document.getElementById('filter-status').value = filters.status;
                }
                if (filters.dataCriacaoDe) {
                    document.getElementById('filter-data-criacao-de').value = filters.dataCriacaoDe;
                }
                if (filters.dataCriacaoAte) {
                    document.getElementById('filter-data-criacao-ate').value = filters.dataCriacaoAte;
                }
                
                // Aplicar filtros salvos
                if (filters.nome || filters.status || filters.dataCriacaoDe || filters.dataCriacaoAte) {
                    this.searchProprietarios();
                }
            } catch (error) {
                console.error('Erro ao carregar filtros salvos:', error);
            }
        }
    }

    async searchProprietarios() {
        const nome = document.getElementById('search-nome').value;
        const status = document.getElementById('filter-status').value;
        const dataCriacaoDe = document.getElementById('filter-data-criacao-de').value;
        const dataCriacaoAte = document.getElementById('filter-data-criacao-ate').value;

        let url = '/usuarios?role=proprietario';
        if (nome) url += `&nome=${encodeURIComponent(nome)}`;
        if (status && status !== '') url += `&ativo=${status === 'ativo'}`;
        if (dataCriacaoDe) url += `&created_at_de=${dataCriacaoDe}`;
        if (dataCriacaoAte) url += `&created_at_ate=${dataCriacaoAte}`;

        try {
            const proprietarios = await this.apiClient.get(url.replace('/usuarios', '/api/usuarios/'));
            this.updateTable(proprietarios);
        } catch (error) {
            console.error('Erro ao buscar proprietários:', error);
        }
    }

    updateTable(proprietarios) {
        // Atualizar dados originais
        this.proprietariosData = proprietarios;

        const data = proprietarios.map(prop => [
            prop.id,
            prop.nome,
            prop.email,
            prop.telefone || '',
            prop.cpf_cnpj || '',
            prop.ativo,
            'Ações'
        ]);

        this.proprietariosTable.loadData(data);
    }

    showModal(proprietario = null) {
        this.currentProprietario = proprietario;
        const modal = document.getElementById('proprietario-modal');
        const form = document.getElementById('proprietario-form');
        const title = document.getElementById('modal-title');

        if (proprietario) {
            title.textContent = 'Editar Proprietário';
            form['id'].value = proprietario.id;
            form['nome'].value = proprietario.nome;
            form['email'].value = proprietario.email;
            form['telefone'].value = proprietario.telefone || '';
            form['endereco'].value = proprietario.endereco || '';
            form['banco'].value = proprietario.banco || '';
            form['agencia'].value = proprietario.agencia || '';
            form['conta'].value = proprietario.conta || '';
            form['pix'].value = proprietario.pix || '';
            form['ativo'].checked = proprietario.ativo;
        } else {
            title.textContent = 'Novo Proprietário';
            form.reset();
            form['id'].value = '';
        }

        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('proprietario-modal').classList.add('hidden');
        this.currentProprietario = null;
    }

    async saveProprietario(event) {
        event.preventDefault();

        const form = document.getElementById('proprietario-form');
        const formData = new FormData(form);

        const proprietarioData = {
            nome: formData.get('nome'),
            tipo: 'usuario',
            email: formData.get('email'),
            telefone: formData.get('telefone'),
            ativo: form['ativo'].checked
        };

        try {
            if (this.currentProprietario) {
                await this.apiClient.put(`/api/usuarios/${this.currentProprietario.id}/`, proprietarioData);
            } else {
                await this.apiClient.post('/api/usuarios/', proprietarioData);
            }

            this.hideModal();
            await this.loadProprietarios();
            alert('Proprietário salvo com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar proprietário:', error);
            alert('Erro ao salvar proprietário. Tente novamente.');
        }
    }

    async editProprietario(id) {
        try {
            const proprietario = await this.apiClient.get(`/api/usuarios/${id}/`);
            this.showModal(proprietario);
        } catch (error) {
            console.error('Erro ao carregar proprietário:', error);
        }
    }

    async deleteProprietario(id) {
        if (!confirm('Tem certeza que deseja excluir este proprietário?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/usuarios/${id}/`);
            await this.loadProprietarios();
            alert('Proprietário excluído com sucesso!');
        } catch (error) {
            console.error('Erro ao excluir proprietário:', error);
            alert('Erro ao excluir proprietário. Tente novamente.');
        }
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
            const nome = document.getElementById('search-nome').value.trim();
            const status = document.getElementById('filter-status').value;
            
            // Construir parâmetros da URL
            const params = new URLSearchParams();
            if (nome) params.append('q', nome);
            if (status && status !== '') params.append('status', status === 'ativo' ? 'Ativo' : 'Inativo');
            params.append('format', format);
            
            // Fazer download
            const url = `/api/usuarios/export?${params.toString()}`;
            const link = document.createElement('a');
            link.href = url;
            link.download = ''; // Deixar o servidor definir o nome
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            alert(`Exportação ${format.toUpperCase()} iniciada com sucesso!`);
            
        } catch (error) {
            console.error('Erro na exportação:', error);
            alert('Erro ao exportar dados');
        }
    }

    loadSortConfig() {
        try {
            const saved = localStorage.getItem('proprietarios_sort_config');
            return saved ? JSON.parse(saved) : undefined;
        } catch (error) {
            console.error('Erro ao carregar configuração de ordenação:', error);
            return undefined;
        }
    }

    saveSortConfig(config) {
        try {
            if (config && config.length > 0) {
                localStorage.setItem('proprietarios_sort_config', JSON.stringify(config));
            } else {
                localStorage.removeItem('proprietarios_sort_config');
            }
        } catch (error) {
            console.error('Erro ao salvar configuração de ordenação:', error);
        }
    }
}

// Instância global
let proprietariosManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    proprietariosManager = new ProprietariosManager();
});