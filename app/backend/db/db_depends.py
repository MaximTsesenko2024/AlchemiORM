from .db import session_local
from sqlalchemy import update
from app.models.users import User


async def get_db():
    db = session_local()
    try:
        yield db
    finally:
       # db.execute(update(User).values(login=''))
        #db.commit()
        db.close()
