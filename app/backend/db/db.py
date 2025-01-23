from sqlalchemy import create_engine, event, Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlite3 import Connection as SQLite3Connection


engine = create_engine('sqlite:///shop_db.db', echo=True)

session_local = sessionmaker(bind=engine)


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        print('turning on foreign keys ...')
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON;')
        cursor.close()


class Base(DeclarativeBase):
    pass

