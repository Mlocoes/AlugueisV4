// Administração JavaScript
class AdministracaoManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.usuariosTable = null;
            this.backupTable = null;
            this.currentUser = null;
            this.currentTab = 'usuarios';
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.usuariosTable = null;
                this.backupTable = null;
                this.currentUser = null;
                this.currentTab = 'usuarios';
                this.init();
            });
        }
    }

    async init() {
        await this.checkAuth();
        this.setupEventListeners();
        this.showTab('usuarios');
        
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

                    // Se a chamada não lançar exceção, consideramos o login bem-sucedido
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

        // Abas
        document.getElementById('tab-usuarios').addEventListener('click', () => this.showTab('usuarios'));
    document.getElementById('tab-permissoes').addEventListener('click', () => this.showTab('permissoes'));
        document.getElementById('tab-backup').addEventListener('click', () => this.showTab('backup'));
        document.getElementById('tab-config').addEventListener('click', () => this.showTab('config'));
        document.getElementById('tab-logs').addEventListener('click', () => this.showTab('logs'));

        // Usuários
        document.getElementById('add-user-btn').addEventListener('click', () => this.showUserModal());
    const addPermBtn = document.getElementById('add-perm-btn');
    if (addPermBtn) addPermBtn.addEventListener('click', () => this.showPermModal());

    // Perm modal listeners
    const closePermBtn = document.getElementById('close-perm-modal-btn');
    if (closePermBtn) closePermBtn.addEventListener('click', () => this.hidePermModal());
    const cancelPermBtn = document.getElementById('cancel-perm-btn');
    if (cancelPermBtn) cancelPermBtn.addEventListener('click', () => this.hidePermModal());
    document.getElementById('perm-form').addEventListener('submit', (e) => this.savePerm(e));

    // Autocomplete searches
    const userSearch = document.getElementById('perm-user-search');
    const userList = document.getElementById('perm-user-list');
    if (userSearch) userSearch.addEventListener('input', (e) => this.searchUsers(e.target.value, userList, 'perm-user-id', 'perm-user-search'));

    const propSearch = document.getElementById('perm-prop-search');
    const propList = document.getElementById('perm-prop-list');
    if (propSearch) propSearch.addEventListener('input', (e) => this.searchProprietarios(e.target.value, propList, 'perm-prop-id', 'perm-prop-search'));
        document.getElementById('close-user-modal-btn').addEventListener('click', () => this.hideUserModal());
        document.getElementById('cancel-user-btn').addEventListener('click', () => this.hideUserModal());
        document.getElementById('user-form').addEventListener('submit', (e) => this.saveUser(e));
        document.getElementById('user-change-password').addEventListener('change', (e) => this.togglePasswordFields(e.target.checked));

        // Backup
        document.getElementById('create-backup-btn').addEventListener('click', () => this.createBackup());
        document.getElementById('restore-backup-btn').addEventListener('click', () => this.restoreBackup());

        // Configurações
        document.getElementById('config-form').addEventListener('submit', (e) => this.saveConfig(e));

        // Logs
        document.getElementById('refresh-logs-btn').addEventListener('click', () => this.loadLogs());
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
    }

    async logout() {
        try {
            await this.apiClient.logout();
            window.location.href = '/login';
        } catch (error) {
            console.error('Erro ao fazer logout:', error);
        }
    }

    showTab(tabName) {
        this.currentTab = tabName;

        // Esconder todas as abas
        document.querySelectorAll('.tab-content').forEach(tab => tab.classList.add('hidden'));

        // Mostrar aba selecionada
        document.getElementById(`content-${tabName}`).classList.remove('hidden');

        // Atualizar estilos das abas
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-600');
            btn.classList.add('border-transparent', 'text-gray-500');
        });

        document.getElementById(`tab-${tabName}`).classList.remove('border-transparent', 'text-gray-500');
        document.getElementById(`tab-${tabName}`).classList.add('border-blue-500', 'text-blue-600');

        // Carregar dados da aba
        this.loadTabData(tabName);
    }

    async loadTabData(tabName) {
        switch (tabName) {
            case 'usuarios':
                await this.loadUsuarios();
                break;
            case 'permissoes':
                await this.loadPermissoes();
                break;
            case 'backup':
                await this.loadBackupHistory();
                break;
            case 'config':
                await this.loadConfig();
                break;
            case 'logs':
                await this.loadLogs();
                break;
        }
    }

    // Usuários
    async loadUsuarios() {
        try {
            const usuarios = await this.apiClient.get('/api/usuarios/');

            const container = document.getElementById('usuarios-table');

            if (this.usuariosTable) {
                this.usuariosTable.destroy();
            }

            const data = usuarios.map(user => [
                user.id,
                user.nome,
                user.email,
                user.role,
                user.ativo ? 'Ativo' : 'Inativo',
                'Editar | Excluir'
            ]);

            this.usuariosTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Nome', 'Email', 'Função', 'Status', 'Ações'],
                columns: [
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
                            const userId = instance.getDataAtRow(row)[0];
                            td.innerHTML = `
                                <button class="text-blue-600 hover:text-blue-800 mr-2" onclick="administracaoManager.editUser(${userId})">Editar</button>
                                <button class="text-red-600 hover:text-red-800" onclick="administracaoManager.deleteUser(${userId})">Excluir</button>
                            `;
                        }
                    }
                ],
                height: 400,
                readOnly: true,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation'
            });

        } catch (error) {
            console.error('Erro ao carregar usuários:', error);
        }
    }

    // Permissões
    async loadPermissoes() {
        try {
            const perms = await this.apiClient.get('/api/permissoes_financeiras/');

            const container = document.getElementById('permissoes-table');

            if (this.permissoesTable) {
                this.permissoesTable.destroy();
            }

            const data = perms.map(p => [p.id, p.id_usuario, p.id_proprietario, p.visualizar ? 'Sim' : 'Não', p.editar ? 'Sim' : 'Não', 'Editar | Excluir']);

            this.permissoesTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'ID Usuário', 'ID Proprietário', 'Visualizar', 'Editar', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true },
                    { type: 'text' },
                    { type: 'text' },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            const permId = instance.getDataAtRow(row)[0];
                            td.innerHTML = `
                                <button class="text-blue-600 hover:text-blue-800 mr-2" onclick="administracaoManager.editPerm(${permId})">Editar</button>
                                <button class="text-red-600 hover:text-red-800" onclick="administracaoManager.deletePerm(${permId})">Excluir</button>
                            `;
                        }
                    }
                ],
                height: 300,
                readOnly: true,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation'
            });

        } catch (error) {
            console.error('Erro ao carregar permissões:', error);
        }
    }

    editPerm(id) {
        // Abrir modal de edição - simplificado: redirecionar para admin page ou usar prompt
        const newVisualizar = confirm('Deseja ativar a permissão de visualizar? OK=Sim, Cancel=Nao');
        const newEditar = confirm('Deseja ativar a permissão de editar? OK=Sim, Cancel=Nao');

        this.apiClient.put(`/api/permissoes_financeiras/${id}`, { visualizar: newVisualizar, editar: newEditar })
            .then(() => { this.loadPermissoes(); alert('Permissão atualizada'); })
            .catch(err => { console.error(err); alert('Erro ao atualizar permissão'); });
    }

    async deletePerm(id) {
        if (!confirm('Tem certeza que deseja excluir esta permissão?')) return;
        try {
            await this.apiClient.delete(`/api/permissoes_financeiras/${id}`);
            await this.loadPermissoes();
            alert('Permissão excluída');
        } catch (error) {
            console.error('Erro ao excluir permissão:', error);
            alert('Erro ao excluir permissão.');
        }
    }

    // Handler simplificado para criar nova permissão
    async createPerm() {
        const id_usuario = parseInt(prompt('ID do usuário:', ''), 10);
        const id_proprietario = parseInt(prompt('ID do proprietário:', ''), 10);
        if (!id_usuario || !id_proprietario) { alert('IDs inválidos'); return; }

        try {
            await this.apiClient.post('/api/permissoes_financeiras/', { id_usuario, id_proprietario, visualizar: true, editar: false });
            await this.loadPermissoes();
            alert('Permissão criada');
        } catch (error) {
            console.error('Erro ao criar permissão:', error);
            alert('Erro ao criar permissão.');
        }
    }

    showPermModal(existing = null) {
        const modal = document.getElementById('perm-modal');
        const form = document.getElementById('perm-form');

        form.reset();
        document.getElementById('perm-user-id').value = '';
        document.getElementById('perm-prop-id').value = '';
        document.getElementById('perm-user-list').classList.add('hidden');
        document.getElementById('perm-prop-list').classList.add('hidden');

        if (existing) {
            document.getElementById('perm-id').value = existing.id;
            document.getElementById('perm-user-id').value = existing.id_usuario;
            document.getElementById('perm-prop-id').value = existing.id_proprietario;
            document.getElementById('perm-visualizar').checked = existing.visualizar;
            document.getElementById('perm-editar').checked = existing.editar;
            document.getElementById('perm-user-search').value = existing.usuario_nome || '';
            document.getElementById('perm-prop-search').value = existing.proprietario_nome || '';
            document.getElementById('perm-modal-title').textContent = 'Editar Permissão';
        } else {
            document.getElementById('perm-modal-title').textContent = 'Nova Permissão';
        }

        modal.classList.remove('hidden');
    }

    hidePermModal() {
        const modal = document.getElementById('perm-modal');
        modal.classList.add('hidden');
    }

    async searchUsers(query, container, hiddenFieldId, inputId) {
        if (!query || query.length < 2) {
            container.classList.add('hidden');
            container.innerHTML = '';
            return;
        }

        try {
            const users = await this.apiClient.get(`/api/usuarios/?q=${encodeURIComponent(query)}&limit=10`);
            container.innerHTML = '';
            if (!users || users.length === 0) {
                container.classList.add('hidden');
                return;
            }
            users.forEach(u => {
                const item = document.createElement('div');
                item.className = 'p-2 hover:bg-gray-100 cursor-pointer';
                item.textContent = `${u.nome} (${u.email})`;
                item.addEventListener('click', () => {
                    document.getElementById(hiddenFieldId).value = u.id;
                    document.getElementById(inputId).value = `${u.nome} (${u.email})`;
                    container.classList.add('hidden');
                });
                container.appendChild(item);
            });
            container.classList.remove('hidden');
        } catch (error) {
            console.error('Erro buscando usuários:', error);
            container.classList.add('hidden');
        }
    }

    async searchProprietarios(query, container, hiddenFieldId, inputId) {
        if (!query || query.length < 2) {
            container.classList.add('hidden');
            container.innerHTML = '';
            return;
        }

        try {
            const props = await this.apiClient.get(`/api/usuarios/?q=${encodeURIComponent(query)}&tipo=usuario&limit=10`);
            container.innerHTML = '';
            if (!props || props.length === 0) {
                container.classList.add('hidden');
                return;
            }
            props.forEach(p => {
                const item = document.createElement('div');
                item.className = 'p-2 hover:bg-gray-100 cursor-pointer';
                item.textContent = `${p.nome} (${p.email})`;
                item.addEventListener('click', () => {
                    document.getElementById(hiddenFieldId).value = p.id;
                    document.getElementById(inputId).value = `${p.nome} (${p.email})`;
                    container.classList.add('hidden');
                });
                container.appendChild(item);
            });
            container.classList.remove('hidden');
        } catch (error) {
            console.error('Erro buscando proprietários:', error);
            container.classList.add('hidden');
        }
    }

    async savePerm(event) {
        event.preventDefault();
        const id = document.getElementById('perm-id').value;
        const id_usuario = parseInt(document.getElementById('perm-user-id').value, 10);
        const id_proprietario = parseInt(document.getElementById('perm-prop-id').value, 10);
        const visualizar = document.getElementById('perm-visualizar').checked;
        const editar = document.getElementById('perm-editar').checked;

        if (!id_usuario || !id_proprietario) {
            // Mostrar mensaje inline
            this.showPermError('Selecione usuário e proprietário válidos.');
            return;
        }

        try {
            if (id) {
                await this.apiClient.put(`/api/permissoes_financeiras/${id}`, { visualizar, editar });
            } else {
                await this.apiClient.post('/api/permissoes_financeiras/', { id_usuario, id_proprietario, visualizar, editar });
            }

            this.hidePermModal();
            await this.loadPermissoes();
            // Opcional: mostrar notificación
            utils.showAlert('Permissão salva com sucesso', 'success');
        } catch (error) {
            console.error('Erro ao salvar permissão:', error);
            // Si es conflicto (409), mostrar mensaje inline y ofrecer editar
            const msg = error.message || String(error);
            if (msg.toLowerCase().includes('já existe') || msg.toLowerCase().includes('ja existe') || msg.toLowerCase().includes('conflict')) {
                this.showPermError('Permissão já existe para este usuário/proprietário. Você deseja editar a permissão existente? <a href="#" id="perm-edit-existing">Editar</a>');
                // Añadir listener para enlace de editar
                setTimeout(() => {
                    const link = document.getElementById('perm-edit-existing');
                    if (link) {
                        link.addEventListener('click', async (e) => {
                            e.preventDefault();
                            // Buscar la permissão existente (buscar por usuario+proprietario)
                            try {
                                const perms = await this.apiClient.get(`/api/permissoes_financeiras/?q=&skip=0&limit=200`);
                                const found = perms.find(p => p.id_usuario === id_usuario && p.id_proprietario === id_proprietario);
                                if (found) {
                                    this.showPermModal(found);
                                } else {
                                    this.showPermError('Permissão existente não encontrada.');
                                }
                            } catch (err) {
                                console.error('Erro buscando permissão existente:', err);
                                this.showPermError('Erro ao buscar permissão existente.');
                            }
                        });
                    }
                }, 50);
                return;
            }

            this.showPermError('Erro ao salvar permissão. ' + msg);
        }
    }

    showPermError(message) {
        let container = document.getElementById('perm-error');
        if (!container) {
            const form = document.getElementById('perm-form');
            container = document.createElement('div');
            container.id = 'perm-error';
            container.className = 'text-sm text-red-600 mt-2';
            form.insertBefore(container, form.firstChild);
        }
        container.innerHTML = message;
    }

    showUserModal(user = null) {
        this.currentUser = user;
        const modal = document.getElementById('user-modal');
        const form = document.getElementById('user-form');
        const title = document.getElementById('user-modal-title');

        if (user) {
            title.textContent = 'Editar Usuário';
            form['id'].value = user.id;
            form['user-nome'].value = user.nome;
            form['user-email'].value = user.email;
            form['user-role'].value = user.role;
            form['user-status'].value = user.ativo ? 'ativo' : 'inativo';
            document.getElementById('user-change-password').checked = false;
            this.togglePasswordFields(false);
        } else {
            title.textContent = 'Novo Usuário';
            form.reset();
            form['id'].value = '';
            document.getElementById('user-change-password').checked = true;
            this.togglePasswordFields(true);
        }

        modal.classList.remove('hidden');
    }

    hideUserModal() {
        document.getElementById('user-modal').classList.add('hidden');
        this.currentUser = null;
    }

    togglePasswordFields(show) {
        const passwordFields = document.getElementById('password-fields');
        const passwordInput = document.getElementById('user-password');
        const confirmPasswordInput = document.getElementById('user-confirm-password');

        if (show) {
            passwordFields.classList.remove('hidden');
            passwordInput.required = true;
            confirmPasswordInput.required = true;
        } else {
            passwordFields.classList.add('hidden');
            passwordInput.required = false;
            confirmPasswordInput.required = false;
        }
    }

    async saveUser(event) {
        event.preventDefault();

        const form = document.getElementById('user-form');
        const formData = new FormData(form);

        const userData = {
            nome: formData.get('nome'),
            email: formData.get('email'),
            role: formData.get('role'),
            ativo: formData.get('status') === 'ativo'
        };

        if (document.getElementById('user-change-password').checked) {
            const password = formData.get('password');
            const confirmPassword = formData.get('confirm-password');

            if (password !== confirmPassword) {
                alert('As senhas não coincidem.');
                return;
            }

            userData.password = password;
        }

        try {
            if (this.currentUser) {
                await this.apiClient.put(`/api/usuarios/${this.currentUser.id}/`, userData);
            } else {
                await this.apiClient.post('/api/usuarios/', userData);
            }

            this.hideUserModal();
            await this.loadUsuarios();
            alert('Usuário salvo com sucesso!');

        } catch (error) {
            console.error('Erro ao salvar usuário:', error);
            alert('Erro ao salvar usuário. Tente novamente.');
        }
    }

    async editUser(id) {
        try {
            const user = await this.apiClient.get(`/api/usuarios/${id}/`);
            this.showUserModal(user);
        } catch (error) {
            console.error('Erro ao carregar usuário:', error);
        }
    }

    async deleteUser(id) {
        if (!confirm('Tem certeza que deseja excluir este usuário?')) {
            return;
        }

        try {
            await this.apiClient.delete(`/api/usuarios/${id}/`);
            await this.loadUsuarios();
            alert('Usuário excluído com sucesso!');
        } catch (error) {
            console.error('Erro ao excluir usuário:', error);
            alert('Erro ao excluir usuário. Tente novamente.');
        }
    }

    // Backup
    async createBackup() {
        const backupType = document.getElementById('backup-type').value;

        try {
            await this.apiClient.post('/api/admin/backup/', { tipo: backupType });
            alert('Backup criado com sucesso!');
            await this.loadBackupHistory();
        } catch (error) {
            console.error('Erro ao criar backup:', error);
            alert('Erro ao criar backup. Tente novamente.');
        }
    }

    async restoreBackup() {
        const fileInput = document.getElementById('backup-file');
        const file = fileInput.files[0];

        if (!file) {
            alert('Selecione um arquivo de backup.');
            return;
        }

        if (!confirm('Tem certeza que deseja restaurar o backup? Isso pode sobrescrever dados existentes.')) {
            return;
        }

        try {
            const formData = new FormData();
            formData.append('backup_file', file);

            await this.apiClient.post('/api/admin/backup/restore/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            alert('Backup restaurado com sucesso!');
            // Recarregar a página para refletir as mudanças
            window.location.reload();

        } catch (error) {
            console.error('Erro ao restaurar backup:', error);
            alert('Erro ao restaurar backup. Tente novamente.');
        }
    }

    async loadBackupHistory() {
        try {
            const backups = await this.apiClient.get('/api/admin/backup/history/');

            const container = document.getElementById('backup-history-table');

            if (this.backupTable) {
                this.backupTable.destroy();
            }

            const data = backups.map(backup => [
                backup.id,
                backup.tipo,
                new Date(backup.data_criacao).toLocaleString('pt-BR'),
                `${(backup.tamanho / 1024 / 1024).toFixed(2)} MB`,
                'Download | Restaurar'
            ]);

            this.backupTable = new Handsontable(container, {
                data: data,
                colHeaders: ['ID', 'Tipo', 'Data', 'Tamanho', 'Ações'],
                columns: [
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    { type: 'text', readOnly: true },
                    {
                        type: 'text',
                        readOnly: true,
                        renderer: function(instance, td, row, col, prop, value, cellProperties) {
                            const backupId = instance.getDataAtRow(row)[0];
                            td.innerHTML = `
                                <button class="text-blue-600 hover:text-blue-800 mr-2" onclick="administracaoManager.downloadBackup(${backupId})">Download</button>
                                <button class="text-green-600 hover:text-green-800" onclick="administracaoManager.restoreBackupFromHistory(${backupId})">Restaurar</button>
                            `;
                        }
                    }
                ],
                height: 300,
                readOnly: true,
                stretchH: 'all',
                licenseKey: 'non-commercial-and-evaluation'
            });

        } catch (error) {
            console.error('Erro ao carregar histórico de backup:', error);
        }
    }

    async downloadBackup(id) {
        try {
            const response = await this.apiClient.get(`/api/admin/backup/${id}/download`, { responseType: 'blob' });

            const blob = new Blob([response]);
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.download = `backup_${id}_${new Date().toISOString().split('T')[0]}.sql`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);

        } catch (error) {
            console.error('Erro ao baixar backup:', error);
            alert('Erro ao baixar backup. Tente novamente.');
        }
    }

    async restoreBackupFromHistory(id) {
        if (!confirm('Tem certeza que deseja restaurar este backup? Isso pode sobrescrever dados existentes.')) {
            return;
        }

        try {
            await this.apiClient.post(`/api/admin/backup/${id}/restore`);
            alert('Backup restaurado com sucesso!');
            window.location.reload();
        } catch (error) {
            console.error('Erro ao restaurar backup:', error);
            alert('Erro ao restaurar backup. Tente novamente.');
        }
    }

    // Configurações
    async loadConfig() {
        try {
            const config = await this.apiClient.get('/api/admin/config/');

            document.getElementById('system-name').value = config.system_name || '';
            document.getElementById('default-currency').value = config.default_currency || 'BRL';
            document.getElementById('timezone').value = config.timezone || 'America/Sao_Paulo';
            document.getElementById('session-timeout').value = config.session_timeout || 60;
            document.getElementById('max-login-attempts').value = config.max_login_attempts || 5;
            document.getElementById('smtp-server').value = config.smtp_server || '';
            document.getElementById('smtp-port').value = config.smtp_port || '';
            document.getElementById('email-from').value = config.email_from || '';

        } catch (error) {
            console.error('Erro ao carregar configurações:', error);
        }
    }

    async saveConfig(event) {
        event.preventDefault();

        const form = document.getElementById('config-form');
        const formData = new FormData(form);

        const configData = {
            system_name: formData.get('system-name'),
            default_currency: formData.get('default-currency'),
            timezone: formData.get('timezone'),
            session_timeout: parseInt(formData.get('session-timeout')),
            max_login_attempts: parseInt(formData.get('max-login-attempts')),
            smtp_server: formData.get('smtp-server'),
            smtp_port: formData.get('smtp-port') ? parseInt(formData.get('smtp-port')) : null,
            email_from: formData.get('email-from')
        };

        try {
            await this.apiClient.put('/api/admin/config/', configData);
            alert('Configurações salvas com sucesso!');
        } catch (error) {
            console.error('Erro ao salvar configurações:', error);
            alert('Erro ao salvar configurações. Tente novamente.');
        }
    }

    // Logs
    async loadLogs() {
        const level = document.getElementById('log-level').value;

        try {
            const logs = await this.apiClient.get(`/api/admin/logs?level=${level}`);

            const logsContent = document.getElementById('logs-content');
            logsContent.innerHTML = '';

            logs.forEach(log => {
                const logEntry = document.createElement('div');
                logEntry.className = `p-2 border-b border-gray-200 text-sm font-mono ${
                    log.level === 'ERROR' ? 'bg-red-50 text-red-800' :
                    log.level === 'WARNING' ? 'bg-yellow-50 text-yellow-800' :
                    log.level === 'INFO' ? 'bg-blue-50 text-blue-800' :
                    'bg-gray-50 text-gray-800'
                }`;

                const timestamp = new Date(log.timestamp).toLocaleString('pt-BR');
                logEntry.textContent = `[${timestamp}] ${log.level}: ${log.message}`;

                logsContent.appendChild(logEntry);
            });

        } catch (error) {
            console.error('Erro ao carregar logs:', error);
        }
    }

    async clearLogs() {
        if (!confirm('Tem certeza que deseja limpar todos os logs?')) {
            return;
        }

        try {
            await this.apiClient.delete('/api/admin/logs/');
            await this.loadLogs();
            alert('Logs limpos com sucesso!');
        } catch (error) {
            console.error('Erro ao limpar logs:', error);
            alert('Erro ao limpar logs. Tente novamente.');
        }
    }
}

// Instância global
let administracaoManager;

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    administracaoManager = new AdministracaoManager();
});