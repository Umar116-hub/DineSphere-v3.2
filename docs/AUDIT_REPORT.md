# DineSphere Full Audit Report

**Date:** 2026-04-12  
**Scope:** All Django apps (Core, UsersHandling, Restaurants, Reservations)

---

## Critical Issues (Fix Immediately)

### 1. PCI Compliance Violation - Card Data Storage
**File:** `Reservations/models.py:25-27`  
**Issue:** Storing raw credit card numbers violates PCI DSS compliance.
```python
card_number = models.CharField(max_length=16)  # VIOLATION
name_on_the_card = models.CharField(max_length=50)
```
**Fix:** Remove fields, use payment processor tokens only.

---

### 2. Missing Null Check Crash
**File:** `Restaurants/views.py:129`  
**Issue:** Will crash with AttributeError if user has no RestaurantStaff record.
```python
if RestaurantStaff.objects.filter(user=request.user).first().role != "OWNER":
```
**Fix:** Add null check: `staff = RestaurantStaff.objects.filter(user=request.user).first(); if not staff or staff.role != "OWNER":`

---

### 3. Hardcoded Secrets
**File:** `Dinesphere/settings.py:24,134-135`
**Issue:** Hardcoded SECRET_KEY and MongoDB credentials.
**Fix:** Use environment variables.

---

### 4. Security: No Ownership Validation on Booking Update
**File:** `Reservations/views.py:72-76`  
**Issue:** Any authenticated user can update any booking matching the datetime.
**Fix:** Use `get_object_or_404(Booking, id=booking_id, customer=request.user)` before update.

---

### 5. Unhandled DoesNotExist Exception
**Files:** `Reservations/views.py:93`, `Reservations/views.py:122`  
**Issue:** `.get(name=...)` raises 500 error if restaurant not found.
**Fix:** Use `get_object_or_404(Restaurant, name=...)`

---

## High Priority Issues

### 6. Field Name Mismatch in ReviewForm
**File:** `Restaurants/forms.py:80-86`  
**Issue:** Widget references `review_text` but model field is `comment`.
**Fix:** Change `'review_text'` to `'comment'`.

---

### 7. Services Using Non-Existent Booking Fields
**File:** `Reservations/services.py:42-58, 81-92, 111-124`  
**Issue:** Functions reference fields that don't exist on Booking model (date, start_time, end_time, is_confirmed, locked_at, user).
**Fix:** Update to use actual model fields: `booking_start_datetime`, `booking_end_datetime`, `customer`, `status`.

---

### 8. Empty Redirect URL
**File:** `Restaurants/views.py:59`  
**Issue:** `redirect("")` redirects to empty string.
**Fix:** Use `redirect("home")`

---

### 9. Wrong URL Name in Redirect
**File:** `UsersHandling/services.py:46`  
**Issue:** Redirects to `'staff_list'` but URL name is `'staff_management'`.
**Fix:** Change to `redirect('staff_management')`

---

### 10. Missing @wraps on Decorator
**File:** `Restaurants/decorators.py:8`  
**Issue:** `@wraps` is commented out.
**Fix:** Uncomment `@wraps(view_func)`.

---

## Medium Priority Issues

### 11. N+1 Query in build_combined
**File:** `Core/utils.py:52-60`  
**Issue:** Queries ReviewSummary for each restaurant in loop.
**Fix:** Use `select_related()` or prefetch.

---

### 12. Logic Error in placeOrder_view
**File:** `Reservations/views.py:70`  
**Issue:** `naive_dt` is always truthy, `all()` check is meaningless.
**Fix:** Remove `naive_dt` from check.

---

### 13. Duplicate Import
**File:** `Reservations/views.py:6,11`  
**Issue:** `Restaurant` imported twice.
**Fix:** Remove duplicate import.

---

### 14. Debug Print Statements
**Files:** Multiple files with debug prints:
- `Core/views.py:48`
- `UsersHandling/views.py:59-60, 67, 82-85`
- `UsersHandling/services.py:97, 100`
- `Restaurants/views.py:63, 126, 130, 147, 248`
- `Restaurants/decorators.py:7, 10, 20`
- `Reservations/views.py:81, 83, 85, 101, 117`
**Fix:** Remove all debug prints.

---

### 15. Bare Except Clauses
**File:** `Restaurants/views.py:147`  
**Issue:** Bare `except:` catches KeyboardInterrupt, SystemExit.
**Fix:** Use specific exception: `except ValueError:`

---

### 16. Indentation Issues
**File:** `Restaurants/views.py` (multiple)  
**Issues:** Lines 126, 200-207, 265-270, 373-378, 404-409 have wrong indentation.
**Fix:** Fix indentation for `log_event` calls and `return redirect`.

---

### 17. Unused Empty Context Dict
**File:** `Restaurants/Services.py:244-248`  
**Issue:** Creates empty dict, prints, returns different dict.
**Fix:** Remove unused `context = {}`.

---

### 18. Incorrect Access Pattern
**File:** `Core/views.py:37`  
**Issue:** Accessing `user_profile.user.image` when `request.user.image` is direct.
**Fix:** Simplify to `request.user.image`.

---

### 19. No Error Handling for MongoDB
**File:** `Restaurants/services/logger.py:5`  
**Issue:** MongoDB insert can fail silently.
**Fix:** Add try/except with fallback.

---

### 20. logout_user View Issue
**File:** `UsersHandling/views.py:78-86`  
**Issue:** Returns `auth(request)` for non-POST instead of redirect.
**Fix:** Return `redirect("home")` for GET requests.

---

## Summary

| Severity | Count |
|----------|-------|
| Critical | 5 |
| High | 5 |
| Medium | 11 |
| **Total** | **21** |

**Fix Priority:**
1. **Immediate:** PCI compliance, hardcoded secrets, null check crash
2. **This Sprint:** DoesNotExist exceptions, ReviewForm field, service layer fields
3. **Next Sprint:** Debug prints, indentation, bare excepts

---

## QA Audit Findings - Manual Testing & UX Review

| ID | Area | File | Description | Severity |
|----|------|------|-------------|----------|
| 1 | Functional | `Reservations/services.py` | Registration happening without creating account first | Critical |
| 2 | Functional | `Core/views.py:37` | Random error on profile page (image access without null check) | Critical |
| 3 | Functional | `Core/templates/Core/home.html:88` | Search button not working (form action or JS issue) | Critical |
| 4 | Functional | `Reservations/views.py:501-507` | Duration always booking 2 hours regardless of selection | Critical |
| 5 | UX/UI | `Reservations/templates/Reservations/reservation.html:193` | Time picker accepts random minutes (7:32) instead of fixed 15/30/60 min intervals | Medium |
| 6 | UX/UI | `Reservations/views.py:76` | No success/receipt page after order placed | Medium |
| 7 | UX/UI | `Reservations/templates/Reservations/checkout.html:34` | Card number field accepts alphabets (no validation) | Medium |
| 8 | UX/UI | `Core/templates/Core/base.html` | Profile link shows lowercase 'p' instead of 'P' | Minor |
| 9 | Missing Feature | `Restaurants/views.py:251-261` | Restaurant owner gets no notification/status on approval | Medium |
| 10 | UX/UI | `Restaurants/templates/Restaurants/analytics.html:12-38` | Revenue and order stats showing static values instead of real data | Medium |
| 11 | UX/UI | `Restaurants/templates/Restaurants/reservations.html:72` | Unclear "Label" filter with meaningless options (Adventure/Iconic/Modern) | Minor |
| 12 | UX/UI | `Restaurants/templates/Restaurants/tables.html:150-164` | Analytics showing again in Table Size page (redundant/confusing) | Minor |
| 13 | UX/UI | `Restaurants/templates/Restaurants/base.html` | Random "kk" text appearing on every dashboard page | Minor |
| 14 | UX/UI | `Restaurants/templates/Restaurants/staff_management.html:86-91` | "Budget" and "Available" checkboxes unclear purpose on staff page | Minor |
| 15 | Missing Feature | `Restaurants/templates/Restaurants/staff_management.html:12-54` | Business page icon purpose unclear (no tooltip or label) | Minor |
| 16 | Functional | `Restaurants/templates/Restaurants/staff_management.html:99-144` | Staff management page shows static values ($560K, $150K) instead of real staff data | Medium |
| 17 | Functional | `Restaurants/context_processors.py:40-54` | Restaurant switch not updating orders (session not refreshing properly) | Critical |
| 18 | Database | All models | Dual database (SQLite + MongoDB) needs migration to MongoDB only | High |
| 19 | UX/UI | `Reservations/templates/Reservations/checkout.html` | No order confirmation/receipt page after successful payment | Medium |
| 20 | Accessibility | `Core/templates/Core/home.html:43-49` | User profile image missing alt text | Minor |
| 21 | UX/UI | `Restaurants/templates/Restaurants/analytics.html:14` | Typo: "Revenew" should be "Revenue" | Minor |
| 22 | UX/UI | `Restaurants/templates/Restaurants/tables.html:149` | "tablesize" tab label not capitalized (should be "Table Size") | Minor |
| 23 | Functional | `Restaurants/templates/Restaurants/staff_management.html:57` | Wrong model name block: shows "holidays" instead of "staff" | Minor |
| 24 | UX/UI | Multiple templates | Static placeholder values ($560K, $150K, $185K, $742K) on action cards | Medium |
| 25 | UX/UI | `Core/templates/Core/Profile.html:82-178` | Profile tab content nested incorrectly (orders inside profile-info) | Medium |
| 26 | UX/UI | `Restaurants/templates/Restaurants/staff_management.html:73-96` | Filter panel has irrelevant filters for staff (Labels, Available, Budget) | Minor |
| 27 | Security | `Reservations/templates/Reservations/checkout.html:34` | Card number stored as plain text (type="text" not password) | Medium |
| 28 | UX/UI | `Reservations/templates/Reservations/reservation.html:300-302` | "No Testimonails to show" typo + empty state not styled | Minor |
| 29 | UX/UI | `Restaurants/templates/Restaurants/analytics.html:104-146` | Large commented-out code blocks left in template | Minor |
| 30 | Responsiveness | All templates | No viewport meta tag check for mobile responsiveness | Medium |

---

## Database Migration Note

**Current State:** SQLite (relational data) + MongoDB (logs only)  
**Target State:** MongoDB only for all data

**Migration Strategy (don't break existing functionality):**
1. Keep SQLite as read-only fallback during transition
2. Create MongoDB schemas for all models
3. Migrate data in batches
4. Update queries to use MongoDB
5. Remove SQLite dependencies after verification

**Files to modify:**
- `Dinesphere/settings.py` - Database configuration
- All `models.py` files - Add MongoDB document models
- `Restaurants/services/mongo.py` - Expand collections
- Create migration script for data transfer