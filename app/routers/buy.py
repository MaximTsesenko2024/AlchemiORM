import math
from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import insert, select, update, delete, desc, func
from sqlalchemy.orm import Session
from typing import Annotated

from app.backend.service.service import pagination
from app.depends import find_category, get_product, update_count_product, get_shop, get_shop_list, get_current_user
from app.models.buy import BuyerProd
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.models.users import User
from app.models.shop import Shops
from app.shemas import Car, Payment


class BuyProd:
    """
    Класс товар в корзине
    """

    def __init__(self, number: int, id_prod: int, name: str, price: float, count: int):
        """
        Инициализация элемента класса.
        :param number: Номер товара в корзине пользователя.
        :param id_prod: Идентификатор товара.
        :param name: Название товара.
        :param price: Цена товара.
        :param count: Количество товара.
        """
        self.number = number
        self.id_prod = id_prod
        self.name = name
        self.price = price
        self.count = count


class Order:
    """
    Класс отображения заказа
    """

    def __init__(self, number: int, shop: Shops | None = None, user_id: int | None = None):
        """
        Инициализация элемента класс.
        :param number: Номер заказа.
        :param shop: Объект магазин.
        :param user_id: Идентификатор пользователя
        """
        self.shop = shop
        self.number = number
        self.user_id = user_id
        self.data_prods = []

    def __str__(self):
        return f'Заказ номер: {self.number}'

    def add_prods_by_db(self, database: Annotated[Session, Depends(get_db)]):
        """
        Добавление данных по товарам
        :param database: База данных
        """
        order = database.scalars(select(BuyerProd).where(BuyerProd.id_operation == self.number)).all()
        if self.shop is None:
            self.shop = order[0].shop
        if self.user_id is None:
            self.user_id = order[0].user_id
        for prod in order:
            self.data_prods.append({'product': prod.product, 'count': prod.count, 'used': prod.is_used})

    def add_prods_by_list(self, buy_prod_list: list):
        """
        Добавление данных по товарам
        :param buy_prod_list: Список заказанных товаров
        """
        if self.shop is None:
            self.shop = buy_prod_list[0].shop
        if self.user_id is None:
            self.user_id = buy_prod_list[0].user_id
        for prod in buy_prod_list:
            if prod.id_operation == self.number:
                self.data_prods.append({'product': prod.product, 'count': prod.count, 'used': prod.is_used})

    def get_index_prod(self, prod_id: int):
        """
        Получение индекса товара по идентификатору товара
        :param prod_id: Идентификатор товаров
        :return: Индекс или None
        """
        for index in range(len(self.data_prods)):
            if self.data_prods[index]['prod_id'] == prod_id:
                return index
        return None

    def set_used_prod(self, prod_id, used):
        index = self.get_index_prod(prod_id)
        self.data_prods[index]['is_used'] = used


def get_orders_by_list(buy_prods_list: list):
    """
    Получение списка заказов по списку покупок
    :param buy_prods_list: Список покупок
    :return: Список заказов
    """
    orders = []
    orders_number = []
    for buy_prods in buy_prods_list:
        if buy_prods.id_operation not in orders_number:
            order = Order(buy_prods.id_operation, buy_prods.shop, buy_prods.user_id)
            order.add_prods_by_list(buy_prods_list)
            orders.append(order)
            orders_number.append(buy_prods.id_operation)
    return orders


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
        res = True
        for i in range(len(cars[user.id])):
            if cars[user.id][i].id_prod == id_product:
                cars[user.id][i].count += car_user.count
                res = False
        if res:
            cars[user.id].append(BuyProd(len(cars[user.id]), product.id, product.name, product.price, car_user.count))
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


@buy_router.get('/orders/{user_id}')
async def orders_get(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int = -1, number: str = '',
                     page: str = '', user=Depends(get_current_user)):
    """
    Отображение страницы история заказов.
    :param number: Строка поиска
    :param page: Номер страницы списка заказов
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user_id: Идентификатор пользователя.
    :param user: Текущий пользователь.
    :return: Страница история заказов
    """
    info = {'request': request, 'title': 'История заказов'}
    if page == '':
        page = 0
    else:
        page = int(page)
    if user is None:
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    if not any((user.is_staff, user.admin)) and user.id != user_id:
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    if number != '':
        buy_prods = db.scalars(select(BuyerProd).where((BuyerProd.user_id == user_id) &
                                                       (BuyerProd.id_operation == number))).all()
    else:
        buy_prods = db.scalars(select(BuyerProd).where(BuyerProd.user_id == user_id).
                               order_by(BuyerProd.id_operation.desc())).all()
    if buy_prods is not None:
        orders = get_orders_by_list(list(buy_prods))
        info['orders'], info['service'] = pagination(orders, page, 4)
    return templates.TemplateResponse('order_list_page.html', info)


@buy_router.get('/orders/number/{number}')
async def orders_get(request: Request, db: Annotated[Session, Depends(get_db)], number: int = -1, used: str = '',
                     prod: int = -1, user=Depends(get_current_user)):
    """
    Отображение заказа
    :param request: Запрос.
    :param db: Подключение к базе данных.
    :param number: Номер заказа.
    :param used: Признак операции с товаром
    :param prod: Идентификатор товара
    :param user: Текущий пользователь.
    :return: Страница заказа
    """
    info = {'request': request, 'title': 'Описание заказа'}
    if prod > -1:
        res = used == '1'
        db.execute(update(BuyerProd).where((BuyerProd.id_operation == number) &
                                           (BuyerProd.product_id == prod)).values(is_used=res))
        db.commit()
    buy_prods = db.scalars(select(BuyerProd).where(BuyerProd.id_operation == number)).all()
    if buy_prods is None:
        info['message'] = 'Заказ не найден'
    if user is None:
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    if not any((user.is_staff, user.admin)) and user.id != buy_prods[0].user_id:
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    orders = get_orders_by_list(list(buy_prods))
    order = orders[0]
    info['order'] = order
    info['is_staff'] = user.is_staff
    info['admin'] = user.admin
    return templates.TemplateResponse('order_page.html', info)


@buy_router.get('/orders')
async def orders_get(request: Request, db: Annotated[Session, Depends(get_db)], number: str = '',
                     page: str = '', user=Depends(get_current_user)):
    """
    Отображение страницы поиска заказа.
    :param number: Строка поиска
    :param page: Номер страницы списка заказов
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница история заказов
    """
    info = {'request': request, 'title': 'Поиск заказа'}
    if page == '':
        page = 0
    else:
        page = int(page)
    if user is None:
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    if not any((user.is_staff, user.admin)):
        return RedirectResponse(f'/main', status_code=status.HTTP_303_SEE_OTHER)
    if number != '':
        number = int(number)
        buy_prods = db.scalars(select(BuyerProd).where(BuyerProd.id_operation == number)).all()
        if buy_prods is not None:
            orders = get_orders_by_list(list(buy_prods))
            info['orders'], info['service'] = pagination(orders, page, 4)
    return templates.TemplateResponse('order_list_page.html', info)
