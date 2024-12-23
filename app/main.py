import uvicorn
from fastapi import FastAPI, Request, Depends
from typing import Annotated
from fastapi.responses import RedirectResponse
from app.routers.users import user_router
from app.routers.dependencies import get_current_user
from sqlalchemy import select
from app.backend.db.db_depends import get_db
from sqlalchemy.orm import Session
from app.routers.product import product_router
from fastapi.templating import Jinja2Templates
from app.models.product import ProductModel, Categories
from fastapi.staticfiles import StaticFiles

templates = Jinja2Templates(directory='app/templates/')

api = FastAPI()
api.mount("/app/static", StaticFiles(directory="app/static"), name="static")


@api.get('/')
async def redirect():
    """
    Переадресация на главную страницу.+
    """
    return RedirectResponse('/main')


@api.get('/main')
async def welcome(db: Annotated[Session, Depends(get_db)], request: Request,
                  user=Depends(get_current_user), category: int = -1, q: str = ''):
    """
    Главная страница, обеспечение маршрутизации задач по управлению пользователями и управлению товарами
    :param db: Подключение к базе данных
    :param request: запрос от пользователя к системе
    :param user: текущий пользователь
    :param category: выбранная категория товара
    :param q: строка для поиска товара по названию или описанию
    :return: страница html - для общения с пользователем
    """
    info = {'request': request, 'title': 'Главная страница'}
    info['name'] = 'Вход не выполнен'
    if user is not None:
        info['name'] = user.username
        info['is_staff'] = user.is_staff
        info['user_id'] = user.id
    else:
        info['name'] = 'Вход не выполнен'
    info['categories'] = db.scalars(select(Categories).where(Categories.parent == -1)).all()
    if category > -1 and q != '':
        return RedirectResponse(f"/product/list?category={category}&q={q}")
    elif category > -1:
        return RedirectResponse(f"/product/list?category={category}")
    elif q != '':
        return RedirectResponse(f"/product/list?q={q}")
    return templates.TemplateResponse("product/main.html", info)


api.include_router(user_router)  # подключение маршрутов управления пользователями
api.include_router(product_router)  # подключение маршрутов управления товарами

if __name__ == "__main__":
    uvicorn.run(api, host="127.0.0.1", port=8000, log_level="info")
