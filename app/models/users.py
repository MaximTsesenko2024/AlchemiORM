from app.backend.db.db import Base
from sqlalchemy import INTEGER, String, ForeignKey, Column, BOOLEAN, DATETIME, DATE
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {'keep_existing': True}
    id = Column(INTEGER, primary_key=True, index=True)
    # имя пользователя в системе
    username = Column(String, index=True, unique=True)
    # адрес электронной почты
    email = Column(String, index=True, unique=True)
    # дата рождения
    day_birth = Column(DATE)
    password = Column(String)
    # Флаг активности пользователя
    is_active = Column(BOOLEAN, default=True)
    # Флаг принадлежности к сотрудникам
    is_staff = Column(BOOLEAN, default=False)
    # Флаг принадлежности к администраторам
    admin = Column(BOOLEAN, default=False)
    # Временная метка создания объекта.
    created_at = Column(DATETIME)
    # Временная метка показывающая время последнего обновления объекта.
    updated_at = Column(DATETIME)
    purchase = relationship(
        'BuyerProd',
        back_populates='user',
        cascade='save-update, merge, delete',
        passive_deletes=True,
    )


