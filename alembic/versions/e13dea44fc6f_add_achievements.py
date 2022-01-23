"""add achievements

Revision ID: e13dea44fc6f
Revises: 6bd7b4b4aabf
Create Date: 2022-01-20 21:05:21.877224

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e13dea44fc6f'
down_revision = '6bd7b4b4aabf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('scrap',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('message', sa.VARCHAR(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('parent_scrap_id', sa.Integer(), nullable=True),
                    sa.Column('author_id', sa.Integer(), nullable=True),
                    sa.Column('profile_id', sa.Integer(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_foreign_key(u'scrap_scrap_fkey', 'scrap', 'scrap', ['parent_scrap_id'], ['id'])
    op.create_foreign_key(u'scrap_user_author_fkey', 'scrap', 'user', ['author_id'], ['id'])
    op.create_foreign_key(u'scrap_user_profile_fkey', 'scrap', 'user', ['profile_id'], ['id'])

    op.create_table('achievement',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('hero_id', sa.Integer(), nullable=False),
                    sa.Column('hero_name', sa.VARCHAR(), nullable=False),
                    sa.Column('description', sa.VARCHAR(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )

    op.create_table('achievement_user',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('user_id', sa.Integer(), nullable=False),
                    sa.Column('achievement_id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_foreign_key(u'achievement_user_achievement_fkey', 'achievement_user', 'achievement', ['achievement_id'], ['id'])
    op.create_foreign_key(u'achievement_user_user_fkey', 'achievement_user', 'user', ['user_id'], ['id'])


def downgrade():
    op.drop_table('scrap')
    op.drop_table('achievement')
    op.drop_table('achievement_user')
