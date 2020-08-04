"""add state to league

Revision ID: 1927f60a4e13
Revises: c19c42ac0f3c
Create Date: 2020-07-26 22:23:59.755675

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1927f60a4e13'
down_revision = 'c19c42ac0f3c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('category', 'state')
    op.execute('UPDATE "league" SET "state" = \'available\'')
    op.alter_column('league', 'state',
                    existing_type=sa.VARCHAR(length=20),
                    nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('league', 'state',
               existing_type=sa.VARCHAR(length=20),
               nullable=True)
    op.add_column('category', sa.Column('state', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###