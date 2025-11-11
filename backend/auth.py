# auth.py - simple JWT auth helpers
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
import os

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET = os.getenv("JWT_SECRET", "change_this")
ALGO = "HS256"
ACCESS_EXPIRE_MINUTES = 60*24

def hash_password(pw: str):
    return pwd_ctx.hash(pw)

def verify_password(plain, hashed):
    return pwd_ctx.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGO)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return payload
    except JWTError:
        return None
