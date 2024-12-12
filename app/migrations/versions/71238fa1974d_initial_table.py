"""initial table

Revision ID: 71238fa1974d
Revises: 
Create Date: 2024-12-09 18:45:51.455736

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '71238fa1974d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('categories',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('parent', sa.INTEGER(), nullable=True),
    sa.ForeignKeyConstraint(['parent'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('shops',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('location', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('email', sa.String(), nullable=True),
    sa.Column('day_birth', sa.DATE(), nullable=True),
    sa.Column('password', sa.String(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('is_staff', sa.BOOLEAN(), nullable=True),
    sa.Column('admin', sa.BOOLEAN(), nullable=True),
    sa.Column('created_at', sa.DATETIME(), nullable=True),
    sa.Column('updated_at', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('products',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('item_number', sa.String(), nullable=True),
    sa.Column('price', sa.DOUBLE(), nullable=True),
    sa.Column('count', sa.INTEGER(), nullable=True),
    sa.Column('is_active', sa.BOOLEAN(), nullable=True),
    sa.Column('category', sa.INTEGER(), nullable=False),
    sa.Column('action', sa.BOOLEAN(), nullable=True),
    sa.Column('img', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['category'], ['categories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_products_name'), 'products', ['name'], unique=False)
    op.create_table('buyer',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('user', sa.INTEGER(), nullable=False),
    sa.Column('product', sa.INTEGER(), nullable=False),
    sa.Column('id_operation', sa.INTEGER(), nullable=False),
    sa.Column('id_shop', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['id_shop'], ['shops.id'], ),
    sa.ForeignKeyConstraint(['product'], ['products.id'], ),
    sa.ForeignKeyConstraint(['user'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('buyer')
    op.drop_index(op.f('ix_products_name'), table_name='products')
    op.drop_table('products')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('shops')
    op.drop_table('categories')
    # ### end Alembic commands ###
