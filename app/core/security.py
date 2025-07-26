from datetime import datetime, timedelta
from typing import Optional
import secrets
import string
import hashlib

from jose import jwt

from app.core.config import JWT_SECRET_KEY, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    salt, stored_hash = hashed_password.split(':', 1)
    computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
    return computed_hash == stored_hash

def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = secrets.token_hex(8)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def generate_api_key() -> str:
    """Generate a secure API key."""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(32))
    return api_key