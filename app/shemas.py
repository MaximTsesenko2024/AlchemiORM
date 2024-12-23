import datetime
from typing import Optional

from pydantic import BaseModel, Field
from datetime import date
from fastapi_filter.base.filter import BaseFilterModel


class AdminUser(BaseModel):
    # имя пользователя в системе
    username: str
    # адрес электронной почты
    email: str
    # дата рождения
    day_birth: date
    # Флаг активности пользователя
    is_active: bool
    # Флаг принадлежности к сотрудникам
    is_staff: bool
    # Флаг принадлежности к администраторам
    admin: bool

class CreateUser(BaseModel):
    username: str
    email: str
    day_birth: date
    password: str
    repeat_password: str


class SelectUser(BaseModel):
    username: str
    password: str


class UpdateUser(BaseModel):
    email: str
    day_birth: date


class RepairPassword(BaseModel):
    username: str
    email: str


class CreatePassword(BaseModel):
    password: str
    repeat_password: str


class Product(BaseModel):
    name: str
    description: str
    price: int
    count: int
    item_number: str

    img: str


class Product(BaseModel):
    name: str
    description: str
    price: float
    count: int
    item_number: str
    category: int


class Car(BaseModel):
    count: int


class Payment(BaseModel):
    name: str
    card_number: int
    expiry_date: str
    security_code: int


class Category(BaseModel):
    id: int
    name: str
    parent: int


class Shop(BaseModel):
    name: str
    location: str
