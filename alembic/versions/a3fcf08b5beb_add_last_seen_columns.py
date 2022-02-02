"""add last seen columns

Revision ID: a3fcf08b5beb
Revises: 25a830c68649
Create Date: 2022-02-02 16:54:41.876181

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3fcf08b5beb'
down_revision = '25a830c68649'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('last_fantasy_at', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('last_message_seen', sa.Integer(), nullable=True))
    op.add_column('user', sa.Column('last_scrap_seen', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'last_fantasy_at')
    op.drop_column('user', 'last_message_seen')
    op.drop_column('user', 'last_scrap_seen')
    # ### end Alembic commands ###
