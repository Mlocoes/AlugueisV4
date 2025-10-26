// Participações JavaScript
class ParticipacoesManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.participacoesTable = null;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.participacoesTable = null;
                this.init();
            });
        }
    }

    async init() {
        await this.checkAuth();
        await this.loadData();
        // Obter permissões do usuário para controlar ações por proprietário
        this.permissions = await this.apiClient.getMyPermissions();
        this.setupEventListeners();
        
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
                formData.append('password', 'admin123');

                const response = await this.apiClient.login('admin', 'admin123');
                console.log('Login automático bem-sucedido');
                await this.apiClient.getCurrentUser();
            } catch (loginError) {
                console.log('Erro no login automático, redirecionando para login');
                window.location.href = '/login';
            }
        }
    }

    setupEventListeners() {
        document.getElementById('logout-btn').addEventListener('click', () => this.logout());
        document.getElementById('add-participacao-btn').addEventListener('click', () => this.showModal());
        document.getElementById('search-btn').addEventListener('click', () => this.searchParticipacoes());
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('cancel-btn').addEventListener('click', () => this.hideModal());
        document.getElementById('participacao-form').addEventListener('submit', (e) => this.saveParticipacao(e));
        
        // Event listeners para filtros
        document.getElementById('clear-filters-btn').addEventListener('click', () => this.clearFilters());
        this.loadSavedFilters();
        document.getElementById('filter-imovel').addEventListener('change', () => this.saveFilters());
        document.getElementById('filter-proprietario').addEventListener('change', () => this.saveFilters());
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
        
        // Depois carregar participações (que depende dos dados acima)
        await this.loadParticipacoes();
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
            this.proprietarios = await this.apiClient.get('/api/usuarios/?role=proprietario');
            this.populateProprietarioSelect();
        } catch (error) {
            console.error('Erro ao carregar proprietários:', error);
        }
    }

    populateImovelSelect() {
        const selects = document.querySelectorAll('#imovel_id, #filter-imovel');
        selects.forEach(select => {
            select.innerHTML = '<option value="">Selecione um imóvel...</option>';
            this.imoveis.forEach(imovel => {
                const option = document.createElement('option');
                option.value = imovel.id;
                option.textContent = `${imovel.endereco} - ${imovel.cidade}`;
                select.appendChild(option);
            });
        });
    }

    populateProprietarioSelect() {
        const selects = document.querySelectorAll('#proprietario_id, #filter-proprietario');
        selects.forEach(select => {
            select.innerHTML = '<option value="">Selecione um proprietário...</option>';
            this.proprietarios.forEach(prop => {
                const option = document.createElement('option');
                option.value = prop.id;
                option.textContent = prop.nome;
                select.appendChild(option);
            });
        });
    }

    async loadParticipacoes() {
        try {
            const participacoes = await this.apiClient.get('/api/participacoes/');
            // armazenar dados originais para lookup de permissões
            this.participacoesData = participacoes;

            const container = document.getElementById('participacoes-table');

            if (this.participacoesTable) {
                this.participacoesTable.destroy();
            }

            const data = participacoes.map(part => {
                const imovel = this.imoveis.find(i => i.id === part.id_imovel);
                const proprietario = this.proprietarios.find(p => p.id === part.id_proprietario);

                return [
                    part.id,
                    imovel ? `${imovel.nome}` : 'N/A',
                    proprietario ? proprietario.nome : 'N/A',
                    `${part.participacao}%`,
                    new Date(part.data_cadastro).toLocaleDateString('pt-BR'),
                    'N/A', // Data fim não existe no modelo
                    'Ativo', // Status fixo por enquanto
                    'Editar | Excluir'
                ];
            });

            this.participacoesTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Imóvel', 'Proprietário', 'Participação', 'Data Cadastro', 'Data Fim', 'Status', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value) {
                            Handsontable.renderers.TextRenderer.apply(this, arguments);
                            if (value === 'Ativo') {
                                td.style.backgroundColor = '#dcfce7';
                                td.style.color = '#166534';
                            } else {
                                td.style.backgroundColor = '#fef2f2';
                                td.style.color = '#dc2626';
                            }
                        }
                    },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                                const participacaoId = instance.getDataAtRow(row)[0];
                                // Obter proprietario do registro para checar permissão
                                const part = participacoesManager.participacoesData ? participacoesManager.participacoesData.find(p => p.id === participacaoId) : null;
                                const ownerId = part ? part.id_proprietario : null;
                                const isAdmin = participacoesManager.apiClient.isAdmin();
                                const canEditSet = new Set((participacoesManager.permissions && participacoesManager.permissions.editar) || []);
                                const canEdit = isAdmin || (ownerId !== null && canEditSet.has(ownerId));
                                if (canEdit) {
                                    td.innerHTML = `
                                        <button class="text-blue-600 hover:text-blue-800 mr-2" onclick="participacoesManager.editParticipacao(${participacaoId})">Editar</button>
                                        <button class="text-red-600 hover:text-red-800" onclick="participacoesManager.deleteParticipacao(${participacaoId})">Excluir</button>
                                    `;
                                } else {
                                    td.innerHTML = '-';
                                }
                            }
                    }
                ],
                height: 500,
                readOnly: true,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation'
            });

        } catch (error) {
            console.error('Erro ao carregar participações:', error);
        }
    }

    clearFilters() {
        // Limpar os campos de filtro
        document.getElementById('filter-imovel').value = '';
        document.getElementById('filter-proprietario').value = '';
        
        // Limpar localStorage
        localStorage.removeItem('participacoes_filters');
        
        // Recarregar todos os dados
        this.loadParticipacoes();
    }

    saveFilters() {
        const filters = {
            imovel: document.getElementById('filter-imovel').value,
            proprietario: document.getElementById('filter-proprietario').value
        };
        
        localStorage.setItem('participacoes_filters', JSON.stringify(filters));
    }

    loadSavedFilters() {
        const saved = localStorage.getItem('participacoes_filters');
        if (saved) {
            try {
                const filters = JSON.parse(saved);
                
                if (filters.imovel) {
                    document.getElementById('filter-imovel').value = filters.imovel;
                }
                if (filters.proprietario) {
                    document.getElementById('filter-proprietario').value = filters.proprietario;
                }
                
                // Aplicar filtros salvos
                if (filters.imovel || filters.proprietario) {
                    this.searchParticipacoes();
                }
            } catch (error) {
                console.error('Erro ao carregar filtros salvos:', error);
            }
        }
    }

    async searchParticipacoes() {
        const imovelId = document.getElementById('filter-imovel').value;
        const proprietarioId = document.getElementById('filter-proprietario').value;

        let url = '/participacoes?';
        const params = [];
        if (imovelId) params.push(`imovel_id=${imovelId}`);
        if (proprietarioId) params.push(`proprietario_id=${proprietarioId}`);

        url += params.join('&');

        try {
            const participacoes = await this.apiClient.get(url.replace('/participacoes', '/api/participacoes/'));
            this.updateTable(participacoes);
        } catch (error) {
            console.error('Erro ao buscar participações:', error);
        }
    }

    updateTable(participacoes) {
        if (!this.participacoesTable) {
            console.warn('Tabela de participações ainda não foi inicializada');
            return;
        }
        // atualizar cache local
        this.participacoesData = participacoes;
        
        const data = participacoes.map(part => {
            const imovel = this.imoveis.find(i => i.id === part.id_imovel);
            const proprietario = this.proprietarios.find(p => p.id === part.id_proprietario);

            return [
                part.id,
                imovel ? `${imovel.nome}` : 'N/A',
                proprietario ? proprietario.nome : 'N/A',
                `${part.participacao}%`,
                new Date(part.data_cadastro).toLocaleDateString('pt-BR'),
                'N/A', // Data fim não existe no modelo
                'Ativo', // Status fixo por enquanto
                'Editar | Excluir'
            ];
        });

        this.participacoesTable.loadData(data);
    }

    showModal(participacao = null) {
        this.currentParticipacao = participacao;
        const modal = document.getElementById('participacao-modal');
        const form = document.getElementById('participacao-form');
        const title = document.getElementById('modal-title');

        if (participacao) {
            title.textContent = 'Editar Participação';
            form['id'].value = participacao.id;
            form['imovel_id'].value = participacao.id_imovel;
            form['proprietario_id'].value = participacao.id_proprietario;
            form['percentual'].value = participacao.participacao;
            form['data_cadastro'].value = new Date(participacao.data_cadastro).toISOString().split('T')[0];
        } else {
            title.textContent = 'Nova Participação';
            form.reset();
            form['id'].value = '';
            // Definir data atual como padrão
            form['data_cadastro'].value = new Date().toISOString().split('T')[0];
        }

        modal.classList.remove('hidden');
    }

    hideModal() {
        document.getElementById('participacao-modal').classList.add('hidden');
        this.currentParticipacao = null;
    }

    async saveParticipacao(event) {
        event.preventDefault();

        const form = document.getElementById('participacao-form');
        const formData = new FormData(form);

        const participacaoData = {
            id_imovel: parseInt(formData.get('imovel_id')),
            id_proprietario: parseInt(formData.get('proprietario_id')),
            participacao: parseFloat(formData.get('percentual')),
            data_cadastro: formData.get('data_cadastro') || new Date().toISOString().split('T')[0]
        };

        try {
            if (this.currentParticipacao) {
                await this.apiClient.put(`/api/participacoes/${this.currentParticipacao.id}/`, participacaoData);
            } else {
                await this.apiClient.post('/api/participacoes/', participacaoData);
            }

            this.hideModal();
            await this.loadParticipacoes();
            alert('Participação salva com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar participação:', error);
            alert('Erro ao salvar participação. Tente novamente.');
        }
    }

    async editParticipacao(id) {
        try {
            const participacao = await this.apiClient.get(`/api/participacoes/${id}/`);
            this.showModal(participacao);
        } catch (error) {
            console.error('Erro ao carregar participação:', error);
        }
    }

    async deleteParticipacao(id) {
        if (!confirm('Tem certeza que deseja excluir esta participação?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/participacoes/${id}/`);
            await this.loadParticipacoes();
            alert('Participação excluída com sucesso!');
        } catch (error) {
            console.error('Erro ao excluir participação:', error);
            alert('Erro ao excluir participação. Tente novamente.');
        }
    }
}

// Instância global
let participacoesManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    participacoesManager = new ParticipacoesManager();
});