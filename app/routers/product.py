import math

from fastapi import File, UploadFile, APIRouter, Depends, status, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import insert, select, update, delete, desc
from sqlalchemy.orm import Session
from typing import Annotated
from app.models.product import ProductModel, BuyerProd, Categories, Shops
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.models.users import User
from app.shemas import Product, Category, Car, Shop
from app.routers.users import get_current_user
import base64
import os
from PIL import Image

product_router = APIRouter(prefix='/product', tags=['product'])
templates = Jinja2Templates(directory='app/templates/')
# корзины для покупки
cars = {}


def pagination(list_product: list, page: int, size: int):
    offset_min = page * size
    offset_max = (page + 1) * size
    result = list_product[offset_min:offset_max], {
        "page": page,
        "size": size,
        "total": math.ceil(len(list_product) / size) - 1,
    }
    return result


def image_to_str(product: Product, key: str):
    if key == 'list':
        file_path = os.path.join("./app/templates/product/image/" + product.name, 'small_' + product.img)
    else:
        file_path = os.path.join("./app/templates/product/image/" + product.name, product.img)
    try:
        with open(file_path, "rb") as image_file:
            contents = image_file.read()
        base64_encoded_image = base64.b64encode(contents).decode("utf-8")
        _, format_file = os.path.splitext(file_path)
    except Exception:
        base64_encoded_image = ''
        format_file = 'jpeg'
    return base64_encoded_image, format_file


def get_categories_subgroups(list_categories, id_category):
    result = []
    for category in list_categories:
        if category.parent == id_category:
            result.append(category)
    return result


def get_category(list_categories, id_category):
    for category in list_categories:
        if category.id == id_category:
            return category
    return None


def find_category(categories, id_category):
    if id_category is None or id_category == -1:
        return ''
    for category in categories:
        if category.id == id_category:
            if category.parent is None or category.parent == -1:
                return category.name
            else:
                return find_category(categories, category.parent) + ' / ' + category.name
    return ''


# Обработка таблицы Categories
# просмотр списка категорий
@product_router.get('/category/list')
async def list_categories_get(request: Request, db: Annotated[Session, Depends(get_db)],
                              curent_user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Список категорий'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = db.scalars(select(Categories)).all()
        if categories is not None:
            info['categories'] = categories
    return templates.TemplateResponse('product/categories_list.html', info)


# отображение формы для изменения категории
@product_router.get('/category/update/{id_category}')
async def update_category_get(request: Request, db: Annotated[Session, Depends(get_db)], id_category: int,
                              curent_user: Annotated[User, Depends(get_current_user)], parent: str = ''):
    info = {'request': request, 'title': 'Обновление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    elif parent == '':
        info['display'] = 'Ok'
        categories = list(db.scalars(select(Categories)).all())
        category = get_category(categories, id_category)
        if category is None:
            return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Категория не найдена')
        info['category'] = category
        info['id_category'] = category.id
        info['categories'] = categories
        print(info['category'].id, info['category'].name, info['category'].parent)
    else:
        info['display'] = 'Ok'
        db.execute(update(Categories).where(Categories.id == id_category).values(parent=int(parent)))
        db.commit()
        info['message'] = 'Обновлено'
        return RedirectResponse(f'/product/category/{id_category}',
                                status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('product/category_update.html', info)


# создание новой категории
@product_router.get('/category/create')
async def add_category_get(request: Request, db: Annotated[Session, Depends(get_db)],
                           curent_user: Annotated[User, Depends(get_current_user)],
                           name: str = '', parent: str = ''):
    info = {'request': request, 'title': 'Создание категории'}
    print('create', name, parent)
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        if name == '' and parent == '':
            categories = db.scalars(select(Categories)).all()
            if categories is not None:
                info['categories'] = categories
        elif name == '':
            info['message'] = 'Поле название не может быть пустым'
        elif parent == '':
            info['message'] = 'Поле родительская категория не может быть пустым'
        else:
            db.execute(insert(Categories).values(name=name, parent=int(parent)))
            db.commit()
            return RedirectResponse('/product/category/list')
    return templates.TemplateResponse('product/category_create.html', info)


# удаление категории
@product_router.get('/category/delete/{id_category}')
async def delete_category_get(request: Request, db: Annotated[Session, Depends(get_db)],
                              curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
    info = {'request': request, 'title': 'Удаление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        categories = list(db.scalars(select(Categories)).all())
        children = get_categories_subgroups(categories, id_category)
        info['id_category'] = id_category
        info['name'] = get_category(categories, id_category).name
        if len(children) > 0:
            info['message'] = 'Удаление запрещено. Имеются связанные категории'
            info['children'] = children
        else:
            info['delete'] = 1
    return templates.TemplateResponse('product/category_delete.html', info)


@product_router.post('/category/delete/{id_category}')
async def delete_category_post(request: Request, db: Annotated[Session, Depends(get_db)],
                               curent_user: Annotated[User, Depends(get_current_user)], id_category: int):
    info = {'request': request, 'title': 'Удаление категории'}
    if curent_user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not curent_user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        db.execute(delete(Categories).where(Categories.id == id_category))
        db.commit()
        return RedirectResponse('/product/category/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('product/category_delete.html', info)


# просмотр категории
@product_router.get('/category/{id_category}')
async def category_get(request: Request, db: Annotated[Session, Depends(get_db)], id_category: int):
    info = {'request': request, 'title': 'Описание категории'}
    categories = list(db.scalars(select(Categories)).all())
    category = get_category(categories, id_category)
    if category is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Категория не найдена')
    info['parent'] = get_category(categories, category.parent)
    info['children'] = get_categories_subgroups(categories, id_category)
    info['category'] = category
    info['categories'] = categories
    return templates.TemplateResponse('product/category.html', info)


# Обработка таблицы Product
@product_router.get('/list')
async def select_products_list_get(request: Request, db: Annotated[Session, Depends(get_db)],
                                   user: Annotated[User, Depends(get_current_user)], category: str = '', q: str = '',
                                   page: str = ''):
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
        products = db.scalars(select(ProductModel, Categories).where((ProductModel.category == Categories.id) &
                                                                     ((ProductModel.name.icontains(q)) |
                                                                      (ProductModel.description.icontains(q))) &
                                                                     (Category.id == int(category)))).all()
    elif q != '':
        print('Только имя', q)
        products = db.scalars(select(ProductModel, Categories).where((ProductModel.category == Categories.id) &
                                                                     (ProductModel.name.icontains(q)))).all()
    elif category != '':
        products = db.scalars(select(ProductModel, Categories).where((ProductModel.category == Categories.id) &
                                                                     (Category.id == int(category)))).all()
    else:
        products = db.scalars(select(ProductModel, Categories).where(ProductModel.category == Categories.id)).all()
    if products is not None:
        product_list = []
        for product in products:
            print(product.name)
            image_str, format_file = image_to_str(product, 'list')
            product_list.append({'name': product.name, 'price': product.price, 'id': product.id, 'image_str': image_str,
                                 'format_file': format_file})
        info['products'], service = pagination(product_list, page, 4)
        print(service)
        pages = [x for x in range(service['total'] + 1)]
        info['service'] = {'page': service['page'], 'size': service['size'], 'pages': pages}
        print(info['service'])
    return templates.TemplateResponse('product/product_list_page.html', info)


# Создание нового продукты
@product_router.post('/create')
async def create_product_post(request: Request, db: Annotated[Session, Depends(get_db)],
                              user: Annotated[User, Depends(get_current_user)], name: str = Form(...),
                              item_number: str = Form(...), description: str = Form(...), price: float = Form(...),
                              count: int = Form(...), category: str = Form(...), file: UploadFile = File(...)):
    info = {'request': request, 'title': 'Добавление товара'}
    print(name, item_number, description, price, count, category, file.filename)

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
                                               is_active=count > 0, category=int(category), item_number=item_number,
                                               img=file_name))
        db.commit()
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse('/product/add_product_page.html', info)


@product_router.get('/create')
async def create_product_get(request: Request, db: Annotated[Session, Depends(get_db)],
                             user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Добавление товара'}
    if user is None:
        info['message'] = 'Вы не авторизованы. Пройдите авторизацию.'
    elif not user.is_staff:
        info['message'] = 'У вас нет прав'
    else:
        info['display'] = 'Ok'
        info['categories'] = list(db.scalars(select(Categories)).all())
    return templates.TemplateResponse('/product/add_product_page.html', info)


@product_router.post('/update_product/{id_product}')
async def update_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                              user=Depends(get_current_user),
                              item_number: str = Form(...), description: str = Form(...), price: str = Form(...),
                              count: int = Form(...), category: str = Form(...)):
    if user is not None and user.is_staff:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        print(product.name)
        db.execute(update(ProductModel).where(ProductModel.id == id_product).values(description=description,
                                                                                    price=price, count=count,
                                                                                    is_active=count > 0,
                                                                                    category=int(category),
                                                                                    item_number=item_number))
        db.commit()
        return RedirectResponse(f'/product/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(f'/product/{id_product}')


@product_router.get('/update_product/{id_product}')
async def update_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        info['categories'] = list(db.scalars(select(Categories)).all())
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('product/update_product_page.html', info)


@product_router.post('/update_image_product/{id_product}')
async def update_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                              user=Depends(get_current_user), file: UploadFile = Form(...)):
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is not None and user.is_staff:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        print(product.name)
        try:
            if not os.path.exists("app/templates/product/image/" + product.name):
                os.mkdir("app/templates/product/image/" + product.name)

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
async def update_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Изменение описания товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        info['categories'] = list(db.scalars(select(Categories)).all())
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('product/update_product_page.html', info)


@product_router.post('/delete/{id_product}')
async def delete_product_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                              user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление товара'}
    if user is not None and user.is_staff:
        product_use = db.scalars(select(BuyerProd).where(BuyerProd.product == id_product)).all()
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        if product_use is None:
            os.remove("./app/templates/product/image/" + product.name)
            db.execute(delete(ProductModel).where(ProductModel.id == id_product))
            db.commit()
            return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)
        elif user.admin:
            db.execute(delete(BuyerProd).where(BuyerProd.product == id_product))
            os.remove("./app/templates/product/image/" + product.name)
            db.execute(delete(ProductModel).where(ProductModel.id == id_product))
            db.commit()
        else:
            info['message'] = 'Товар уже покупали. Для удаления обратитесь к администратору'
            return templates.TemplateResponse('product/delete_product_page.html', info)
    return RedirectResponse(f'/product/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/delete/{id_product}')
async def delete_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление товара'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/product/list')
    else:
        product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
        categories = list(db.scalars(select(Categories)).all())
        info['category'] = find_category(categories, product.category)
        info['product'] = product
        info['display'] = 'Ok'
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        return templates.TemplateResponse('product/delete_product_page.html', info)


@product_router.get('/{id_product}')
async def select_product_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                             user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Описание товара'}
    product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
    if product is not None:
        categories = list(db.scalars(select(Categories)).all())
        info['product_category'] = find_category(categories, product.category)
        info['product'] = product
        info['image_str'], info['format_file'] = image_to_str(product, 'page')
        if user is not None:
            info['is_staff'] = user.is_staff
    else:
        return HTTPException(status.HTTP_404_NOT_FOUND, detail='Товар отсутствует')
    return templates.TemplateResponse('product/product_page.html', info)


@product_router.post('/car/{id_product}')
async def car_post(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                   car_user: Car = Form(), user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/user/login', status_code=status.HTTP_303_SEE_OTHER)
    product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
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
        else:
            db.execute(update(ProductModel).where(ProductModel.id == id_product).values(count=new_count))
            db.commit()
        if user.id in cars.keys():
            cars[user.id].append((product.id, product.name, product.price, car_user.count))
        else:
            cars[user.id] = [(product.id, product.name, product.price, car_user.count), ]
    return templates.TemplateResponse('product/car.html', info)


@product_router.get('/car/{id_product}')
async def car_get(request: Request, db: Annotated[Session, Depends(get_db)], id_product: int = -1,
                  user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Корзина'}
    if user is None:
        return RedirectResponse(f'/product/list/{id_product}', status_code=status.HTTP_303_SEE_OTHER)
    product = db.scalar(select(ProductModel).where(ProductModel.id == id_product))
    if product is None:
        return HTTPException(status.HTTP_404_NOT_FOUND, 'Товар не найден')
    info['product'] = product
    info['user'] = user
    info['count'] = 1
    return templates.TemplateResponse('product/car.html', info)


@product_router.get('/buy/{user_id}')
async def buy_get(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int = -1, delet: int = -1,
                  shop: str = '', user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    if delet > -1:
        for i in range(len(cars[user_id])):
            if cars[user_id][i][0] == delet:
                product = db.scalar(select(ProductModel).where(ProductModel.id == delet))
                db.execute(update(ProductModel).where(ProductModel.id == delet).values(
                    count=product.count + cars[user_id][i][3], is_active=True))
                db.commit()
                cars[user_id].pop(i)
    if user_id not in cars.keys():
        return RedirectResponse('/product/list', status_code=status.HTTP_303_SEE_OTHER)
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    info['shops'] = db.scalars(select(Shops)).all()
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    return templates.TemplateResponse('product/buy.html', info)


@product_router.post('/buy/{user_id}')
async def buy_post(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int = -1,
                   user=Depends(get_current_user), shop: str = Form(...)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    print(shop)
    if shop == '':
        info['message'] = 'Выберите магазин'
        return templates.TemplateResponse('product/buy.html', info)

    return RedirectResponse(f'/product/payment/{user_id}?shop={shop}', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/payment/{user_id}')
async def payment_get(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int = -1, shop: str = '',
                      user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Оплата товара'}
    cost = 0
    car = cars[user_id]
    info['car'] = car
    info['user'] = user
    for item in car:
        cost += item[2] * item[3]
    info['cost'] = cost
    shop = db.scalar(select(Shops).where(Shops.id == int(shop)))
    info['shop'] = shop
    return templates.TemplateResponse('product/payment.html', info)


@product_router.post('/payment/{user_id}')
async def payment_post(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int = -1,
                       user=Depends(get_current_user), shop: str = ''):
    operations = db.scalars(select(BuyerProd).order_by(desc(BuyerProd.id_operation))).first()
    if operations is None:
        operation = 1
    else:
        operation = operations.id_operation + 1
    for item in cars[user_id]:
        db.execute(
            insert(BuyerProd).values(user=user.id, product=item[0], id_operation=operation, id_shop=int(shop)))
    db.commit()
    cars.pop(user_id)
    return HTMLResponse('Спасибо за покупку')


@product_router.get('/shop/create')
async def create_shop_get(request: Request, db: Annotated[Session, Depends(get_db)],
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        return templates.TemplateResponse('product/add_shop_page.html', info)


@product_router.post('/shop/create')
async def create_shop_post(request: Request, db: Annotated[Session, Depends(get_db)], shop: Shop = Form(),
                           user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Добавление магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(insert(Shops).values(name=shop.name, location=shop.location))
        db.commit()
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/update/{shop_id}')
async def update_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = db.scalar(select(Shops).where(Shops.id == shop_id))
        if shop is None:
            return RedirectResponse('/product/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('product/update_shop_page.html', info)


@product_router.post('/shop/update/{shop_id}')
async def update_shop_post(request: Request, db: Annotated[Session, Depends(get_db)], shop: Shop = Form(),
                           shop_id: int = -1, user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Изменение данных магазина'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(update(Shops).where(Shops.id == shop_id).values(name=shop.name, location=shop.location))
        db.commit()
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/delete/{shop_id}')
async def delete_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        shop = db.scalar(select(Shops).where(Shops.id == shop_id))
        if shop is None:
            return RedirectResponse('/product/shop/list')
        info['shop'] = shop
        return templates.TemplateResponse('product/delete_shop_page.html', info)


@product_router.post('/shop/delete/{shop_id}')
async def delete_shop_post(request: Request, db: Annotated[Session, Depends(get_db)],
                           shop_id: int = -1, user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Удаление данных о магазине'}
    if user is None:
        return RedirectResponse('/user/login')
    elif not user.is_staff:
        return RedirectResponse('/main')
    else:
        info['display'] = 'Ok'
        db.execute(delete(Shops).where(Shops.id == shop_id))
        db.commit()
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)


@product_router.get('/shop/list')
async def select_shop_get(request: Request, db: Annotated[Session, Depends(get_db)],
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Список магазинов'}
    shops = db.scalars(select(Shops)).all()
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    info['shops'] = shops
    return templates.TemplateResponse('product/shop_list_page.html', info)


@product_router.get('/shop/{shop_id}')
async def select_shop_get(request: Request, db: Annotated[Session, Depends(get_db)], shop_id: int = -1,
                          user=Depends(get_current_user)):
    info = {'request': request, 'title': 'Данные магазина'}
    if user is None:
        pass
    elif user.is_staff:
        info['display'] = 'Ok'
    shop = db.scalar(select(Shops).where(Shops.id == shop_id))
    if shop is None:
        return RedirectResponse('/product/shop/list', status_code=status.HTTP_303_SEE_OTHER)
    info['shop'] = shop
    return templates.TemplateResponse('product/shop_page.html', info)
