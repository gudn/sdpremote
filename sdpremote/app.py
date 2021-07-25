from fastapi import FastAPI

from . import __version__
from .config import settings


app = FastAPI(
    version=__version__
)


@app.get('/')
def index():
    return str(settings['intro'])
