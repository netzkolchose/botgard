

def get_full_username(user) -> str:
    username = getattr(user, "username", None)
    first_name = getattr(user, "first_name", None)
    last_name = getattr(user, "last_name", None)

    name = list(filter(bool, [first_name, last_name]))
    if not name:
        return username or "-"
    else:
        return " ".join(name)
