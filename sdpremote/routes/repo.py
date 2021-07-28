import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import PlainTextResponse

from ..database import engine, repos_table
from ..user import user

router = APIRouter(tags=['repo'])


def repo_name(user: str = Depends(user), repo: str = Path(...)) -> str:
    return f'{user}/{repo}'


@router.post(
    '/{user}/{repo}',
    response_class=PlainTextResponse,
    response_description='Created',
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {
            'description': 'Repo with given name already exists',
        }
    },
)
async def create_repo(repo: str = Depends(repo_name)) -> str:
    query = sa.insert(repos_table).values(name=repo)
    async with engine.begin() as conn:
        try:
            await conn.execute(query)
            await conn.commit()
        except sa.exc.IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT)
    return 'created'


@router.delete(
    '/{user}/{repo}',
    response_class=PlainTextResponse,
    response_description='Deleted',
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            'description': 'Repo with given name is not exist',
        }
    },
)
async def delete_repo(repo: str = Depends(repo_name)) -> str:
    query = sa.delete(repos_table).where(repos_table.c.name == repo)
    async with engine.begin() as conn:
        result: int = (await conn.execute(query)).rowcount
        await conn.commit()
    if not result:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return 'deleted'
