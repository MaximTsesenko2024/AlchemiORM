from fastapi import FastAPI, Request, Depends
from typing import Annotated
from fastapi.responses import RedirectResponse
from .routers.users import user_router
from .routers.dependencies import get_current_user
from sqlalchemy import select
from app.backend.db.db_depends import get_db
from sqlalchemy.orm import Session
from .routers.product import product_router
from fastapi.templating import Jinja2Templates
from app.models.product import ProductModel, Categories

templates = Jinja2Templates(directory='app/templates/')

api = FastAPI()


@api.get('/')
async def redirect():
    return RedirectResponse('/main')


@api.get('/main')
async def welcome(db: Annotated[Session, Depends(get_db)], request: Request,
                  user=Depends(get_current_user), category:int = -1, q:str = ''):
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


api.include_router(user_router)
api.include_router(product_router)
