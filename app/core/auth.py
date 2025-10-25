from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.usuario import Usuario

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    """Verifica a senha com tratamento de hashes desconhecidos.

    Retorna False em vez de lançar se o hash não for identificado pelo passlib,
    evitando erros 500 quando existirem valores antigos ou inválidos no banco.
    """
    if not hashed_password:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # Hash com formato desconhecido — não autentica, mas evita erro de servidor
        return False
    except Exception:
        # Qualquer outro erro — falhar de forma segura
        return False

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(Usuario).filter(Usuario.username == username).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: Usuario = Depends(get_current_user)):
    if not current_user.ativo:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def refresh_access_token(token: str):
    """Verifica se o token precisa ser renovado e retorna um novo se necessário"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        exp = payload.get("exp")
        now = datetime.utcnow().timestamp()
        
        # Se faltar menos de 30 minutos para expirar, renovar
        if exp - now < 30 * 60:
            username = payload.get("sub")
            if username:
                # Criar novo token
                access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
                new_token = create_access_token(
                    data={"sub": username}, expires_delta=access_token_expires
                )
                return new_token
    except JWTError:
        pass
    
    return None

def get_current_admin_user(current_user: Usuario = Depends(get_current_active_user)):
    """Verifica se o usuário atual é administrador"""
    from app.core.permissions import require_admin
    return require_admin(current_user)