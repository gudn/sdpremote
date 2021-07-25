"""add scopes table

Revision ID: 62ca5dfee7b1
Revises: 52811586999c
Create Date: 2021-07-25 15:29:27.781406

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '62ca5dfee7b1'
down_revision = '52811586999c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(  # type: ignore
        'scopes',
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('repo', sa.Text(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('creator', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['repo'],
            ['repos.name'],
            name=op.f('fk__scopes__repo__repos'),  # type: ignore
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint(
            'name',
            'repo',
            name=op.f('pk__scopes'),  # type: ignore
        ),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scopes')  # type: ignore
    # ### end Alembic commands ###