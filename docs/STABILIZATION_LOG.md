# DineSphere Stabilization Changelog

This file tracks all critical fixes and structural improvements made to the DineSphere platform to ensure stability and professional-grade performance.

## [2026-04-12] - System Stabilization & Role Separation

### 🛠️ Architecture & Account System
- **Strict Role Separation:** Implemented the "One User, One Role" policy. Users are now either `CUSTOMER`, `OWNER`, or `STAFF`.
- **Model Hardening:** Added `clean()` and `full_clean()` logic to the `Booking` model to prevent non-customers from making reservations.
- **Role Expansion:** Added `STAFF` to the `User` model role choices.
- **Automated Onboarding:** Enhanced staff management to auto-create `User` accounts for new employees added by owners.

### 🐛 Dashboard & Analytics Fixes
- **Backend Analytics Fix:** Resolved critical 500 errors in `getAnalytics` by correcting invalid field references (`user` → `customer`) and replacing database-level `Avg` calls on dynamic properties with Python-based calculations.
- **Template Safety:** Implemented image existence checks in `analytics.html` and `Profile.html` to prevent template crashes when profile pictures are missing.
- **Context Fix:** Resolved a `NameError` in `context_processors.py` that caused dashboard crashes for certain users.

### 🛡️ Access Control & Routing
- **New Decorator:** Created `@customer_required` to strictly protect the booking lifecycle from business accounts.
- **Reservation Guard:** Applied role-based visibility to the Home and Reservation pages, hiding search and booking UI from Owners and Staff.
- **Cancellation Namespace Fix:** Resolved a 404 error in the reservation cancellation flow by correcting URL mapping.

### 📝 Documentation
- **Account Architecture:** Created [ACCOUNT_ARCHITECTURE.md](file:///c:/Users/Admin/Documents/DineSphere-v3.2/docs/ACCOUNT_ARCHITECTURE.md) detailing the 3-tier account system.
- **Stabilization Log:** Initialized this log to keep track of system health improvements.

---
*End of Log for April 12, 2026*
