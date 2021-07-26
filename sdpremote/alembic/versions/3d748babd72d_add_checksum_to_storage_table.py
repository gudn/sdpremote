"""add checksum to storage table

Revision ID: 3d748babd72d
Revises: 6e301d833b85
Create Date: 2021-07-26 19:47:37.914756

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '3d748babd72d'
down_revision = '6e301d833b85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(  # type: ignore
        'storage',
        sa.Column('checksum', sa.String(length=64), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('storage', 'checksum')  # type: ignore
    # ### end Alembic commands ###
