# 🛡️ Ingrexa: Smart Ingredient Analysis

**Decode what you eat.** Ingrexa is a high-performance platform that transforms complex food labels into clear, actionable health insights using AI and scientific scoring.

---

### 🌟 Our Vision & Philosophy
- **Health First**: We believe health should never be compromised. Our mission is to provide transparency so you know exactly what goes into your body.
- **Free Forever**: Ingrexa is committed to remaining free for everyone, for a lifetime. Access to health information is a right, not a privilege.
- **Keep it Simple**: We prioritize a simple, minimalist design. No clutter—just the insights you need to make better health choices.

---

### 🚀 Live Features
- **🔍 Smart Search**: Instantly find 3,000+ products (optimized for Indian brands).
- **🧪 AI Insights**: Get "Purpose vs. Risk" explanations for complex additives in plain English.
- **📊 Scientific Scoring**: Real-time health scoring based on processing levels (NOVA group).
- **💡 Better Choices**: Don't just see the bad—find healthier alternatives for your favorite snacks.

---

### 🛠️ Tech Stack (The Simple Version)
- **Frontend**: React (The user interface)
- **Backend**: Django (The brain that processes data)
- **AI**: OpenAI GPT-4o-mini (The expert analysis)
- **Database**: OpenFoodFacts (The world's largest food database)

---

### ⚡ Quick Start for Beginners

Getting started is easy! Follow these steps to run Ingrexa on your computer:

#### 1. Pre-requisites
Make sure you have [Python](https://www.python.org/) and [Node.js](https://nodejs.org/) installed.

#### 2. Setup the Backend (The Brain)
```bash
cd backend
python3 -m venv venv           # Create a virtual environment
source venv/bin/activate       # Activate it (Windows users: venv\Scripts\activate)
pip install -r requirements.txt # Install dependencies
cp .env.example .env           # Create your environment file
python3 manage.py migrate      # Prepare the database
python3 manage.py runserver    # Start the engine!
```

#### 3. Setup the Frontend (The Interface)
Open a **new terminal window** and run:
```bash
cd frontend
npm install                    # Install dependencies
npm run dev                    # Start the app!
```
Now open `http://localhost:3000` in your browser! 🎉

---

### 🤝 Contributing
Want to help build the future of food transparency? We love contributors!
Please read our [**Contributing Guidelines**](CONTRIBUTING.md) to get started.

Developed with ❤️ by [Jaimin Kansagara](https://github.com/Jaiminkansagara1327)
