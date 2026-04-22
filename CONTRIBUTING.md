# Contributing to Ingrexa 🌟

First off, thank you for considering contributing to Ingrexa! It's people like you that make open source such a great community. We are thrilled to welcome contributions for GSSoC '26 and beyond.

## 📝 Code of Conduct
By participating in this project, you are expected to uphold our code of conduct. Please be respectful, welcoming, and collaborative.

## 🚀 Getting Started

### 1. Fork & Clone
1. Fork the repository to your own GitHub account using the "Fork" button at the top right of the repository page.
2. Clone the repository to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Ingrexa.git
   cd Ingrexa
   ```

### 2. Backend Setup (Django)
The backend is built with Python and Django.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Environment Variables**: We use a `.env` file for configuration and secrets.
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - *Note:* You do not need real API keys (like OpenAI or Razorpay) for basic local development unless you are explicitly testing those features. The application will use defaults or show clear errors if optional keys are missing.
   - **🚨 SECURITY CRITICAL: Never commit your `.env` file or hardcode secrets!**
5. Run database migrations:
   ```bash
   python manage.py migrate
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```

### 3. Frontend Setup
1. Open a new terminal tab/window and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the frontend development server:
   ```bash
   npm run dev
   ```

## 🛠️ Making Changes

1. **Create a Branch**: Always create a new branch for your feature, bug fix, or documentation update.
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Write Clean Code**: 
   - Follow PEP 8 guidelines for Python code.
   - Write meaningful, descriptive variable names.
   - Add comments only where the code isn't self-explanatory.
3. **Commit your changes**: Write clear, descriptive commit messages indicating what changed and why.
   ```bash
   git commit -m "feat: add user profile picture upload"
   ```

## 🛡️ Security Guidelines (CRITICAL)
- **Do NOT commit `.env` files, API keys, or database credentials.**
- If you discover a security vulnerability, please do **NOT** create a public GitHub issue. Reach out to the maintainer directly.
- Always use parameterized queries or Django's ORM to prevent SQL injection.

## 📤 Submitting a Pull Request
1. Push your branch to your forked repository:
   ```bash
   git push origin feature/your-feature-name
   ```
2. Go to the original Ingrexa repository and open a Pull Request (PR) against the `main` branch.
3. Provide a clear PR description explaining what your changes do. If it fixes an issue, link the issue (e.g., `Fixes #12`).
4. Be patient! A maintainer will review your code. You might be asked to make some tweaks before it gets merged.

Thank you for contributing! Let's build something awesome together.
