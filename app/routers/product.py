from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import insert, select, update
from sqlalchemy.orm import Session
from typing import Annotated
from app.backend.service.service import image_to_str, pagination
from app.depends import find_category, get_categories
from app.models.product import ProductModel
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.models.users import User
from app.routers.users import get_current_user
import os
from PIL import Image

product_router = APIRouter(prefix='/product', tags=['product'])
templates = Jinja2Templates(directory='app/templates/product')


# Обработка таблицы Product
@product_router.get('/list')
async def select_products_list_get(request: Request, db: Annotated[Session, Depends(get_db)],
                                   user: Annotated[User, Depends(get_current_user)], category: str = '', q: str = '',
                                   page: str = ''):
    """
    Просмотр списка товаров. Список товаров может быть ограничен выбранной категорией, совпадением названия или
    описания со строкой поиска.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user: Текущий пользователь
    :param category: Идентификатор категории
    :param q: строка поиска
    :param page: номер страницы списка товаров
    :return: Страница списка товаров.
    """
    info = {'request': request, 'title': 'Список товаров'}
    if page == '':
        page = 0
    else:
        page = int(page)
    if user is None:
        pass
    elif user.is_staff:
        info['is_staff'] = 'Ok'
    if q != '' and category != '':
        products = db.scalars(select(ProductModel).where(((ProductModel.name.icontains(q)) |
                                                          (ProductModel.description.icontains(q))) &
                                                         (ProductModel.category_id == int(category)))).all()
    elif q != '':
        print('Только имя', q)
        products = db.scalars(select(ProductModel).where((ProductModel.description.icontains(q)) &
                                                         (ProductModel.name.icontains(q)))).all()
    elif category != '':
        products = db.scalars(select(ProductModel).where((ProductModel.category_id == int(category)))).all()
    else:
        products = db.scalars(select(ProductModel)).all()
    if products is not None:
        product_list = []
        for product in products:
            image_str, format_file = image_to_str(product, 'list')
            product_list.append({'name': product.name, 'price': product.price, 'id': product.id, 'image_str': image_str,
                                 'format_file': format_file, 'count': product.count, 'is_active': product.is_active})
        info['products'], service = pagination(product_list, page, 4)
        categories = get_categories(db)
        if categories is not None:
            info['categories'] = categories
        print(service)
        pages = [x for x in range(service['total'] + 1)]
        info['service'] = {'page': service['page'], 'size': service['size'], 'pages': pages}
        print(info['service'])
    return templates.TemplateResponse('product_list_page.html', info)


# Создание нового продукты
@product_router.post('/create')
async def create_product_post(request: Request, db: Annotated[Session, Depends(get_db)],
                              user: Annotated[User, Depends(get_current_user)], name: str = Form(...),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    """
    Добавление нового товара. Выполняется проверка пользователя на наличие прав сотрудника. При подтверждении прав
    выполняется запись введённых пользователем данных о товаре.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user: Текущий пользователь
    :param name: Название товара
    :param item_number: Артикул товара
    :param description: Описание товара
    :param price: Цена товара
    :param count: Количество товара
    :param category: Идентификатор категории товара
    :param file: Изображение товара
    :return: Страницу списка товаров или страницу добавления товара с описанием ошибки
    """
    info = {'request': request, 'title': 'Добавление товара'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '':
            info['message'] = 'Поле имя не может быть пустым'
        try:
            if not os.path.exists("app/templates/product/image/" + name):
                os.mkdir("app/templates/product/image/" + name)

            contents = file.file.read()
            file_name = file.filename
            with open("app/templates/product/image/" + name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./app/templates/product/image/" + name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./app/templates/product/image/" + name + '/small_' + file_name)
        db.execute(insert(ProductModel).values(name=name, description=description,
                                               price=price, count=count,
                                               is_active=count > 0, category_id=int(category), item_number=item_number,
                                               img=file_name))
        db.commit()
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('add_product_page.html', info)


@product_router.get('/create')
async def create_product_get(request: Request, db: Annotated[Session, Depends(get_db)],
                             user: Annotated[User, Depends(get_current_user)]):
    """
    Добавление нового товара. Выполняется проверка пользователя на наличие прав сотрудника.
    В случае наличия прав сотрудника отображается страница с формой для добавления товара, иначе страница с
    описанием ошибки.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param user: Текущий пользователь.
    :return: Страница добавления товара.
    """
    info = {'request': request, 'title': 'Добавление товара'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['categories'] = get_categories(db)
    return templates.TemplateResponse('add_product_page.html', info)


@product_router.post('/update_product/{id_product}')
async def update_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                              user=Depends(get_current_user),
                              item_number: str = Form(...), description: str = Form(...), price: str = Form(...),
                              count: int = Form(...), category: str = Form(...)):
    """
    Изменение данных о товаре. Запись данных о товаре, введённых пользователем при наличии у него прав.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :param item_number: Артикул товара.
    :param description: Описание товара.
    :param price: Цена товара.
    :param count: Количество товара.
    :param category: Идентификатор категории товара.
    :return: Страница с информацией о товаре.
    """
    if user is not None and user.is_staff:
        db.execute(update(ProductModel).where(ProductModel.id == id_product).values(description=description,
                                                                                    price=price, count=count,
                                                                                    is_active=count > 0,
                                                                                    category_id=int(category),
                                                                                    item_number=item_number))
        db.commit()
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_product/{id_product}')
async def update_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    """
    Отображение страницы с формой для изменения данных о товаре
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница с формой изменения данных о товаре или переадресация на страницу входа в систему или
    на список товара.
    """
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        info['categories'] = get_categories(db)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_product_page.html', info)


@product_router.post('/update_image_product/{id_product}')
async def update_image_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                                    user=Depends(get_current_user), file: UploadFile = Form(...)):
    """
    Изменение изображения товара. Запись нового изображения товара только при наличии прав.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :param file: Новое изображение товара.
    :return: Страница с отображением данных о товаре.
    """
    info = {'request': request, 'title': 'Изменение изображения товара'}
    if user is not None and user.is_staff:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        try:
            if not os.path.exists("./templates/product/image/" + product.name):
                os.mkdir("./templates/product/image/" + product.name)
            else:
                os.remove("./templates/product/image/" + product.name + '/' + product.img)
                os.remove("./templates/product/image/" + product.name + '/small_' + product.img)
            contents = file.file.read()
            file_name = file.filename
            with open("app/templates/product/image/" + product.name + '/' + file_name, "wb") as f:
                f.write(contents)
        except Exception:
            raise HTTPException(status_code=500, detail='Something went wrong')
        finally:
            file.file.close()
        image = Image.open("./app/templates/product/image/" + product.name + '/' + file_name)
        image.thumbnail(size=(100, 100))
        image.save("./app/templates/product/image/" + product.name + '/small_' + file_name)
        db.execute(update(ProductModel).where(ProductModel.id == id_product).values(img=product.name))
        db.commit()
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_image_product/{id_product}')
async def update_image_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                                   user=Depends(get_current_user)):
    """
    Изменение изображения товара. Отображение страницы изменения изображения товара только при наличии прав.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница изменения изображения о товаре или страница входа в систему или страница со списком товаров
    """
    info = {'request': request, 'title': 'Изменение изображения товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        info['categories'] = get_categories(db)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('update_image_product_page.html', info)


@product_router.post('/delete/{id_product}')
async def delete_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                              user=Depends(get_current_user)):
    """
    Удаление товара. Удаление данных о товаре из базы данных. Если текущий пользователь имеет права сотрудника, то
    возможно удаление товара, который ещё никто не покупал.  Если текущий пользователь имеет права администратора, то
    при удалении товара, также удаляются данные о его покупках если его покупали.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница со списком товаров: если удаление прошло успешно или у пользователя нет прав на удаление или
    страница удаления с сообщением об использовании.
    """
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        RedirectResponse(f'/user/login')
    elif user.is_staff:
        db.execute(update(ProductModel).where(ProductModel.id == id_product).values(is_active=False))
        db.commit()
    return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/delete/{id_product}')
async def delete_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    """
    Удаление товара. Отображение страницы удаления товара при наличии прав сотрудника или администратора. Отображение
    страницы входа в систему если пользователь не авторизован. Отображение страницы со списком товаров если у
    пользователя нет прав на удаление.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница удаления товара или страница входа в систему или страница со списком товаров.
    """
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        categories = get_categories(db)
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('delete_product_page.html', info)


@product_router.get('/{id_product}')
async def select_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    """
    Отображение информации о товаре если он существует в базе или сообщение об ошибке.
    :param db: Подключение к базе данных
    :param request: Запрос.
    :param id_product: Идентификатор товара.
    :param user: Текущий пользователь.
    :return: Страница с информацией о товаре или сообщение об ошибке.
    """
    info = {'request': request, 'title': 'Описание товара'}
    product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
    if product is not None:
        categories = get_categories(db)
        info['product_category'] = find_category(categories, product.category_id)
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['user'] = user
    else:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail='Товар отсутствует')
    return templates.TemplateResponse('product_page.html', info)
