import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client

    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=30.0, pool=5.0),
            limits=httpx.Limits(
                max_connections=50,
                max_keepalive_connections=20,
            ),
        )

    return _client


async def close_client():
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()