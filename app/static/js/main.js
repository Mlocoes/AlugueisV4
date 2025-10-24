// Main JavaScript file for the rental system

// ApiClient class for handling API requests
class ApiClient {
    constructor() {
        this.baseURL = window.location.origin;
        this.token = this.getToken();
        this.isRedirecting = false; // Flag para evitar loops de redirecionamento
        
        // Verificar token periodicamente (a cada 5 minutos)
        setInterval(() => {
            this.refreshTokenIfNeeded();
        }, 5 * 60 * 1000);
    }

    getToken() {
        return localStorage.getItem('token') || sessionStorage.getItem('token');
    }

    setToken(token, remember = false) {
        this.token = token;
        if (remember) {
            localStorage.setItem('token', token);
        } else {
            sessionStorage.setItem('token', token);
        }
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
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (config.body && typeof config.body === 'object' && !(config.body instanceof FormData)) {
            config.body = JSON.stringify(config.body);
        }

        const response = await fetch(url, config);

        if (!response.ok) {
            if (response.status === 401 && !this.isRedirecting) {
                // Token expirado, redirecionar para login apenas se não estiver na página de login
                if (!window.location.pathname.includes('/login')) {
                    this.isRedirecting = true;
                    // Limpar token
                    localStorage.removeItem('token');
                    sessionStorage.removeItem('token');
                    this.token = null;
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
            throw new Error(errorData.message || `Erro ${response.status}: ${response.statusText}`);
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
        const formBody = Object.keys(details).map(key => 
            encodeURIComponent(key) + '=' + encodeURIComponent(details[key])).join('&');

        const response = await this.request('/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
            },
            body: formBody
        });
        
        return response;
    }

    async logout() {
        // Logout no JWT é apenas remover o token do lado cliente
        localStorage.removeItem('token');
        sessionStorage.removeItem('token');
        localStorage.removeItem('userRole');
        localStorage.removeItem('userName');
        this.token = null;
        this.userRole = null;
        this.userName = null;
        console.log('Logout realizado - token e dados removidos');
    }

    async getCurrentUser() {
        try {
            const user = await this.get('/auth/me');
            // Armazenar informações do usuário
            if (user) {
                localStorage.setItem('userRole', user.tipo);
                localStorage.setItem('userName', user.nome);
                this.userRole = user.tipo;
                this.userName = user.nome;
            }
            return user;
        } catch (error) {
            console.error('Erro ao obter usuário atual:', error);
            throw error;
        }
    }

    isAdmin() {
        const role = localStorage.getItem('userRole') || this.userRole;
        return role === 'administrador';
    }

    isUsuario() {
        const role = localStorage.getItem('userRole') || this.userRole;
        return role === 'usuario';
    }

    getUserName() {
        return localStorage.getItem('userName') || this.userName || 'Usuário';
    }

    getUserRole() {
        return localStorage.getItem('userRole') || this.userRole || 'usuario';
    }

    async isTokenValid() {
        if (!this.token) return false;
        
        try {
            // Tentar fazer uma requisição simples para verificar se o token é válido
            await this.get('/auth/me');
            return true;
        } catch (error) {
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
        if (this.token) {
            try {
                const payload = JSON.parse(atob(this.token.split('.')[1]));
                const exp = payload.exp * 1000; // converter para milissegundos
                const now = Date.now();
                const timeToExpiry = exp - now;
                
                // Se faltar menos de 30 minutos, renovar
                if (timeToExpiry < 30 * 60 * 1000) {
                    console.log('Token próximo de expirar, renovando...');
                    try {
                        const response = await this.post('/auth/refresh');
                        if (response.access_token) {
                            this.setToken(response.access_token, localStorage.getItem('token') !== null);
                            console.log('Token renovado com sucesso');
                        }
                    } catch (error) {
                        console.error('Erro ao renovar token:', error);
                        // Se falhar, deixar o fluxo continuar - será tratado pelo erro 401
                    }
                }
            } catch (error) {
                console.error('Erro ao verificar expiração do token:', error);
            }
        }
    }
}

// Global API client instance
const api = window.apiClient;

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
    const mobileMenuButton = document.querySelector('[aria-controls="mobile-menu"]');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
});