from decimal import Decimal
from typing import Annotated, List
from fastapi import FastAPI, HTTPException, Depends, Body
from pydantic import BaseModel, Field
from sqlalchemy import select, Numeric, TIMESTAMP, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, joinedload, query
from sqlalchemy import ForeignKey, String, Numeric, Integer, DateTime
from contextlib import asynccontextmanager
from typing import Optional
import asyncpg
import uvicorn
from datetime import datetime


# Конфигурация подключения
POSTGRES_CONFIG = {
    "user": "postgres",
    "password": "4585",
    "host": "localhost",
    "port": "5433",
    "database": "coffee"
}


SQLALCHEMY_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
ASYNCPG_DATABASE_URL = f"postgres://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"

# Инициализация SQLAlchemy hold connect асинхронный движок
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
# Создаем фабрику сессий для взаимодействия с базой данных,
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


#DeclarativeBase: Основной класс для всех моделей, от которого будут наследоваться все таблицы
class Base(DeclarativeBase):
    pass

#(SQLModel, table=True) сообщает что модель таблицы должна представлять базу данных, почему mapped
# почему я делала не через SQLModel
# mapped для явного указания типа данных в новой версии
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
    #created_at: Mapped[DateTime] = mapped_column(DateTime , server_default='now()')
    created_at: Mapped[DateTime] = mapped_column(TIMESTAMP , server_default=func.now())

    drink: Mapped['Drink'] = relationship(back_populates='orders')



class DrinkGetSchema(BaseModel): #падантик модель схема данных для определения структуры данных которую возвращает или ожидает фастапи
    name_drink: str
    price: float

class OrderGetSchema(BaseModel):
    id_drink: int
    id_order: int
    payment_status: str
    created_at: datetime
    drink: DrinkGetSchema #drink relationship from modeldb order

class OrderPostSchema(BaseModel):
    id_drink: int
    sugar_amount: int = Field(..., ge=0, le=5)

class IngredientGetSchema(
    BaseModel):
    id_ingredient: int
    name_ingredient: str
    unit: str

class IngredientDrinkGetSchema(
    BaseModel):
    id_ingredient: int
    id_drink: int
    drink: DrinkGetSchema
    ingredient: IngredientGetSchema

class InventoryGetSchema(
    BaseModel):
    id_ingredient: int
    quantity: float
    ingredient: IngredientGetSchema

    class Config:
        from_attributes = True  # считать поля из их атрибутов при передаче орм объектов


@asynccontextmanager
async def lifespan(app: FastAPI): #выполняется при запуске и при завершении
    # Проверка подключения при старте
    try:
        conn = await asyncpg.connect(ASYNCPG_DATABASE_URL)
        await conn.close()
        print("Подключение успешно!")
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        raise RuntimeError("Не удалось подключиться")

    # Создание таблиц
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Очистка при завершении
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# создание сессии которая хранит объекты в памяти и отслеживает изменения в данных, использует движок для взаимодействия с БД
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session # предоставление одной сессии на один запрос

#SessionDep = Annotated[AsyncSession, Depends(get_db)] #можно удалить

@app.post("/setup")
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database tables recreated"}

@app.get("/Drinks", response_model=list[DrinkGetSchema])
async def get_drinks(session: AsyncSession=Depends(get_db)):
    stmt = select(Drink)
    result = await session.execute(stmt)
    drinks = result.scalars().all()
    return drinks

@app.get("/Ingredients", response_model=list[IngredientGetSchema])
async def get_ingredients(session: AsyncSession=Depends(get_db)):
    stmt = select(Ingredient)
    result = await session.execute(stmt)
    ingredients = result.scalars().all()
    return ingredients

@app.get("/Orders", response_model=list[OrderGetSchema])
async def get_orders(session: AsyncSession=Depends(get_db)):
    stmt = select(Order).options(joinedload(Order.drink))  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    orders = result.scalars().all()
    return orders


@app.post("/Orders", response_model=OrderGetSchema)
async def create_order(
    order_input: OrderPostSchema = Body(...),
    session: AsyncSession = Depends(get_db)
):
    # делаем выборку из напитков и проверяем наличие такого товара
    stmt = select(Drink).where(Drink.id_drink == order_input.id_drink)
    result = await session.execute(stmt)
    drink = result.scalar_one_or_none()

    if not drink:
        print(f"ошибка нет напитка")

    # создание объекта для представления и последующей передачи данных
    new_order = Order(
        id_drink=drink.id_drink,
        sugar_amount=order_input.sugar_amount,
        payment_status="paid"
    )
    #открываем подключение и передаем объект в бд и сохраняем
    session.add(new_order)
    await session.commit()
    await session.refresh(new_order)

    # делаем выборку напитка для определения его ингредиентов, подключаемся, ожидание ответа, запуск, передаем в переменную
    stmt = select(DrinkIngredient).where(DrinkIngredient.id_drink == drink.id_drink)
    result = await session.execute(stmt)
    drink_ingredients = result.scalars().all()

    # создаем цикл для перебора всех объектов из таблицы напиток/ингредиент входящих в напиток
    for i in drink_ingredients:
        #делаем выборку на складе, сравниваем и выбираем ингредиент на складе с напиток/ингредиент
        stmt = select(Inventory).where(Inventory.id_ingredient == i.id_ingredient)
        result = await session.execute(stmt)
        inventory_item = result.scalar_one_or_none() #получаем нужные ингредиенты

        if inventory_item is not None: #условие для найденного товара
            inventory_item.quantity -= Decimal(str(i.amount)) #из количества ингредиентов на складе вычитаем количество ингредиента из заказа
        else:
            print(f"ошибка ингредиенты")


    sugar_id = 6 #вычитаем сахар непосредственно из заказа
    if order_input.sugar_amount > 0: #если в модель в переменную количество сахара >0
        stmt = select(Inventory).where(Inventory.id_ingredient == sugar_id)
        result = await session.execute(stmt)
        sugar_inventory = result.scalar_one_or_none()

        if sugar_inventory:
            sugar_inventory.quantity -= order_input.sugar_amount * 5  # по 5 г за ложку
        else:
            print(f"ошибка сахар")
    await session.commit()


    stmt = select(Order).options(joinedload(Order.drink)).where(Order.id_order == new_order.id_order)
    result = await session.execute(stmt)
    order_with_drink = result.scalar_one()

    return order_with_drink

@app.get("/IngredintDrink", response_model=list[IngredientDrinkGetSchema]) #добавить фильтрацию
async def get_DrinkIngredient(session: AsyncSession=Depends(get_db)):
    stmt = select(DrinkIngredient).options(joinedload(DrinkIngredient.drink), joinedload(DrinkIngredient.ingredient))  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    drinkingredient = result.scalars().all()
    return drinkingredient

@app.get("/Inventory", response_model=list[InventoryGetSchema]) #добавить фильтрацию
async def get_Inventory(session: AsyncSession=Depends(get_db)):
    stmt = select(Inventory).options( joinedload(Inventory.ingredient))  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    drinkingredient = result.scalars().all()
    return drinkingredient

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)

# python main.py
# http://127.0.0.1:8001/docs