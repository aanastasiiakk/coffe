from decimal import Decimal
from fastapi import Depends, Body, APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from models.Base import Base
from core.db import engine
from core.get_db import get_db
from models.ModelBase import Drink, Ingredient, DrinkIngredient, Inventory, Order
from models.Schemas import DrinkGetSchema, OrderGetSchema, OrderPostSchema, IngredientGetSchema, IngredientDrinkGetSchema, InventoryGetSchema



myrouter=APIRouter()

@myrouter.post("/setup", tags=["Модификация бд"])
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return {"message": "Database tables recreated"}

@myrouter.get("/Drinks", response_model=list[DrinkGetSchema], tags=["Вывод данных об ингредиентах"])
async def get_drinks(session: AsyncSession=Depends(get_db)):
    stmt = select(Drink)
    result = await session.execute(stmt)
    drinks = result.scalars().all()
    return drinks

@myrouter.get("/Ingredients", response_model=list[IngredientGetSchema], tags=["Вывод данных об ингредиентах"])
async def get_ingredients(session: AsyncSession=Depends(get_db)):
    stmt = select(Ingredient)
    result = await session.execute(stmt)
    ingredients = result.scalars().all()
    return ingredients

@myrouter.get("/Orders", response_model=list[OrderGetSchema], tags=["Заказ"])
async def get_orders(session: AsyncSession=Depends(get_db)):
  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    stmt = select(Order).options(
        joinedload(Order.drink),
        joinedload(Order.ingredient)
    )
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    orders = result.scalars().all()
    return orders


@myrouter.post("/Orders", response_model=OrderGetSchema, tags=["Заказ"])
async def create_order(
    order_input: OrderPostSchema = Body(...),
    session: AsyncSession = Depends(get_db)
):
    # делаем выборку из напитков и проверяем наличие такого товара
    stmt = select(Drink).where(Drink.id_drink == order_input.id_drink)
    result = await session.execute(stmt)
    drink = result.scalar_one_or_none()

    if not drink:
        raise HTTPException(status_code=404, detail="Напиток не найден")

    # получение ингредиента, если он указан
    ingredient = None
    if order_input.id_ingredient:
        stmt = select(Ingredient).where(Ingredient.id_ingredient == order_input.id_ingredient)
        result = await session.execute(stmt)
        ingredient = result.scalar_one_or_none()

        if not ingredient:
            raise HTTPException(status_code=404, detail="Ингредиент не найден")

    # создание объекта для представления и последующей передачи данных
    new_order = Order(
        id_drink=drink.id_drink,
        sugar_amount=order_input.sugar_amount,
        payment_status="paid",
        id_ingredient=ingredient.id_ingredient
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

    # Вычитание дополнительного ингредиента, если он выбран
    if ingredient:
        stmt = select(Inventory).where(Inventory.id_ingredient == ingredient.id_ingredient)
        result = await session.execute(stmt)
        extra_inventory = result.scalar_one_or_none()

        if extra_inventory:
             extra_inventory.quantity -= Decimal(str(ingredient.portion))
        else:
            print(f"Ошибка: не найден ингредиент на складе (id={ingredient.id_ingredient})")


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

    if extra_inventory.quantity < Decimal(str(ingredient.portion)):
        raise HTTPException(status_code=400, detail="Недостаточно ингредиента на складе")

    stmt = select(Order).options(
        joinedload(Order.drink),
        joinedload(Order.ingredient)
    ).where(Order.id_order == new_order.id_order)

    result = await session.execute(stmt)
    order_with_drink = result.scalar_one()

    return order_with_drink

@myrouter.get("/IngredintDrink", response_model=list[IngredientDrinkGetSchema], tags=["Вывод данных об ингредиентах"]) #добавить фильтрацию
async def get_DrinkIngredient(session: AsyncSession=Depends(get_db)):
    stmt = select(DrinkIngredient).options(joinedload(DrinkIngredient.drink), joinedload(DrinkIngredient.ingredient))  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    drinkingredient = result.scalars().all()
    return drinkingredient

@myrouter.get("/Inventory", response_model=list[InventoryGetSchema], tags=["Вывод данных об ингредиентах"]) #добавить фильтрацию
async def get_Inventory(session: AsyncSession=Depends(get_db)):
    stmt = select(Inventory).options( joinedload(Inventory.ingredient))  #select * from, stmt переменная содержащая скл запрос, joinload для загрузки связной таблицы напитки одновременно с заказами в одном запросе
    result = await session.execute(stmt) #await--ожидание ответа и завершение, execute --планирует и запускает запрос, session--подключение к бд
    drinkingredient = result.scalars().all()
    return drinkingredient