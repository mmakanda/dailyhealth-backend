import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import Base, Product

Base.metadata.create_all(bind=engine)

products = [
    Product(name="Paracetamol 500mg", description="Effective for headaches and fever.", price=2.50, stock=200),
    Product(name="Amoxicillin 250mg", description="Broad-spectrum antibiotic.", price=8.00, stock=50),
    Product(name="Vitamin C 1000mg", description="Immune system support supplement.", price=5.00, stock=150),
    Product(name="Ibuprofen 400mg", description="Anti-inflammatory pain relief.", price=3.00, stock=180),
    Product(name="Metformin 500mg", description="Type 2 diabetes management.", price=6.50, stock=80),
    Product(name="Cetirizine 10mg", description="Non-drowsy antihistamine for allergies.", price=4.00, stock=120),
    Product(name="Omeprazole 20mg", description="Reduces stomach acid and treats heartburn.", price=5.50, stock=100),
    Product(name="Loratadine 10mg", description="24-hour allergy relief.", price=3.50, stock=130),
]

def seed():
    db = SessionLocal()
    try:
        if db.query(Product).count() > 0:
            print("Products already exist — skipping seed.")
            return
        db.add_all(products)
        db.commit()
        print(f"Seeded {len(products)} products successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
