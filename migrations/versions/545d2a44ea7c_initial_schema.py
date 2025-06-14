"""initial schema

Revision ID: 545d2a44ea7c
Revises: 
Create Date: 2025-06-06 19:44:55.685325

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '545d2a44ea7c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('duration', sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reservations', schema=None) as batch_op:
        batch_op.drop_column('duration')

    # ### end Alembic commands ###
