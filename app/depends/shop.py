from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from app.backend.db.db_depends import get_db
from ..models.shop import Shops


def get_shop(db: Annotated[Session, Depends(get_db)], shop_id: int) -> Shops | None:
    """
    Получение объекта магазин по его идентификатору
    :param db: Подключение к базе данных.
    :param shop_id: Идентификатор объекта магазин
    :return: объект магазин или None
    """
    return db.scalar(select(Shops).where(Shops.is_active and Shops.id == shop_id))


def get_shop_list(db: Annotated[Session, Depends(get_db)]) -> list[Shops]:
    """
    Получение списка доступных магазинов
    :param db: Подключение к базе данных.
    :return: Список магазинов
    """
    shop_list = db.scalars(select(Shops).where(Shops.is_active)).all()
    if shop_list is not None:
        shop_list = list(shop_list)
    return shop_list
