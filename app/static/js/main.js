class ApiClient {
    constructor() {
        // Usar porta 8000 (porta correta do servidor)
        this.baseURL = window.location.protocol + '//' + window.location.hostname + ':8000';
        // Usar apenas sessionStorage para armazenar o token (perdido no reload)
        this.token = sessionStorage.getItem('access_token');
        this.isRedirecting = false; // Flag para evitar loops de redirecionamento
        
        // Verificar token periodicamente (a cada 5 minutos)
        setInterval(() => {
            this.refreshTokenIfNeeded();
        }, 5 * 60 * 1000);
    }

    getToken() {
        // Retornar token do sessionStorage
        return sessionStorage.getItem('access_token');
    }

    setToken(token, remember = false) {
        // Antigo comportamento: armazenar token no cliente. Agora usamos cookies HttpOnly,
        // portanto esta função foi transformada em no-op para evitar salvar tokens no storage.
        console.warn('setToken chamado, mas a aplicação usa cookies HttpOnly. Nenhuma ação realizada.');
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                ...options.headers
            },
            ...options
        };

        // Não definir Content-Type se for FormData (deixa o fetch definir automaticamente)
        if (!(options.body instanceof FormData) && (!options.headers || !options.headers['Content-Type'])) {
            config.headers['Content-Type'] = 'application/json';
        }

        if (this.token) {
            // Usar token do sessionStorage para autenticação via header Authorization
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        // Adicionar automaticamente o header CSRF quando disponível no sessionStorage
        try {
            const method = (config.method || 'GET').toUpperCase();
            const mutating = ['POST', 'PUT', 'DELETE', 'PATCH'];
            if (mutating.includes(method)) {
                const csrf = sessionStorage.getItem('csrf_token');
                if (csrf) {
                    config.headers = config.headers || {};
                    config.headers['X-CSRF-Token'] = csrf;
                }
            }
        } catch (e) {
            // Em ambientes não DOM (ex: SSR) falhar silenciosamente
            console.debug('CSRF header injection failed:', e);
        }

        const response = await fetch(url, config);

        if (!response.ok) {
            if (response.status === 401 && !this.isRedirecting) {
                // Token expirado, redirecionar para login apenas se não estiver na página de login
                if (!window.location.pathname.includes('/login')) {
                    this.isRedirecting = true;
                    // Limpar dados locais de autenticação
                    this.clearStoredAuth();
                    // Delay para evitar throttling
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 100);
                    throw new Error('Sessão expirada. Faça login novamente.');
                } else {
                    throw new Error('Não autenticado');
                }
            }

                const errorData = await response.json().catch(() => ({ message: 'Erro na requisição' }));
                // Preferir 'detail' (FastAPI) o 'message' no corpo do erro
                const errMsg = errorData.detail || errorData.message || `Erro ${response.status}: ${response.statusText}`;
                throw new Error(errMsg);
        }

        // Para respostas de download, retornar o blob diretamente
        if (options.responseType === 'blob') {
            return await response.blob();
        }

        return await response.json();
    }

    async get(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'GET' });
    }

    async post(endpoint, data = null, options = {}) {
        return this.request(endpoint, { ...options, method: 'POST', body: data });
    }

    async put(endpoint, data = null, options = {}) {
        return this.request(endpoint, { ...options, method: 'PUT', body: data });
    }

    async delete(endpoint, options = {}) {
        return this.request(endpoint, { ...options, method: 'DELETE' });
    }

    async login(username, password) {
        const details = {
            'username': username,
            'password': password
        };

        // Usar JSON para compatibilidade com a API
        const response = await this.request('/api/auth/login/json', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(details)
        });

        // Armazenar o token retornado no sessionStorage
        if (response.access_token) {
            sessionStorage.setItem('access_token', response.access_token);
            this.token = response.access_token;

            // Gerar e armazenar token CSRF no sessionStorage
            const csrf_token = this.generateCSRFToken();
            sessionStorage.setItem('csrf_token', csrf_token);
        }

        return response;
    }    async logout() {
        // Para logout, pedir ao backend para limpar cookie e limpar dados locais
        try {
            await this.post('/api/auth/logout');
        } catch (e) {
            // ignore
        }
        
        // Limpar dados locais de autenticação
        this.clearStoredAuth();
    }

    async getCurrentUser() {
        try {
            const user = await this.get('/api/auth/me');
            // Armazenar informações do usuário
            if (user) {
                sessionStorage.setItem('userRole', user.tipo);
                sessionStorage.setItem('userName', user.nome);
                this.userRole = user.tipo;
                this.userName = user.nome;
            }
            return user;
        } catch (error) {
            console.error('Erro ao obter usuário atual:', error);
            throw error;
        }
    }

    async getMyPermissions(force = false) {
        // Retorna um objeto com arrays: { visualizar: [...ids], editar: [...ids] }
        if (!force && this._cachedPermissions) return this._cachedPermissions;
        try {
            const perms = await this.get('/api/permissoes_financeiras/me');
            const visualizar = (perms || []).filter(p => p.visualizar).map(p => p.id_proprietario);
            const editar = (perms || []).filter(p => p.editar).map(p => p.id_proprietario);
            this._cachedPermissions = { visualizar, editar };
            return this._cachedPermissions;
        } catch (e) {
            console.warn('Não foi possível obter permissões do usuário:', e);
            this._cachedPermissions = { visualizar: [], editar: [] };
            return this._cachedPermissions;
        }
    }

    canEditProprietario(proprietarioId) {
        if (this.isAdmin()) return true;
        const perms = this._cachedPermissions;
        if (!perms) return false;
        return (perms.editar || []).includes(proprietarioId);
    }

    canViewProprietario(proprietarioId) {
        if (this.isAdmin()) return true;
        const perms = this._cachedPermissions;
        if (!perms) return false;
        return (perms.visualizar || []).includes(proprietarioId);
    }

    isAdmin() {
        const role = sessionStorage.getItem('userRole') || this.userRole;
        return role === 'administrador';
    }

    isUsuario() {
        const role = sessionStorage.getItem('userRole') || this.userRole;
        return role === 'usuario';
    }

    getUserName() {
        return sessionStorage.getItem('userName') || this.userName || 'Usuário';
    }

    getUserRole() {
        return sessionStorage.getItem('userRole') || this.userRole || 'usuario';
    }

    async isTokenValid() {
        if (!this.token) return false;
        
        try {
            // Tentar fazer uma requisição simples para verificar se o token é válido
            await this.get('/api/auth/me');
            return true;
        }
        catch (error) {
            if (error.message.includes('401') || error.message.includes('Sessão expirada')) {
                return false;
            }
            // Para outros erros, assumir que o token é válido
            return true;
        }
    }

    async ensureValidToken() {
        await this.refreshTokenIfNeeded();
        
        if (!await this.isTokenValid()) {
            throw new Error('Sessão expirada. Faça login novamente.');
        }
    }

    async refreshTokenIfNeeded() {
        // Verificar se o token precisa ser renovado (se faltar menos de 30 minutos para expirar)
        // Como o token não é compartilhado com o cliente,
        // apenas chamamos /auth/refresh periodicamente para que o servidor renove o cookie quando necessário.
        try {
            await this.post('/api/auth/refresh');
        } catch (error) {
            // Falhas silenciosas serão tratadas por chamadas que retornarem 401
            // (não tentar setar header Authorization porque token é HttpOnly)
        }
    }

    clearStoredAuth() {
        // Limpar todos os dados de autenticação armazenados no sessionStorage
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('userRole');
        sessionStorage.removeItem('userName');
        sessionStorage.removeItem('csrf_token');
        this.token = null;
        this.userRole = null;
        this.userName = null;
    }

    generateCSRFToken() {
        // Gerar token CSRF aleatório
        const array = new Uint8Array(32);
        window.crypto.getRandomValues(array);
        return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('');
    }

    getCsrfToken() {
        // Retornar token CSRF do sessionStorage
        return sessionStorage.getItem('csrf_token');
    }
}

// Global API client instance
const api = window.apiClient;

// Sistema de detecção de reload - implementação robusta
(function() {
    try {
        let isReload = false;

        // Preferir Navigation Timing Level 2
        if (performance.getEntriesByType) {
            const navEntries = performance.getEntriesByType('navigation');
            if (navEntries && navEntries.length > 0) {
                isReload = navEntries[0].type === 'reload';
            }
        }

        // Fallback para Navigation Timing Level 1
        if (!isReload && performance.navigation) {
            // Older APIs: TYPE_RELOAD or numeric value 1
            isReload = (performance.navigation.type === performance.navigation.TYPE_RELOAD) || (performance.navigation.type === 1);
        }

        if (isReload) {
            console.log('🔄 Detected page reload via Navigation Timing API - clearing sessionStorage and redirecting to /login');
            // limpar todas as credenciais locais
            sessionStorage.clear();
            // garantir que o usuário vá para a tela de login
            if (!window.location.pathname.includes('/login')) {
                window.location.href = '/login';
            }
        } else {
            // Não é reload: nada a fazer aqui. Permitir navegação normal.
            console.debug('Página carregada por navegação normal (not reload)');
        }
    } catch (e) {
        console.debug('Reload detection failed:', e);
        // Em caso de falha, não forçar logout para evitar interromper a navegação normal
    }
})();

// Utility functions
const utils = {
    formatCurrency(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    formatDate(date) {
        return new Intl.DateTimeFormat('pt-BR').format(new Date(date));
    },

    formatDateTime(date) {
        return new Intl.DateTimeFormat('pt-BR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },

    showAlert(message, type = 'info') {
        // Criar elemento de alerta
        const alertDiv = document.createElement('div');
        alertDiv.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${
            type === 'error' ? 'bg-red-500 text-white' :
            type === 'success' ? 'bg-green-500 text-white' :
            type === 'warning' ? 'bg-yellow-500 text-white' :
            'bg-blue-500 text-white'
        }`;

        alertDiv.innerHTML = `
            <div class="flex items-center">
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        document.body.appendChild(alertDiv);

        // Remover automaticamente após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.remove();
            }
        }, 5000);
    },

    hideElementsForNonAdmin(apiClient) {
        // Verificar se api está disponível
        if (!apiClient || !apiClient.isAdmin) {
            console.warn('API não disponível para controle de acesso');
            return;
        }
        
        // Ocultar elementos que só administradores devem ver
        if (!apiClient.isAdmin()) {
            document.querySelectorAll('[data-admin-only]').forEach(el => {
                el.style.display = 'none';
            });
        }
    },

    disableElementsForNonAdmin() {
        // Desabilitar elementos para não-administradores
        if (!api.isAdmin()) {
            document.querySelectorAll('[data-admin-edit]').forEach(el => {
                el.disabled = true;
                el.style.opacity = '0.5';
                el.style.cursor = 'not-allowed';
            });
        }
    },

    showUserInfo(apiClient) {
        // Atualizar informações do usuário na interface
        const userInfoElement = document.getElementById('user-info');
        if (userInfoElement && apiClient) {
            const userName = apiClient.getUserName();
            const role = apiClient.getUserRole();
            const roleLabel = role === 'administrador' ? '👑 Admin' : '👤 Usuário';
            userInfoElement.innerHTML = `
                <span class="font-medium">${userName}</span>
                <span class="ml-2 text-xs px-2 py-1 rounded ${role === 'administrador' ? 'bg-yellow-400 text-gray-900' : 'bg-blue-400 text-white'}">${roleLabel}</span>
            `;
        }
    },

    checkAdminAccess(action = 'realizar esta ação') {
        if (!api.isAdmin()) {
            this.showAlert(`Apenas administradores podem ${action}`, 'warning');
            return false;
        }
        return true;
    }
};

// Modal management
function openModal(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Form handling
function serializeForm(form) {
    const data = {};
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    return data;
}

function populateForm(form, data) {
    for (const [key, value] of Object.entries(data)) {
        const element = form.querySelector(`[name="${key}"]`);
        if (element) {
            element.value = value;
        }
    }
}

// Table utilities
function createTable(headers, data, actions = []) {
    const table = document.createElement('table');
    table.className = 'custom-table';

    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });

    if (actions.length > 0) {
        const th = document.createElement('th');
        th.textContent = 'Ações';
        headerRow.appendChild(th);
    }

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Create body
    const tbody = document.createElement('tbody');

    data.forEach((row, index) => {
        const tr = document.createElement('tr');

        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = row[header.toLowerCase()] || '';
            tr.appendChild(td);
        });

        if (actions.length > 0) {
            const td = document.createElement('td');
            actions.forEach(action => {
                const button = document.createElement('button');
                button.className = `btn-${action.type} mr-2`;
                button.innerHTML = `<i class="fas ${action.icon}"></i> ${action.label}`;
                button.onclick = () => action.callback(row, index);
                td.appendChild(button);
            });
            tr.appendChild(td);
        }

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    return table;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sistema de Aluguéis inicializado');

    // Criar instância global do ApiClient
    window.apiClient = new ApiClient();

    // Disparar evento quando API estiver pronta
    window.dispatchEvent(new CustomEvent('apiReady', { detail: window.apiClient }));

    // Mobile menu toggle
    const mobileMenuButton = document.querySelector('#mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            const isExpanded = mobileMenuButton.getAttribute('aria-expanded') === 'true';
            mobileMenuButton.setAttribute('aria-expanded', !isExpanded);
            mobileMenu.classList.toggle('hidden');

            // Change icon based on state
            const icon = mobileMenuButton.querySelector('i');
            if (icon) {
                icon.className = isExpanded ? 'fas fa-bars text-xl' : 'fas fa-times text-xl';
            }
        });

        // Close mobile menu when clicking on a link
        mobileMenu.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                mobileMenu.classList.add('hidden');
                mobileMenuButton.setAttribute('aria-expanded', 'false');
                const icon = mobileMenuButton.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-bars text-xl';
                }
            }
        });
    }

    // Update user info in mobile menu
    function updateUserInfo() {
        const userInfo = document.getElementById('user-info');
        const userInfoMobile = document.getElementById('user-info-mobile');

        if (window.apiClient && window.apiClient.token) {
            // Decode JWT token to get user info
            try {
                const payload = JSON.parse(atob(window.apiClient.token.split('.')[1]));
                const username = payload.sub || 'Usuário';

                if (userInfo) userInfo.textContent = `Olá, ${username}`;
                if (userInfoMobile) userInfoMobile.textContent = `Olá, ${username}`;
            } catch (e) {
                console.warn('Erro ao decodificar token:', e);
                if (userInfo) userInfo.textContent = 'Usuário';
                if (userInfoMobile) userInfoMobile.textContent = 'Usuário';
            }
        }
    }

    // Update user info when API is ready
    window.addEventListener('apiReady', updateUserInfo);

    // Logout functionality for mobile
    const logoutBtnMobile = document.getElementById('logout-btn-mobile');
    if (logoutBtnMobile) {
        logoutBtnMobile.addEventListener('click', async function() {
            if (window.apiClient) {
                await window.apiClient.logout();
            }
            window.location.href = '/login';
        });
    }
});