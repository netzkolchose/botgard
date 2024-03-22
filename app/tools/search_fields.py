from typing import Union, List, Tuple


def search_fields_compatible(
        search_fields: Union[Tuple[str, ...], List[str]]
) -> Union[Tuple[str, ...], List[str]]:
    """
    Removes the `@` operator from the searchfields
    if no postgres database is configured.

    :param search_fields: list or tuple of search field names
    :return:
    """

    from django.conf import settings
    if not settings.IS_POSTGRES:
        search_fields = tuple(
            s.replace("@", "")
            for s in search_fields
        )

    return search_fields
