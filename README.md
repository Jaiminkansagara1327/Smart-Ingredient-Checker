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
- **Frontend:** React + Vite (Premium Minimalist UI)
- **Backend:** Django REST Framework
- **Intelligence:** OpenAI GPT-4o-mini + Custom Scorer
- **Database:** OpenFoodFacts + Local Product Cache

---

### ⚡ Quick Start

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

---

### � Configuration
Create a `.env` in `backend/` and add:
`OPENAI_API_KEY=your_key_here`

---

Developed with ❤️ by [Jaimin Kansagara](https://github.com/Jaiminkansagara1327)
