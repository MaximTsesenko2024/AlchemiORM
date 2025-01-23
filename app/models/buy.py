from app.backend.db.db import Base
from sqlalchemy import INTEGER, String, ForeignKey, Column, BOOLEAN, DOUBLE
from sqlalchemy.orm import relationship


class BuyerProd(Base):
    """
    Модель, описывающая сущность покупки товара
    """
    __tablename__ = 'buyer'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True)
    user_id = Column(INTEGER, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = Column(INTEGER, ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    id_operation = Column(INTEGER, nullable=False)
    id_shop = Column(INTEGER, ForeignKey('shops.id', ondelete='CASCADE'), nullable=False)
    is_used = Column(BOOLEAN, default=False)
    count = Column(INTEGER)
    user = relationship('User', back_populates='purchase',)
    product = relationship('ProductModel', back_populates='used_buy')
    shop = relationship('Shops')
