import base64
import json
import httpx
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])
settings = get_settings()

@router.post("/verify")
async def verify_prescription(
    file: UploadFile = File(...),
    rx_items: str = Form(...),
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are accepted.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 5MB.")

    b64 = base64.b64encode(contents).decode()
    media_type = file.content_type

    try:
        items_list = json.loads(rx_items)
        items_str = "\n".join(f"- {item}" for item in items_list)
    except Exception:
        items_str = rx_items

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{media_type};base64,{b64}"}
                },
                {
                    "type": "text",
                    "text": (
                        "You are a pharmacy prescription verification assistant.\n\n"
                        "STEP 1 — Is this a valid prescription?\n"
                        "A valid prescription has: doctor/clinic name, patient name, date, at least one medication with dosage, and a signature or stamp.\n"
                        "Reject selfies, ID cards, receipts, blank pages.\n\n"
                        "STEP 2 — Do these cart items appear on the prescription?\n"
                        "Be flexible: brand names match generics, partial matches count.\n\n"
                        f"Cart items:\n{items_str}\n\n"
                        "Respond ONLY with valid JSON, no markdown:\n"
                        '{"valid": true, "reason": "explanation", "missing_items": []}'
                    )
                }
            ]
        }]
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    logger.error(f"GROQ STATUS: {resp.status_code}")
    logger.error(f"GROQ RESPONSE: {resp.text}")

    if resp.status_code != 200:
        raise HTTPException(502, f"Groq error {resp.status_code}: {resp.text}")

    text = resp.json()["choices"][0]["message"]["content"]
    clean = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(clean)
    except Exception:
        return {"valid": False, "reason": f"Could not parse response: {text}"}

    if result.get("missing_items") and len(result["missing_items"]) > 0:
        result["valid"] = False
        missing = ", ".join(result["missing_items"])
        result["reason"] = f"Your prescription does not cover: {missing}."

    return result
