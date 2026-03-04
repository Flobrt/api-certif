from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import EmailStr

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(unique=True)
    hashed_password: str
    role: str = Field(default="reader") # Ajouté pour la gestion des droits

class UserCreate(SQLModel):
    username: str
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str = Field(default="reader") # L'admin pourra choisir le rôle
    
class UserOut(SQLModel):
    id: int
    username: str
    email: str
    role: str