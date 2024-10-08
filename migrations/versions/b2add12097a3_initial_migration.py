"""Initial migration

Revision ID: b2add12097a3
Revises: 51bbc429a025
Create Date: 2024-09-28 01:25:38.208054

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'b2add12097a3'
down_revision = '51bbc429a025'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('spot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image1', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image2', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image3', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image4', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image5', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('image6', sa.Text(), nullable=True))
        batch_op.drop_column('image')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('spot', schema=None) as batch_op:
        batch_op.add_column(sa.Column('image', mysql.TEXT(), nullable=True))
        batch_op.drop_column('image6')
        batch_op.drop_column('image5')
        batch_op.drop_column('image4')
        batch_op.drop_column('image3')
        batch_op.drop_column('image2')
        batch_op.drop_column('image1')

    # ### end Alembic commands ###
