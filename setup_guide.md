# 📦 Project Setup Guide

This document provides step-by-step instructions to clone, set up, and run the project in a local development environment. DineSphere requires practically zero configuration because it relies on standard Python packages and a local SQLite database!

---

## 🚀 Prerequisites

Ensure the following are installed:
* Python (>= 3.8 recommended)
* Git
* MongoDB (optional — required only for logging & analytics features)

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

**DineSphere now includes a pre-configured `.env` file!** 

For standard local development, you do not need to do anything. The email system, database settings, and security keys are already set up to work right out of the box.

*If you need to use your own SMTP (Email) or MongoDB settings, you can edit the `.env` file in the root directory.*

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

## 🍃 6. MongoDB Setup (Optional — for Logging & Analytics)

MongoDB is used for **activity logging** (tracking staff actions like adding tables, holidays, updating business info) and allows owners to **download their activity logs** as text files.

### Install & Start MongoDB

**Windows:**
```powershell
# Install MongoDB Community Edition from https://www.mongodb.com/try/download/community
# Then start the service:
net start MongoDB
```

**macOS (Homebrew):**
```bash
brew install mongodb-community
brew services start mongodb-community
```

**Linux:**
```bash
sudo systemctl start mongod
```

### Enable MongoDB in DineSphere

Edit the `.env` file in the project root and ensure these values are set:
```
USE_MONGO=True
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=DineSphere
```

### Verify Connection

You can verify the MongoDB connection by running:
```bash
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dinesphere.settings'); import django; django.setup(); from Restaurants.services.mongo import is_mongo_available; print(f'MongoDB available: {is_mongo_available()}')"
```

### Migrate Existing Data to MongoDB (Optional)

If you already have data in SQLite and want to mirror it to MongoDB:
```bash
python migrate_to_mongo.py
```

### What MongoDB Logs

When enabled, MongoDB automatically records:
- 🏪 Restaurant registrations & updates
- 🪑 Table additions & modifications
- 🎉 Holiday additions & updates
- 👥 Staff member additions
- 📊 Business info changes

Owners can download their activity logs from the dashboard via the **Download Logs** button.

> **Note:** MongoDB is fully optional. If `USE_MONGO=False` (the default) or MongoDB is not running, DineSphere works perfectly fine using just SQLite — logging features will simply be disabled.

---

## ▶️ 7. Run Development Server

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
* **MongoDB connection errors**: Ensure `mongod` service is running. If you don't need logging, set `USE_MONGO=False` in `.env`.
