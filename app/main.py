from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import get_settings
from app.routes import chat, products, orders, auth

settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Daily Health Pharmacy API",
    description="Backend for Daily Health Pharmacy — Bulawayo, Zimbabwe",
    version="1.0.0",
)

allowed_origins = [
    settings.frontend_url,
    "https://dailyhealth-frontend.vercel.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(chat.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "Daily Health Pharmacy API"}

@app.get("/")
def root():
    return {"message": "Daily Health Pharmacy API — visit /docs for API reference"}
