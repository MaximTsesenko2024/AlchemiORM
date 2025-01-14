from fastapi import APIRouter, Depends, status, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session
from typing import Annotated
from app.models.shop import Shops
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.shemas import Shop
from app.depends import get_current_user

shop_router = APIRouter(prefix='/shop', tags=['shop'])
templates = Jinja2Templates(directory='app/templates/shop')


@shop_router.get('/create')
async def create_shop_get(request: Request, user=Depends(get_current_user)):
    """
    Добавление нового магазина. Отображение страницы с формой добавления нового магазина, если пользователь - сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница добавления магазина или переход на другую страницу.
    """
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        return templates.TemplateResponse('add_shop_page.html', info)


@shop_router.post('/create')
async def create_shop_post(request: Request, db: Annotated[Session, Depends(get_db)], shop: Shop = Form(),
                           user=Depends(get_current_user)):
    """
    Добавление нового магазина. Добавление данных о магазине в базу данных и переход к списку магазинов.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop: Данные по магазину: название и расположение.
    :param user: Текущий пользователь.
    :return: Переход на страницу.
    """
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(insert(Shops).values(name=shop.name, location=shop.location))
        db.commit()
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/update/{shop_id}')
async def update_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    """
    Изменение данных магазина. Отображение страницы с формой изменения данных магазина, если пользователь - сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Страница изменения данных магазина или переход на другую страницу.
    """
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = db.scalar(select(Shops).where(Shops.id == shop_id))
        if shop is None:
            return RedirectResponse('/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('update_shop_page.html', info)


@shop_router.post('/update/{shop_id}')
async def update_shop_post(request: Request, db: Annotated[Session, Depends(get_db)], shop: Shop = Form(),
                           shop_id: int = -1, user=Depends(get_current_user)):
    """
    Изменение данных магазина. Внесение изменений в базу данных и переход к списку магазинов,
    если пользователь - сотрудник. Если пользователь не определён, то переход к странице входа в систему.
    Если пользователь не имеет прав сотрудника, то переход на главную страницу.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop: Новые данные по магазину: расположение.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Переход на другую страницу
    """
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(update(Shops).where(Shops.id == shop_id).values(name=shop.name, location=shop.location))
        db.commit()
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/delete/{shop_id}')
async def delete_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    """
    Удаление магазина. Отображение формы с подтверждением удаления если пользователь сотрудник.
    Если пользователь не определён, то переход к странице входа в систему. Если пользователь не имеет прав сотрудника,
    то переход на главную страницу.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Отображение страницы удаления или переадресация на другие страницы.
    """
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = db.scalar(select(Shops).where(Shops.id == shop_id))
        if shop is None:
            return RedirectResponse('/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('delete_shop_page.html', info)


@shop_router.post('/delete/{shop_id}')
async def delete_shop_post(request: Request, db: Annotated[Session, Depends(get_db)],
                           shop_id: int = -1, user=Depends(get_current_user)):
    """
     Удаление магазина. Удаление магазина из базы данных и переадресация на список магазинов
     если пользователь сотрудник. Если пользователь не определён, то переход к странице входа в систему.
     Если пользователь не имеет прав сотрудника,то переход на главную страницу.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Переадресация на другие страницы
    """
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(update(Shops).where(Shops.id == shop_id).values(is_active=False))
        db.commit()
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@shop_router.get('/list')
async def select_shop_list_get(request: Request, db: Annotated[Session, Depends(get_db)],
                               user=Depends(get_current_user)):
    """
    Отображение страницы со списком магазинов.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница со списком магазинов.
    """
    info = {'request': request, 'title': 'Список магазинов'}
    shops = db.scalars(select(Shops).where(Shops.is_active)).all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return templates.TemplateResponse('shop_list_page.html', info)


@shop_router.get('/{shop_id}')
async def select_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    """
    Отображение страницы с данными по магазину.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param shop_id: Идентификатор магазина.
    :param user: Текущий пользователь.
    :return: Страница магазина.
    """
    info = {'request': request, 'title': 'Данные магазина'}
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    shop = db.scalar(select(Shops).where(Shops.id == shop_id))
    if shop is None:
        return RedirectResponse('/shop/list', status_code=status.HTTP_303_SEE_OTHER)
    info['shop'] = shop
    return templates.TemplateResponse('shop_page.html', info)
