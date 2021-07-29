from typing import Any, Optional

import sqlalchemy as sa

from ..database import scopes_table
from .checksum import calc_checksum
from .object import ObjectData, ObjectExtra, ObjectPath, create_object


async def set_scope(
        objects: dict[str, ObjectData],
        repo: str,
        scope: str,
        user: str,
        extra: ObjectExtra,
        conn: Any,  # HACK AsyncConnection
) -> Optional[str]:
    checksums: dict[str, str] = {
        key: await create_object(
            ObjectPath(key=key, scope=scope, repo=repo),
            data,
            extra,
            user,
            conn,
        )
        for key, data in objects.items()
    }

    checksum = None
    if checksums:
        checksum = calc_checksum(checksums)
        await conn.execute(
            sa.update(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo)\
                .values(checksum=checksum)
        )

    return checksum
