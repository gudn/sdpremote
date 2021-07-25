import binascii
from base64 import b64decode
from typing import Optional

from fastapi import Depends, Header, status
from fastapi.exceptions import HTTPException


def _user_header(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    splitted = authorization.split()
    if len(splitted) != 2:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'only support basic authz schema',
        )

    schema, value = splitted
    if schema != 'Basic':
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'only support basic authz schema',
        )

    try:
        value = b64decode(value).decode()
    except binascii.Error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            'unable to decode value',
        )

    splitted = value.split(':')
    if len(splitted) != 2:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'invalid value')

    user = splitted[0]
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, 'invalid value')

    return user


def user(
        user: Optional[str] = None,
        login: str = Depends(_user_header),
) -> str:
    print(user)
    if user is not None and user != login:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return login
