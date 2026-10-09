"""SQL identifiers that come from the feed map."""

import re

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def ident(name: str) -> str:
    if not _IDENT.fullmatch(name):
        raise ValueError(f"invalid SQL identifier: {name}")
    return name
