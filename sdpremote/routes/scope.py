from datetime import datetime
from typing import Any, Optional, Union

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse

from ..database import engine, scopes_table, objects_table
from ..entities.scope import Scope
from ..user import user
from ..utils.scope import set_scope
from .repo import repo_name

router = APIRouter(tags=['scope'])


class ScopeNew(BaseModel):
    creator_suffix: str = ''
    objects: dict[str, Union[int, None]] = Field(
        {},
        description='Mapping object key to SID or `null`',
    )

    def use_suffix(self, username: str) -> str:
        suffix = self.creator_suffix.strip()
        if suffix:
            return f'{username}@{suffix}'
        return username


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


@router.post(
    '/{user}/{repo}/{scope}',
    status_code=201,
    response_class=PlainTextResponse,
    responses={
        status.HTTP_409_CONFLICT: {
            'description': 'Scope with given name already exists'
        },
    },
)
async def create_scope(
        scopeInput: ScopeNew,
        repo_name: str = Depends(repo_name),
        scope: str = Path(...),
        username: str = Depends(user),
) -> str:
    timestamp = datetime.utcnow() if scopeInput.objects else None
    creator = scopeInput.use_suffix(username) if scopeInput.objects else None
    async with engine.begin() as conn:
        try:
            await conn.execute(
                sa.insert(scopes_table).values(
                    name=scope,
                    repo=repo_name,
                    timestamp=timestamp,
                    creator=creator,
                ))
        except sa.exc.IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT)
        if scopeInput.objects:
            await set_scope(
                scopeInput.objects,
                repo_name,
                scope,
                username,
                creator,  # type: ignore
                timestamp,  # type: ignore
                conn,
            )
        await conn.commit()
    return 'created'


@router.put(
    '/{user}/{repo}/{scope}',
    response_class=PlainTextResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'description': 'Something is not found or invalid checksum'
        },
    },
)
async def replace_scope(
        scopeInput: ScopeNew,
        checksum: Optional[str] = Query(
            None,
            description='checksum of current scope state',
        ),
        repo_name: str = Depends(repo_name),
        scope: str = Path(...),
        username: str = Depends(user),
):
    timestamp = datetime.utcnow() if scopeInput.objects else None
    creator = scopeInput.use_suffix(username) if scopeInput.objects else None
    async with engine.begin() as conn:
        result: Any= await conn.execute(
            sa.update(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo_name)\
                .where(scopes_table.c.checksum == checksum)\
                .values(
                    timestamp=timestamp,
                    creator=creator,
                    checksum=None,
                )
        )
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await conn.execute(
            sa.delete(objects_table)\
                .where(objects_table.c.name == scope)\
                .where(objects_table.c.repo == repo_name)
        )
        if scopeInput.objects:
            await set_scope(
                scopeInput.objects,
                repo_name,
                scope,
                username,
                creator,  # type: ignore
                timestamp,  # type: ignore
                conn,
            )
        await conn.commit()
    return 'updated'
