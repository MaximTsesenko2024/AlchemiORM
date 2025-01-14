from typing import Annotated
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session
from fastapi import Depends
from app.backend.db.db_depends import get_db
from ..models.product import ProductModel


def check_use_category(db: Annotated[Session, Depends(get_db)], category: int):
    """
    Проверка наличия товара выбранной категории
    :param db: Подключение к базе данных.
    :param category: Идентификатор категории
    :return: True - есть товар указанной категории, False - нет товара
    """
    count = db.scalar(func.count(ProductModel).where(ProductModel.category_id == category))
    if count > 0:
        return True
    else:
        return False


def get_product(db: Annotated[Session, Depends(get_db)], product_id: int) -> ProductModel | None:
    """
    Получение объекта продукт по идентификатору
    :param db: Подключение к базе данных.
    :param product_id: Идентификатор объекта продукт
    :return: объекта продукт или None
    """
    return db.scalar(select(ProductModel).where(ProductModel.id == product_id))


def update_count_product(db: Annotated[Session, Depends(get_db)], product_id: int, update_count: int) -> bool:
    """
    Изменение количества товара
    :param db: Подключение к базе данных.
    :param product_id: Идентификатор товара.
    :param update_count: Изменение количества + увеличение, - уменьшение.
    :return статус операции
    """
    product = db.scalar(select(ProductModel).where(ProductModel.id == product_id))
    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(count=product.count + update_count))
    db.commit()
    return True
