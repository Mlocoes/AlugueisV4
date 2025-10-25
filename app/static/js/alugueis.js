// Aluguéis JavaScript
class AlugueisManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.alugueisTable = null;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.alugueisTable = null;
                this.init();
            });
        }
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        await this.loadData();
        
        // Controle de acesso baseado em papel
        utils.hideElementsForNonAdmin(this.apiClient);
        utils.showUserInfo(this.apiClient);
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
        document.getElementById('add-aluguel-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchAlugueis());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('aluguel-form').addEventListener('submit', (e) => this.saveAluguel(e));
        
        // Event listeners para filtros
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        this.loadSavedFilters();
        document.getElementById('filter-imovel').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-mes').addEventListener('change', () => this.saveFilters());
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
                            const aluguelId = instance.getDataAtRow(row)[0];
                            if (isAdmin) {
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
                afterChange: (changes, source) => {
                    if (source === 'edit' && isAdmin) {
                        this.handleCellChange(changes);
                    }
                },
                cells: function(row, col) {
                    const cellProperties = {};
                    if (!isAdmin && col !== 0 && col !== 1 && col !== 6) {
                        cellProperties.className = 'htDimmed';
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
        
        // Limpar localStorage
        localStorage.removeItem('alugueis_filters');
        
        // Recarregar todos os dados
        this.loadAlugueis();
    }

    saveFilters() {
        const filters = {
            imovel: document.getElementById('filter-imovel').value,
            mes: document.getElementById('filter-mes').value
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
                
                // Aplicar filtros salvos
                if (filters.imovel || filters.mes) {
                    this.searchAlugueis();
                }
            } catch (error) {
                console.error('Erro ao carregar filtros salvos:', error);
            }
        }
    }

    async searchAlugueis() {
        const imovelId = document.getElementById('filter-imovel').value;
        const mes = document.getElementById('filter-mes').value;

        let url = '/alugueis?';
        const params = [];
        if (imovelId) params.push(`imovel_id=${imovelId}`);
        if (mes) params.push(`mes_referencia=${mes}`);

        url += params.join('&');

        try {
            const alugueis = await this.apiClient.get(url.replace('/alugueis', '/api/alugueis'));
            this.updateTable(alugueis);
        } catch (error) {
            console.error('Erro ao buscar aluguéis:', error);
        }
    }

    updateTable(alugueis) {
        const data = alugueis.map(aluguel => {
            const imovel = this.imoveis.find(i => i.id === aluguel.imovel_id);

            return [
                aluguel.id,
                imovel ? `${imovel.endereco} - ${imovel.cidade}` : 'N/A',
                aluguel.inquilino_nome,
                `R$ ${aluguel.valor_aluguel.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`,
                aluguel.dia_vencimento,
                new Date(aluguel.data_inicio).toLocaleDateString('pt-BR'),
                aluguel.data_fim ? new Date(aluguel.data_fim).toLocaleDateString('pt-BR') : 'N/A',
                'Editar | Excluir'
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
}

// Instância global
let alugueisManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    alugueisManager = new AlugueisManager();
});