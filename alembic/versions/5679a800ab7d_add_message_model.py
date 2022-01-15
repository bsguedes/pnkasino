"""add message model

Revision ID: 5679a800ab7d
Revises: 48fcb2d13469
Create Date: 2022-01-12 19:30:37.324256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5679a800ab7d'
down_revision = '48fcb2d13469'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('message',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('message', sa.VARCHAR(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('likes', sa.Integer(), nullable=False),
                    sa.Column('dislikes', sa.Integer(), nullable=False),
                    sa.Column('parent_message_id', sa.Integer(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_foreign_key(u'message_message_fkey', 'message', 'message', ['parent_message_id'], ['id'])


def downgrade():
    op.drop_table('message')
