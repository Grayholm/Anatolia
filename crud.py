from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
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
    user = result.scalars().first()
    return user

async def create_user(session: AsyncSession, email: str, hashed_password: str):
    user = models.Users(email=email, hashed_password=hashed_password, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_current_user(session: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')
        user = await get_user_by_email(session, email)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate token')
    

@router.post('/books', response_model=schemas.BookResponse, tags=['Библиотека'])
async def add_book(
        book: schemas.BookCreate,
        session: AsyncSession = Depends(get_db),
        user: str = Depends(get_current_user)
):
    try:
        new_book = models.Library(
            title = book.title,
            author = book.author,
            published_year = book.published_year,
            owner_id = user.id
        )
        session.add(new_book)
        await session.commit()
        await session.refresh(new_book)
        return new_book
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=505, detail=f'Database Error: {str(e)}')
    
@router.get('/books', response_model=list[schemas.BookResponse], tags=['Библиотека'])
async def get_books(session: AsyncSession = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    result = await session.execute(select(models.Library).where(models.Library.owner_id == current_user.id))
    return result.scalars().all()

@router.get('/books/{book_id}', response_model=schemas.BookResponse, tags=['Админ Панель'])
async def get_book(book_id: int, session: AsyncSession = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    result = await session.execute(select(models.Library).where(models.Library.id == book_id))
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')
    
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    try:
        return book
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'{str(e)}')

@router.delete('/books/{book_id}', tags=['Библиотека'])
async def delete_book(book_id: int, session: AsyncSession = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    result = await session.execute(select(models.Library).where(models.Library.id == book_id))
    book = result.scalars().first()
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')
    
    if book.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own books"
        )

    try:
        await session.delete(book)
        await session.commit()
        return {'success': f'Book {book_id} successfully deleted'}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f'{str(e)}')
    
@router.delete('/adminpanel/{user_id}', summary='Delete user by ID (Admin only)', tags=['Админ Панель'])
async def delete_user(user_id: int, session: AsyncSession = Depends(get_db), current_user: schemas.UserResponse = Depends(get_current_user)):
    if current_user.role != models.UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
    )

    user = await session.get(models.Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
        
    try:
        await session.execute(delete(models.Library).where(models.Library.owner_id == user_id))

        await session.delete(user)
        await session.commit()
        return {'success': f'User {user.id} successfully deleted'}
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f'{str(e)}'
        )