from fastapi import APIRouter, HTTPException, Depends, status
from app.services.database_service import User
from app.utils.helpers import hash_password
from app.utils.secrets import encrypt_secret, decrypt_secret
from sqlalchemy.orm import Session
from typing import Dict
from pydantic import BaseModel, Field, validator
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi_limiter.depends import RateLimiter
import os

router = APIRouter()

SECRET_KEY = os.getenv("JWT_SECRET", "changeme")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8)
    email: str
    @validator('email')
    def email_valid(cls, v):
        assert "@" in v, "Invalid email"
        return v

@router.post('/register', dependencies=[Depends(RateLimiter(times=3, seconds=60))])
def register_user(user: UserCreate):
    # Hash and encrypt password
    hashed = hash_password(user.password)
    encrypted = encrypt_secret(hashed)
    # Save user to DB (placeholder)
    return {'msg': 'User registered'}

@router.post('/login', dependencies=[Depends(RateLimiter(times=5, seconds=60))])
def login_user(user: UserCreate):
    # Validate user and password (placeholder)
    # On success, return JWT
    token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {'access_token': token}

@router.get('/premium')
def check_premium():
    # Placeholder: check if user is premium
    return {'is_premium': True} 