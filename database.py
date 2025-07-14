from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Numeric, Integer, DateTime
from sqlmodel import SQLModel, Field, Session
from typing import Optional

DATABASE_URL = "postgresql+asyncpg://postgres:4585@localhost:5433/coffee"
engine = create_async_engine(DATABASE_URL, echo=True)
new_async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Drink(Base):
    __tablename__ = 'drink'

    id_drink: Mapped[int] = mapped_column(primary_key=True)
    name_drink: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)

    ingredients: Mapped[list['DrinkIngredient']] = relationship(back_populates='drink')
    orders: Mapped[list['Order']] = relationship(back_populates='drink')


class Ingredient(Base):
    __tablename__ = 'ingredient'

    id_ingredient: Mapped[int] = mapped_column(primary_key=True)
    name_ingredient: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)

    drinks: Mapped[list['DrinkIngredient']] = relationship(back_populates='ingredient')
    inventory: Mapped[Optional['Inventory']] = relationship(back_populates='ingredient')


class DrinkIngredient(Base):
    __tablename__ = 'drink_ingredient'

    id_drink: Mapped[int] = mapped_column(ForeignKey('drink.id_drink', ondelete='CASCADE'), primary_key=True)
    id_ingredient: Mapped[int] = mapped_column(ForeignKey('ingredient.id_ingredient'), primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)

    drink: Mapped['Drink'] = relationship(back_populates='ingredients')
    ingredient: Mapped['Ingredient'] = relationship(back_populates='drinks')


class Inventory(Base):
    __tablename__ = 'inventory'

    id_ingredient: Mapped[int] = mapped_column(ForeignKey('ingredient.id_ingredient', ondelete='CASCADE'),
                                               primary_key=True)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    ingredient: Mapped['Ingredient'] = relationship(back_populates='inventory')


class Order(Base):
    __tablename__ = 'orders'

    id_order: Mapped[int] = mapped_column(primary_key=True)
    id_drink: Mapped[int] = mapped_column(ForeignKey('drink.id_drink'), nullable=False)
    sugar_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default='now()')

    drink: Mapped['Drink'] = relationship(back_populates='orders')


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with new_async_session() as session:
        yield session




