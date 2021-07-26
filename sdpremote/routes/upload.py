from typing import Optional
import sqlalchemy as sa
from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel

from ..database import engine, storage_table
from ..storage import uploadObject

router = APIRouter(tags=['upload'])


class Uploaded(BaseModel):
    sid: int


@router.post(
    '/upload',
    response_model=Uploaded,
    status_code=status.HTTP_201_CREATED,
)
async def upload(obj: UploadFile = File(...)):
    query = sa.text(
        f'INSERT INTO {storage_table.fullname} DEFAULT VALUES RETURNING id')
    async with engine.begin() as conn:
        result = await conn.execute(query)
        sid: Optional[int] = result.scalar()
        await conn.commit()
    if not sid:
        raise HTTPException(status.HTTP_507_INSUFFICIENT_STORAGE,
                            'Cannot create storage entry')
    await uploadObject(sid, obj)
    return Uploaded(sid=sid)
