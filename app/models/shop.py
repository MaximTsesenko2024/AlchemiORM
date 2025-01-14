from app.backend.db.db import Base
from sqlalchemy import INTEGER, String, ForeignKey, Column, BOOLEAN, DOUBLE
from sqlalchemy.orm import relationship


class Shops(Base):
    """
    Модель, описывающая сущность магазин
    """
    __tablename__ = 'shops'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    name = Column(String, unique=True)
    location = Column(String)
    is_active = Column(BOOLEAN, default=True)
    