from urllib.parse import urljoin

from app.core.config import settings

base_url=settings.BASE_URL
def ensure_full_url(url: str,) -> str:
    if not url:
        return url
    url = url.strip()
    if url.startswith(("http://", "https://")):
        return url
    print(url)
    print(base_url)
    return urljoin(base_url, url)