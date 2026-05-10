from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from app.database import get_db
from app import models
from app.dependencies import get_current_user, require_admin
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/products", tags=["products"])

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)

# Public — anyone can browse products (pharmacy catalogue)
@router.get("/")
@limiter.limit("60/minute")
def get_products(request: Request, db: Session = Depends(get_db)):
    return db.query(models.Product).all()

# Admin only — seed, create, update, delete
@router.post("/seed")
def seed_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    if db.query(models.Product).count() > 0:
        return {"message": "Already seeded"}
    products = [
        models.Product(name="Panado 500mg",        description="Paracetamol pain relief · 20 tablets",         price=1.50, stock=200),
        models.Product(name="Ibuprofen 400mg",      description="Anti-inflammatory tablets · 24 tabs",           price=2.10, stock=150),
        models.Product(name="Zinc + Multivitamin",  description="Immune support · 30 capsules",                  price=5.50, stock=80),
        models.Product(name="ORS Sachets",          description="Oral Rehydration Salts · 10 sachets",           price=0.90, stock=300),
        models.Product(name="Amoxicillin 500mg",    description="Antibiotic · 21 capsules · Rx required",        price=4.20, stock=60),
        models.Product(name="Loratadine 10mg",      description="Antihistamine · 30 tablets",                    price=3.80, stock=90),
        models.Product(name="Omeprazole 20mg",      description="Acid reflux relief · 14 capsules",              price=3.20, stock=70),
        models.Product(name="Baby Paracetamol Syrup", description="Infant fever & pain relief · 100ml",          price=2.80, stock=50),
    ]
    db.add_all(products)
    db.commit()
    return {"message": f"Seeded {len(products)} products"}

@router.post("/")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    product = models.Product(**data.dict())
    db.add(product); db.commit(); db.refresh(product)
    return product

@router.put("/{product_id}")
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit(); db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    db.delete(product); db.commit()
    return {"message": "Product deleted"}
