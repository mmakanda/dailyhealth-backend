from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/")
def get_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).all()
