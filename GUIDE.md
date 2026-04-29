# Daily Health Pharmacy — Complete Build & Deployment Guide
**For: Mike | Stack: FastAPI + Next.js + PostgreSQL + Groq AI + WhatsApp**

---

## What This Document Is

This is your end-to-end reference. Every step is explained — not just *what* to run, but *why*. Keep this for when you're onboarding someone or revisiting the project in 6 months.

---

## The Changes From the Original Plan (and Why)

| Original Plan | This Plan | Reason |
|---|---|---|
| Ollama (local LLM) | Groq API (cloud LLM) | Ollama needs a GPU/RAM. Railway has neither. Your app would crash in production. Groq runs LLaMA 3 free in the cloud. |
| `os.getenv()` for config | `pydantic-settings` | Type-checks all env vars at startup. Missing var = instant clear error, not a mysterious runtime crash. |
| `allow_origins=["*"]` | `allow_origins=[your domain]` | `"*"` means ANY website can call your API. Dangerous in prod. Restrict to your own frontend only. |
| No `.gitignore` | `.gitignore` included | Without it you'd push `.env` (with all your API keys) to GitHub. |
| Hardcoded order price ($2) | Price pulled from DB | Product prices change. Hardcoding breaks orders every time you update a price. |
| No rate limiting | `slowapi` rate limiting | Without it, anyone can hammer your `/chat` endpoint 10,000 times and rack up your Groq bill. |
| Admin key in header | JWT auth | Header keys don't expire. JWTs do. Much safer. |
| No WhatsApp None-text guard | `entry.get("messages")` check | WhatsApp sends delivery receipts (non-message events) that would crash the original code. |

---

## Architecture Overview

```
User's Browser
     │
     │  HTTPS
     ▼
Vercel (Frontend — Next.js)
     │
     │  HTTPS API calls
     ▼
Railway (Backend — FastAPI + PostgreSQL)
     │              │
     │              ├── Groq API (AI responses)
     │              └── Meta WhatsApp API (messaging)
     │
     ▼
PostgreSQL (Railway managed)
```

**Why this split?**
- Vercel is optimised for frontend (CDN, caching, zero-config SSL). Free.
- Railway is optimised for backends + managed databases. Free tier available.
- Separation means you can scale each independently.

---

## Part 1 — Local Environment Setup

### 1.1 Install Required Tools

**Python 3.11+**
```bash
python3 --version
# If not installed: sudo apt install python3.11  (Ubuntu/WSL)
# Or download from python.org
```
*Why 3.11?* FastAPI and pydantic-settings require 3.10+. 3.11 is the current stable LTS.

**Node.js 18+**
```bash
node -v
# Install via: https://nodejs.org  or  nvm install 18
```

**Git**
```bash
git --version
# Ubuntu: sudo apt install git
```

**PostgreSQL (local dev only)**
```bash
# Ubuntu/WSL:
sudo apt install postgresql
sudo service postgresql start
sudo -u postgres psql
```

Inside psql:
```sql
CREATE DATABASE pharmacy_db;
CREATE USER pharmacy_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE pharmacy_db TO pharmacy_user;
\q
```

---

## Part 2 — Backend Setup

### 2.1 Clone / Create Project

```bash
mkdir pharmacy-backend
cd pharmacy-backend
git init
```

Copy all the project files from this repository into this folder.

### 2.2 Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate    # Linux/Mac
# Windows:  venv\Scripts\activate
```

*Why venv?* Isolates your project's packages from your system Python. Prevents version conflicts between projects.

### 2.3 Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages explained:
- `fastapi` — web framework
- `uvicorn` — ASGI server (runs FastAPI)
- `sqlalchemy` — ORM (Python → SQL)
- `psycopg2-binary` — PostgreSQL driver
- `passlib[bcrypt]` — password hashing
- `python-jose` — JWT creation/verification
- `alembic` — database migrations
- `httpx` — async HTTP client (for Groq + WhatsApp API calls)
- `slowapi` — rate limiting
- `pydantic-settings` — typed environment variable loading

### 2.4 Set Up Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```bash
DATABASE_URL=postgresql://pharmacy_user:your_password@localhost/pharmacy_db
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ALLOWED_ORIGINS=http://localhost:3000
GROQ_API_KEY=<from https://console.groq.com — free>
```

Leave WhatsApp + Paynow blank for now (configure during deployment).

### 2.5 Set Up Database Migrations (Alembic)

*Why Alembic?*
When you change `models.py` later (add a column, rename a table), you need a way to update the live database without wiping all your data. Alembic generates migration scripts that apply changes incrementally.

```bash
alembic init alembic
```

Edit `alembic/env.py` — find this line:
```python
target_metadata = None
```
Replace with:
```python
from app.models import Base
from app.config import get_settings
target_metadata = Base.metadata

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
```

Generate your first migration:
```bash
alembic revision --autogenerate -m "initial tables"
alembic upgrade head
```

*Run `alembic upgrade head` every time you change models.py.*

### 2.6 Run the Backend

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` — you'll see the Swagger UI with all your endpoints.
Visit `http://localhost:8000` — should return `{"status": "ok"}`.

---

## Part 3 — Get a Free AI Key (Groq)

1. Go to https://console.groq.com
2. Sign up (free — no credit card)
3. Go to **API Keys** → **Create API Key**
4. Copy it into your `.env`:
   ```
   GROQ_API_KEY=gsk_...
   ```

Free tier: 14,400 requests/day with LLaMA 3. More than enough to start.

*Why not ChatGPT/OpenAI?* Requires a paid plan for API access. Groq is free and fast.

---

## Part 4 — Frontend Setup (Next.js)

### 4.1 Create Project

```bash
cd ..
npx create-next-app@latest pharmacy-frontend
cd pharmacy-frontend
```

When prompted:
- TypeScript: **No** (keep it simple for now)
- ESLint: **Yes**
- Tailwind CSS: **Yes**
- App Router: **Yes**

### 4.2 Environment Variable

Create `.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

*Why `NEXT_PUBLIC_`?* Next.js only exposes env vars to the browser if they start with `NEXT_PUBLIC_`. Everything else stays server-side.

### 4.3 Run Frontend

```bash
npm run dev
```

Visit `http://localhost:3000`.

### 4.4 Create Components

Create `app/components/ProductList.js`:
```javascript
"use client";
import { useEffect, useState } from "react";

export default function ProductList() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(process.env.NEXT_PUBLIC_API_URL + "/products")
      .then(res => res.json())
      .then(data => { setProducts(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading products...</p>;

  return (
    <div>
      <h2>Our Products</h2>
      {products.map(p => (
        <div key={p.id}>
          <strong>{p.name}</strong> — ${p.price}
          <p>{p.description}</p>
        </div>
      ))}
    </div>
  );
}
```

Create `app/components/ChatBox.js`:
```javascript
"use client";
import { useState } from "react";

export default function ChatBox() {
  const [messages, setMessages] = useState([
    { role: "bot", text: "Hi! I'm the Daily Health assistant. Ask me about products, health tips, or place an order." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: userMsg }]);
    setLoading(true);

    try {
      const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "bot", text: data.response }]);
    } catch {
      setMessages(prev => [...prev, { role: "bot", text: "Sorry, I'm offline right now." }]);
    }
    setLoading(false);
  };

  return (
    <div>
      <div style={{ height: 300, overflowY: "auto", border: "1px solid #ccc", padding: 10 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ textAlign: m.role === "user" ? "right" : "left" }}>
            <span><strong>{m.role === "user" ? "You" : "Bot"}:</strong> {m.text}</span>
          </div>
        ))}
        {loading && <p>Typing...</p>}
      </div>
      <input value={input} onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === "Enter" && send()}
        placeholder="Ask about medicine or place an order..." style={{ width: "80%" }} />
      <button onClick={send} disabled={loading}>Send</button>
    </div>
  );
}
```

Update `app/page.js`:
```javascript
import ProductList from "./components/ProductList";
import ChatBox from "./components/ChatBox";

export default function Home() {
  return (
    <main style={{ padding: 20 }}>
      <h1>Daily Health Pharmacy</h1>
      <p>Harare's trusted pharmacy — now with AI assistance.</p>
      <ChatBox />
      <hr />
      <ProductList />
    </main>
  );
}
```

Create `app/admin/page.js` (admin dashboard):
```javascript
"use client";
import { useState, useEffect } from "react";

export default function Admin() {
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [token, setToken] = useState("");
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const API = process.env.NEXT_PUBLIC_API_URL;

  const login = async () => {
    const res = await fetch(API + "/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(loginForm),
    });
    const data = await res.json();
    if (data.access_token) {
      setToken(data.access_token);
      loadAll(data.access_token);
    } else alert("Login failed");
  };

  const loadAll = async (t) => {
    const [p, o] = await Promise.all([
      fetch(API + "/products").then(r => r.json()),
      fetch(API + "/orders", { headers: { Authorization: `Bearer ${t}` } }).then(r => r.json()),
    ]);
    setProducts(p);
    setOrders(o);
  };

  const updateOrderStatus = async (id, status) => {
    await fetch(API + `/orders/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ status }),
    });
    loadAll(token);
  };

  if (!token) return (
    <div style={{ padding: 20 }}>
      <h1>Admin Login</h1>
      <input placeholder="Username" onChange={e => setLoginForm({ ...loginForm, username: e.target.value })} />
      <input type="password" placeholder="Password" onChange={e => setLoginForm({ ...loginForm, password: e.target.value })} />
      <button onClick={login}>Login</button>
    </div>
  );

  return (
    <div style={{ padding: 20 }}>
      <h1>Admin Dashboard</h1>
      <h2>Orders ({orders.length})</h2>
      {orders.map(o => (
        <div key={o.id} style={{ border: "1px solid #ccc", padding: 10, marginBottom: 10 }}>
          <strong>{o.product_name}</strong> x{o.quantity} — ${o.total_price}<br />
          📱 {o.customer_phone} | 📍 {o.address || "No address yet"}<br />
          Status: <strong>{o.status}</strong> | Payment: {o.payment_status}<br />
          <button onClick={() => updateOrderStatus(o.id, "processing")}>Mark Processing</button>
          <button onClick={() => updateOrderStatus(o.id, "completed")}>Mark Completed</button>
          <button onClick={() => updateOrderStatus(o.id, "cancelled")}>Cancel</button>
        </div>
      ))}
    </div>
  );
}
```

---

## Part 5 — Deployment

### 5.1 Backend → Railway

**Step 1: Push to GitHub**
```bash
cd pharmacy-backend
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pharmacy-backend.git
git push -u origin main
```

**Step 2: Deploy on Railway**
1. Go to https://railway.app → sign in with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select `pharmacy-backend`
4. Railway detects Python automatically (via `Procfile`)

**Step 3: Add PostgreSQL**
1. In your Railway project → **+ New** → **Database** → **PostgreSQL**
2. Railway auto-sets `DATABASE_URL` in your app's environment

**Step 4: Set Environment Variables**
In Railway → your app → **Variables** tab, add:
```
SECRET_KEY=your_generated_secret
GROQ_API_KEY=your_groq_key
ALLOWED_ORIGINS=https://your-app.vercel.app
WHATSAPP_TOKEN=           (set this after WhatsApp setup)
WHATSAPP_VERIFY_TOKEN=    (set this after WhatsApp setup)
WHATSAPP_PHONE_ID=        (set this after WhatsApp setup)
```

**Step 5: Get your Railway URL**
Railway gives you: `https://pharmacy-backend-production.up.railway.app`

Test it: `https://your-railway-url.up.railway.app/`
Should return: `{"status": "ok"}`

---

### 5.2 Frontend → Vercel

**Step 1: Push to GitHub**
```bash
cd pharmacy-frontend
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/YOUR_USERNAME/pharmacy-frontend.git
git push -u origin main
```

**Step 2: Deploy on Vercel**
1. Go to https://vercel.com → sign in with GitHub
2. **Import Project** → select `pharmacy-frontend`
3. Under **Environment Variables** add:
   ```
   NEXT_PUBLIC_API_URL=https://your-railway-url.up.railway.app
   ```
4. Click **Deploy**

Vercel gives you: `https://pharmacy-frontend.vercel.app`

**Step 3: Update Railway ALLOWED_ORIGINS**
Go back to Railway → Variables → update:
```
ALLOWED_ORIGINS=https://pharmacy-frontend.vercel.app
```
Redeploy Railway app.

---

### 5.3 Custom Domain (amaryllissuccess.co.zw or similar)

In your domain registrar's DNS panel, add:

| Type | Name | Value |
|---|---|---|
| CNAME | `www` | `cname.vercel-dns.com` |
| A | `@` | `76.76.21.21` |

In Vercel → your project → **Settings** → **Domains** → add your domain.

Vercel automatically provisions SSL (HTTPS) — free.

---

## Part 6 — WhatsApp Setup (Meta Cloud API)

### 6.1 Create Meta Developer App

1. Go to https://developers.facebook.com
2. **My Apps** → **Create App**
3. Choose **Business** → give it a name
4. Add product: **WhatsApp**
5. Under WhatsApp → **Getting Started**:
   - Copy your **Phone Number ID** → set `WHATSAPP_PHONE_ID` in Railway
   - Copy your **Access Token** → set `WHATSAPP_TOKEN` in Railway

### 6.2 Set Up Webhook

1. WhatsApp → **Configuration** → **Webhook**
2. Set **Callback URL**:
   ```
   https://your-railway-url.up.railway.app/whatsapp
   ```
3. Set **Verify Token**: same value as `WHATSAPP_VERIFY_TOKEN` in Railway
4. Click **Verify** — Meta calls your `/whatsapp` GET endpoint
5. Subscribe to: **messages**

### 6.3 Test WhatsApp

Meta provides a test number. Send it a message — you should get an AI response.

---

## Part 7 — Creating Your First Admin Account

After deployment, call your register endpoint once:

```bash
curl -X POST https://your-railway-url.up.railway.app/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "mike", "password": "your_strong_password"}'
```

**Then protect /auth/register** — comment out or delete that endpoint so no one else can create admin accounts.

Login to get a token:
```bash
curl -X POST https://your-railway-url.up.railway.app/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "mike", "password": "your_strong_password"}'
```

Use the token in admin pages (your frontend handles this automatically).

---

## Part 8 — Database Migrations (When You Change Models)

Whenever you add/modify a column in `models.py`:

```bash
# 1. Generate migration script
alembic revision --autogenerate -m "describe what changed"

# 2. Apply to database
alembic upgrade head
```

Never manually edit the production database. Always use migrations.

---

## Part 9 — Security Checklist Before Going Live

- [ ] `SECRET_KEY` is a random 64-char hex string (not "supersecretkey")
- [ ] `.env` is in `.gitignore` and never committed to GitHub
- [ ] `ALLOWED_ORIGINS` only lists your real frontend URL (no `*`)
- [ ] `/auth/register` endpoint is disabled or removed after creating your admin account
- [ ] All admin routes require JWT (`Depends(verify_token)`)
- [ ] Rate limiting is active (via `slowapi`)
- [ ] HTTPS is enforced (Railway + Vercel do this automatically)
- [ ] AI prompt explicitly blocks diagnoses and prescriptions

---

## Part 10 — WhatsApp Conversation Flow Reference

```
User sends any message
         │
         ▼
   Check DB for conversation state
         │
   ┌─────┴──────────────────────────────────────────┐
   │                                                 │
state = "awaiting_confirm"            state = None (fresh)
   │                                                 │
   ▼                                                 ▼
 YES → move to "awaiting_address"    AI checks if message = order intent
  NO → cancel order                       │
   │                              Yes ──► Create order in DB
   ▼                              No  ──► General AI response (RAG)
state = "awaiting_address"
   │
   ▼
Save address → move to "awaiting_payment"
Show EcoCash details + total
   │
   ▼
state = "awaiting_payment"
   │
   ▼
User replies "DONE"
→ Mark payment = pending_verification
→ Mark order = processing
→ Reset state
→ Admin sees it in dashboard
```

---

## Part 11 — Scaling to Acess Pharmaceuticals (Phase 2)

Once Daily Health is live, you reuse this entire backend and add:

1. **New `business_type` field on User** — `retail` vs `distributor`
2. **B2B pricing table** — different prices for pharmacy clients vs public
3. **Client accounts** — pharmacies/hospitals register and get wholesale prices
4. **Bulk order logic** — minimum quantities, volume discounts
5. **Stock sync** — import from supplier spreadsheet via CSV upload endpoint

The AI chatbot, WhatsApp flow, and admin dashboard all carry over unchanged.

---

## Quick Reference — Common Commands

```bash
# Start backend locally
uvicorn app.main:app --reload

# Start frontend locally
npm run dev

# Apply DB migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "what changed"

# Add a product via API (with JWT token)
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Panado", "description": "Paracetamol 500mg", "price": 1.50, "stock": 200, "category": "painkillers"}'
```

---

*Built for Mike — Daily Health Pharmacy + Acess Pharmaceuticals project*
*Stack: FastAPI · PostgreSQL · Next.js · Groq (LLaMA 3) · WhatsApp Cloud API*
*Hosting: Railway (backend + DB) · Vercel (frontend) — Zero upfront cost*

