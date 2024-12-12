from fastapi import APIRouter, Depends, status, HTTPException, Body, Request, Form, Response, Cookie, Header
from fastapi import params
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy import insert, select, update, delete
from sqlalchemy.orm import Session
from typing import Annotated
from app.models.users import User
from app.models.product import BuyerProd
from app.backend.db.db_depends import get_db
from fastapi.templating import Jinja2Templates
from app.shemas import CreateUser, SelectUser, UpdateUser, AdminUser, RepairPassword, CreatePassword
from datetime import datetime, date
from .auth import get_password_hash, create_access_token, verify_password
from .dependencies import get_current_user, find_user_by_id

user_router = APIRouter(prefix='/user', tags=['user'])
templates = Jinja2Templates(directory='app/templates/')


def check_user(db: Annotated[Session, Depends(get_db)], name: str, password: str):
    if name == '':
        return 'Имя пользователя не может быть пустым!', 'error', None
    user = db.scalar(select(User).where(User.username == name))
    if user is None:
        return 'Пользователь не найден.', 'error', user
    elif not verify_password(plain_password=password, hashed_password=user.password):
        return 'Пароль не верен!', 'error', user
    return 'Авторизованы', 'Ok', user


def check_uniq(users: list, username, email):
    result = {'username': True, 'email': True}
    for user in users:
        if user.username == username:
            result['username'] = False
        if user.email == email:
            result['email'] = False
    return result


@user_router.post('/registration')
async def add_user_post(request: Request, db: Annotated[Session, Depends(get_db)],
                        create_user: CreateUser = Form()):
    info = {'request': request, 'title': 'Регистрация'}
    username = create_user.username
    # адрес электронной почты
    email = create_user.email
    # дата рождения пользователя
    day_birth = create_user.day_birth
    password = create_user.password
    repeat_password = create_user.repeat_password
    users = list(db.scalars(select(User)).all())
    check = check_uniq(users, username, email)
    if not check['username']:
        info['message'] = f'Пользователь {username} уже существует!'
    elif password != repeat_password:
        info['message'] = f'Пароли не совпадают!'
    elif not check['email']:
        info['message'] = f'Пользователь c email: {email} уже существует!'
    else:
        password = get_password_hash(password)
        result = db.execute(
            insert(User).values(username=username, day_birth=day_birth, email=email, password=password,
                                created_at=datetime.now(), updated_at=datetime.now()))

        db.commit()
        info['message'] = 'Зарегистрированы'
        user = db.scalar(select(User).where(User.username == username))
        access_token = create_access_token({"sub": str(user.id)})
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
        return response
    return templates.TemplateResponse("users/registration.html", info)


@user_router.get('/registration')
async def add_user_get(request: Request, db: Annotated[Session, Depends(get_db)],
                       user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Регистрация'}
    if user:
        info['message'] = user.username
    return templates.TemplateResponse("users/registration.html", info)


@user_router.get('/login')
async def enter_user_get(request: Request, db: Annotated[Session, Depends(get_db)]):
    info = {'request': request, 'title': 'Вход'}

    return templates.TemplateResponse("users/login.html", info)


@user_router.post('/login')
async def enter_user_post(request: Request, db: Annotated[Session, Depends(get_db)],
                          select_user: SelectUser = Form()):
    info = {'request': request, 'title': 'Вход'}
    username = select_user.username
    password = select_user.password

    info['message'], stat, user = check_user(db, username, password)
    print(info['message'], stat)
    if stat == 'Ok':
        access_token = create_access_token({"sub": str(user.id)})
        print(access_token)
        response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="users_access_token", value=access_token, httponly=True)
        print('set token')
    else:
        response = templates.TemplateResponse("users/login.html", info)
    return response


@user_router.get('/logout')
async def exit_user_get(request: Request,
                        user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Выход'}
    if user is not None:
        info['login'] = True
    return templates.TemplateResponse('users/logout.html', info)


@user_router.post('/logout')
async def exit_user_post(request: Request,
                         user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Выход'}
    if user is not None:
        info['message'] = f'Пользователь: {user.username} вышел из системы'
        response = templates.TemplateResponse('users/logout.html', info)
        response.delete_cookie(key="users_access_token")
        info['login'] = True
    else:
        info['message'] = 'Вы не были авторизованы'
        response = templates.TemplateResponse('users/logout.html', info)
    return response


@user_router.post('/update/{user_id}', response_class=HTMLResponse)
async def update_user_post(request: Request, db: Annotated[Session, Depends(get_db)],
                           user: Annotated[User, Depends(get_current_user)], user_id: int = -1,
                           update_user: UpdateUser = Form()):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        RedirectResponse('/user/login', status_code=status.HTTP_401_UNAUTHORIZED)
    elif user_id != user.id:
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Нет доступа')
    # адрес электронной почты
    email = update_user.email
    # возраст пользователя
    day_birth = update_user.day_birth
    db.execute(
        update(User).where(User.id == user_id).values(email=email, day_birth=day_birth, updated_at=datetime.now()))
    db.commit()
    info['message'] = 'Обновлено'
    info['user'] = user
    return templates.TemplateResponse("users/update_user.html", info)


@user_router.get('/update/{user_id}')
async def update_user_get(request: Request, db: Annotated[Session, Depends(get_db)],
                          user: Annotated[User, Depends(get_current_user)], user_id: int = -1):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        RedirectResponse('/user/login', status_code=status.HTTP_401_UNAUTHORIZED)
    elif user_id != user.id:
        return HTTPException(status.HTTP_401_UNAUTHORIZED, detail='Нет доступа')
    else:
        info['user'] = user
    return templates.TemplateResponse("users/update_user.html", info)


@user_router.get('/delete')
async def delete_user_self(request: Request, db: Annotated[Session, Depends(get_db)],
                           user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Удаление пользователя'}
    if user is not None:
        return RedirectResponse('/main', status_code=303)
    db.execute(update(User).where(User.id == user.id).values(is_active=False, updated_at=datetime.now()))
    db.commit()
    return RedirectResponse('/main', status_code=303)


@user_router.get('/')
async def select_user_get(request: Request, db: Annotated[Session, Depends(get_db)],
                          user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is not None:
        info['tk'] = True
        info['user'] = user
    return templates.TemplateResponse("users/user_page.html", info)


@user_router.get('/list/delete/{id_user}')
async def delete_user_admin_get(request: Request, db: Annotated[Session, Depends(get_db)],
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    info = {'request': request, 'title': 'Удаление пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(db, id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
        info['is_staff'] = user.admin
    return templates.TemplateResponse("users/user_page.html", info)


@user_router.post('/list/delete/{id_user}')
async def delete_user_admin_post(request: Request, db: Annotated[Session, Depends(get_db)],
                                 user: Annotated[User, Depends(get_current_user)], id_user: int):
    info = {'request': request, 'title': 'Удаление пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(db, id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        buy_products = db.scalars(select(BuyerProd).where(BuyerProd.user == user.id)).all()
        if buy_products is not None:
            db.execute(delete(BuyerProd).where(BuyerProd.user == user.id))
        db.execute(delete(User).where(User.id == user.id))
        db.commit()
        return RedirectResponse('user/list', status_code=status.HTTP_303_SEE_OTHER)


@user_router.post('/list/update/{id_user}')
async def update_user_admin_post(request: Request, db: Annotated[Session, Depends(get_db)],
                                 user: Annotated[User, Depends(get_current_user)], user_update: AdminUser = Form(),
                                 id_user: int = -1):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(db, id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
        db.execute(update(User).where(User.id == user.id).values(email=user_update.email,
                                                                 day_birth=user_update.day_birth,
                                                                 is_active=user_update.is_active,
                                                                 is_staff=user_update.is_staff, admin=user_update.admin,
                                                                 updated_at=datetime.now()))
        db.commit()
    return RedirectResponse('user/list', status_code=status.HTTP_303_SEE_OTHER)


@user_router.get('/list/update/{id_user}')
async def update_user_admin_get(request: Request, db: Annotated[Session, Depends(get_db)],
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(db, id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
    return templates.TemplateResponse("users/update_admin_user.html", info)


@user_router.get('/list/{id_user}')
async def select_user_admin_get(request: Request, db: Annotated[Session, Depends(get_db)],
                                user: Annotated[User, Depends(get_current_user)], id_user: int):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')
    elif not user.admin:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                             detail='Вы не авторизованны или у вас отсутствуют права')

    user = find_user_by_id(db, id_user)
    if user is None:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Пользователь не найден')
    else:
        info['user'] = user
        info['is_staff'] = user.admin
    return templates.TemplateResponse("users/user_page.html", info)


@user_router.get('/list')
async def select_list_user_get(request: Request, db: Annotated[Session, Depends(get_db)],
                               user: Annotated[User, Depends(get_current_user)]):
    info = {'request': request, 'title': 'Данные пользователя'}
    if user is None:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail='вы не авторизованны. Пройдите авторизацию')
    elif user.admin:
        users = db.scalars(select(User)).all()
        info['users'] = users
    return templates.TemplateResponse("users/users_list.html", info)


@user_router.get('/repair')
async def repair_password_get(request: Request, db: Annotated[Session, Depends(get_db)]):
    info = {'request': request, 'title': 'Востановление пароля'}
    return templates.TemplateResponse("users/repair.html", info)


@user_router.post('/repair')
async def repair_password_post(request: Request, db: Annotated[Session, Depends(get_db)],
                               repair: RepairPassword = Form()):
    info = {'request': request, 'title': 'Востановление пароля'}
    user = db.scalar(select(User).where(repair.username == User.username and repair.email == User.email))
    if user is None:
        info['message'] = 'Пользователь не найден'
        return templates.TemplateResponse("users/repair.html", info)
    return RedirectResponse(f'/user/create_password/{user.id}', status_code=status.HTTP_303_SEE_OTHER)


@user_router.get('/create_password/{user_id}')
async def create_password_get(request: Request, db: Annotated[Session, Depends(get_db)], user_id: int=-1):
    info = {'request': request, 'title': 'Создание нового пароля'}
    user = db.scalar(select(User).where(user_id == User.id).column(User.username))
    if user is None:
        info['message'] = 'Пользователь не найден'
        return RedirectResponse('/user', status_code=status.HTTP_303_SEE_OTHER)
    info['name'] = user.username
    info['user_id'] = user_id
    return templates.TemplateResponse("users/create_new_password.html", info)


@user_router.post('/create_password/{user_id}')
async def create_password_post(request: Request, db: Annotated[Session, Depends(get_db)],
                               create_password:CreatePassword = Form(), user_id: int=-1):
    info = {'request': request, 'title': 'Создание нового пароля'}
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        info['message'] = 'Пользователь не найден'
        return RedirectResponse('/user', status_code=status.HTTP_303_SEE_OTHER)
    password = create_password.password
    repeat_password = create_password.repeat_password
    if password != repeat_password:
        info['message'] = 'Пароли не соответствуют'
        info['name'] = user.username
        info['user_id'] = user_id
        return templates.TemplateResponse("users/create_new_password.html", info)
    password = get_password_hash(password)
    result = db.execute(
        update(User).where(User.id==user_id).values(password=password,updated_at=datetime.now()))
    db.commit()
    info['message'] = 'Пароль изменён'
    access_token = create_access_token({"sub": str(user.id)})
    response = RedirectResponse(f'/user', status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="users_access_token", value=access_token, httponly=True)
    return response

