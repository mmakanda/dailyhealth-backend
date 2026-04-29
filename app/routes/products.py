from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import models

router = APIRouter(prefix="/products", tags=["products"])

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
