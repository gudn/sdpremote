from typing import Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Path, Query, status

from ..database import engine, objects_table
from ..entities.object import Object
from .repo import repo_name

router = APIRouter(tags=['object'])


@router.get(
    '/{user}/{repo}/{scope}',
    response_model=list[Object],
    responses={
        status.HTTP_404_NOT_FOUND: {
            'descrtiption': 'Something not found',
        },
    },
)
async def list_objects(
        repo: str = Depends(repo_name),
        scope: str = Path(...),
        key: Optional[str] = Query(None),
        is_prefix: bool = Query(True),
) -> list[Object]:
    query = sa.select([
        objects_table.c.key,
        objects_table.c.checksum,
        objects_table.c.creator,
        objects_table.c.timestamp,
    ]).where(objects_table.c.scope == scope)\
        .where(objects_table.c.repo == repo)
    if key:
        if is_prefix:
            query = query.where(objects_table.c.key.like(f'{key}%'))

        else:
            query = query.where(objects_table.c.key == key)
    async with engine.connect() as conn:
        res: list[Object] = list(
            map(
                lambda d: Object(**d),
                (await conn.execute(query)).mappings(),
            ))
    return res
