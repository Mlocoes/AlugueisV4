from datetime import timedelta
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
from app.core.config import settings

router = APIRouter()


@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
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
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=Usuario)
async def read_users_me(current_user: Usuario = Depends(get_current_active_user)):
    return current_user


@router.post("/logout")
async def logout():
    # Como estamos usando JWT, o logout é feito no lado do cliente
    # removendo o token. Aqui apenas retornamos sucesso.
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh", response_model=Token)
async def refresh_access_token_endpoint(
    current_user: Usuario = Depends(get_current_active_user)
):
    """Renova o token de acesso se estiver próximo de expirar"""
    # Como o usuário já foi autenticado, apenas criar um novo token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}