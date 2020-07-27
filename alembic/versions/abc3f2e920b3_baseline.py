"""baseline

Revision ID: abc3f2e920b3
Revises: 
Create Date: 2020-07-26 20:15:52.944453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'abc3f2e920b3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('pnkoins', sa.Integer(), nullable=False))
    op.create_table(
        'league',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False))
    op.create_table(
        'category',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('question', sa.String(), nullable=False),
        sa.Column('max_bet', sa.Integer(), nullable=False),
        sa.Column('state', sa.String(), nullable=False),
        sa.Column('winner_option_id', sa.Integer()),
        sa.Column('league_id', sa.Integer(), nullable=False))
    op.create_table(
        'option',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('odds', sa.Float(), nullable=False))
    op.create_table(
        'bet',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.Integer(), nullable=False))

    op.create_foreign_key(u'category_option_fkey', 'category', 'option', ['winner_option_id'], ['id'])
    op.create_foreign_key(u'category_league_fkey', 'category', 'league', ['league_id'], ['id'])
    op.create_foreign_key(u'option_category_fkey', 'option', 'category', ['category_id'], ['id'])
    op.create_foreign_key(u'bet_category_fkey', 'bet', 'category', ['category_id'], ['id'])
    op.create_foreign_key(u'bet_user_fkey', 'bet', 'user', ['user_id'], ['id'])
    op.create_foreign_key(u'bet_option_fkey', 'bet', 'option', ['option_id'], ['id'])


def downgrade():
    op.drop_table('bet')
    op.drop_table('option')
    op.drop_table('category')
    op.drop_table('league')
    op.drop_table('user')
    op.drop_constraint(u'category_option_fkey', 'category', type_='foreignkey')
    op.drop_constraint(u'category_league_fkey', 'category', type_='foreignkey')
    op.drop_constraint(u'option_category_fkey', 'option', type_='foreignkey')
    op.drop_constraint(u'bet_category_fkey', 'bet', type_='foreignkey')
    op.drop_constraint(u'bet_user_fkey', 'bet', type_='foreignkey')
    op.drop_constraint(u'bet_option_fkey', 'bet', type_='foreignkey')


