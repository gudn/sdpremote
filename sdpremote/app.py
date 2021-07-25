from fastapi import FastAPI

from . import __version__


app = FastAPI(
    version=__version__
)


@app.get('/')
def index():
    return 'sdpremote'
