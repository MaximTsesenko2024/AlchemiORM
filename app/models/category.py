from app.backend.db.db import Base
from sqlalchemy import INTEGER, String, ForeignKey, Column, BOOLEAN, DOUBLE
from sqlalchemy.orm import relationship


class Categories(Base):
    """
    Модель, описывающая сущность категории
    """
    __tablename__ = 'categories'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    name = Column(String, unique=True)
    parent = Column(INTEGER, ForeignKey('categories.id'), default=-1)
    parent_category = relationship('Categories')
