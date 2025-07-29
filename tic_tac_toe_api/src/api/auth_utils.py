"""Common authentication helpers: password hash/verify, JWT encoding/decoding."""
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError

# Constants (fetch from environment if available)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = 60 * 24  # One day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against the hash."""
    return pwd_context.verify(plain, hashed)

# PUBLIC_INTERFACE
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Encode a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=JWT_EXPIRES_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def decode_access_token(token: str) -> dict:
    """Decode a JWT access token, raise if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
