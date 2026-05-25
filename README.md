<div align="center">

# 🛡️ Ingrexa — Smart Ingredient Analysis

**Decode what you eat.**

Ingrexa transforms complex food labels into clear, actionable health insights using AI and scientific scoring — free, forever.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![GSSoC 2026](https://img.shields.io/badge/GSSoC-2026-orange.svg)](https://gssoc.girlscript.tech/)
[![Made with Django](https://img.shields.io/badge/Backend-Django-green)](https://djangoproject.com)
[![Made with React](https://img.shields.io/badge/Frontend-React-blue)](https://reactjs.org)

</div>

---

## 📖 Table of Contents

- [Vision & Philosophy](#-vision--philosophy)
- [Live Features](#-live-features)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
  - [Prerequisites](#1-prerequisites)
  - [Backend Setup](#2-backend-setup)
  - [Frontend Setup](#3-frontend-setup)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---


## 🌟 Vision & Philosophy

| Principle | What it means |
|-----------|--------------|
| **Health First** | Transparency so you know exactly what goes into your body — no hidden risks. |
| **Free Forever** | Access to health information is a right, not a privilege. Ingrexa will always be free. |
| **Keep it Simple** | A minimal, clutter-free design. Just the insights you need to make better choices. |

---

### 🚀 Live Features
- **🔍 Smart Search**: Instantly find 3,000+ products (optimized for Indian brands).
- **🧪 AI Insights**: Get "Purpose vs. Risk" explanations for complex additives in plain English.
- **📊 Scientific Scoring**: Real-time health scoring based on processing levels (NOVA group).
- **💡 Better Choices**: Don't just see the bad—find healthier alternatives for your favorite snacks.

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| Frontend | React | User interface |
| Backend | Django | Core application logic |
| AI | OpenAI GPT-4o-mini | Ingredient analysis |
| Database | OpenFoodFacts | World's largest food database |
| Cache / Queue | Redis + Celery | Async analysis tasks |
| Auth / Storage | Supabase | Secure data layer |

---


## ⚡ Quick Start

### 1. Prerequisites

Make sure you have the following installed:

- [Python 3.9+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)
- [Git](https://git-scm.com/)

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Jaiminkansagara1327/Smart-Ingredient-Checker.git
cd Smart-Ingredient-Checker

# Navigate to backend
cd backend

# Create and activate a virtual environment
python3 -m venv venv

# Mac / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys (see Environment Variables section below)

# Run database migrations
python3 manage.py migrate

# Start the development server
python3 manage.py runserver
```

> The backend will be running at `http://localhost:8000`

### 3. Frontend Setup

Open a **new terminal window** and run:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

> Open [http://localhost:3000](http://localhost:3000) in your browser. 🎉

---

## 📁 Project Structure

```
Smart-Ingredient-Checker/
├── backend/               # Django application
│   ├── .env.example       # Environment variable template
│   └── requirements.txt   # Python dependencies
├── frontend/              # React application
├── docs/                  # Project documentation & memory
├── docker-compose.yml     # Docker configuration (Redis, Celery)
├── CONTRIBUTING.md        # Contribution guidelines
└── README.md
```

---


## 📄 License

Distributed under the [GNU General Public License v3.0](LICENSE).

---

## 🤝 Contributing
Want to help build the future of food transparency? We love contributors!
Please read our [**Contributing Guidelines**](CONTRIBUTING.md) to get started.

Developed with ❤️ by [Jaimin Kansagara](https://github.com/Jaiminkansagara1327)
