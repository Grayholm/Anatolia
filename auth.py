from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from dotenv import load_dotenv
import crud
import schemas
import os

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
ALGORITHM = 'HS256'

pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

@router.post('/auth/register', response_model = schemas.UserResponse)
async def register(user: schemas.UserCreate, session: AsyncSession = Depends(get_db)):
    db_user = await crud.get_user_by_email(session, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    return await crud.create_user(session, user.email, hashed_password)

@router.post('/auth/login', response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: AsyncSession = Depends(get_db)):
    user = await crud.get_user_by_email(session, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Email not registered")
    
    token = create_access_token(data={'sub': user.email})
    return {'token': token, "token_type": "bearer"}