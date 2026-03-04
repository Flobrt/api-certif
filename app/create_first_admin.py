# create_first_admin.py
from sqlmodel import Session
from app.db import engine, get_password_hash
from app.model import User
from app.db import settings

def create_admin():
    with Session(engine) as session:
        admin_name = settings.ADMIN_USERNAME
        existing = session.query(User).filter(User.username == admin_name).first()
        
        if not existing:
            new_admin = User(
                username=admin_name,
                email=settings.ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=settings.ADMIN_ROLE
            )
            session.add(new_admin)
            session.commit()
            print(f"L'utilisateur '{admin_name}' a été créé avec le rôle ADMIN.")
        else:
            print("L'admin existe déjà.")

if __name__ == "__main__":
    create_admin()