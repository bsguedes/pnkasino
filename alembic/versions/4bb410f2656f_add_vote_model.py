"""add vote model

Revision ID: 4bb410f2656f
Revises: 5679a800ab7d
Create Date: 2022-01-15 17:29:21.257908

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4bb410f2656f'
down_revision = '5679a800ab7d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('vote',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('message_id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_foreign_key(u'vote_message_fkey', 'vote', 'message', ['message_id'], ['id'])
    op.create_foreign_key(u'vote_user_fkey', 'vote', 'user', ['user_id'], ['id'])


def downgrade():
    op.drop_table('vote')
