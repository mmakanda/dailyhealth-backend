from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.config import get_settings
from app.routes import chat, products, orders, auth

settings = get_settings()

# Create all tables on startup (safe to run repeatedly)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Daily Health Pharmacy API",
    description="Backend for Daily Health Pharmacy — Bulawayo, Zimbabwe",
    version="1.0.0",
)

# ── CORS ────────────────────────────────────────────────────────────────────
# Allows the Vercel frontend to call this API
allowed_origins = [
    settings.frontend_url,          # e.g. https://daily-health.vercel.app
    "http://localhost:3000",         # local dev
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(products.router)
app.include_router(orders.router)
app.include_router(chat.router)


# ── Health check (Railway uses this to confirm the app is alive) ─────────────
@app.get("/health")
def health():
    return {"status": "ok", "service": "Daily Health Pharmacy API"}


@app.get("/")
def root():
    return {"message": "Daily Health Pharmacy API — visit /docs for API reference"}
