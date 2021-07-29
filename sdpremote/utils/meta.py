import hashlib
from dataclasses import dataclass
from typing import Any, Optional, Union

import sqlalchemy as sa
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from ..database import metas_table, storage_table


@dataclass(frozen=True)
class MetaPath:
    key: str
    object_key: Optional[str]
    scope: str
    repo: str


MetaData = Union[int, bytes, None]


def _format_checksum(key: str, object_key: Optional[str],
                     checksum: Optional[str]) -> str:
    if not checksum:
        checksum = 'null'
    if object_key:
        prefix = f'{key}({object_key})'
    else:
        prefix = f'{key}'
    return f'meta {prefix} {checksum}'


async def create_meta(
        path: MetaPath,
        value: MetaData,
        user: str,
        conn: Any,  # HACK AsyncConnection
) -> str:
    trx = await conn.begin_nested()

    checksum = None
    if isinstance(value, int):
        result: Any = await conn.execute(
            sa.update(storage_table).where(storage_table.c.id == value)\
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
    elif isinstance(value, bytes):
        checksum = hashlib.sha256(value).hexdigest()

    data = value if isinstance(value, int) else None
    value = value if isinstance(value, bytes) else None

    result = await conn.execute(
        sa.select(sa.func.count(metas_table.c.id))\
            .where(metas_table.c.key == path.key)\
            .where(metas_table.c.object_key == path.object_key)\
            .where(metas_table.c.scope == path.scope)\
            .where(metas_table.c.repo == path.repo)\
    )

    try:
        if result.scalar() == 0:
            await conn.execute(
                sa.insert(metas_table).values(
                    key=path.key,
                    object_key=path.object_key,
                    scope=path.scope,
                    repo=path.repo,
                    checksum=checksum,
                    data=data,
                    value=value,
                ))
        else:
            await conn.execute(
                sa.update(metas_table)\
                    .where(metas_table.c.key == path.key)\
                    .where(metas_table.c.object_key == path.object_key)\
                    .where(metas_table.c.scope == path.scope)\
                    .where(metas_table.c.repo == path.repo)\
                    .values(
                        checksum=checksum,
                        data=data,
                        value=value,
                    )
            )
    except sa.exc.IntegrityError:
        raise HTTPException(status.HTTP_404_NOT_FOUND)

    await trx.commit()

    return _format_checksum(path.key, path.object_key, checksum)
