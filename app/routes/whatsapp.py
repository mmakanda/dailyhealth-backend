from fastapi import APIRouter, Request

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

@router.get("/")
def verify(request: Request):
    return {"status": "ok"}
