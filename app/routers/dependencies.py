from fastapi import Request, HTTPException, status, Depends
from jose import jwt, JWTError
from datetime import datetime, timezone
from .auth import SECRET_KEY, ALGORITHM
from sqlalchemy.orm import Session
from typing import Annotated
from app.models.users import User
from app.backend.db.db_depends import get_db
from sqlalchemy import select


def find_user_by_id(db: Annotated[Session, Depends(get_db)], user_id: int = -1) -> User | None:
    """
    Поиск пользователя по идентификационному номеру.
    :param db: Подключение к базе данных
    :param user_id: Идентификационный номер пользователя.
    :return: Объект user если пользователь в базе данных найден, None - в противном случае
    """
    if user_id < 0:
        return None
    user = db.scalar(select(User).where(User.id == user_id))
    return user


def get_token(request: Request):
    """
    Получение значения токена из запроса
    :param request: Запрос
    :return: Токен если он имеется и None в противном случае.
    """
    token = request.cookies.get('users_access_token')
    if not token:
        return None
    return token


async def get_current_user(db: Annotated[Session, Depends(get_db)], token: str | None = Depends(get_token)):
    """
    Получение пользователя по токену.
    :param db: Подключение к базе данных
    :param token: Токен пользователя или None
    :return: Пользователь - в случае наличия токена и наличия идентификатора пользователя в базе данных, или
             None - в противном случае.
    """
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

    expire = payload.get('exp')
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        return None

    user_id = payload.get('sub')
    if not user_id:
        return None

    user = find_user_by_id(db=db, user_id=int(user_id))
    if not user:
        return None
    return user
