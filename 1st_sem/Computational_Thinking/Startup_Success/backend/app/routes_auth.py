from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict
import os
import hashlib
import hmac
import secrets

router = APIRouter()

HERE = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(HERE, "data", "users.txt")


# --- Models ---

class AuthCredentials(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    username: str
    token: str
    message: str


class UserUpdateRequest(BaseModel):
    username: str
    password: str
    new_username: str | None = None
    new_password: str | None = None


class UserDeleteRequest(BaseModel):
    username: str
    password: str


class MessageResponse(BaseModel):
    message: str


# --- Simple file-based auth helpers ---

def ensure_users_file() -> None:
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as file:
            file.write("")


def normalize_username(username: str) -> str:
    return username.strip().lower()


def load_users() -> Dict[str, str]:
    ensure_users_file()
    users: Dict[str, str] = {}
    with open(USERS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            try:
                name, hashed = raw.split(":", 1)
            except ValueError:
                continue
            normalized = normalize_username(name)
            if not normalized:
                continue
            users[normalized] = hashed
    return users


def save_user(username: str, hashed_password: str) -> None:
    ensure_users_file()
    normalized = normalize_username(username)
    if not normalized:
        raise ValueError("Username cannot be empty.")
    with open(USERS_FILE, "a", encoding="utf-8") as file:
        file.write(f"{normalized}:{hashed_password}\n")


def write_users(users: Dict[str, str]) -> None:
    ensure_users_file()
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        for name in sorted(users):
            file.write(f"{name}:{users[name]}\n")


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, stored_hash = stored.split("$", 1)
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000).hex()
    return hmac.compare_digest(digest, stored_hash)


def create_session_payload(username: str, message: str) -> Dict[str, str]:
    return {
        "username": username,
        "token": secrets.token_urlsafe(32),
        "message": message,
    }


# --- Auth endpoints ---

@router.post("/auth/register", response_model=AuthResponse, tags=["Auth"])
def register_user(credentials: AuthCredentials):
    username = normalize_username(credentials.username)
    if not username or not credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    users = load_users()
    if username in users:
        raise HTTPException(status_code=409, detail="User already exists.")

    hashed_password = hash_password(credentials.password)
    save_user(username, hashed_password)
    return create_session_payload(username, "Registration successful.")


@router.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
def login_user(credentials: AuthCredentials):
    username = normalize_username(credentials.username)
    if not username or not credentials.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    users = load_users()
    stored_hash = users.get(username)
    if stored_hash is None or not verify_password(credentials.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return create_session_payload(username, "Login successful.")


@router.put("/auth/user", response_model=AuthResponse, tags=["Auth"])
def update_user(payload: UserUpdateRequest):
    username = normalize_username(payload.username)
    if not username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    if not payload.new_username and not payload.new_password:
        raise HTTPException(status_code=400, detail="Provide a new username or password to update.")

    users = load_users()
    stored_hash = users.get(username)
    if stored_hash is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(payload.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    updated_username = normalize_username(payload.new_username) if payload.new_username else username
    if not updated_username:
        raise HTTPException(status_code=400, detail="New username cannot be empty.")
    if updated_username != username and updated_username in users:
        raise HTTPException(status_code=409, detail="New username already exists.")

    updated_hash = hash_password(payload.new_password) if payload.new_password else stored_hash
    if updated_username != username:
        users.pop(username, None)
    users[updated_username] = updated_hash
    write_users(users)

    return create_session_payload(updated_username, "Account updated successfully.")


@router.delete("/auth/user", response_model=MessageResponse, tags=["Auth"])
def delete_user(payload: UserDeleteRequest):
    username = normalize_username(payload.username)
    if not username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    users = load_users()
    stored_hash = users.get(username)
    if stored_hash is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(payload.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    users.pop(username, None)
    write_users(users)

    return MessageResponse(message="Account deleted successfully.")
