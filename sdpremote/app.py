from fastapi import FastAPI
from sqlalchemy.sql import text

from . import __version__
from .config import settings
from .database import engine
from .routes import repo, scope

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


app.include_router(repo.router)
app.include_router(scope.router)
