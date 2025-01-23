from .db import session_local


async def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()
