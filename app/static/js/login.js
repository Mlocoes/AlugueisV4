// Login JavaScript
class LoginManager {
    constructor() {
        // Aguardar API estar pronta antes de inicializar
        if (window.apiClient) {
            this.apiClient = window.apiClient;
            this.init();
        } else {
            window.addEventListener('apiReady', (event) => {
                this.apiClient = event.detail;
                this.init();
            });
        }
    }

    init() {
        // Verificar autenticação apenas uma vez, sem causar loop
        this.checkExistingToken();
        this.setupEventListeners();
    }

    async checkExistingToken() {
        const token = this.apiClient.getToken();
        if (token) {
            try {
                const user = await this.apiClient.getCurrentUser();
                // Token válido, redirecionar para dashboard
                window.location.href = '/';
            } catch (error) {
                // Token inválido, limpar e permanecer na página
                localStorage.removeItem('token');
                sessionStorage.removeItem('token');
                this.apiClient.token = null;
            }
        }
    }

    setupEventListeners() {
        const loginForm = document.getElementById('login-form');
        if (!loginForm) {
            console.error('Formulário de login não encontrado!');
            return;
        }
        
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin(e);
        });
    }

    async handleLogin(event) {
        // event.preventDefault(); // Já feito no event listener

        const emailInput = document.querySelector('#email');
        const passwordInput = document.querySelector('#password');
        const rememberMeInput = document.querySelector('#remember-me');

        const username = emailInput.value.trim();
        const password = passwordInput.value.trim();
        const rememberMe = rememberMeInput.checked;

        if (!username || !password) {
            console.error('Campos obrigatórios não preenchidos:', { username: !!username, password: !!password });
            // Mostrar erro
            const errorMessage = document.getElementById('error-message');
            const errorText = document.getElementById('error-text');
            errorText.textContent = 'Por favor, preencha usuário e senha.';
            errorMessage.classList.remove('hidden');
            return;
        }

        console.log('Tentando login com:', { username, password: '***', rememberMe });

        const errorMessage = document.getElementById('error-message');
        const errorText = document.getElementById('error-text');

        try {
            // Esconder mensagem de erro anterior
            errorMessage.classList.add('hidden');

            // Fazer login
            console.log('Enviando requisição de login...');
            const response = await this.apiClient.login(username, password);

            // O servidor definiu o cookie HttpOnly com o token; nós não podemos ler o token.
            // Salvar apenas informações de UX (se houver) e redirecionar.
            // Limpar possíveis valores antigos
            localStorage.removeItem('userRole');
            localStorage.removeItem('userName');

            // Tentar obter /auth/me com retries curtos (o cookie é setado pelo servidor na resposta anterior)
            let gotUser = false;
            for (let i = 0; i < 3; i++) {
                try {
                    await this.apiClient.getCurrentUser();
                    gotUser = true;
                    break;
                } catch (e) {
                    // esperar um pouco antes de tentar novamente
                    await new Promise(r => setTimeout(r, 200));
                }
            }

            if (!gotUser) {
                // Como fallback, redirecionar para login para forçar nova autenticação manual
                window.location.href = '/login';
                return;
            }

            // Se conseguiu obter usuário, redirecionar para raiz
            window.location.href = '/';

        } catch (error) {
            console.error('Erro no login:', error);

            // Mostrar mensagem de erro
            errorText.textContent = error.message || 'Erro ao fazer login. Verifique suas credenciais.';
            errorMessage.classList.remove('hidden');
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});