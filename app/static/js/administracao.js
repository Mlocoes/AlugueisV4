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

        // Abas
        document.getElementById('tab-usuarios').addEventListener('click', () => this.showTab('usuarios'));
        document.getElementById('tab-backup').addEventListener('click', () => this.showTab('backup'));
        document.getElementById('tab-config').addEventListener('click', () => this.showTab('config'));
        document.getElementById('tab-logs').addEventListener('click', () => this.showTab('logs'));

        // Usuários
        document.getElementById('add-user-btn').addEventListener('click', () => this.showUserModal());
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