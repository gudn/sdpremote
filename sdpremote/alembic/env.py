from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from sdpremote.database import metadata
from sdpremote.config import settings

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config  # type: ignore

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings['database.uri_sync']
    context.configure(  # type: ignore
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
    )

    with context.begin_transaction():  # type: ignore
        context.run_migrations()  # type: ignore


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = create_engine(settings['database.uri_sync'])

    with connectable.connect() as connection:  # type: ignore
        context.configure(  # type: ignore
            connection=connection,
            target_metadata=target_metadata,
            compare_server_default=True,
        )

        with context.begin_transaction():  # type: ignore
            context.run_migrations()  # type: ignore


if context.is_offline_mode():  # type: ignore
    run_migrations_offline()
else:
    run_migrations_online()
