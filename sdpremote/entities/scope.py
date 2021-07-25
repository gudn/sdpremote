from typing import Optional

from pydantic import BaseModel, Field


class Scope(BaseModel):
    name: str = Field(
        ...,
        description='Unique scope identifier. Cant start with dot',
    )
    checksum: Optional[str] = Field(
        None,
        description=
        '''Checksum of file that contains object checksums sorted by key,
        separated with newline (unix style, without trailing empty line).
        Algorithm SHA-256. Example: `abcdef123\\n abcdef124\\n defcba987\\n`.
        `null` if no objects in scope''',
    )
    creator: Optional[str] = Field(
        None,
        description=
        'Creator of most recent object, `null` if no objects in scope',
    )
    timestamp: Optional[str] = Field(
        None,
        description=
        'Milliseconds since epoch of most recent object, `null` if no objects in scope',
    )
