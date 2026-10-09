"""Cast a source value using the cast named in the feed map."""

from pipeline.quality import blank, flag, number, whole


def cast(value, kind: str):
    if kind == "real":
        return number(value)
    if kind == "int":
        return whole(value)
    if kind == "flag":
        return flag(value)
    if kind == "driver":
        if value is None or value == "" or value == "-":
            return None
        return value
    return blank(value)
