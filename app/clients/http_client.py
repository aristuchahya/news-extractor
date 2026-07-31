import asyncio

import httpx

from app.config.constants import DEFAULT_HEADERS, TEMPO_SESSION_COOKIE_NAME
from app.config.settings import Settings, get_settings
from app.exceptions.extractor_exception import NetworkError
from app.utils.logger import get_logger
from app.utils.url import get_domain

logger = get_logger(__name__)


class HttpClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "HttpClient":
        self._client = self._build_client()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    def _build_client(self) -> httpx.AsyncClient:
        settings = self._settings
        limits = httpx.Limits(
            max_connections=settings.max_connections,
            max_keepalive_connections=settings.max_keepalive_connections,
        )
        headers = {**DEFAULT_HEADERS, "User-Agent": settings.user_agent}
        return httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(settings.request_timeout),
            limits=limits,
            http2=settings.http2,
            follow_redirects=settings.follow_redirect,
            verify=settings.verify_ssl,
        )

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = self._build_client()
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _session_headers(self, url: str) -> dict[str, str]:
        """Attach a bring-your-own session cookie for gated sources. See docs/auth.md."""
        domain = get_domain(url)
        if domain == "tempo.co" or domain.endswith(".tempo.co"):
            if self._settings.tempo_session_cookie:
                cookie = f"{TEMPO_SESSION_COOKIE_NAME}={self._settings.tempo_session_cookie}"
                return {"Cookie": cookie}
        return {}

    async def get(self, url: str) -> httpx.Response:
        """GET a URL with retry on timeout/connection errors and exponential backoff."""
        settings = self._settings
        last_exc: Exception | None = None
        extra_headers = self._session_headers(url)

        for attempt in range(1, settings.max_retry + 1):
            try:
                logger.info(
                    "Downloading HTML (attempt %d/%d): %s", attempt, settings.max_retry, url
                )
                response = await self.client.get(url, headers=extra_headers)
                logger.info("Status Code: %d", response.status_code)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                logger.error("HTTP error %d for %s", exc.response.status_code, url)
                raise NetworkError(f"HTTP {exc.response.status_code} for {url}") from exc
            except httpx.TooManyRedirects as exc:
                logger.error("Redirect loop for %s", url)
                raise NetworkError(f"Redirect loop for {url}") from exc
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as exc:
                last_exc = exc
                logger.warning("Retryable network error on attempt %d: %s", attempt, exc)
                if attempt < settings.max_retry:
                    await asyncio.sleep(settings.retry_backoff_base * (2 ** (attempt - 1)))

        logger.error("Connection failed after %d attempts: %s", settings.max_retry, url)
        raise NetworkError(
            f"Failed to download {url} after {settings.max_retry} attempts"
        ) from last_exc
