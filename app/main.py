from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from sqlalchemy import text
from jose import JWTError, jwt
from typing import Optional

# Imports locaux
from app.db import engine, create_access_token, verify_password, get_password_hash, get_session, settings
from app.model import User, UserCreate, UserOut, SQLModel

api = FastAPI(title="Qlik Monitoring API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@api.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# --- LOGIQUE DE SÉCURITÉ ---

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token invalide")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

async def get_current_admin(
    token: str = Depends(oauth2_scheme), 
    session: Session = Depends(get_session)
):
    username = await get_current_user(token)
    user = session.exec(select(User).where(User.username == username)).first()
    
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Accès refusé : privilèges administrateur requis"
        )
    return user

# --- ROUTES D'AUTHENTIFICATION ---

@api.post("/register", response_model=UserOut, tags=["Admin"])
def register(
    user_in: UserCreate, 
    session: Session = Depends(get_session),
    admin_user: User = Depends(get_current_admin)
):
    existing = session.exec(select(User).where(User.username == user_in.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username déjà pris")
    
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role # L'admin peut choisir le rôle ici
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@api.post("/token", tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- GÉNÉRATION DYNAMIQUE DES ROUTES DE DONNÉES ---

def create_endpoint(table_name: str):
    def get_data(
        run_id: Optional[str] = None, 
        current_user: str = Depends(get_current_user)
    ):
        with Session(engine) as session:
            query_str = f"SELECT * FROM {table_name}"
            params = {}
            if run_id is not None:
                query_str += " WHERE runId = :run_id"
                params["run_id"] = run_id
            
            result = session.execute(text(query_str), params)
            return [dict(row) for row in result.mappings()]
    return get_data

list_path = [
    "obs_qlik_user_capacity", "obs_qlik_export_detail", "obs_qlik_user_activity",
    "obs_qlik_app_activity", "obs_qlik_session_details", "obs_qlik_sheet_activity",
    "obs_qlik_user_time", "obs_qlik_app_time"
]

for path in list_path:
    endpoint_func = create_endpoint(path)
    endpoint_func.__name__ = f"read_{path}" 
    api.get(f"/{path}", tags=["Data Monitoring"])(endpoint_func)