// Imóveis JavaScript
class ImoveisManager {
    constructor() {
        this.apiClient = new ApiClient();
        this.imoveisTable = null;
        this.currentImovel = null;
        this.init();
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadImoveis();
        
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
        document.getElementById('add-imovel-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchImoveis());
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('imovel-form').addEventListener('submit', (e) => this.saveImovel(e));
        
        // Carregar filtros salvos
        this.loadSavedFilters();
        
        // Salvar filtros ao mudar
        document.getElementById('search-endereco').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-tipo').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-status').addEventListener('change', () => this.saveFilters());
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
                imovel.tipo,
                imovel.endereco,
                imovel.cidade,
                imovel.estado || '',
                imovel.status,
                imovel.valor_aluguel || 0,
                'Ações'
            ]);

            const isAdmin = this.apiClient.isAdmin();

            this.imoveisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Tipo', 'Endereço', 'Cidade', 'Estado', 'Status', 'Valor Aluguel (R$)', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true }, // ID
                    { 
                        type: 'dropdown',
                        source: ['casa', 'apartamento', 'comercial', 'terreno'],
                        readOnly: !isAdmin
                    }, // Tipo
                    { type: 'text', readOnly: !isAdmin }, // Endereço
                    { type: 'text', readOnly: !isAdmin }, // Cidade
                    { type: 'text', readOnly: !isAdmin }, // Estado
                    {
                        type: 'dropdown',
                        source: ['disponivel', 'alugado', 'manutencao'],
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
                            } else if (value === 'manutencao') {
                                td.style.backgroundColor = '#fef3c7';
                                td.style.color = '#92400e';
                                td.textContent = 'Manutenção';
                            }
                        }
                    }, // Status
                    { 
                        type: 'numeric',
                        numericFormat: { pattern: '0,0.00' },
                        readOnly: !isAdmin
                    }, // Valor Aluguel
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
                afterChange: (changes, source) => {
                    if (source === 'edit' && isAdmin) {
                        this.handleCellChange(changes);
                    }
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
            
            // Mapeamento de colunas
            const columnMap = {
                1: 'tipo',
                2: 'endereco',
                3: 'cidade',
                4: 'estado',
                5: 'status',
                6: 'valor_aluguel'
            };

            const fieldName = columnMap[col];
            if (!fieldName) continue;

            // Encontrar o imóvel original
            const originalImovel = this.imoveisData.find(i => i.id === imovelId);
            if (!originalImovel) continue;

            // Preparar dados para atualização
            const updatedData = {
                tipo: rowData[1],
                endereco: rowData[2],
                cidade: rowData[3],
                estado: rowData[4],
                cep: originalImovel.cep || '',
                status: rowData[5],
                area: originalImovel.area,
                quartos: originalImovel.quartos,
                banheiros: originalImovel.banheiros,
                vagas_garagem: originalImovel.vagas_garagem,
                valor_aluguel: parseFloat(rowData[6]) || 0,
                valor_venda: originalImovel.valor_venda,
                descricao: originalImovel.descricao || ''
            };

            try {
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
                    setTimeout(() => {
                        cell.style.backgroundColor = '';
                    }, 2000);
                }

                // Atualizar dados originais
                Object.assign(originalImovel, updatedData);

                console.log(`✓ Imóvel ${imovelId} atualizado: ${fieldName} = ${newValue}`);

            } catch (error) {
                console.error('Erro ao atualizar imóvel:', error);
                
                // Feedback visual: célula vermelha (erro)
                const cell = this.imoveisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fee2e2';
                }

                // Reverter valor
                this.imoveisTable.setDataAtCell(row, col, oldValue, 'revert');

                utils.showAlert('Erro ao salvar alteração. Tente novamente.', 'error');
            }
        }
    }

    clearFilters() {
        // Limpar os campos de filtro
        document.getElementById('search-endereco').value = '';
        document.getElementById('filter-tipo').value = '';
        document.getElementById('filter-status').value = '';
        
        // Limpar localStorage
        localStorage.removeItem('imoveis_filters');
        
        // Recarregar todos os dados
        this.loadImoveis();
    }

    saveFilters() {
        const filters = {
            endereco: document.getElementById('search-endereco').value,
            tipo: document.getElementById('filter-tipo').value,
            status: document.getElementById('filter-status').value
        };
        
        localStorage.setItem('imoveis_filters', JSON.stringify(filters));
    }

    loadSavedFilters() {
        const saved = localStorage.getItem('imoveis_filters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                
                if (filters.endereco) {
                    document.getElementById('search-endereco').value = filters.endereco;
                }
                if (filters.tipo) {
                    document.getElementById('filter-tipo').value = filters.tipo;
                }
                if (filters.status) {
                    document.getElementById('filter-status').value = filters.status;
                }
                
                // Aplicar filtros salvos
                if (filters.endereco || filters.tipo || filters.status) {
                    this.searchImoveis();
                }
            } catch (error) {
                console.error('Erro ao carregar filtros salvos:', error);
            }
        }
    }

    async searchImoveis() {
        const endereco = document.getElementById('search-endereco').value;
        const tipo = document.getElementById('filter-tipo').value;
        const status = document.getElementById('filter-status').value;

        let url = '/imoveis?';
        const params = [];
        if (endereco) params.push(`endereco=${encodeURIComponent(endereco)}`);
        if (tipo && tipo !== '') params.push(`tipo=${tipo}`);
        if (status && status !== '') params.push(`status=${status}`);

        url += params.join('&');

        try {
            const imoveis = await this.apiClient.get(url);
            this.updateTable(imoveis);
        } catch (error) {
            console.error('Erro ao buscar imóveis:', error);
        }
    }

    updateTable(imoveis) {
        // Atualizar dados originais
        this.imoveisData = imoveis;

        const data = imoveis.map(imovel => [
            imovel.id,
            imovel.tipo,
            imovel.endereco,
            imovel.cidade,
            imovel.estado || '',
            imovel.status,
            imovel.valor_aluguel || 0,
            'Ações'
        ]);

        this.imoveisTable.loadData(data);
    }

    showModal(imovel = null) {
        this.currentImovel = imovel;
        const modal = document.getElementById('imovel-modal');
        const form = document.getElementById('imovel-form');
        const title = document.getElementById('modal-title');

        if (imovel) {
            title.textContent = 'Editar Imóvel';
            form['id'].value = imovel.id;
            form['tipo'].value = imovel.tipo;
            form['status'].value = imovel.status;
            form['endereco'].value = imovel.endereco;
            form['cidade'].value = imovel.cidade;
            form['estado'].value = imovel.estado;
            form['cep'].value = imovel.cep || '';
            form['area'].value = imovel.area || '';
            form['quartos'].value = imovel.quartos || '';
            form['banheiros'].value = imovel.banheiros || '';
            form['vagas_garagem'].value = imovel.vagas_garagem || '';
            form['valor_aluguel'].value = imovel.valor_aluguel || '';
            form['valor_venda'].value = imovel.valor_venda || '';
            form['descricao'].value = imovel.descricao || '';
        } else {
            title.textContent = 'Novo Imóvel';
            form.reset();
            form['id'].value = '';
        }

        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('imovel-modal').classList.add('hidden');
        this.currentImovel = null;
    }

    async saveImovel(event) {
        event.preventDefault();

        const form = document.getElementById('imovel-form');
        const formData = new FormData(form);

        const imovelData = {
            nome: `${formData.get('tipo')} - ${formData.get('endereco')}`.substring(0, 120),
            endereco: formData.get('endereco'),
            alugado: formData.get('status') === 'alugado',
            ativo: true
        };

        try {
            if (this.currentImovel) {
                await this.apiClient.put(`/api/imoveis/${this.currentImovel.id}/`, imovelData);
            } else {
                await this.apiClient.post('/api/imoveis/', imovelData);
            }

            this.hideModal();
            await this.loadImoveis();
            alert('Imóvel salvo com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar imóvel:', error);
            alert('Erro ao salvar imóvel. Tente novamente.');
        }
    }

    async editImovel(id) {
        try {
            const imovel = await this.apiClient.get(`/imoveis/${id}`);
            this.showModal(imovel);
        } catch (error) {
            console.error('Erro ao carregar imóvel:', error);
        }
    }

    async deleteImovel(id) {
        if (!confirm('Tem certeza que deseja excluir este imóvel?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/imoveis/${id}/`);
            await this.loadImoveis();
            alert('Imóvel excluído com sucesso!');
        } catch (error) {
            console.error('Erro ao excluir imóvel:', error);
            alert('Erro ao excluir imóvel. Tente novamente.');
        }
    }
}

// Instância global
let imoveisManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    imoveisManager = new ImoveisManager();
});