from sqlalchemy.orm import DeclarativeBase


#DeclarativeBase: Основной класс для всех моделей, от которого будут наследоваться все таблицы
class Base(DeclarativeBase):
    pass