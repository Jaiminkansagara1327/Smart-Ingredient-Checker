# 🍽️ FoodView - Smart Ingredient Checker

A modern, minimalist web application for analyzing food product ingredients with a warm, trustworthy cream-themed UI.

![FoodView Preview](https://img.shields.io/badge/Status-Active-success)
![React](https://img.shields.io/badge/React-18.2.0-blue)
![Django](https://img.shields.io/badge/Django-4.2.7-green)

## ✨ Features

- **📸 Image Upload** - Drag & drop or click to upload product images
- **🔗 URL Analysis** - Paste product URLs for instant analysis
- **📊 Comprehensive Analysis**:
  - Product information (name, brand, category)
  - One-line verdict
  - Suitability score (X/10)
  - Context-based suitability (Good for, Caution for, Not ideal for)
  - Grouped ingredient summary
  - Notable flags
- **🎨 Premium UI** - Warm cream color scheme designed for trust and ease of use
- **📱 Responsive Design** - Works seamlessly on desktop and mobile devices

## 🛠️ Tech Stack

### Frontend
- **React 18.2.0** - Modern UI library
- **Vite 5.0.0** - Fast build tool
- **Axios 1.6.0** - HTTP client
- **Custom CSS** - Warm cream design system

### Backend
- **Django 4.2.7** - Python web framework
- **Django REST Framework 3.14.0** - API toolkit
- **Django CORS Headers 4.3.0** - CORS handling
- **Pillow 10.1.0** - Image processing

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **Node.js 18+** and npm

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/foodview.git
cd foodview
```

2. **Backend Setup**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

3. **Frontend Setup** (in a new terminal)
```bash
cd frontend
npm install
npm run dev
```

4. **Open in browser**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/

## 📁 Project Structure

```
foodview/
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/   # React components
│   │   │   ├── Header.jsx
│   │   │   ├── UploadSection.jsx
│   │   │   └── ResultsSection.jsx
│   │   ├── App.jsx       # Main app component
│   │   ├── main.jsx      # Entry point
│   │   └── index.css     # Global styles (cream theme)
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── backend/              # Django backend
│   ├── foodview_api/    # Django project
│   │   ├── settings.py
│   │   └── urls.py
│   ├── analyzer/        # Analyzer app
│   │   ├── views.py     # API endpoints
│   │   └── urls.py
│   ├── manage.py
│   └── requirements.txt
│
└── README.md
```

## 🎯 API Endpoints

### Analyze Image
```http
POST /api/analyze/image/
Content-Type: multipart/form-data

Body:
- image: <image file>
```

### Analyze URL
```http
POST /api/analyze/url/
Content-Type: application/json

Body:
{
  "url": "https://example.com/product"
}
```

### Health Check
```http
GET /api/health/
```

## 🎨 Design System

The application uses a warm, trustworthy cream color palette:

- **Primary Background**: `#faf8f5` (Cream)
- **Secondary Background**: `#f5f2ed` (Light Beige)
- **Accent Primary**: `#d97706` (Warm Amber)
- **Accent Secondary**: `#92400e` (Dark Brown)
- **Success**: `#059669` (Green)
- **Warning**: `#d97706` (Amber)
- **Danger**: `#dc2626` (Red)

## 🔮 Future Enhancements

- [ ] Real ingredient analysis using OCR and NLP
- [ ] Product comparison feature
- [ ] User accounts and analysis history
- [ ] Dietary preference profiles
- [ ] Allergen detection and warnings
- [ ] Nutritional scoring algorithms
- [ ] Database of known products
- [ ] Mobile app versions

## 📝 Development

### Frontend Development
```bash
cd frontend
npm run dev      # Start dev server
npm run build    # Build for production
npm run preview  # Preview production build
```

### Backend Development
```bash
cd backend
source venv/bin/activate
python manage.py runserver           # Start server
python manage.py makemigrations      # Create migrations
python manage.py migrate             # Apply migrations
python manage.py createsuperuser     # Create admin user
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Design inspired by modern health and wellness applications
- Color palette chosen for trust and accessibility
- Built with modern web technologies

## 📧 Contact

Your Name - [@yourusername](https://twitter.com/yourusername)

Project Link: [https://github.com/yourusername/foodview](https://github.com/yourusername/foodview)

---

**Note**: This project currently uses mock data for demonstration. For production use, implement actual OCR for ingredient extraction and integrate with product databases.
