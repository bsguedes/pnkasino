"""add friendships

Revision ID: 776061ca57c0
Revises: 0361942b23e3
Create Date: 2022-02-06 16:25:04.307259

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '776061ca57c0'
down_revision = '0361942b23e3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('friendship',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('friend_id', sa.Integer(), nullable=False),
                    sa.Column('invited_id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_foreign_key(u'friendship_user_from_fkey', 'friendship', 'user', ['friend_id'], ['id'])
    op.create_foreign_key(u'friendship_user_to_fkey', 'friendship', 'user', ['invited_id'], ['id'])

    op.add_column('achievement', sa.Column('category', sa.Integer(), nullable=True))


def downgrade():
    op.drop_table('friendship')
    op.drop_column('achievement', 'category')
