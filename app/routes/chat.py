from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app import models
from app.ai import generate_response, extract_order_from_message

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    message: str


def build_product_context(products: list) -> str:
    """
    Builds a rich, structured product list for the AI.
    The more detail the model has, the better it can answer questions
    like "do you have cough syrup?" or "what brands of painkillers do you stock?"
    """
    if not products:
        return ""

    lines = []
    for p in products:
        stock_status = f"{p.stock} in stock" if p.stock > 0 else "OUT OF STOCK"
        lines.append(
            f"- {p.name} | Price: ${p.price:.2f} | {stock_status} | Info: {p.description}"
        )
    return "\n".join(lines)


@router.post("/")
async def chat(body: ChatMessage, db: Session = Depends(get_db)):
    # Fetch ALL products — the AI needs the full inventory to answer
    # category questions like "what cough syrups do you have?"
    products = db.query(models.Product).all()
    product_context = build_product_context(products)

    response = await generate_response(body.message, product_context)
    return {"response": response}


@router.post("/extract-order")
async def extract_order(body: ChatMessage, db: Session = Depends(get_db)):
    """
    AI-powered order extraction from natural language.
    Handles Shona/Ndebele messages for the WhatsApp bot.
    """
    products = db.query(models.Product).all()
    product_list = "\n".join(f"- {p.name}" for p in products)
    result = await extract_order_from_message(body.message, product_list)
    return result
