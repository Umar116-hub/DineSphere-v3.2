# DineSphere Account Architecture

This document explains the 3-tier account system implemented in DineSphere v3.2, detailing how Customers, Owners, and Staff are handled in the database and the application logic.

## 1. Account Roles (The 'User' Model)
All users in the system are instances of the `User` model (`UsersHandling.models.User`). The primary discriminator is the `role` field:

| Role | Backend Value | Description |
|---|---|---|
| **Customer** | `CUSTOMER` | The default user. Can search, favorite, and book restaurants. |
| **Owner** | `OWNER` | Business entity. Can register restaurants and manage them. Cannot book reservations. |
| **Staff** | `STAFF` | Employee of a restaurant. Can view the dashboard but has restricted management rights. |

## 2. Relationships & Profiles

### Customer Profile
- **Model:** `CustomerProfile` (1:1 with `User`)
- **Applies to:** `CUSTOMER` roles only.
- **Data:** Tracks total spent, reservation count, and loyalty tiers.
- **Rule:** If a user's role is `OWNER` or `STAFF`, they **do not** have a `CustomerProfile`.

### Business Linkage (RestaurantStaff)
- **Model:** `RestaurantStaff` (FK to `User` and `Restaurant`)
- **Applies to:** `OWNER` and `STAFF` roles.
- **Purpose:** Connects a human user to one or more business entities.
- **Role Field:** Distinguishes between the restaurant owner (full access) and employees (limited access).

## 3. Sophisticated Onboarding Flow

### Owner Registration
1. User signs up via the **List Restaurant** tab.
2. The account is created with `role='OWNER'`. No `CustomerProfile` is generated.
3. The user is redirected to the restaurant registration form to link their first business entity.

### Staff Automated Onboarding
To simplify business management, Owners can add staff by username or email:
- **If the user exists:** They are simply linked to the restaurant as a `STAFF` member.
- **If the user doesn't exist:** The system **automatically creates** a new `User` account:
    - **Role:** `STAFF`
    - **Default Password:** `DineSphere123!`
    - **Email:** `username@dinesphere.internal` (if not provided).
    - **Notification:** The owner is notified of the login credentials to pass to the employee.

## 4. Access Control (Guards)
Access is protected at two levels:
1. **View Level (Decorators):** 
    - `@customer_required`: Blocks Owners/Staff from booking.
    - `@restrict_access`: Blocks Customers from business dashboards.
2. **Model Level (Validation):**
    - `Booking.clean()`: Prevents non-customers from creating reservation records in the database.

---
*Created: April 2026*
