

def full_url(url: str) -> str:
    """
    Add https:// before an url if required
    """
    if "//" not in url:
        return f"https://{url}"
    else:
        return url
