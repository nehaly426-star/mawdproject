import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

app = FastAPI(title="Pet Adoption Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "pet_adoption.db"
SECRET_KEY = "lnmiit_college"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Security and Authentication Helpers


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, saved: str) -> bool:
    salt, hashed = saved.split("$")
    new_hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
    return new_hashed == hashed


def find_user(username: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM User WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user


def create_token(username: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    data = {
        "sub": username,
        "role": role,
        "exp": expire
    }
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token claims.")

        user = find_user(username)
        if user is None:
            raise HTTPException(status_code=401, detail="User account not found.")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired credentials.")


def require_role(allowed_roles: list[str], current_user, action_msg: str):
    if current_user["role"] not in allowed_roles:
        raise HTTPException(status_code=403, detail=f"Access denied: {action_msg}.")


# Database Schema Initialization


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS User (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            role TEXT CHECK(role IN ('admin', 'adopter', 'support')) NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Pet (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_name TEXT NOT NULL,
            image_url TEXT,
            adoption_fee REAL NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AdoptionRequest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            pet_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY(user_id) REFERENCES User(id),
            FOREIGN KEY(pet_id) REFERENCES Pet(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Support (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT NOT NULL,
            msg TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES User(id)
        )
    ''')

    conn.commit()
    conn.close()


def create_default_admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM User WHERE role = 'admin'")
    if cursor.fetchone()[0] == 0:
        hashed_pw = hash_password("admin123")
        cursor.execute('''
            INSERT INTO User (name, username, password, phone, role)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Administrator", "adminmeow", hashed_pw, "9999999999", "admin"))
        conn.commit()
        print("Default administrator account created (username: adminmeow, password: admin123).")

    conn.close()

def seed_sample_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Pet")
    if cursor.fetchone()[0] == 0:
        pets = [
            ("Bella", "https://placedog.net/500/400?id=3", 50),
            ("Max", "https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg", 75),
            ("Luna", "https://upload.wikimedia.org/wikipedia/commons/3/31/CalicoCat.jpg", 30),
            ("Whiskers", "https://upload.wikimedia.org/wikipedia/commons/4/4d/Cat_November_2010-1a.jpg", 25),
            ("Thumper", "https://commons.wikimedia.org/wiki/Special:FilePath/Small_European_Rabbit.jpg?width=500", 20),
            ("Kiwi", "https://commons.wikimedia.org/wiki/Special:FilePath/Ara-Zoo-Muenster.jpg?width=500", 120),
        ]
        cursor.executemany(
            "INSERT INTO Pet (pet_name, image_url, adoption_fee) VALUES (?, ?, ?)", pets
        )

    cursor.execute("SELECT COUNT(*) FROM Support")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO Support (ticket_id, msg, user_id) VALUES (?, ?, ?)",
            ("TCK-101", "All adopters must be 18+ and bring a valid ID when collecting a pet.", None),
        )

    conn.commit()
    conn.close()


initialize_database()
create_default_admin()
seed_sample_data()
print("Database and default administrator initialized successfully.")


# Request Schemas (Pydantic Models)


class RegisterUser(BaseModel):
    name: str
    username: str
    password: str
    phone: str | None = None


class PetCreateUpdate(BaseModel):
    pet_name: str
    image_url: str | None = None
    adoption_fee: float


class AdoptionCreate(BaseModel):
    pet_id: int


class AdoptionStatusUpdate(BaseModel):
    status: str


class SupportTicketCreate(BaseModel):
    ticket_id: str
    msg: str


class SupportTicketUpdate(BaseModel):
    msg: str


# System Health and Utility Endpoints


@app.get("/")
def root():
    return {"status": "ok", "message": "Pet Adoption API is operational. Refer to /docs for API documentation."}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


# Authentication Endpoints


@app.post("/register", status_code=201)
def register(user: RegisterUser):
    existing = find_user(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username is already registered.")

    hashed_pw = hash_password(user.password)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO User (name, username, password, phone, role)
        VALUES (?, ?, ?, ?, ?)
    ''', (user.name, user.username, hashed_pw, user.phone, "adopter"))
    conn.commit()
    conn.close()

    return {"message": f"Account created successfully for '{user.username}' with role 'adopter'."}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = find_user(form_data.username)

    if not user or not verify_password(form_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = create_token(user["username"], user["role"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "name": user["name"],
        "role": user["role"]
    }


# Pet Catalog Endpoints (Read: Public | Create, Update, Delete: Administrator Only)


@app.get("/pets")
def read_pets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pet")
    pets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return pets


@app.post("/pets", status_code=201)
def create_pet(pet: PetCreateUpdate, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may add pets")
    if pet.adoption_fee < 0:
        raise HTTPException(status_code=400, detail="Adoption fee cannot be negative.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Pet (pet_name, image_url, adoption_fee) VALUES (?, ?, ?)",
        (pet.pet_name, pet.image_url, pet.adoption_fee)
    )
    conn.commit()
    conn.close()
    return {"message": "Pet record added successfully."}


@app.put("/pets/{pet_id}")
def update_pet(pet_id: int, pet: PetCreateUpdate, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may update pets")
    if pet.adoption_fee < 0:
        raise HTTPException(status_code=400, detail="Adoption fee cannot be negative.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Pet SET pet_name = ?, image_url = ?, adoption_fee = ? WHERE id = ?",
        (pet.pet_name, pet.image_url, pet.adoption_fee, pet_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Pet record not found.")
    conn.commit()
    conn.close()
    return {"message": "Pet record updated successfully."}


@app.delete("/pets/{pet_id}")
def delete_pet(pet_id: int, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may delete pets")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Pet WHERE id = ?", (pet_id,))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Pet record not found.")
    conn.commit()
    conn.close()
    return {"message": "Pet record deleted successfully."}


# Adoption Request Endpoints


@app.post("/adoptions", status_code=201)
def create_adoption_request(req: AdoptionCreate, current_user=Depends(get_current_user)):
    require_role(["adopter"], current_user, "only registered adopters may submit adoption requests")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Pet WHERE id = ?", (req.pet_id,))
    pet = cursor.fetchone()
    if not pet:
        conn.close()
        raise HTTPException(status_code=404, detail="Pet record not found.")

    cursor.execute(
        "SELECT id FROM AdoptionRequest WHERE user_id = ? AND pet_id = ? AND status != 'rejected'",
        (current_user["id"], req.pet_id)
    )
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="An active adoption request already exists for this pet.")

    cursor.execute('''
        INSERT INTO AdoptionRequest (user_id, pet_id, status)
        VALUES (?, ?, ?)
    ''', (current_user["id"], req.pet_id, "pending"))
    conn.commit()
    conn.close()
    return {"message": "Adoption request submitted successfully."}


@app.get("/adoptions")
def view_adoption_requests(current_user=Depends(get_current_user)):
    conn = get_connection()
    cursor = conn.cursor()

    if current_user["role"] == "admin":
        cursor.execute("SELECT * FROM AdoptionRequest")
    elif current_user["role"] == "adopter":
        cursor.execute("SELECT * FROM AdoptionRequest WHERE user_id = ?", (current_user["id"],))
    else:
        conn.close()
        raise HTTPException(status_code=403, detail="Access denied: insufficient permissions to view adoption requests.")

    requests_rows = cursor.fetchall()

    cursor.execute("SELECT id, name, username, phone, role FROM User")
    users_rows = cursor.fetchall()

    cursor.execute("SELECT id, pet_name, image_url, adoption_fee FROM Pet")
    pets_rows = cursor.fetchall()
    conn.close()

    enriched_requests = []

    # Resolve foreign keys (user_id and pet_id) using nested loops
    for req in requests_rows:
        matched_user = None
        matched_pet = None

        for u in users_rows:
            if u["id"] == req["user_id"]:
                matched_user = {
                    "id": u["id"],
                    "name": u["name"],
                    "username": u["username"],
                    "phone": u["phone"],
                    "role": u["role"]
                }
                break

        for p in pets_rows:
            if p["id"] == req["pet_id"]:
                matched_pet = {
                    "id": p["id"],
                    "pet_name": p["pet_name"],
                    "image_url": p["image_url"],
                    "adoption_fee": p["adoption_fee"]
                }
                break

        enriched_requests.append({
            "id": req["id"],
            "status": req["status"],
            "adopter": matched_user,
            "pet": matched_pet
        })

    return enriched_requests


@app.patch("/adoptions/{request_id}")
def update_adoption_status(request_id: int, body: AdoptionStatusUpdate, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may update adoption request status")
    if body.status not in ("pending", "approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'pending', 'approved', or 'rejected'.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE AdoptionRequest SET status = ? WHERE id = ?", (body.status, request_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Adoption request not found.")
    conn.commit()
    conn.close()
    return {"message": f"Adoption request status updated to '{body.status}'."}


# Support Ticket Endpoints (Read: Public | Create and Update: Administrator Only)


@app.get("/support")
def get_support_tickets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Support")
    tickets = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tickets


@app.post("/support", status_code=201)
def create_support_ticket(ticket: SupportTicketCreate, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may create support tickets")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Support (ticket_id, msg, user_id) VALUES (?, ?, ?)",
        (ticket.ticket_id, ticket.msg, current_user["id"])
    )
    conn.commit()
    conn.close()
    return {"message": "Support ticket created successfully."}


@app.put("/support/{ticket_id}")
def update_support_ticket(ticket_id: str, ticket: SupportTicketUpdate, current_user=Depends(get_current_user)):
    require_role(["admin"], current_user, "only administrators may update support tickets")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE Support SET msg = ? WHERE ticket_id = ?", (ticket.msg, ticket_id))
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Support ticket not found.")
    conn.commit()
    conn.close()
    return {"message": "Support ticket updated successfully."}
