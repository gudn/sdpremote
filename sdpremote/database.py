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
