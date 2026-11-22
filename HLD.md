# High-Level Design (HLD) — PawAdopt Pet Adoption Platform

## 1. System Overview
PawAdopt is a three-tier web application consisting of:
- **Frontend Client:** Static HTML, CSS, and JavaScript pages (`index.html`, `dashboard.html`) communicating via `fetch`.
- **Backend API:** FastAPI service handling authentication, JWT issuance, RBAC enforcement, business logic, and foreign-key data enrichment.
- **Database:** SQLite (`pet_adoption.db`) storing users, pets, adoption requests, and support tickets.

## 2. Architecture Flow
`Browser (HTML/CSS/JS)` ──HTTP/JSON (Bearer JWT)──▶ `FastAPI (Auth + RBAC + Routes)` ──SQLite (`sqlite3`)──▶ `pet_adoption.db`

## 3. Roles & Permissions (RBAC)
- **Guest (Unauthenticated):** Can view available pets (`GET /pets`) and support updates (`GET /support`); can register or log in.
- **Adopter:** Registered user role; can browse pets and support, submit adoption requests (`POST /adoptions`), and view their own adoption requests (`GET /adoptions`).
- **Admin:** Auto-seeded default admin on startup; can create, update, and delete pets, view all adoption requests with enriched adopter/pet data, update request status (`PATCH /adoptions/{id}`), and create/update support tickets.
