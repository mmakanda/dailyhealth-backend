import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import SessionLocal, engine
from app.models import Base, Product
Base.metadata.create_all(bind=engine)

products = [
    # ── Antibiotics (Rx) ─────────────────────────────────────────────
    Product(name="Amoxicillin 250mg", description="Broad-spectrum antibiotic for bacterial infections.", price=8.00, stock=50),
    Product(name="Amoxicillin 500mg", description="Higher dose broad-spectrum antibiotic.", price=12.00, stock=60),
    Product(name="Azithromycin 500mg", description="Antibiotic for respiratory and skin infections.", price=15.00, stock=40),
    Product(name="Ciprofloxacin 500mg", description="Antibiotic for urinary and GI infections.", price=14.00, stock=35),
    Product(name="Doxycycline 100mg", description="Antibiotic for chest and skin infections.", price=10.00, stock=45),
    Product(name="Metronidazole 400mg", description="Antibiotic for anaerobic and parasitic infections.", price=7.50, stock=55),
    Product(name="Cloxacillin 500mg", description="Antibiotic for staphylococcal infections.", price=9.00, stock=40),
    Product(name="Erythromycin 250mg", description="Antibiotic for respiratory tract infections.", price=11.00, stock=30),

    # ── Painkillers & Anti-inflammatories ────────────────────────────
    Product(name="Paracetamol 500mg", description="Effective for headaches, fever and mild pain.", price=2.50, stock=200),
    Product(name="Paracetamol 1000mg", description="Extra strength pain and fever relief.", price=3.50, stock=150),
    Product(name="Ibuprofen 200mg", description="Anti-inflammatory for mild pain and fever.", price=2.80, stock=180),
    Product(name="Ibuprofen 400mg", description="Anti-inflammatory pain relief.", price=3.00, stock=180),
    Product(name="Diclofenac 50mg", description="Anti-inflammatory for arthritis and muscle pain.", price=5.00, stock=100),
    Product(name="Aspirin 300mg", description="Pain relief and fever reduction.", price=2.00, stock=160),
    Product(name="Tramadol 50mg", description="Moderate to severe pain relief.", price=18.00, stock=25),
    Product(name="Codeine Phosphate 30mg", description="Pain relief for moderate pain.", price=16.00, stock=20),

    # ── Diabetes ─────────────────────────────────────────────────────
    Product(name="Metformin 500mg", description="Type 2 diabetes management.", price=6.50, stock=80),
    Product(name="Metformin 850mg", description="Higher dose for type 2 diabetes.", price=8.00, stock=70),
    Product(name="Glibenclamide 5mg", description="Oral hypoglycaemic for type 2 diabetes.", price=5.50, stock=65),
    Product(name="Glimepiride 2mg", description="Sulphonylurea for blood sugar control.", price=9.00, stock=50),

    # ── Hypertension & Heart ─────────────────────────────────────────
    Product(name="Amlodipine 5mg", description="Calcium channel blocker for high blood pressure.", price=7.00, stock=90),
    Product(name="Amlodipine 10mg", description="Higher dose for hypertension.", price=9.00, stock=75),
    Product(name="Enalapril 5mg", description="ACE inhibitor for heart failure and hypertension.", price=6.00, stock=85),
    Product(name="Losartan 50mg", description="ARB for hypertension and kidney protection.", price=8.50, stock=70),
    Product(name="Atenolol 50mg", description="Beta-blocker for hypertension and angina.", price=5.50, stock=80),
    Product(name="Hydrochlorothiazide 25mg", description="Diuretic for high blood pressure.", price=4.50, stock=90),

    # ── Respiratory ──────────────────────────────────────────────────
    Product(name="Salbutamol Inhaler 100mcg", description="Relieves asthma and bronchospasm.", price=12.00, stock=60),
    Product(name="Beclomethasone Inhaler 200mcg", description="Preventer inhaler for asthma.", price=18.00, stock=40),
    Product(name="Cetirizine 10mg", description="Non-drowsy antihistamine for allergies.", price=4.00, stock=120),
    Product(name="Loratadine 10mg", description="24-hour allergy relief.", price=3.50, stock=130),
    Product(name="Prednisolone 5mg", description="Steroid for inflammation and allergic reactions.", price=6.00, stock=55),
    Product(name="Chlorphenamine 4mg", description="Antihistamine for allergies and hay fever.", price=3.00, stock=110),

    # ── Gastrointestinal ─────────────────────────────────────────────
    Product(name="Omeprazole 20mg", description="Reduces stomach acid and treats heartburn.", price=5.50, stock=100),
    Product(name="Omeprazole 40mg", description="Higher dose for severe acid reflux.", price=7.50, stock=80),
    Product(name="Ranitidine 150mg", description="Reduces stomach acid production.", price=4.50, stock=90),
    Product(name="Loperamide 2mg", description="Fast relief for diarrhoea.", price=3.50, stock=140),
    Product(name="Oral Rehydration Salts", description="Electrolyte replacement for dehydration.", price=2.00, stock=200),
    Product(name="Lactulose Solution 200ml", description="Gentle laxative for constipation.", price=6.00, stock=70),
    Product(name="Mebendazole 100mg", description="Treatment for intestinal worms.", price=4.00, stock=100),

    # ── Vitamins & Supplements ───────────────────────────────────────
    Product(name="Vitamin C 1000mg", description="Immune system support supplement.", price=5.00, stock=150),
    Product(name="Vitamin D3 1000IU", description="Bone health and immune support.", price=6.00, stock=130),
    Product(name="Zinc 20mg", description="Immune support and wound healing.", price=4.50, stock=140),
    Product(name="Folic Acid 5mg", description="Essential for pregnancy and anaemia prevention.", price=3.00, stock=160),
    Product(name="Ferrous Sulphate 200mg", description="Iron supplement for anaemia.", price=4.00, stock=120),
    Product(name="Calcium + Vitamin D3", description="Bone strength combination supplement.", price=7.00, stock=110),
    Product(name="Multivitamin Tablets", description="Daily essential vitamins and minerals.", price=8.00, stock=150),
    Product(name="Vitamin B Complex", description="Supports energy and nerve function.", price=5.50, stock=130),

    # ── Malaria ──────────────────────────────────────────────────────
    Product(name="Artemether/Lumefantrine 20/120mg", description="First-line treatment for uncomplicated malaria.", price=14.00, stock=60),
    Product(name="Quinine 300mg", description="Treatment for severe malaria.", price=10.00, stock=40),
    Product(name="Chloroquine 150mg", description="Malaria prophylaxis and treatment.", price=6.00, stock=50),

    # ── Skin & Topical ───────────────────────────────────────────────
    Product(name="Hydrocortisone Cream 1%", description="Relieves skin inflammation and itching.", price=4.50, stock=100),
    Product(name="Clotrimazole Cream 1%", description="Antifungal for ringworm and athlete's foot.", price=5.00, stock=90),
    Product(name="Betamethasone Cream 0.1%", description="Potent steroid cream for skin conditions.", price=6.50, stock=70),
    Product(name="Permethrin Cream 5%", description="Treatment for scabies.", price=8.00, stock=50),

    # ── Eye & Ear ────────────────────────────────────────────────────
    Product(name="Chloramphenicol Eye Drops 0.5%", description="Antibiotic eye drops for conjunctivitis.", price=5.00, stock=80),
    Product(name="Gentamicin Eye Drops 0.3%", description="Antibiotic drops for eye infections.", price=6.00, stock=70),
    Product(name="Otosporin Ear Drops", description="Antibiotic and steroid drops for ear infections.", price=7.50, stock=60),
]

def seed():
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        print(f"Existing products: {existing}")
        
        # Add only products that don't already exist by name
        existing_names = {p.name for p in db.query(Product).all()}
        new_products = [p for p in products if p.name not in existing_names]
        
        if not new_products:
            print("All products already exist — nothing to add.")
            return
            
        db.add_all(new_products)
        db.commit()
        print(f"Added {len(new_products)} new products. Total: {existing + len(new_products)}")
    except Exception as e:
        db.rollback()
        print(f"Error seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
