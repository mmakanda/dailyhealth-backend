from sqlalchemy.orm import Session
from app.database import get_db
from app import models

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    stock: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None

@router.get("/")
def get_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

@router.post("/seed")
def seed_products(db: Session = Depends(get_db)):
    if db.query(models.Product).count() > 0:
        return {"message": "Already seeded"}
    products = [
        models.Product(name="Panado 500mg", description="Paracetamol pain relief · 20 tablets", price=1.50, stock=200),
        models.Product(name="Ibuprofen 400mg", description="Anti-inflammatory tablets · 24 tabs", price=2.10, stock=150),
        models.Product(name="Zinc + Multivitamin", description="Immune support · 30 capsules", price=5.50, stock=80),
        models.Product(name="ORS Sachets", description="Oral Rehydration Salts · 10 sachets", price=0.90, stock=300),
        models.Product(name="Amoxicillin 500mg", description="Antibiotic · 21 capsules · Rx required", price=4.20, stock=60),
        models.Product(name="Loratadine 10mg", description="Antihistamine · 30 tablets", price=3.80, stock=90),
        models.Product(name="Omeprazole 20mg", description="Acid reflux relief · 14 capsules", price=3.20, stock=70),
        models.Product(name="Baby Paracetamol Syrup", description="Infant fever & pain relief · 100ml", price=2.80, stock=50),
    ]
    db.add_all(products)
    db.commit()
    return {"message": f"Seeded {len(products)} products"}

@router.post("/")
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}")
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"message": "Product deleted"}
