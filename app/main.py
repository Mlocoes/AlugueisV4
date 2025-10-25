from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import auth, usuarios, imoveis, participacoes, alugueis, alias, transferencias, permissoes_financeiras, dashboard, import_routes

# Criar tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Aluguéis",
    description="Sistema completo para gestão de imóveis e aluguéis",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir rotas
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(usuarios.router, prefix="/api/usuarios", tags=["Usuários"])
app.include_router(imoveis.router, prefix="/api/imoveis", tags=["Imóveis"])
app.include_router(participacoes.router, prefix="/api/participacoes", tags=["Participações"])
app.include_router(alugueis.router, prefix="/api/alugueis", tags=["Aluguéis"])
app.include_router(alias.router, prefix="/api/alias", tags=["Aliás"])
app.include_router(transferencias.router, prefix="/api/transferencias", tags=["Transferências"])
app.include_router(permissoes_financeiras.router, prefix="/api/permissoes_financeiras", tags=["Permissões Financeiras"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(import_routes.router, prefix="/api/importacao", tags=["Importação"])

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Frontend routes
@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard")
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/proprietarios")
async def proprietarios_page(request: Request):
    return templates.TemplateResponse("proprietarios.html", {"request": request})

@app.get("/imoveis")
async def imoveis_page(request: Request):
    return templates.TemplateResponse("imoveis.html", {"request": request})

@app.get("/participacoes")
async def participacoes_page(request: Request):
    return templates.TemplateResponse("participacoes.html", {"request": request})

@app.get("/aluguel")
async def aluguel_page(request: Request):
    return templates.TemplateResponse("aluguel.html", {"request": request})

@app.get("/relatorios")
async def relatorios_page(request: Request):
    return templates.TemplateResponse("relatorios.html", {"request": request})

@app.get("/importacao")
async def importacao_page(request: Request):
    return templates.TemplateResponse("importacao.html", {"request": request})

@app.get("/administracao")
async def administracao_page(request: Request):
    return templates.TemplateResponse("administracao.html", {"request": request})

import os

# Rotas para download de modelos Excel
@app.get("/Proprietarios.xlsx")
async def download_proprietarios_model():
    """Serve o arquivo modelo Excel para proprietários"""
    return FileResponse(
        path=os.path.join(os.path.dirname(__file__), "..", "Proprietarios.xlsx"),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename="Modelo_Proprietarios.xlsx"
    )

@app.get("/Imoveis.xlsx")
async def download_imoveis_model():
    """Serve o arquivo modelo Excel para imóveis"""
    return FileResponse(
        path=os.path.join(os.path.dirname(__file__), "..", "Imoveis.xlsx"),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename="Modelo_Imoveis.xlsx"
    )

@app.get("/Alugueis.xlsx")
async def download_alugueis_model():
    """Serve o arquivo modelo Excel para aluguéis"""
    return FileResponse(
        path=os.path.join(os.path.dirname(__file__), "..", "Alugueis.xlsx"),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename="Modelo_Alugueis.xlsx"
    )

@app.get("/Participacoes.xlsx")
async def download_participacoes_model():
    """Serve o arquivo modelo Excel para participações"""
    return FileResponse(
        path=os.path.join(os.path.dirname(__file__), "..", "Participacoes.xlsx"),
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename="Modelo_Participacoes.xlsx"
    )