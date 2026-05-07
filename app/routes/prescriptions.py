import base64
import json
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import get_settings

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])
settings = get_settings()

@router.post("/verify")
async def verify_prescription(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only image files are accepted.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(400, "File too large. Maximum 5MB.")

    b64 = base64.b64encode(contents).decode()
    media_type = file.content_type

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "max_tokens": 150,
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
                        "You are a pharmacy prescription verification assistant. Examine this image strictly.\n\n"
                        "A valid prescription must have: doctor or clinic name, patient name, date, "
                        "at least one medication with dosage, and a signature or stamp.\n\n"
                        "Respond ONLY with valid JSON, no extra text:\n"
                        '{"valid": true, "reason": "one sentence explanation"}\n'
                        "or\n"
                        '{"valid": false, "reason": "one sentence explanation"}\n\n'
                        "Reject anything that is not clearly a medical prescription."
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
    return json.loads(clean)
