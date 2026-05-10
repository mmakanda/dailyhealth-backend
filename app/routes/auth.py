from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.config import get_settings
from app.limiter import limiter
from pydantic import BaseModel, Field, field_validator
import re

router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def strong_password(cls, v):
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password needs an uppercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password needs a digit")
        return v

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=64)

def create_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(hours=1)
    return jwt.encode({**data, "exp": expire}, settings.secret_key, algorithm="HS256")

@router.post("/register")
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(400, "Username already exists")
    user = models.User(
        username=payload.username,
        hashed_password=pwd_context.hash(payload.password)
    )
    db.add(user); db.commit(); db.refresh(user)
    return {"message": "User created"}

@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    dummy = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQyCMRozaVJTOE.zQHBdQYyau"
    valid = pwd_context.verify(payload.password, user.hashed_password if user else dummy)
    if not user or not valid:
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token({"sub": user.username}), "token_type": "bearer"}
