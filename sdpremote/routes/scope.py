from datetime import datetime
from enum import Enum
from typing import Any, Optional, Union

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, Field
from starlette.responses import PlainTextResponse

from ..database import engine, objects_table, scopes_table
from ..entities.scope import Scope
from ..utils.checksum import calc_checksum
from ..utils.object import ObjectData, ObjectExtra, ObjectPath, create_object
from ..utils.scope import calc_checksum, set_scope
from ..utils.user import user
from .repo import repo_name

router = APIRouter(tags=['scope'])


class Action(str, Enum):
    delete = 'delete'


class _ScopeBase(BaseModel):
    creator_suffix: str = ''

    def use_suffix(self, username: str) -> str:
        suffix = self.creator_suffix.strip()
        if suffix:
            return f'{username}@{suffix}'
        return username


class ScopeNew(_ScopeBase):
    objects: dict[str, ObjectData] = Field(
        dict(),
        description='Mapping object key to SID or `null`',
    )


class ScopePatch(_ScopeBase):
    objects: dict[str, Union[ObjectData, Action]] = Field(
        dict(),
        description='Mapping object key to SID (for replace/create), `null`'
        '(to set `null`) or to `"delete"` for deleting key',
    )


@router.get(
    '/{user}/{repo}',
    response_model=list[Scope],
)
async def list_scopes(
        repo: str = Depends(repo_name),
        scope: Optional[str] = Query(None),
        is_prefix: bool = Query(True),
) -> list[Scope]:
    query = sa.select([
        scopes_table.c.name, scopes_table.c.checksum, scopes_table.c.creator,
        scopes_table.c.timestamp
    ]).where(scopes_table.c.repo == repo)
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
    response_model=Scope,
    responses={
        status.HTTP_409_CONFLICT: {
            'description': 'Scope with given name already exists'
        },
    },
)
async def create_scope(
        scopeInput: ScopeNew,
        repo: str = Depends(repo_name),
        scope: str = Path(...),
        username: str = Depends(user),
) -> Scope:
    timestamp = datetime.utcnow() if scopeInput.objects else None
    creator = scopeInput.use_suffix(username) if scopeInput.objects else None
    async with engine.begin() as conn:
        try:
            await conn.execute(
                sa.insert(scopes_table).values(
                    name=scope,
                    repo=repo,
                    timestamp=timestamp,
                    creator=creator,
                ))
        except sa.exc.IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT)

        checksum = None
        if scopeInput.objects:
            checksum = await set_scope(
                scopeInput.objects,
                repo,
                scope,
                username,
                ObjectExtra(
                    creator=creator,  # type: ignore
                    timestamp=timestamp,  # type: ignore
                ),
                conn,
            )
        await conn.commit()

    return Scope(
        name=scope,
        checksum=checksum,
        creator=creator,
        timestamp=timestamp,
    )


@router.put(
    '/{user}/{repo}/{scope}',
    status_code=status.HTTP_205_RESET_CONTENT,
    response_model=Scope,
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
        repo: str = Depends(repo_name),
        scope: str = Path(...),
        username: str = Depends(user),
) -> Scope:
    timestamp = datetime.utcnow() if scopeInput.objects else None
    creator = scopeInput.use_suffix(username) if scopeInput.objects else None
    async with engine.begin() as conn:
        result: Any = await conn.execute(
            sa.update(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo)\
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
                .where(objects_table.c.scope == scope)\
                .where(objects_table.c.repo == repo)
        )

        checksum = None
        if scopeInput.objects:
            checksum = await set_scope(
                scopeInput.objects,
                repo,
                scope,
                username,
                ObjectExtra(
                    creator=creator,  # type: ignore
                    timestamp=timestamp,  # type: ignore
                ),
                conn,
            )
        await conn.commit()

    return Scope(
        name=scope,
        checksum=checksum,
        creator=creator,
        timestamp=timestamp,
    )


@router.patch(
    '/{user}/{repo}/{scope}',
    status_code=status.HTTP_202_ACCEPTED,
    response_model=Scope,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'description': 'Something is not found or invalid checksum'
        },
        status.HTTP_204_NO_CONTENT: {
            'description': 'No changes was provided in requiest'
        }
    },
)
async def patch_scope(
        scopeInput: ScopePatch,
        checksum: Optional[str] = Query(
            None,
            description='checksum of current scope state',
        ),
        repo: str = Depends(repo_name),
        scope: str = Path(...),
        username: str = Depends(user),
) -> Scope:
    if not scopeInput.objects:
        raise HTTPException(status.HTTP_204_NO_CONTENT)
    extra = ObjectExtra(
        creator=scopeInput.use_suffix(username),
        timestamp=datetime.utcnow(),
    )
    async with engine.begin() as conn:
        result: Any = await conn.execute(
            sa.update(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo)\
                .where(scopes_table.c.checksum == checksum)\
                .values(
                    timestamp=None,
                    creator=None,
                    checksum=None,
                )
        )
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND)

        checksums: dict[str, str] = {}

        result = await conn.execute(
            sa.select([objects_table.c.key, objects_table.c.checksum])\
                .where(objects_table.c.scope == scope)\
                .where(objects_table.c.repo == repo)
        )
        for key, checksum in result:
            checksums[key] = f'{key} ' + (checksum if checksum else 'null')

        to_delete: list[str] = []
        for key, value in scopeInput.objects.items():
            if value == Action.delete:
                to_delete.append(key)
                if key not in checksums:
                    raise HTTPException(status.HTTP_404_NOT_FOUND,
                                        f'not found object {key}')
                del checksums[key]
                continue
            checksums[key] = await create_object(
                ObjectPath(key=key, scope=scope, repo=repo),
                value,
                extra,
                username,
                conn,
            )
        if to_delete:
            await conn.execute(
                sa.delete(objects_table)\
                    .where(objects_table.c.scope == scope)\
                    .where(objects_table.c.repo == repo)\
                    .where(objects_table.c.key.in_(to_delete))
            )

        checksum = None
        if checksums:
            checksum = calc_checksum(checksums)
            await conn.execute(
                sa.update(scopes_table)\
                    .where(scopes_table.c.name == scope)\
                    .where(scopes_table.c.repo == repo)\
                    .values(
                        checksum=checksum,
                        creator=extra.creator,
                        timestamp=extra.timestamp,
                    )
            )

        await conn.commit()

    return Scope(
        name=scope,
        checksum=checksum,
        creator=extra.creator,
        timestamp=extra.timestamp,
    )


@router.delete(
    '/{user}/{repo}/{scope}',
    response_class=PlainTextResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'description': 'Something is not found or invalid checksum',
        },
    },
)
async def delete_scope(
        checksum: Optional[str] = Query(
            None,
            description='checksum of current scope state',
        ),
        repo: str = Depends(repo_name),
        scope: str = Path(...),
):
    async with engine.begin() as conn:
        result = await conn.execute(
            sa.delete(scopes_table)\
                .where(scopes_table.c.name == scope)\
                .where(scopes_table.c.repo == repo)\
                .where(scopes_table.c.checksum == checksum)
        )
        if result.rowcount == 0:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        await conn.commit()
    return 'deleted'
