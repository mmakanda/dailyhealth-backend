from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({**data, "exp": expire}, settings.secret_key, algorithm="HS256")

@router.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = models.User(username=username, hashed_password=pwd_context.hash(password))
    db.add(user); db.commit(); db.refresh(user)
    return {"message": "User created"}

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": create_token({"sub": user.username}), "token_type": "bearer"}
