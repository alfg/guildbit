"""Add Token.package_id column.

Revision ID: d5f07e2ac9ab
Revises: 
Create Date: 2021-01-27 07:11:00.123785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5f07e2ac9ab'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('token', sa.Column('package_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_token_package_id'), 'token', ['package_id'], unique=False)
    op.create_foreign_key(None, 'token', 'package', ['package_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'token', type_='foreignkey')
    op.drop_index(op.f('ix_token_package_id'), table_name='token')
    op.drop_column('token', 'package_id')
    # ### end Alembic commands ###
