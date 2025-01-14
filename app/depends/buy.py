from typing import Annotated
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.models.buy import BuyerProd
from fastapi import Depends
from app.backend.db.db_depends import get_db


def check_use_product(db: Annotated[Session, Depends(get_db)], product: int):
    """
    Проверка наличия покупки выбранного товара
    :param db: Подключение к базе данных.
    :param product: Идентификатор товара
    :return: True - есть товар покупали, False - нет
    """
    result = db.scalars(select(BuyerProd).where(BuyerProd.product_id == product)).all()
    if result:
        return True
    else:
        return False


def check_use_user(db: Annotated[Session, Depends(get_db)], user: int):
    """
    Проверка наличия покупки выбранного товара
    :param db: Подключение к базе данных.
    :param user: Идентификатор пользователя
    :return: True - есть пользователь покупал, False - нет
    """
    result = db.scalars(select(BuyerProd).where(BuyerProd.user_id == user)).all()
    if result:
        return True
    else:
        return False


def delete_buyer(db: Annotated[Session, Depends(get_db)], key: str, value: int) -> bool:
    """
    Удаление записей о покупках по ключу и значению.
    :param db: Подключение к базе данных.
    :param key: Ключ
    :param value: Значение
    :return:
    """
    try:
        if key == 'product':
            db.execute(delete(BuyerProd).where(BuyerProd.product_id == value))
        elif key == 'user':
            db.execute(delete(BuyerProd).where(BuyerProd.user_id == value))
        db.commit()
    except Exception:
        return False
    return True
