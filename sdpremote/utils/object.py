from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Union

import sqlalchemy as sa
from fastapi import HTTPException, status

from ..database import storage_table, objects_table


@dataclass(frozen=True)
class ObjectPath:
    key: str
    scope: str
    repo: str


@dataclass(frozen=True)
class ObjectExtra:
    creator: str
    timestamp: datetime


ObjectData = Union[int, None]


async def create_object(
        path: ObjectPath,
        data: ObjectData,
        extra: ObjectExtra,
        user: str,
        conn: Any,  # HACK AsyncConnection
) -> str:
    trx = await conn.begin_nested()

    checksum = None

    if data is not None:
        result: Any = await conn.execute(
            sa.update(storage_table).where(storage_table.c.id == data)\
                .values(expire_at=None)\
                .returning(storage_table.c.checksum, storage_table.c.owner)
        )
        if result.rowcount != 1:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                'storage object not found',
            )
        checksum, owner = result.one()
        if owner != user:
            raise HTTPException(status.HTTP_403_FORBIDDEN)

    query = sa.dialects.postgresql.insert(objects_table).values(
        key=path.key,
        scope=path.scope,
        repo=path.repo,
        checksum=checksum,
        creator=extra.creator,
        timestamp=extra.timestamp,
        data=data,
    ).on_conflict_do_update(
        index_elements=[
            objects_table.c.key,
            objects_table.c.scope,
            objects_table.c.repo,
        ],
        set_=dict(
            checksum=checksum,
            creator=extra.creator,
            timestamp=extra.timestamp,
            data=data,
        ),
    )
    await conn.execute(query)

    await trx.commit()

    return f'{path.key} ' + (checksum if checksum else 'null')
