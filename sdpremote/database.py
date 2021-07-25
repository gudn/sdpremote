import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine  # type: ignore

from .config import settings

engine = create_async_engine(
    settings['database.uri'],
    echo=bool(settings['debug']),
)

convention = {
    'all_column_names':
    lambda consts, _: '_'.join(col.name for col in consts.columns.values()),
    'ix':
    'ix__%(table_name)s__%(all_column_names)s',
    'uq':
    'uq__%(table_name)s__%(all_column_names)s',
    'ck':
    'ck__%(table_name)s__%(constraint_name)s',
    'fk':
    'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',
    'pk':
    'pk__%(table_name)s'
}

metadata = sa.MetaData(naming_convention=convention)

repos_table = sa.Table(
    'repos',
    metadata,
    sa.Column('name', sa.Text, primary_key=True),
)

scopes_table = sa.Table(
    'scopes',
    metadata,
    sa.Column('name', sa.Text, nullable=False),
    sa.Column(
        'repo',
        sa.ForeignKey(
            'repos.name',
            onupdate='CASCADE',
            ondelete='CASCADE',
        ),
        nullable=False,
    ),
    sa.PrimaryKeyConstraint('name', 'repo'),
    sa.Column('checksum', sa.String(64), nullable=True),
    sa.Column('creator', sa.Text, nullable=True),
    sa.Column('timestamp', sa.DateTime, nullable=True),
)
