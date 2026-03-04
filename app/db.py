from sqlmodel import Session, create_engine
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

class Settings(BaseSettings):
    USER: str
    PASSWORD: str
    HOST: str
    PORT: str
    DATABASE: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str
    ADMIN_ROLE: str
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

url = f"mysql+pymysql://{settings.USER}:{settings.PASSWORD}@{settings.HOST}:{settings.PORT}/{settings.DATABASE}"
engine = create_engine(url, pool_pre_ping=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password[:72])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_session():
    with Session(engine) as session:
        yield session