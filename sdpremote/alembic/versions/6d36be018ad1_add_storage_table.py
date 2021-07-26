"""add storage table

Revision ID: 6d36be018ad1
Revises: 62ca5dfee7b1
Create Date: 2021-07-26 13:19:51.024510

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '6d36be018ad1'
down_revision = '62ca5dfee7b1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(  # type: ignore
        'storage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            'expire_at',
            sa.DateTime(),
            server_default=sa.text("current_timestamp + interval '6 hour'"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint('id',
                                name=op.f('pk__storage')),  # type: ignore
    )
    op.create_index(  # type: ignore
        op.f('ix__storage__expire_at'),  # type: ignore
        'storage',
        ['expire_at'],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix__storage__expire_at'),  # type: ignore
                  table_name='storage')
    op.drop_table('storage')  # type: ignore
    # ### end Alembic commands ###
