"""rename name column to scope in objects table

Revision ID: d32ee62c4759
Revises: 3d748babd72d
Create Date: 2021-07-28 21:46:07.241456

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd32ee62c4759'
down_revision = '3d748babd72d'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(  # type: ignore
        'objects',
        'name',
        new_column_name='scope',
    )
    op.drop_constraint(  # type: ignore
        'fk__objects__name_repo__scopes',
        'objects',
    )
    op.create_foreign_key(  # type: ignore
        'fk__objects__scope_repo__scopes',
        source_table='objects',
        referent_table='scopes',
        local_cols=['scope', 'repo'],
        remote_cols=['name', 'repo'],
        ondelete='CASCADE',
        onupdate='CASCADE',
    )


def downgrade():
    op.alter_column(  # type: ignore
        'objects',
        'scope',
        new_column_name='name',
    )
    op.drop_constraint(  # type: ignore
        'fk__objects__scope_repo__scopes',
        'objects',
    )
    op.create_foreign_key(  # type: ignore
        'fk__objects__name_repo__scopes',
        source_table='objects',
        referent_table='scopes',
        local_cols=['name', 'repo'],
        remote_cols=['name', 'repo'],
        ondelete='CASCADE',
        onupdate='CASCADE',
    )
