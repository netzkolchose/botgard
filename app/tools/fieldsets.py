from typing import Tuple


def remove_from_fieldsets(
        fieldsets: tuple,
        *remove_fields: str,
) -> tuple:
    """
    Remove one or more fields from a ModelAdmin fieldsets object.
    Returns a copy of the fieldsets object with the specified fields removed.
    """

    def _has_field(fields) -> bool:
        for field in fields:
            if isinstance(field, str):
                if field in remove_fields:
                    return True
            elif isinstance(field, (tuple, list)):
                for f in field:
                    if f in remove_fields:
                        return True
        return False

    def _remove_fields(fields) -> tuple:
        ret_fields = []
        for field in fields:
            if isinstance(field, str) and field in remove_fields:
                continue
            elif isinstance(field, (tuple, list)):
                field = tuple(
                    f for f in field
                    if f not in remove_fields
                )
            ret_fields.append(field)
        return tuple(ret_fields)

    fieldsets = list(fieldsets)

    for i, entry in enumerate(fieldsets):
        entry: Tuple[str, dict]
        if fields := entry[1].get("fields"):
            if _has_field(fields):
                fieldsets[i] = (entry[0], {
                    **entry[1],
                    "fields": _remove_fields(fields),
                })

    return tuple(fieldsets)
