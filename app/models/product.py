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
    category_id = Column(INTEGER, ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    # участие в акции
    action = Column(BOOLEAN, default=False)
    # картинка товара
    img = Column(String)
    category = relationship('Categories', back_populates='product')
    used_buy = relationship(
        'BuyerProd',
        back_populates='product',
        cascade='save-update, merge, delete, delete-orphan',
        passive_deletes=True,
    )


