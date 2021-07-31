from datetime import timedelta
from typing import Optional, Union

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import RedirectResponse, Response

from ..database import engine, objects_table
from ..entities.object import Object
from ..storage import storage
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


@router.get(
    '/{user}/{repo}/{scope}/{key}/data',
    responses={
        status.HTTP_204_NO_CONTENT: {
            'description': 'Data is null'
        },
        status.HTTP_307_TEMPORARY_REDIRECT: {
            'description': 'Redirect to data'
        },
        status.HTTP_404_NOT_FOUND: {
            'description': 'Something not found'
        }
    },
)
async def get_data(
        repo: str = Depends(repo_name),
        scope: str = Path(...),
        key: str = Path(...),
) -> Union[RedirectResponse, Response]:
    query = sa.select([objects_table.c.data])\
        .where(objects_table.c.key == key)\
        .where(objects_table.c.scope == scope)\
        .where(objects_table.c.repo == repo)
    async with engine.connect() as conn:
        result = await conn.execute(query)
    try:
        sid = result.scalar_one()
    except sa.exc.NoResultFound:  # type: ignore
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    if not sid:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    url = storage.presigned_get_object(
        'sdpremote',
        str(sid),
        timedelta(hours=6),
    )
    return RedirectResponse(url)
