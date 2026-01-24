# FoodView - Smart Ingredient Checker

A modern web application for analyzing food product ingredients with a warm, trustworthy UI.

## Tech Stack

- **Frontend**: React 18.2.0 + Vite
- **Backend**: Django 4.2.7 + REST Framework
- **Design**: Warm cream theme with responsive layout

## Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Features

- Image upload with drag & drop
- URL analysis
- Ingredient breakdown
- Suitability scoring
- Responsive design
