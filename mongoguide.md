# 🍃 DineSphere MongoDB Guide

This guide helps you manage MongoDB for DineSphere, check its status, and view logs via terminal or MongoDB Compass.

---

## 🧭 1. Using MongoDB Compass

In your Compass "Connections" list, you might see multiple entries named `localhost:27017`. This usually happens if you've saved the connection multiple times.

### Which one to click?
1. **The Active Connection:** Look for the connection with the **green dot** or the one that allows you to expand its dropdown.
2. **Find the Database:** Once connected, look for the **`DineSphere`** database in the list.
3. **Open Logs:** Click on `DineSphere` -> `logs` to see the activity data.

> [!TIP]
> You can delete old/duplicate connections in Compass by clicking the three dots `...` next to the connection name and selecting **"Remove from Recents"** or **"Delete"**.

---

## 💻 2. Terminal: Checking if MongoDB is Running

If DineSphere says MongoDB is unavailable, check if the service is active.

**Windows (PowerShell/CMD):**
```powershell
# Check service status
Get-Service -Name MongoDB

# Start the service if it is stopped
net start MongoDB
```

**Verify Connection via Python (Quick Check):**
```bash
python -c "from pymongo import MongoClient; print('Connected!' if MongoClient('mongodb://localhost:27017/').admin.command('ping') else 'Failed')"
```

---

## 🐚 3. Basic `mongosh` Commands

If you have `mongosh` installed, you can query your logs directly from the terminal.

### Start the shell
```bash
mongosh
```

### Useful Commands (inside mongosh)
```javascript
// 1. Switch to the DineSphere database
use DineSphere

// 2. Show all collections
show collections

// 3. View the latest 5 logs
db.logs.find().sort({timestamp: -1}).limit(5)

// 4. Find logs for a specific event/user
db.logs.find({ "event": "admin" })

// 5. Count total logs
db.logs.count_documents({})

// 6. Clear all logs (Warning: Permanent!)
// db.logs.deleteMany({})

// 7. Exit
exit
```

---

## 🐍 4. View Logs via Python (Simple Step)

If `mongosh` pathing is tricky, use this command to print all logs to your terminal:

```bash
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Dinesphere.settings'); import django; django.setup(); from Restaurants.services.parser import get_user_logs, format_logs_to_text; print(format_logs_to_text(get_user_logs('admin')))"
```
*(Replace 'admin' with the username you want to check)*

---

## 🛠 Troubleshooting
- **Refused Connection:** Ensure `USE_MONGO=True` is in your `.env` and the service is started.
- **Empty Logs:** Activity is only logged when actions happen (e.g., adding a table, updating business info). Perform an action in the app, then check again.
