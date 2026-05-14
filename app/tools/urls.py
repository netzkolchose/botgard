import urllib.parse
from django.conf import settings


def full_url(url: str) -> str:
    """
    Add https:// before an url if required
    """
    if "//" not in url:
        return f"https://{url}"
    else:
        return url


def full_server_url(url: str) -> str:
    """
    Add https://<botgard-host>/ before an url.
    If the url contains some other scheme or host it is replaced!
    """
    url = urllib.parse.urlparse(url)
    scheme, netloc = settings.FULL_SERVER_HOST.split("//")
    url = url._replace(scheme=scheme[:-1], netloc=netloc)
    return url.geturl()
