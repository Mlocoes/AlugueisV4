from datetime import timedelta
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_active_user,
    refresh_access_token,
)
from app.schemas import Token, UserLogin, Usuario
from app.core.config import settings, APP_ENV
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """Autentica o usuário e seta um cookie HttpOnly com o access token.

    Em ambientes de produção o cookie será Secure e SameSite=Lax. Em desenvolvimento
    usa-se SameSite=Lax e Secure=False para permitir testes locais sem HTTPS.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Preparar cookie
    secure_cookie = APP_ENV == 'production'
    cookie_params = {
        'httponly': True,
        'samesite': 'lax',
        'secure': secure_cookie,
        'max_age': settings.access_token_expire_minutes * 60,
        'expires': settings.access_token_expire_minutes * 60,
        'path': '/'
    }
    response = JSONResponse({"access_token": "(set-in-cookie)", "token_type": "bearer"})
    # Usar set_cookie do Starlette/Response
    response.set_cookie(key='access_token', value=access_token, **cookie_params)
    # Gerar CSRF token exposto ao cliente (não HttpOnly)
    csrf_value = secrets.token_urlsafe(32)
    response.set_cookie(key='csrf_token', value=csrf_value, httponly=False, samesite='lax', secure=secure_cookie, path='/', max_age=settings.access_token_expire_minutes * 60)
    return response


@router.post("/login/json", response_model=Token)
async def login_json(
    user_credentials: UserLogin, db: Session = Depends(get_db)
):
    """Autentica o usuário via JSON e retorna token de acesso + define cookies.

    Esta rota é compatível com requisições JSON do frontend e define cookies HttpOnly.
    """
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    # Preparar cookie HttpOnly (igual à rota /login)
    secure_cookie = APP_ENV == 'production'
    cookie_params = {
        'httponly': True,
        'samesite': 'lax',
        'secure': secure_cookie,
        'max_age': settings.access_token_expire_minutes * 60,
        'expires': settings.access_token_expire_minutes * 60,
        'path': '/'
    }

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    # Usar set_cookie do Starlette/Response
    response.set_cookie(key='access_token', value=access_token, **cookie_params)
    # Gerar CSRF token exposto ao cliente (não HttpOnly)
    csrf_value = secrets.token_urlsafe(32)
    response.set_cookie(key='csrf_token', value=csrf_value, httponly=False, samesite='lax', secure=secure_cookie, path='/', max_age=settings.access_token_expire_minutes * 60)
    return response


@router.get("/me", response_model=Usuario)
async def read_users_me(current_user: Usuario = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
async def logout():
    # Limpar o cookie HttpOnly 'access_token' para efetuar logout seguro
    from fastapi.responses import JSONResponse

    response = JSONResponse({"message": "Logout realizado com sucesso"})
    # Expirar o cookie
    response.delete_cookie(key='access_token', path='/')
    return response


@router.post("/refresh", response_model=Token)
async def refresh_access_token_endpoint(
    current_user: Usuario = Depends(get_current_active_user)
):
    """Renova o token de acesso e redefine o cookie HttpOnly"""
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )

    secure_cookie = APP_ENV == 'production'
    cookie_params = {
        'httponly': True,
        'samesite': 'lax',
        'secure': secure_cookie,
        'max_age': settings.access_token_expire_minutes * 60,
        'expires': settings.access_token_expire_minutes * 60,
        'path': '/'
    }

    response = JSONResponse({"access_token": "(set-in-cookie)", "token_type": "bearer"})
    response.set_cookie(key='access_token', value=access_token, **cookie_params)
    csrf_value = secrets.token_urlsafe(32)
    response.set_cookie(key='csrf_token', value=csrf_value, httponly=False, samesite='lax', secure=secure_cookie, path='/', max_age=settings.access_token_expire_minutes * 60)
    return response