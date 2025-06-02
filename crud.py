from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from dotenv import load_dotenv
import models
import os
import schemas

load_dotenv()

router = APIRouter()

SECRET_KEY = os.getenv('SECRET_KEY', 'secret')
ALGORITHM = 'HS256'
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

async def get_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(select(models.Users).where(models.Users.email == email))
    return result.scalars().first()

async def create_user(session: AsyncSession, email: str, hashed_password: str):
    user = models.Users(email=email, hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def dependies(session: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        user = await get_user_by_email(session, email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        user_id = user.id
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate token')
    

@router.post('/books', response_model=schemas.BookResponse)
async def add_book(
        book: schemas.BookCreate,
        session: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
):
    user_id = dependies(token)
    try:
        new_book = models.Library(
            title = book.title,
            author = book.author,
            published_year = book.published_year,
            owner_id = user_id
        )
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=505, detail=f'Database Error: {str(e)}')
    
@router.get('/books', response_model=list[schemas.BookResponse])
async def get_books(session: AsyncSession = Depends(get_db)):
    result = await session.execute(select(models.Library))
    return result.scalars().all()

