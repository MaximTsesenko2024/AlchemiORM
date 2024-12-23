from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = 'gV64m9aIzFG4qpgVphvQbPQrtAO0nM-7YwwOvu0XPt5KJOjAy4AfgLkqJXYEt'
ALGORITHM = 'HS256'

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def get_password_hash(password: str) -> str:
    """
    Преобразование пароля в hash - строку с учётом секретного ключа и алгоритма шифрования
    :param password: Пароль введённый пользователем
    :return: hash - строка с учётом секретного ключа и алгоритма шифрования
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка соответствия введённого пароля записанной в базу данных hash строке
    :param plain_password: Введённый пароль пользователем
    :param hashed_password: Сохранённая hash строка пароля
    :return: True - соответствуют и False - не соответствуют
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Создание токена идентификатора данных пользователя.
    :param data: Данные пользователя.
    :return: Токен данных
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY)
    return encode_jwt
