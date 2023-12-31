"""add description columns

Revision ID: 547c2c4c7d77
Revises: 529a7750a835
Create Date: 2023-07-17 11:35:33.548320

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '547c2c4c7d77'
down_revision = '529a7750a835'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('description1', sa.String(length=200), nullable=True))
    op.add_column('product', sa.Column('description2', sa.String(length=200), nullable=True))
    op.add_column('product', sa.Column('description3', sa.String(length=200), nullable=True))
    op.drop_column('product', 'description')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('product', sa.Column('description', sa.VARCHAR(length=500), nullable=True))
    op.drop_column('product', 'description3')
    op.drop_column('product', 'description2')
    op.drop_column('product', 'description1')
    # ### end Alembic commands ###
