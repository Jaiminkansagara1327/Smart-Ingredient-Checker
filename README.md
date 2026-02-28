# 🛡️ Ingrexa: Smart Ingredient Analysis

**Decode what you eat.** Ingrexa is a high-performance, AI-driven platform that transforms complex food labels into clear, actionable health insights using GPT-4o and scientific scoring.

---

### 🚀 High Impact Features
- **📸 AI Scanner:** Instant OCR extraction from any product label.
- **📖 Layman Terms:** Balanced "Purpose vs. Risk" explanations for 3,000+ additives.
- **🌎 Auto-Translate:** Scan label in any language; analyze in English instantly.
- **📊 Scientific Scoring:** Real-time NOVA (processing) & Nutri-Score analysis.
- **🏠 Indian Priority:** Optimized search for Indian consumer brands and quality data.

---

### 🛠️ Tech Stack
- **Frontend:** React + Vite
- **Backend:** Django REST Framework
- **Intelligence:** OpenAI GPT-4o-mini + Custom Scorer
- **Database:** OpenFoodFacts + Local Product Cache (3000+ products, <1ms response)
- **Docs:** OpenAPI 3.0 via `drf-spectacular` (ReDoc)
- **Containerization:** Docker + Docker Compose (PostgreSQL + Django + React)

---

### 📄 API Documentation
Once the server is running, explore the API:

| URL | Description |
|:----|:------------|
| `http://localhost:8000/api/docs/` | **ReDoc** — professional, clean, read-only API docs |
| `http://localhost:8000/api/schema/` | **Raw OpenAPI JSON** — import into Postman |

---

### ⚡ Quick Start

**Option A: Local Development**

**1. Backend**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 manage.py runserver
```

**2. Frontend**
```bash
cd frontend
npm install && npm run dev
```

**Option B: Docker (Recommended)**
```bash
# Spins up PostgreSQL + Django + React in one command
docker-compose up --build
```
> Backend: `http://localhost:8000` | Frontend: `http://localhost:3000`

---

### 🧪 Automated Tests
```bash
cd backend
source venv/bin/activate
python manage.py test analyzer --verbosity=2
```
**41 tests** covering:
- ✅ Unit Tests — brand detection, ingredient scoring, quality filter
- ✅ API Tests — all 6 endpoints (health, search, analyze, contact, alternatives)
- ✅ Security Tests — SQL injection, XSS, input length, special chars

---

### ⚙️ Configuration
Create a `.env` in `backend/` and add:
```
OPENAI_API_KEY=your_key_here
SECRET_KEY=your_django_secret_key
DEBUG=True
```

---

Developed with ❤️ by [Jaimin Kansagara](https://github.com/Jaiminkansagara1327)
