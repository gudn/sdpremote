import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Iterable, Union

import sqlalchemy as sa
from fastapi import HTTPException, status

from ..database import storage_table, objects_table, scopes_table


@dataclass(frozen=True)
class ObjectPath:
    key: str
    scope: str
    repo: str


@dataclass(frozen=True)
class ObjectExtra:
    creator: str
    timestamp: datetime


async def create_object(
        path: ObjectPath,
        sid: Optional[int],
        extra: ObjectExtra,
        user: str,
        conn: Any,  # HACK AsyncConnection
) -> str:
    trx = await conn.begin_nested()

    checksum = None

    if sid is not None:
        result: Any = await conn.execute(
            sa.update(storage_table).where(storage_table.c.id == sid)\
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
        name=path.scope,
        repo=path.repo,
        checksum=checksum,
        creator=extra.creator,
        timestamp=extra.timestamp,
        data=sid,
    ).on_conflict_do_update(
        index_elements=[
            objects_table.c.key,
            objects_table.c.name,
            objects_table.c.repo,
        ],
        set_=dict(
            checksum=checksum,
            creator=extra.creator,
            timestamp=extra.timestamp,
            data=sid,
        ),
    )
    await conn.execute(query)

    await trx.commit()

    return f'{path.key} ' + (checksum if checksum else 'null')


def calc_checksum(checksums: Iterable[str]) -> str:
    content = '\n'.join(checksums)
    return hashlib.sha256(content.encode()).hexdigest()


async def set_scope(
        objects: dict[str, Union[int, None]],
        repo: str,
        scope: str,
        username: str,
        creator: str,
        timestamp: datetime,
        conn: Any,  # HACK AsyncConnection
):
    keys = sorted(objects.keys())
    # is timestamp/creator is None this var wont be used
    extra = ObjectExtra(creator=creator, timestamp=timestamp)  # type: ignore
    checksums: list[str] = [
        await create_object(
            ObjectPath(key=key, scope=scope, repo=repo),
            objects.get(key),
            extra,
            username,
            conn,
        ) for key in keys
    ]
    if checksums:
        checksum = calc_checksum(checksums)
        await conn.execute(
            sa.update(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo)\
                .values(checksum=checksum)
        )
