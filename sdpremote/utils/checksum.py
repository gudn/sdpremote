import hashlib
import operator
from typing import Any

Checksum = str

_secondItem = operator.itemgetter(1)


def calc_checksum(values: dict[Any, Checksum]) -> str:
    content = '\n'.join(map(_secondItem, sorted(values.items())))
    return hashlib.sha256(content.encode()).hexdigest()
