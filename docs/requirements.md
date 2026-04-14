# 📋 Technical Requirements - DineSphere

This document specifies the software and hardware environments required to run and contribute to the DineSphere project.

## 🐍 Software Requirements

### 1. Core Runtime
- **Python**: 3.8 or higher.
- **Django**: 6.0.3 (as specified in `requirements.txt`).
- **Operating System**: Cross-platform (Windows, macOS, Linux).

### 2. Database
- **SQLite (Primary)**: Included with Python; no separate installation required.
- **MongoDB (Optional)**: Required if `USE_MONGO=True` is set in `.env` for analytics and logging features.

### 3. Key Dependencies
- **python-dotenv**: Essential for loading environment variables.
- **Environment Config**: A pre-configured `.env` is included in the root directory for "zero-config" setup.
- **Pillow**: Required for restaurant image handling (banners/profiles).
- **Pymongo**: Required if connecting to a MongoDB instance.
- **Brevo SMTP**: Recommended service for sending reservation and cancellation emails.

---

## 💻 Hardware Requirements

- **Processor**: 1.6GHz or faster (dual-core recommended).
- **RAM**: 4GB Minimum (8GB recommended for concurrent DB operations).
- **Storage**: ~500MB for the project and local SQLite database.

---

## 🌐 Network Requirements

- **Internet Access**: Required for:
    - Cloning the repository.
    - Installing pip packages.
    - Sending emails via SMTP Relay (Brevo).
    - Optional MongoDB Atlas connections.

---

## 🔧 Developer Tools (Recommended)

- **IDE**: VS Code or PyCharm.
- **Git**: For version control.
- **Python-Venv**: For managing isolated environments.
- **Postman/Thunder Client**: For testing JSON endpoints in `drawerform.js`.
