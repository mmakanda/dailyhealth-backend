from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import models
from app.ai import generate_response, extract_order_from_message
from app.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/chat", tags=["chat"])

class HistoryItem(BaseModel):
    role: str
    content: str

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[HistoryItem]] = []

def build_product_context(products: list) -> str:
    if not products:
        return ""
    lines = []
    for p in products:
        stock_status = "IN STOCK" if p.stock > 0 else "OUT OF STOCK"
        lines.append(f"- {p.name} | Price: ${p.price:.2f} | {stock_status} | Info: {p.description}")
    return "\n".join(lines)

@router.post("/")
@limiter.limit("20/minute;100/hour")
async def chat(
    request: Request,
    body: ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).all()
    product_context = build_product_context(products)
    history = [{"role": h.role, "content": h.content} for h in (body.history or [])]
    response = await generate_response(body.message, product_context, history)
    return {"response": response}

@router.post("/extract-order")
@limiter.limit("30/minute")
async def extract_order(
    request: Request,
    body: ChatMessage,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    products = db.query(models.Product).all()
    product_list = "\n".join(f"- {p.name}" for p in products)
    result = await extract_order_from_message(body.message, product_list)
    return result
