import base64
import json
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.config import get_settings

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
                        "Reject selfies, ID cards, receipts, blank pages, or any non-prescription document.\n\n"
                        "STEP 2 — Do the following cart items appear on the prescription?\n"
                        "Be flexible with matching: brand names match generics, partial name matches count, spelling variations are acceptable.\n\n"
                        f"Cart items to check:\n{items_str}\n\n"
                        "Respond ONLY with valid JSON, no extra text, no markdown:\n"
                        '{"valid": true, "reason": "brief explanation", "missing_items": []}\n\n'
                        "Rules:\n"
                        "- valid=false if document is not a prescription\n"
                        "- valid=false if ANY cart item cannot be matched to the prescription (list them in missing_items)\n"
                        "- valid=true only if it is a real prescription AND all cart items are covered\n"
                        "- missing_items must be an array (empty if all matched)"
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

    if resp.status_code != 200:
        raise HTTPException(502, "Verification service unavailable. Please try again.")

    text = resp.json()["choices"][0]["message"]["content"]
    clean = text.replace("```json", "").replace("```", "").strip()
    
    try:
        result = json.loads(clean)
    except Exception:
        return {"valid": False, "reason": "Could not parse verification response. Please try again."}

    if result.get("missing_items") and len(result["missing_items"]) > 0:
        result["valid"] = False
        missing = ", ".join(result["missing_items"])
        result["reason"] = f"Your prescription does not cover: {missing}. Please provide a prescription that includes all Rx items in your cart."

    return result
