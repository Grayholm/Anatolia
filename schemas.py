from pydantic import BaseModel, Field, EmailStr
import models

class UserCreate(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)

class UserResponse(BaseModel):
    id: int
    email: str
    hashed_password: str
    role: models.UserRole

    class Config:
        orm_mode = True

class BookCreate(BaseModel):
    title: str = Field(..., description='Название книги')
    author: str = Field(..., description='Автор книги')
    published_year: int | None = Field(ge=0, le=2100, description='Год выпуска книги')

class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    published_year: int

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None