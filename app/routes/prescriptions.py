import base64
import json
import httpx
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])
settings = get_settings()

@router.post("/verify")
async def verify_prescription(
    file: UploadFile = File(...),
    rx_items: Optional[str] = Form(default="[]"),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are accepted.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 5MB.")

    b64 = base64.b64encode(contents).decode()
    media_type = (file.content_type or "image/jpeg").split(";")[0].strip()
    if media_type not in ["image/jpeg","image/png","image/gif","image/webp"]:
        media_type = "image/jpeg"

    try:
        items_list = json.loads(rx_items or "[]")
        items_str = "\n".join(f"- {item}" for item in items_list) if items_list else "No specific items to check."
    except Exception:
        items_str = rx_items or "No specific items to check."

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
                        "STEP 1 — Is this a valid medical prescription?\n"
                        "A valid prescription must have: doctor or clinic name, patient name, date, "
                        "at least one medication with dosage, and a signature or stamp.\n"
                        "Reject selfies, ID cards, receipts, blank pages, or any non-prescription document.\n\n"
                        "STEP 2 — Do these cart items appear on the prescription?\n"
                        "Be flexible: brand names match generics, partial name matches count, spelling variations acceptable.\n"
                        "List any cart item NOT found on the prescription in missing_items.\n\n"
                        f"Cart items to verify:\n{items_str}\n\n"
                        "Respond ONLY with valid JSON, no markdown, no extra text:\n"
                        '{"valid": true, "reason": "detailed explanation of what you see on the prescription", "missing_items": []}\n\n'
                        "Set valid=false if: not a prescription, OR any cart item is missing from it."
                    )
                }
            ]
        }]
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        logger.error(f"GROQ STATUS: {resp.status_code} RESPONSE: {resp.text[:500]}")

        if resp.status_code != 200:
            error_detail = resp.json().get("error", {}).get("message", resp.text)
            return {"valid": False, "reason": f"Verification error: {error_detail}", "missing_items": []}

        text = resp.json()["choices"][0]["message"]["content"]
        clean = text.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(clean)
        except Exception:
            return {"valid": False, "reason": f"Could not read verification response. Please try again. Raw: {text[:200]}", "missing_items": []}

        if result.get("missing_items") and len(result["missing_items"]) > 0:
            result["valid"] = False
            missing = ", ".join(result["missing_items"])
            result["reason"] = f"Prescription does not cover: {missing}. Please provide a prescription that includes all items in your cart."

        return result

    except httpx.TimeoutException:
        return {"valid": False, "reason": "Verification timed out. Please try again.", "missing_items": []}
    except Exception as e:
        logger.error(f"Verification exception: {e}")
        return {"valid": False, "reason": f"Verification failed: {str(e)}", "missing_items": []}
