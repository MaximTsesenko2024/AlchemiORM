from typing import Annotated
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from app.backend.db.db_depends import get_db
from ..models.category import Categories
from ..shemas import Category


def get_categories_subgroups(list_categories, id_category) -> list[Category]:
    """
    Получение списка подкатегорий для категории указанной идентификатором.
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Список категорий для которых указанный идентификатор является родительским
    """
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category) -> Categories | None:
    """
    Получение объекта категория по идентификатору
    :param list_categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: Объект категория или None
    """
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def get_category_model(db: Annotated[Session, Depends(get_db)], id_category: int) -> Categories | None:
    """
    Получение объекта категория по идентификатору
    :param db: Подключение к базе данных
    :param id_category: Идентификатор категории
    :return: Объект категория или None
    """
    return db.scalar(select(Categories).where(Categories.id == id_category))


def find_category(categories, id_category) -> str:
    """
    Вывод зависимости категорий для указанного идентификатора
    :param categories: Список всех категорий
    :param id_category: Идентификатор категории
    :return: строка представляющая цепочку родителей для указанной категории
    """
    if id_category is None or id_category == -1:
        return ''
    for category in categories:
        if category.id == id_category:
            if category.parent is None or category.parent == -1:
                return category.name
            else:
                return find_category(categories, category.parent) + ' / ' + category.name
    return ''


def get_categories(db: Annotated[Session, Depends(get_db)]):
    """
    Получение списка категорий введённых в базу
    :return: Список категорий
    """
    categories = db.scalars(select(Categories)).all()
    if not categories:
        return None
    return categories
