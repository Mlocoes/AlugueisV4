// Aluguéis JavaScript
class AlugueisManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.alugueisTable = null;
            this.init();
        } else {
            // Aguardar o evento apiReady ou verificar periodicamente
            const checkApiReady = () => {
                if (window.apiClient) {
                    this.apiClient = window.apiClient;
                    this.alugueisTable = null;
                    this.init();
                } else {
                    setTimeout(checkApiReady, 100);
                }
            };
            checkApiReady();
        }
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadData();
        // Obter permissões do usuário para controlar permissões por proprietário
        this.permissions = await this.apiClient.getMyPermissions();
        
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
        document.getElementById('add-aluguel-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchAlugueis());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('aluguel-form').addEventListener('submit', (e) => this.saveAluguel(e));
        
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
        
        // Filtros
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        this.loadSavedFilters();
        document.getElementById('filter-imovel').addEventListener('change', () => {
            this.saveFilters();
            this.searchAlugueis();
        });
        document.getElementById('filter-mes').addEventListener('change', () => {
            this.saveFilters();
            this.searchAlugueis();
        });
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    async loadData() {
        // Carregar dependências primeiro
        await Promise.all([
            this.loadImoveis(),
            this.loadProprietarios()
        ]);
        
        // Depois carregar aluguéis (que depende dos dados acima)
        await this.loadAlugueis();
    }

    async loadImoveis() {
        try {
            this.imoveis = await this.apiClient.get('/api/imoveis/');
            this.populateImovelSelect();
        } catch (error) {
            console.error('Erro ao carregar imóveis:', error);
        }
    }

    async loadProprietarios() {
        try {
            this.proprietarios = await this.apiClient.get('/api/usuarios/');
            // Incluir proprietários e usuários (que podem ser proprietários)
            this.proprietarios = this.proprietarios.filter(u => u.tipo === 'proprietario' || u.tipo === 'usuario');
        } catch (error) {
            console.error('Erro ao carregar proprietários:', error);
            this.proprietarios = [];
        }
    }

    populateImovelSelect() {
        const select = document.getElementById('imovel_id');
        select.innerHTML = '<option value="">Selecione um imóvel...</option>';
        this.imoveis.forEach(imovel => {
            const option = document.createElement('option');
            option.value = imovel.id;
            option.textContent = `${imovel.endereco} - ${imovel.cidade}`;
            select.appendChild(option);
        });

        // Também popular o filtro
        const filterSelect = document.getElementById('filter-imovel');
        filterSelect.innerHTML = '<option value="">Todos os imóveis</option>';
        this.imoveis.forEach(imovel => {
            const option = document.createElement('option');
            option.value = imovel.id;
            option.textContent = `${imovel.endereco} - ${imovel.cidade}`;
            filterSelect.appendChild(option);
        });
    }

    async loadAlugueis() {
        try {
            const alugueis = await this.apiClient.get('/api/alugueis/mensais/');
            
            // Armazenar dados originais
            this.alugueisData = alugueis;

            const container = document.getElementById('alugueis-table');

            if (this.alugueisTable) {
                this.alugueisTable.destroy();
            }

            const data = alugueis.map(aluguel => {
                const imovel = this.imoveis.find(i => i.id === aluguel.id_imovel);
                const proprietario = this.proprietarios.find(p => p.id === aluguel.id_proprietario);

                return [
                    aluguel.id,
                    imovel ? `${imovel.endereco}` : 'N/A',
                    proprietario ? proprietario.nome : `Proprietário ${aluguel.id_proprietario}`,
                    aluguel.data_referencia,
                    aluguel.valor_total,
                    aluguel.valor_proprietario,
                    aluguel.taxa_administracao,
                    'Ações'
                ];
            });

            const isAdmin = this.apiClient.isAdmin();
            const canEditSet = new Set((this.permissions && this.permissions.editar) || []);
            this.alugueisTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Imóvel', 'Proprietário', 'Data Ref.', 'Valor Total', 'Valor Prop.', 'Taxa Admin', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true }, // ID
                    { type: 'text', readOnly: true }, // Imóvel (não editável)
                    { type: 'text', readOnly: !isAdmin }, // Proprietário
                    {
                        type: 'date',
                        dateFormat: 'YYYY-MM-DD',
                        readOnly: !isAdmin
                    }, // Data Referência
                    {
                        type: 'numeric',
                        readOnly: !isAdmin,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            if (value !== null && value !== undefined && value !== '') {
                                td.innerHTML = utils.formatCurrency(value);
                            } else {
                                td.innerHTML = '';
                            }
                            return td;
                        }
                    }, // Valor Total
                    {
                        type: 'numeric',
                        readOnly: !isAdmin,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            if (value !== null && value !== undefined && value !== '') {
                                td.innerHTML = utils.formatCurrency(value);
                            } else {
                                td.innerHTML = '';
                            }
                            return td;
                        }
                    }, // Valor Proprietário
                    {
                        type: 'numeric',
                        readOnly: !isAdmin,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            if (value !== null && value !== undefined && value !== '') {
                                td.innerHTML = utils.formatCurrency(value);
                            } else {
                                td.innerHTML = '';
                                return td;
                            }
                        }
                    }, // Taxa Administração
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                                const rowData = instance.getDataAtRow(row);
                                const aluguelId = rowData[0];
                                const proprietarioId = rowData[2] && typeof rowData[2] === 'number' ? rowData[2] : null;
                                // proprietarioId may not be numeric in this table; fall back to lookup in manager
                                let ownerId = proprietarioId;
                                if (!ownerId) {
                                    const aluguel = alugueisManager.alugueisData.find(a => a.id === aluguelId);
                                    ownerId = aluguel ? aluguel.id_proprietario : null;
                                }

                                const canEdit = isAdmin || (ownerId !== null && canEditSet.has(ownerId));
                                if (canEdit) {
                                    td.innerHTML = `
                                        <button class="text-red-600 hover:text-red-800 text-sm" onclick="alugueisManager.deleteAluguel(${aluguelId})">
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
                    // Controlar readOnly por célula com base em permissão por proprietário
                    cells: function(row, col) {
                        const cellProperties = {};
                        // Colunas editáveis são 2..7 (exceto ID coluna 0)
                        if (!isAdmin && col >= 2 && col <= 7) {
                            const rowData = this.instance.getDataAtRow(row);
                            let ownerId = null;
                            if (rowData) {
                                const aluguelId = rowData[0];
                                const aluguel = alugueisManager.alugueisData.find(a => a.id === aluguelId);
                                if (aluguel) ownerId = aluguel.id_proprietario;
                            }
                            const canEdit = ownerId !== null && canEditSet.has(ownerId);
                            if (!canEdit) {
                                cellProperties.readOnly = true;
                                cellProperties.className = (cellProperties.className || '') + ' htDimmed';
                            }
                        }
                        return cellProperties;
                    }
            });

        } catch (error) {
            console.error('Erro ao carregar aluguéis:', error);
        }
    }

    async handleCellChange(changes) {
        if (!changes) return;

        for (const change of changes) {
            const [row, col, oldValue, newValue] = change;
            
            if (oldValue === newValue) continue;

            const rowData = this.alugueisTable.getDataAtRow(row);
            const aluguelId = rowData[0];
            
            // Mapeamento de colunas
            const columnMap = {
                2: 'inquilino_nome',
                3: 'valor_aluguel',
                4: 'dia_vencimento',
                5: 'data_inicio',
                6: 'data_fim'
            };

            const fieldName = columnMap[col];
            if (!fieldName) continue;

            // Encontrar o aluguel original
            const originalAluguel = this.alugueisData.find(a => a.id === aluguelId);
            if (!originalAluguel) continue;

            // Preparar dados para atualização
            const updatedData = {
                imovel_id: originalAluguel.imovel_id,
                inquilino_nome: rowData[2],
                inquilino_cpf: originalAluguel.inquilino_cpf,
                inquilino_telefone: originalAluguel.inquilino_telefone || '',
                inquilino_email: originalAluguel.inquilino_email || '',
                valor_aluguel: parseFloat(rowData[3]) || 0,
                dia_vencimento: parseInt(rowData[4]) || 1,
                data_inicio: rowData[5],
                data_fim: rowData[6] || null,
                observacoes: originalAluguel.observacoes || ''
            };

            try {
                // Feedback visual: célula amarela (salvando)
                const cell = this.alugueisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fef3c7';
                }

                // Salvar no backend
                await this.apiClient.put(`/api/alugueis/mensais/${aluguelId}`, updatedData);

                // Feedback visual: célula verde (sucesso)
                if (cell) {
                    cell.style.backgroundColor = '#dcfce7';
                    setTimeout(() => {
                        cell.style.backgroundColor = '';
                    }, 2000);
                }

                // Atualizar dados originais
                Object.assign(originalAluguel, updatedData);

                console.log(`✓ Aluguel ${aluguelId} atualizado: ${fieldName} = ${newValue}`);

            } catch (error) {
                console.error('Erro ao atualizar aluguel:', error);
                
                // Feedback visual: célula vermelha (erro)
                const cell = this.alugueisTable.getCell(row, col);
                if (cell) {
                    cell.style.backgroundColor = '#fee2e2';
                }

                // Reverter valor
                this.alugueisTable.setDataAtCell(row, col, oldValue, 'revert');

                utils.showAlert('Erro ao salvar alteração. Tente novamente.', 'error');
            }
        }
    }

    clearFilters() {
        // Limpar os campos de filtro
        document.getElementById('filter-imovel').value = '';
        document.getElementById('filter-status').value = '';
        document.getElementById('filter-mes').value = '';
        document.getElementById('filter-data-inicio-de').value = '';
        document.getElementById('filter-data-inicio-ate').value = '';
        
        // Limpar localStorage
        localStorage.removeItem('alugueis_filters');
        
        // Recarregar todos os dados
        this.loadAlugueis();
    }

    saveFilters() {
        const filters = {
            imovel: document.getElementById('filter-imovel').value,
            mes: document.getElementById('filter-mes').value,
            dataInicioDe: document.getElementById('filter-data-inicio-de').value,
            dataInicioAte: document.getElementById('filter-data-inicio-ate').value
        };
        
        localStorage.setItem('alugueis_filters', JSON.stringify(filters));
    }

    loadSavedFilters() {
        const saved = localStorage.getItem('alugueis_filters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                
                if (filters.imovel) {
                    document.getElementById('filter-imovel').value = filters.imovel;
                }
                if (filters.mes) {
                    document.getElementById('filter-mes').value = filters.mes;
                }
                if (filters.dataInicioDe) {
                    document.getElementById('filter-data-inicio-de').value = filters.dataInicioDe;
                }
                if (filters.dataInicioAte) {
                    document.getElementById('filter-data-inicio-ate').value = filters.dataInicioAte;
                }
                
                // Aplicar filtros salvos
                if (filters.imovel || filters.mes || filters.dataInicioDe || filters.dataInicioAte) {
                    this.searchAlugueis();
                }
            } catch (error) {
                console.error('Erro ao carregar filtros salvos:', error);
            }
        }
    }

    async searchAlugueis() {
        // Garantir que a tabela esteja inicializada
        if (!this.alugueisTable) {
            console.log('Tabela não inicializada, carregando dados primeiro...');
            await this.loadAlugueis();
            return;
        }

        const imovelId = document.getElementById('filter-imovel').value;
        const mes = document.getElementById('filter-mes').value;
        const dataInicioDe = document.getElementById('filter-data-inicio-de').value;
        const dataInicioAte = document.getElementById('filter-data-inicio-ate').value;

        let url = '/api/alugueis/mensais/?';
        const params = [];
        if (imovelId) params.push(`imovel_id=${imovelId}`);
        if (mes) {
            // Parse do formato YYYY-MM para ano e mes separados
            const [ano, mesNum] = mes.split('-');
            params.push(`ano=${ano}`);
            params.push(`mes=${mesNum}`);
        }
        if (dataInicioDe) params.push(`data_inicio_de=${dataInicioDe}`);
        if (dataInicioAte) params.push(`data_inicio_ate=${dataInicioAte}`);

        url += params.join('&');

        try {
            const alugueis = await this.apiClient.get(url);
            this.updateTable(alugueis);
        } catch (error) {
            console.error('Erro ao buscar aluguéis:', error);
        }
    }

    updateTable(alugueis) {
        if (!this.alugueisTable) {
            console.error('Tabela não inicializada. Tentando inicializar...');
            return;
        }

        const data = alugueis.map(aluguel => {
            const imovel = this.imoveis.find(i => i.id === aluguel.id_imovel);
            const proprietario = this.proprietarios.find(p => p.id === aluguel.id_proprietario);

            return [
                aluguel.id,
                imovel ? `${imovel.endereco}` : 'N/A',
                proprietario ? proprietario.nome : `Proprietário ${aluguel.id_proprietario}`,
                aluguel.data_referencia,
                aluguel.valor_total,
                aluguel.valor_proprietario,
                aluguel.taxa_administracao,
                'Ações'
            ];
        });

        this.alugueisTable.loadData(data);
    }

    showModal(aluguel = null) {
        this.currentAluguel = aluguel;
        const modal = document.getElementById('aluguel-modal');
        const form = document.getElementById('aluguel-form');
        const title = document.getElementById('modal-title');

        if (aluguel) {
            title.textContent = 'Editar Aluguel';
            form['id'].value = aluguel.id;
            form['imovel_id'].value = aluguel.imovel_id;
            form['inquilino_nome'].value = aluguel.inquilino_nome;
            form['inquilino_email'].value = aluguel.inquilino_email || '';
            form['inquilino_telefone'].value = aluguel.inquilino_telefone || '';
            form['valor_aluguel'].value = aluguel.valor_aluguel;
            form['dia_vencimento'].value = aluguel.dia_vencimento;
            form['data_inicio'].value = new Date(aluguel.data_inicio).toISOString().split('T')[0];
            form['data_fim'].value = aluguel.data_fim ? new Date(aluguel.data_fim).toISOString().split('T')[0] : '';
            form['taxa_administracao'].value = aluguel.taxa_administracao || '';
            form['observacoes'].value = aluguel.observacoes || '';
        } else {
            title.textContent = 'Novo Aluguel';
            form.reset();
            form['id'].value = '';
        }

        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('aluguel-modal').classList.add('hidden');
        this.currentAluguel = null;
    }

    async saveAluguel(event) {
        event.preventDefault();

        const form = document.getElementById('aluguel-form');
        const formData = new FormData(form);

        const aluguelData = {
            id_imovel: parseInt(formData.get('imovel_id')),
            id_proprietario: parseInt(formData.get('proprietario_id')),
            aluguel_liquido: parseFloat(formData.get('valor_aluguel')) || 0,
            taxa_administracao_total: parseFloat(formData.get('taxa_administracao')) || 0,
            darf: 0,
            data_cadastro: new Date().toISOString().split('T')[0] // Data atual no formato YYYY-MM-DD
        };

        try {
            if (this.currentAluguel) {
                // Para aluguéis mensais, edição pode não ser apropriada
                alert('Edição de aluguéis mensais não é suportada. Use exclusão se necessário.');
                return;
            } else {
                alert('Criação de aluguéis mensais deve ser feita via importação Excel.');
                return;
            }

            this.hideModal();
            await this.loadAlugueis();
            alert('Aluguel salvo com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar aluguel:', error);
            alert('Erro ao salvar aluguel. Tente novamente.');
        }
    }

    async editAluguel(id) {
        try {
            const aluguel = await this.apiClient.get(`/api/alugueis/mensais/${id}`);
            this.showModal(aluguel);
        } catch (error) {
            console.error('Erro ao carregar aluguel:', error);
        }
    }

    async deleteAluguel(id) {
        if (!confirm('Tem certeza que deseja excluir este aluguel?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/alugueis/mensais/${id}`);
            await this.loadAlugueis();
            alert('Aluguel excluído com sucesso!');
        } catch (error) {
            console.error('Erro ao excluir aluguel:', error);
            alert('Erro ao excluir aluguel. Tente novamente.');
        }
    }

    toggleExportDropdown(event) {
        event.stopPropagation();
        const dropdown = document.getElementById('export-dropdown');
        dropdown.classList.toggle('hidden');
    }

    async exportData(event, format) {
        event.stopPropagation();

        // Fechar dropdown
        document.getElementById('export-dropdown').classList.add('hidden');
        
        try {
            // Obter filtros atuais
            const imovel = document.getElementById('filter-imovel').value;
            const status = document.getElementById('filter-status').value;
            const mes = document.getElementById('filter-mes').value;
            const dataInicioDe = document.getElementById('filter-data-inicio-de').value;
            const dataInicioAte = document.getElementById('filter-data-inicio-ate').value;
            
            // Construir parâmetros da URL
            const params = new URLSearchParams();
            if (imovel) params.append('imovel', imovel);
            if (status && status !== '') params.append('status', status);
            if (mes) params.append('mes', mes);
            if (dataInicioDe) params.append('data_inicio_de', dataInicioDe);
            if (dataInicioAte) params.append('data_inicio_ate', dataInicioAte);
            params.append('format', format);
            
            // Fazer download
            const url = `/api/alugueis/export?${params.toString()}`;
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
            const saved = localStorage.getItem('alugueis_sort_config');
            return saved ? JSON.parse(saved) : undefined;
        } catch (error) {
            console.error('Erro ao carregar configuração de ordenação:', error);
            return undefined;
        }
    }

    saveSortConfig(config) {
        try {
            if (config && config.length > 0) {
                localStorage.setItem('alugueis_sort_config', JSON.stringify(config));
            } else {
                localStorage.removeItem('alugueis_sort_config');
            }
        } catch (error) {
            console.error('Erro ao salvar configuração de ordenação:', error);
        }
    }
}

// Instância global
let alugueisManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    alugueisManager = new AlugueisManager();
});