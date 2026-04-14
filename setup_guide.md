# 📦 Project Setup Guide

This document provides step-by-step instructions to clone, set up, and run the project in a local development environment. DineSphere requires practically zero configuration because it relies on standard Python packages and a local SQLite database!

---

## 🚀 Prerequisites

Ensure the following are installed:
* Python (>= 3.8 recommended)
* Git

---

## 📥 1. Clone Repository  

**Using HTTPS:**
```bash
git clone https://github.com/Umar116-hub/DineSphere-v3.2/tree/fix/full-project-overhaul

cd DineSphere-v3
```

---

## 🐍 2. Create & Activate Virtual Environment  

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

---

Ensure you are inside your virtual environment, then install all project requirements:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🔑 4. Environment Configuration  

DineSphere uses environment variables for sensitive settings like emails and security keys.

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```
   *(On Windows, use `copy .env.example .env`)*

2. **Open `.env`** in your text editor and fill in your details:
   - **SMTP Settings**: Required for sending confirmation emails. We recommend [Brevo](https://www.brevo.com/).
   - **Secret Key**: You can keep the default for local development.

---

## 🗄️ 5. Apply Migrations

Set up the default SQLite database:
```bash
python manage.py makemigrations
python manage.py migrate
```

*(Optional)* Create an admin account to access the backend control panel:
```bash
python manage.py createsuperuser
```

---

## ▶️ 5. Run Development Server

Start the application!
```bash
python manage.py runserver
```

**🌐 Access the Application:**
Open your browser and navigate to `http://127.0.0.1:8000/`

---

## 🛠 Troubleshooting

* **Server crashes on launch**: Make sure your virtual environment `(venv)` is activated.
* **Port 8000 already in use**: Try starting the server on a different port using `python manage.py runserver 8001`
* **Static files missing**: If CSS/JS are weird, run `python manage.py collectstatic` (only necessary for production deployments).
