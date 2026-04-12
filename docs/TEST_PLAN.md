# DineSphere Test Plan

## Use Cases & Test Scenarios

### 1. Authentication Flows

#### TC-AUTH-001: User Registration
**Steps:**
1. Navigate to signup page (/uh/signup/)
2. Fill in username, email, password, confirm password
3. Click "Sign Up"
4. Verify user is created and redirected to login

**Expected:** User account created, success message shown

#### TC-AUTH-002: User Login
**Steps:**
1. Navigate to login page (/uh/login/)
2. Enter valid credentials
3. Click "Login"

**Expected:** User logged in, redirected to home page

#### TC-AUTH-003: User Logout
**Steps:**
1. Login as user
2. Click logout

**Expected:** Session cleared, redirected to home

---

### 2. Customer Flows

#### TC-CUST-001: Search Restaurants
**Steps:**
1. Navigate to home page (/)
2. Enter search query in search box
3. Select city from dropdown
4. Click "Search"

**Expected:** Search results displayed matching criteria

#### TC-CUST-002: View Restaurant Details
**Steps:**
1. Search for restaurants
2. Click on a restaurant card

**Expected:** Restaurant detail page with info, reviews, booking form

#### TC-CUST-003: Book a Table
**Steps:**
1. Navigate to restaurant page
2. Select date
3. Select time from dropdown
4. Select duration
5. Select table(s)
6. Click "Book Now"

**Expected:** Redirected to checkout page with booking summary

#### TC-CUST-004: Complete Payment/Checkout
**Steps:**
1. On checkout page
2. Fill card details (mock)
3. Click "Place Order"

**Expected:** Order success page with booking confirmation

#### TC-CUST-005: View My Bookings
**Steps:**
1. Login as customer
2. Navigate to Profile page (/profile/)
3. Check Pending, Finished, Cancelled tabs

**Expected:** Bookings displayed in correct tabs

#### TC-CUST-006: Cancel Booking
**Steps:**
1. Go to Profile page
2. Find pending booking
3. Click "Cancel" button
4. Confirm cancellation

**Expected:** Booking status changed to cancelled

#### TC-CUST-007: Post Review
**Steps:**
1. Go to restaurant page
2. Scroll to reviews section
3. Fill rating and comment
4. Submit review

**Expected:** Review saved, success message shown

#### TC-CUST-008: Add to Favorites
**Steps:**
1. Search for restaurants
2. Click heart icon on restaurant card

**Expected:** Restaurant added to favorites

---

### 3. Owner/Staff Flows

#### TC-OWNER-001: Access Business Dashboard
**Steps:**
1. Login as owner
2. Click "Business" in navigation

**Expected:** Analytics dashboard displayed

#### TC-OWNER-002: View Approval Status
**Steps:**
1. Go to business dashboard
2. Check approval notification banner

**Expected:** Green banner if approved, yellow if pending

#### TC-OWNER-003: Manage Tables
**Steps:**
1. Go to /business/tables/
2. Click "Add Table"
3. Fill table details
4. Save

**Expected:** Table added to list

#### TC-OWNER-004: Manage Staff
**Steps:**
1. Go to /business/staff-management/
2. Click "Add Staff"
3. Select user and role
4. Save

**Expected:** Staff member added

#### TC-OWNER-005: View Reservations
**Steps:**
1. Go to /business/reservations/
2. Check booking cards

**Expected:** All reservations listed with status

#### TC-OWNER-006: Update Business Info
**Steps:**
1. Go to /business/business-info/
2. Edit restaurant details
3. Save changes

**Expected:** Changes saved, success message shown

#### TC-OWNER-007: Add Holiday
**Steps:**
1. Go to /business/holidays/
2. Add holiday date and name
3. Save

**Expected:** Holiday added to list

---

### 4. Security Tests

#### TC-SEC-001: Unauthorized Access to Business Pages
**Steps:**
1. Logout
2. Try to access /business/analytics/

**Expected:** Redirected to login or 403 error

#### TC-SEC-002: Customer Cannot Access Owner Pages
**Steps:**
1. Login as customer
2. Try to access /business/

**Expected:** Permission denied or redirect

#### TC-SEC-003: SQL Injection Attempt
**Steps:**
1. Try search with SQL injection string

**Expected:** No error, safe query execution

---

## Test Results Log

| ID | Test Case | Status | Issues Found |
|----|-----------|--------|--------------|
| | | | |
