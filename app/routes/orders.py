from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app import models
from app.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1, le=1000)
    notes: Optional[str] = Field(None, max_length=500)

@router.get("/")
def get_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Users only see their own orders
    return db.query(models.Order).filter(
        models.Order.user_id == current_user.id
    ).all()

@router.get("/{order_id}")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if order.user_id != current_user.id:
        raise HTTPException(403, "Not authorised")
    return order

@router.post("/")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    product = db.query(models.Product).filter(models.Product.id == data.product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    if product.stock < data.quantity:
        raise HTTPException(400, "Insufficient stock")
    order = models.Order(
        user_id=current_user.id,
        product_id=data.product_id,
        quantity=data.quantity,
        notes=data.notes
    )
    product.stock -= data.quantity
    db.add(order); db.commit(); db.refresh(order)
    return order
