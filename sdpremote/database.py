from sqlalchemy.ext.asyncio import create_async_engine  # type: ignore

from .config import settings

engine = create_async_engine(settings['database.uri'],
                             echo=bool(settings['debug']))
