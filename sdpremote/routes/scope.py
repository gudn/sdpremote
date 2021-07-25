from typing import Any, Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query

from ..database import engine, scopes_table
from ..entities.scope import Scope
from .repo import repo_name

router = APIRouter(tags=['scope'])


@router.get(
    '/{user}/{repo}',
    response_model=list[Scope],
)
async def list_scopes(
        repo_name: str = Depends(repo_name),
        scope: Optional[str] = Query(None),
        is_prefix: bool = Query(True),
) -> list[Scope]:
    query = sa.select([
        scopes_table.c.name, scopes_table.c.checksum, scopes_table.c.creator,
        scopes_table.c.timestamp
    ]).where(scopes_table.c.repo == repo_name)
    if scope:
        if is_prefix:
            query = query.where(scopes_table.c.name.like(f'{scope}%'))
        else:
            query = query.where(scopes_table.c.name == scope)
    async with engine.connect() as conn:
        res: list[Scope] = list(
            map(
                lambda d: Scope(**d),
                (await conn.execute(query)).mappings(),
            ))
    return res
