from app.backend.db.db import Base
from sqlalchemy import INTEGER, String, ForeignKey, Column, BOOLEAN, DOUBLE
from sqlalchemy.orm import relationship


class ProductModel(Base):
    """
    Модель, описывающая сущность товара
    """
    __tablename__ = 'products'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    # наименование товара
    name = Column(String, index=True)
    # Описание товара
    description = Column(String)
    # артикул товара
    item_number = Column(String)
    # стоимость товара
    price = Column(DOUBLE)
    # доступное количество товара
    count = Column(INTEGER)
    # признак наличия товара
    is_active = Column(BOOLEAN, default=True)
    # категория товаров
    category = Column(INTEGER, ForeignKey('categories.id'), nullable=False)
    # участие в акции
    action = Column(BOOLEAN, default=False)
    # картинка товара
    img = Column(String)


class BuyerProd(Base):
    """
    Модель, описывающая сущность покупки товара
    """
    __tablename__ = 'buyer'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    user = Column(INTEGER, ForeignKey('users.id'), nullable=False)
    product = Column(INTEGER, ForeignKey('products.id'), nullable=False)
    id_operation = Column(INTEGER, nullable=False)
    id_shop = Column(INTEGER, ForeignKey('shops.id'), nullable=False)


class Categories(Base):
    """
    Модель, описывающая сущность категории
    """
    __tablename__ = 'categories'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    name = Column(String, unique=True)
    parent = Column(INTEGER, ForeignKey('categories.id'), default=-1)


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


user = relationship('User', back_populates='id')
product = relationship('ProductModel', back_populates='id')
id = relationship('BuyerProd', back_populates='product')
id = relationship('ProductModel', back_populates='category')
category = relationship('categories', back_populates='id')
id_shop = relationship('Shops', back_populates='id')
id = relationship('BuyerProd', back_populates='id_shop')
