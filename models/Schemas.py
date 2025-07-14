from datetime import datetime
from pydantic import Field, BaseModel


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

