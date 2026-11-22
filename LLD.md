# Low-Level Design (LLD) — PawAdopt Pet Adoption Platform

## 1. Database Schema (`pet_adoption.db`)
- **`User`**: `id` (PK), `name`, `username` (UNIQUE), `password` (`salt$hash` via PBKDF2-HMAC-SHA256), `phone`, `role` (`admin`, `adopter`, `support`).
- **`Pet`**: `id` (PK), `pet_name`, `image_url`, `adoption_fee`.
- **`AdoptionRequest`**: `id` (PK), `user_id` (FK -> `User.id`), `pet_id` (FK -> `Pet.id`), `status` (`pending`, `approved`, `rejected`).
- **`Support`**: `id` (PK), `ticket_id`, `msg`, `user_id` (FK -> `User.id`).

## 2. Authentication & Authorization
- **Login (`POST /login`):** Verifies password with `verify_password` and signs a JWT (`HS256`, 30-minute expiry) containing `sub` (username) and `role`.
- **Authentication (`get_current_user`):** Decodes and validates JWT, loads user from SQLite, or raises `401 Unauthorized`.
- **Authorization (`require_role`):** Checks `current_user["role"]` against allowed roles; raises `403 Forbidden` if unauthorized.

## 3. Key Endpoints & Logic
- **Pets:** `GET /pets` (public); `POST /pets`, `PUT /pets/{pet_id}`, `DELETE /pets/{pet_id}` (`admin` only).
- **Adoptions (`GET /adoptions`):** Filters rows by `user_id` for `adopter` or returns all rows for `admin`. Uses nested loops over `AdoptionRequest`, `User`, and `Pet` rows to attach `adopter` and `pet` dictionaries to each request before returning.
- **Support:** `GET /support` (public); `POST /support`, `PUT /support/{ticket_id}` (`admin` only).