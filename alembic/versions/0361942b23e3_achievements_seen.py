"""achievements seen

Revision ID: 0361942b23e3
Revises: a3fcf08b5beb
Create Date: 2022-02-06 15:22:54.442318

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0361942b23e3'
down_revision = 'a3fcf08b5beb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('user', sa.Column('achievements_seen', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('user', 'achievements_seen')
