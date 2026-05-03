"""
ai.py — Intelligent RAG-powered pharmacy assistant using Groq (LLaMA 3).

HOW RAG WORKS HERE:
1. User asks a question (e.g. "do you have cough syrup?")
2. chat.py fetches ALL products from the DB and passes them as structured context
3. This module sends that context + the question to LLaMA 3
4. The model answers specifically from the real product list — not from general knowledge
5. If something isn't in the product list, it says so honestly

This means responses are always accurate to the actual inventory.
"""

import httpx
import json
import re
from app.config import get_settings

settings = get_settings()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── System Prompt ─────────────────────────────────────────────────────────────
# Instructs the model HOW to use the product context it receives
SYSTEM_PROMPT = """You are a knowledgeable and friendly pharmacy assistant for Daily Health Pharmacy — a trusted pharmacy chain operating across Zimbabwe.

YOUR CORE RULES — follow these strictly:
1. NEVER diagnose any medical condition.
2. NEVER recommend specific dosages beyond what is printed on the packaging.
3. If someone describes serious, severe, or emergency symptoms, ALWAYS say: "Please see a doctor or visit a clinic immediately." and offer to connect them to our pharmacist.
4. ONLY recommend products that appear as IN STOCK in the [CURRENT INVENTORY] section. Never recommend OUT OF STOCK items.
5. NEVER mention stock quantities or numbers (e.g. never say "200 in stock" or "we have 50 units"). Only say "in stock" or "out of stock".
6. If a product is NOT in the inventory list say: "We don't currently stock that — please call us on +263 77 XXX XXXX to check or request it."
7. Keep responses warm, natural and concise — 2–4 sentences max. Do not use bullet points unless listing multiple products.
8. If the user writes in Shona or Ndebele, respond in that language, keeping medical terms in English.
9. If the user replies with just "yes" or "ok" after a recommendation, ask: "Great! Would you like to order via WhatsApp? Just send us a message and we will assist you."
10. For complex issues like drug interactions, prescription changes, chronic conditions (diabetes, hypertension, HIV) or pregnancy — say: "That is best answered by our pharmacist directly. You can reach them on WhatsApp or visit us in store."

HOW TO USE THE INVENTORY:
- Products marked IN STOCK: recommend freely with name and price.
- Products marked OUT OF STOCK: never recommend these. If asked specifically, say it is currently unavailable and suggest an in-stock alternative if one exists.
- When a user describes symptoms (e.g. "back pain", "headache", "fever"), recommend the most relevant IN STOCK product — do not list every option, pick the best one and mention one alternative at most.
- Never say how many units are available. Just say "we have that in stock" or "available in store".

PHARMACY INFORMATION:
- Name: Daily Health Pharmacy
- Hours: Mon–Fri 7:30 AM–6:00 PM | Sat 8:00 AM–5:00 PM | Sun & Public Holidays 9:00 AM–1:00 PM
- WhatsApp orders: 24/7
- Payments: EcoCash, ZIPIT, cash
- All products are MCAZ-approved

TONE: Warm, natural, helpful — like a pharmacist who genuinely cares about the customer."""


async def _call_groq(messages: list[dict]) -> str:
    """Makes a single call to the Groq API and returns the text response."""
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.groq_model,
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.4,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


async def generate_response(user_message: str, product_context: str = "") -> str:
    """
    Main chatbot response with RAG.
    product_context is a formatted string of all products from the DB.
    """
    if product_context:
        # Inject the real inventory into the user message so the model
        # MUST answer from it rather than from general training knowledge
        user_content = (
            f"[CURRENT INVENTORY — use ONLY these products in your answer]\n"
            f"{product_context}\n"
            f"[END OF INVENTORY]\n\n"
            f"Customer question: {user_message}"
        )
    else:
        user_content = (
            f"[NOTE: No inventory data is available right now. "
            f"Tell the customer to call us directly for stock queries.]\n\n"
            f"Customer question: {user_message}"
        )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        return await _call_groq(messages)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return "I'm having a configuration issue right now. Please call the pharmacy directly on +263 77 XXX XXXX."
        return "Sorry, I'm temporarily unavailable. Please call us directly or try again in a moment."
    except Exception:
        return "Sorry, I'm having trouble right now. Please call the pharmacy directly on +263 77 XXX XXXX."


async def extract_order_from_message(user_message: str, product_list: str) -> dict:
    """
    Uses AI to extract structured order details from a natural language message.
    Returns {"product_name": str | None, "quantity": int | None}

    Handles Shona/Ndebele e.g. "ndinoda Panado mbiri" → Panado x2
    """
    prompt = (
        f"Extract order details from this message.\n\n"
        f"Available products (match ONLY from this list):\n{product_list}\n\n"
        f'Message: "{user_message}"\n\n'
        f"Return ONLY valid JSON, no markdown, no explanation:\n"
        f'{{"product_name": "exact product name from list or null", "quantity": number_or_1}}\n\n'
        f"If no order intent, return: "
        f'{{"product_name": null, "quantity": null}}'
    )

    try:
        raw = await _call_groq([{"role": "user", "content": prompt}])
        clean = re.sub(r"```json|```", "", raw).strip()
        return json.loads(clean)
    except Exception:
        return {"product_name": None, "quantity": None}
