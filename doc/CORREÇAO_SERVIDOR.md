# ⚠️ Problema Detectado e Corrigido

## ❌ Erro Identificado

O servidor travou porque o arquivo `app/routes/import_routes.py` tinha imports incorretos:

```python
# ❌ ERRADO (não existe)
from app.dependencies import get_current_active_user, require_admin
from app.database import get_db

# ✅ CORRETO
from app.core.auth import get_current_active_user
from app.core.database import get_db
from app.models.usuario import Usuario
```

## ✅ Correções Aplicadas

### 1. Corrigidos os imports em `import_routes.py`
- Mudado `from app.database` → `from app.core.database`
- Mudado `from app.dependencies` → `from app.core.auth`
- Adicionado `from app.models.usuario import Usuario`

### 2. Criada função `require_admin()` 
Adicionada diretamente no arquivo `import_routes.py`:
```python
def require_admin(current_user: Usuario = Depends(get_current_active_user)):
    """Verifica se o usuário é administrador"""
    if current_user.papel != 'administrador':
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Apenas administradores podem importar dados."
        )
    return current_user
```

### 3. Atualizados todos os 4 endpoints
Mudado de:
```python
@router.post("/proprietarios", dependencies=[Depends(require_admin)])
async def import_proprietarios(file, db):
```

Para:
```python
@router.post("/proprietarios")
async def import_proprietarios(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)  # ✅ ADICIONADO
):
```

## 🔄 Como Reiniciar o Servidor

### Opção 1: Se você tem acesso root
```bash
sudo pkill -f "uvicorn app.main:app"
sudo python -c 'from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)' && \
sudo uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opção 2: Forçar reload (se uvicorn estiver travado)
```bash
# Tocar um arquivo do core para forçar reload
touch app/core/config.py
touch app/main.py
```

### Opção 3: Reiniciar manualmente
1. Parar o processo atual (Ctrl+C no terminal onde está rodando)
2. Executar novamente:
```bash
cd /home/mloco/Escritorio/AlugueisV4
python -c 'from app.core.database import engine, Base; Base.metadata.create_all(bind=engine)' && \
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## ✅ Verificar se Funcionou

Após reiniciar, teste:
```bash
curl http://localhost:8000/login
```

Deve retornar HTML da página de login.

Ou no navegador:
```
http://localhost:8000/importacao
```

Deve mostrar a página de importação.

## 📊 Status dos Arquivos

### Arquivos Corrigidos ✅
- `app/routes/import_routes.py` - Imports corrigidos, função require_admin adicionada

### Arquivos OK (não precisam correção)
- `app/services/import_service.py` - ✅ Imports corretos
- `app/main.py` - ✅ Import do import_routes está correto
- `app/templates/importacao.html` - ✅ OK
- `app/static/js/importacao.js` - ✅ OK
- Modelos Excel - ✅ OK

## 🎯 Resumo

**Causa:** Imports incorretos causaram erro ao iniciar o servidor  
**Solução:** Corrigidos imports para usar `app.core.*` e criada função `require_admin`  
**Status:** ✅ Código corrigido, aguardando reinício do servidor  
**Próximo Passo:** Reiniciar o servidor para aplicar correções
