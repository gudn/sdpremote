from fastapi import FastAPI
from sqlalchemy.sql import text

from . import __version__
from .config import settings
from .database import engine
from .storage import SThread
from .routes import repo, scope, upload

settings.validators.validate()  # type: ignore
app = FastAPI(version=__version__)


@app.get('/')
def index():
    return str(settings['intro'])


@app.on_event('startup')
async def check_engine():
    async with engine.connect() as conn:
        await conn.execute(text('SELECT now()'))


@app.on_event('shutdown')
async def close_engine():
    await engine.dispose()


@app.on_event('startup')
def start_sthread():
    SThread().start()


@app.on_event('shutdown')
def close_sthread():
    SThread.event.set()


app.include_router(repo.router)
app.include_router(scope.router)
app.include_router(upload.router)
