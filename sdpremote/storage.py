import minio

from .config import settings

storage = minio.Minio(**settings['storage'].to_dict())

_buckets = storage.list_buckets()
if not any(b.name == 'sdpremote' for b in _buckets):
    storage.make_bucket('sdpremote')
