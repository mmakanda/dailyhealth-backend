from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.database import engine, Base
from app.config import get_settings
from app.routes import chat, products, orders, auth, prescriptions
import logging, traceback

settings = get_settings()
logger = logging.getLogger("dailyhealth")
logging.basicConfig(level=logging.INFO)

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Daily Health Pharmacy API",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {request.url.path} — {exc}\n{traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})

allowed_origins = [
    "https://dailyhealth-frontend.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(chat.router)
app.include_router(prescriptions.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Daily Health Pharmacy API"}

@app.get("/")
def root():
    return {"message": "Daily Health Pharmacy API"}
