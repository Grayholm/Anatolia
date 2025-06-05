from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import ForeignKey
from enum import Enum

class Base(DeclarativeBase):
    pass

class UserRole(str, Enum):
    USER = 'user'
    ADMIN = 'admin'

class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    email: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str] = mapped_column()
    is_active: Mapped[bool] = mapped_column()
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)

class Library(Base):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column()
    author: Mapped[str] = mapped_column()
    published_year: Mapped[int] = mapped_column()
    owner_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
