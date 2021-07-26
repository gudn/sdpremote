import threading
import time
from datetime import datetime

import minio
from minio.deleteobjects import DeleteObject
import schedule
import sqlalchemy as sa

from .config import settings
from .database import storage_table

storage = minio.Minio(**settings['storage'].to_dict())

_buckets = storage.list_buckets()
if not any(b.name == 'sdpremote' for b in _buckets):
    storage.make_bucket('sdpremote')


class SThread(threading.Thread):
    event = threading.Event()
    interval =  3 * 3600  # sleep interval in seconds

    @classmethod
    def stop(cls):
        cls.event.set()

    @classmethod
    def run(cls):
        while True:
            schedule.run_pending()
            for _ in range(cls.interval):
                time.sleep(1)
                if cls.event.is_set():
                    return


def delete_expired():
    # create engine here because this is only use one time pet 6 hours
    _engine = sa.create_engine(
        settings['database.uri_sync'],
        echo=settings['debug'],
        pool_size=1,
    )
    query = sa.select([storage_table.c.id])\
        .where(storage_table.c.expire_at < datetime.utcnow())
    with _engine.connect() as conn:
        result = conn.execute(query)
        ids: set[int] = set(result.scalars().all())
    objects = [DeleteObject(str(i)) for i in ids]
    errors = {
        error.name
        for error in storage.remove_objects('sdpremote', objects)
    }
    successful_deleted = ids - errors
    query = sa.delete(storage_table)\
        .where(storage_table.c.id.in_(successful_deleted))
    with _engine.connect() as conn:
        conn.execute(query)
    _engine.dispose()


schedule.every(6).hours.do(delete_expired)
