# DineSphere Fix Plan

**Created:** 2026-04-12  
**Based on:** AUDIT_REPORT.md findings (51 total issues)

---

## Phase 1: Critical Fixes (Immediate - 5 issues)

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 1 | Duration always 2h | `Reservations/views.py:501-507` | Fix end time calculation | TODO |
| 2 | Search button not working | `Core/templates/Core/home.html:88` | Check form action | TODO |
| 3 | Profile page error | `Core/views.py:37` | Add null check | TODO |
| 4 | Registration without account | `Reservations/services.py` | Add login_required | TODO |
| 5 | Restaurant switch bug | `Restaurants/context_processors.py:40-54` | Clear cache on change | TODO |

---

## Phase 2: Security & Compliance (5 issues)

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 6 | PCI violation - card storage | `Reservations/models.py:25-27` | Remove fields | TODO |
| 7 | Hardcoded secrets | `Dinesphere/settings.py:24,134` | Use env vars | TODO |
| 8 | Null check crash | `Restaurants/views.py:129` | Add null check | TODO |
| 9 | DoesNotExist exceptions | `Reservations/views.py:93,122` | Use get_object_or_404 | TODO |
| 10 | No ownership validation | `Reservations/views.py:72-76` | Verify ownership | TODO |

---

## Phase 3: UX/UI Fixes (8 issues)

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 11 | Time picker intervals | `Reservations/reservation.html:193` | Add step or dropdown | TODO |
| 12 | Card accepts alphabets | `Reservations/checkout.html:34` | Add pattern validation | TODO |
| 13 | Random kk text | `Restaurants/base.html` | Remove text | TODO |
| 14 | Profile lowercase p | `Core/base.html` | Capitalize | TODO |
| 15 | Revenew typo | `Restaurants/analytics.html:14` | Fix spelling | TODO |
| 16 | Testimonails typo | `Reservations/reservation.html:301` | Fix spelling | TODO |
| 17 | tablesize lowercase | `Restaurants/tables.html:149` | Capitalize | TODO |
| 18 | Wrong model name | `Restaurants/staff_management.html:57` | Change to staff | TODO |

---

## Phase 4: Functional & Quality (12 issues)

| # | Issue | File | Fix | Status |
|---|-------|------|-----|--------|
| 19 | Static values on cards | Multiple | Replace with real data | TODO |
| 20 | Remove debug prints | Multiple files | Find/replace all | TODO |
| 21 | Fix indentation | `Restaurants/views.py` | Fix lines 126, 200-207, etc | TODO |
| 22 | Bare except clauses | `Restaurants/views.py:147` | Use except ValueError | TODO |
| 23 | Duplicate imports | `Reservations/views.py:6,11` | Remove duplicate | TODO |
| 24 | Missing @wraps | `Restaurants/decorators.py:8` | Uncomment | TODO |
| 25 | Field name mismatch | `Restaurants/forms.py:80-86` | review_text → comment | TODO |
| 26 | Profile tab nesting | `Core/Profile.html:82-178` | Fix HTML structure | TODO |
| 27 | No success page | New file | Create success.html | TODO |
| 28 | Staff filters irrelevant | `Restaurants/staff_management.html` | Remove filters | TODO |
| 29 | Analytics static values | `Restaurants/analytics.html` | Connect real data | TODO |
| 30 | No approval notification | `Restaurants/views.py` | Add status message | TODO |

---

## Phase 5: Database Migration (MongoDB)

| # | Task | File | Status |
|---|------|------|--------|
| 31 | Create MongoDB models | All models.py | TODO |
| 32 | Migration script | migrate_to_mongo.py | TODO |
| 33 | Update mongo service | `Restaurants/services/mongo.py` | TODO |
| 34 | Dual-DB fallback | `Dinesphere/settings.py` | TODO |

---

## Summary

| Phase | Issues | Status |
|-------|--------|--------|
| 1 - Critical | 5 | 0/5 |
| 2 - Security | 5 | 0/5 |
| 3 - UX/UI | 8 | 0/8 |
| 4 - Functional | 12 | 0/12 |
| 5 - Database | 4 | 0/4 |
| **Total** | **34** | **0/34** |

---

## Execution Notes

**Priority Order:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5  
**Estimated Time:** ~20-25 hours  
**Can Parallelize:** Phase 5 (MongoDB) can run alongside others