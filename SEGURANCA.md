# 🔒 Guia de Segurança - Sistema de Aluguéis

## 🚨 Riscos Identificados e Correções

### 1. Execução como Root (CRÍTICO)

**Problema:** O sistema estava sendo executado como usuário root, representando um risco de segurança crítico.

**Impacto:**
- Acesso completo ao sistema host
- Possibilidade de escalada de privilégios
- Exposição de arquivos sensíveis
- Risco de comprometimento total do sistema

**Correções Implementadas:**
- ✅ Dockerfile atualizado para criar usuário não-root (`appuser`)
- ✅ Docker Compose configurado para usar usuário não-root
- ✅ Script de verificação de segurança criado

### 2. Permissões de Arquivos

**Verificações Automáticas:**
- Arquivos de configuração: máximo 600 (leitura/escrita apenas para proprietário)
- Banco de dados: máximo 644 (leitura para grupo/outros)
- Logs: máximo 600 (sensível)

### 3. Contêiners Docker

**Práticas Seguras:**
- Nunca executar contêiners como root
- Usar usuários dedicados com privilégios mínimos
- Montar volumes com permissões apropriadas

## 🛡️ Melhores Práticas de Segurança

### Desenvolvimento
```bash
# Executar verificação de segurança
./security_check.sh

# Nunca executar como root
# ❌ sudo python app/main.py
# ✅ python app/main.py (como usuário normal)
```

### Produção
- Usar HTTPS sempre
- Implementar autenticação forte
- Configurar firewall
- Monitorar logs
- Fazer backup regular
- Atualizar dependências

### Docker
```yaml
# docker-compose.yml seguro
services:
  app:
    user: appuser:appuser  # Usuário não-root
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

### Banco de Dados
- Usar conexões criptografadas
- Implementar backup automático
- Controlar acesso por usuário/função
- Auditar queries sensíveis

## 🔍 Monitoramento Contínuo

### Verificações Diárias
```bash
# Executar diariamente
./security_check.sh

# Verificar processos
ps aux | grep -E "(uvicorn|python)" | grep -v grep

# Verificar contêiners
docker ps --format "table {{.ID}}\t{{.Image}}\t{{.Names}}\t{{.Status}}"
```

### Logs a Monitorar
- Tentativas de login falhidas
- Acesso a endpoints sensíveis
- Erros de autenticação
- Atividades de administradores

## 🚦 Status de Segurança Atual

| Componente | Status | Ação Necessária |
|------------|--------|-----------------|
| Dockerfile | ✅ Seguro | - |
| Docker Compose | ✅ Seguro | - |
| Permissões | ✅ Verificado | Monitorar |
| Processos | ⚠️ Monitorar | Verificar execução |
| HTTPS | ❌ Pendente | Implementar em produção |

## 🔐 Configurando HTTPS em Produção

Para garantir a segurança dos dados em trânsito, é fundamental configurar HTTPS no ambiente de produção. A abordagem recomendada é usar um reverse proxy como o Nginx para gerenciar o tráfego HTTPS e encaminhar as requisições para a aplicação.

### Exemplo de Configuração Nginx

Abaixo, um exemplo de configuração do Nginx para um reverse proxy com HTTPS. Esta configuração assume que você já possui um certificado SSL/TLS (você pode obter um gratuitamente com o Let's Encrypt).

```nginx
server {
    listen 80;
    server_name seu_dominio.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name seu_dominio.com;

    ssl_certificate /etc/letsencrypt/live/seu_dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu_dominio.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Passos para Configurar

1.  **Instale o Nginx:** Se ainda não o tiver, instale o Nginx no seu servidor.
2.  **Obtenha um Certificado SSL/TLS:** Use o Certbot para obter um certificado gratuito do Let's Encrypt.
3.  **Configure o Nginx:** Crie um novo arquivo de configuração em `/etc/nginx/sites-available/` com o conteúdo acima, substituindo `seu_dominio.com` pelo seu domínio real.
4.  **Ative a Configuração:** Crie um link simbólico do seu arquivo de configuração para o diretório `/etc/nginx/sites-enabled/`.
5.  **Reinicie o Nginx:** Reinicie o serviço do Nginx para aplicar as alterações.

## 📞 Contato e Suporte

Em caso de suspeita de comprometimento:
1. Pare imediatamente o sistema
2. Execute verificação de segurança
3. Revise logs recentes
4. Consulte equipe de segurança

---

**Última atualização:** Outubro 2025
**Responsável:** Equipe de Desenvolvimento