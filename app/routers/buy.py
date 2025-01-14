import math
from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import insert, select, update, delete, desc, func
from sqlalchemy.orm import Session
from typing import Annotated
from app.depends import find_category, get_product, update_count_product, get_shop, get_shop_list, get_current_user
from app.models.buy import BuyerProd
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.models.users import User
from app.shemas import Car, Payment


class CarView:
    def __init__(self, number, id_prod, name, price, count):
        self.number = number
        self.id_prod = id_prod
        self.name = name
        self.price = price
        self.count = count


buy_router = APIRouter(prefix='/buy', tags=['buy'])
templates = Jinja2Templates(directory='app/templates/buy')
# корзины для покупки
cars = {}


@buy_router.get('/car-user')
async def buy_get(request: Request, db: Annotated[Session, Depends(get_db)], delet: int = -1,
                  shop: str = '', user=Depends(get_current_user)):
    """
    Отображение страницы корзины текущего пользователя.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param delet: Идентификатор удаляемого товара.
    :param shop:  Идентификатор выбранного магазина
    :param user:  Текущий пользователь.
    :return: Страница корзины текущего пользователя.
    """
    info = {'request': request, 'title': 'Корзина'}
    cost = 0
    if user.id not in cars.keys():
        info['message'] = 'Корзина пуста'
    else:
        if delet > -1:
            for i in range(len(cars[user.id])):
                if cars[user.id][i].number == delet:
                    update_count_product(db, cars[user.id][i].id_prod, cars[user.id][i].count)
                    cars[user.id].pop(i)
                    break
        info['display'] = 1
        car = cars[user.id]
        info['car'] = car
        info['user'] = user
        info['shops'] = get_shop_list(db)
        for item in car:
            cost += item.price * item.count
        info['cost'] = cost
    return templates.TemplateResponse('buy.html', info)


@buy_router.post('/car-user')
async def buy_post(request: Request, user=Depends(get_current_user), shop: str = Form(...)):
    """
    Отображение страницы корзины текущего пользователя. Выбор магазина.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param shop: Идентификатор выбранного магазина.
    :return: Переход к оплате или отображение страницы корзины пользователя.
    """
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user.id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item.price * item.count
    info['cost'] = cost
    if shop == '':
        info['message'] = 'Выберите магазин'
        return templates.TemplateResponse('buy.html', info)

    return RedirectResponse(f'/buy/payment/?shop={shop}', status_code=status.HTTP_303_SEE_OTHER)


@buy_router.get('/payment')
async def payment_get(request: Request, db: Annotated[Session, Depends(get_db)], shop: str = '',
                      user=Depends(get_current_user)):
    """
    Оплата товара. Отображение страницы оплаты.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop: Идентификатор выбранного магазина.
    :param user: Текущий пользователь.
    :return: Отображение страницы оплаты
    """
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user.id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item.price * item.count
    info['cost'] = cost
    shop = get_shop(db, int(shop))
    info['shop'] = shop
    info['display'] = True
    return templates.TemplateResponse('payment.html', info)


@buy_router.post('/payment')
async def payment_post(request: Request, db: Annotated[Session, Depends(get_db)], pay: Payment = Form(),
                       user=Depends(get_current_user), shop: str = ''):
    """
    Оплата товара. Выполнение оплаты.
    :param db: Подключение к базе данных
    :param pay: Платёжные данные покупателя.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :param shop: Идентификатор магазина.
    :return: Сообщение об оплате.
    """
    info = {'request': request, 'title': 'Оплата товара'}
    operation = db.scalar(func.max(BuyerProd.id_operation))
    if operation is None:
        operation = 1
    else:
        operation = operation + 1
    print(operation)
    for item in cars[user.id]:
        db.execute(insert(BuyerProd).values(user_id=user.id, product_id=item.id_prod, id_operation=operation,
                                            id_shop=int(shop), count=item.count))
    db.commit()
    cars.pop(user.id)
    info['message'] = f'Спасибо за покупку. Заказ номер: {operation}'
    return templates.TemplateResponse('payment.html', info)


@buy_router.post('/car/{id_product}')
async def car_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                   car_user: Car = Form(), user=Depends(get_current_user)):
    """
    Добавление товара в корзину.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param car_user: Данные по количеству товара
    :param user: Текущий пользователь.
    :return: Страница с формой корзины.
    """
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/user/login', status_code=status.HTTP_303_SEE_OTHER)
    product = get_product(db, id_product)
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    if car_user.count < 1:
        info['message'] = 'Требуемое количество товара не может быть меньше 1'
    else:
        info['product'] = product
        info['user'] = user
        new_count = product.count - car_user.count
        if new_count < 0:
            info['message'] = 'Не достаточно товара'
            info['count'] = product.count
            info['buy'] = 1
        else:
            update_count_product(db, id_product, -car_user.count)
        if user.id not in cars.keys():
            cars[user.id] = []
        cars[user.id].append(CarView(len(cars[user.id]), product.id, product.name, product.price, car_user.count))
    return templates.TemplateResponse('car.html', info)


@buy_router.get('/car/{id_product}')
async def car_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                  user=Depends(get_current_user)):
    """
    Отображение страницы корзины товара. На странице необходимо ввести количество товара.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница корзины товара
    """
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/product/list/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    product = get_product(db, id_product)
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    info['product'] = product
    info['user'] = user
    info['count'] = 1
    info['buy'] = 1
    return templates.TemplateResponse('car.html', info)
