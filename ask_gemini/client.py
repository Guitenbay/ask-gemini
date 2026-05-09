from collections.abc import AsyncIterator

from gemini_webapi import GeminiClient
from loguru import logger

from ask_gemini.config import GeminiCookies, ProxyConfig


class GeminiClientWrapper:
    def __init__(self):
        self._client: GeminiClient | None = None

    async def init(self) -> None:
        if not GeminiCookies.is_configured():
            raise RuntimeError(
                "Gemini cookies not configured. Run `ask-gemini --cookie-setup` for instructions."
            )

        self._client = GeminiClient(
            secure_1psid=GeminiCookies.PSID,
            secure_1psidts=GeminiCookies.PSIDTS,
            proxy=ProxyConfig.url or None,
        )
        await self._client.init(timeout=30, auto_close=False, auto_refresh=True)
        logger.debug("Gemini client initialized")

    async def _refresh_and_retry(self, error: Exception) -> bool:
        """On auth error, reload cookies from browser and reconnect."""
        err = str(error).lower()
        if any(k in err for k in ("auth", "cookie", "expired", "401", "403")):
            logger.warning(f"Auth error detected, refreshing cookies: {error}")
            if GeminiCookies.try_load_from_browser():
                try:
                    self._client = GeminiClient(
                        secure_1psid=GeminiCookies.PSID,
                        secure_1psidts=GeminiCookies.PSIDTS,
                        proxy=ProxyConfig.url or None,
                    )
                    await self._client.init(
                        timeout=30, auto_close=False, auto_refresh=True
                    )
                    return True
                except Exception:
                    pass
        return False

    async def ask(self, message: str, model: str) -> str:
        try:
            resp = await self._client.generate_content(message, model=model)
            return resp.text
        except Exception as e:
            if await self._refresh_and_retry(e):
                resp = await self._client.generate_content(message, model=model)
                return resp.text
            raise

    async def ask_stream(self, message: str, model: str) -> AsyncIterator[str]:
        try:
            async for chunk in self._client.generate_content_stream(
                message, model=model
            ):
                if chunk.text_delta:
                    yield chunk.text_delta
        except Exception as e:
            if await self._refresh_and_retry(e):
                async for chunk in self._client.generate_content_stream(
                    message, model=model
                ):
                    if chunk.text_delta:
                        yield chunk.text_delta
            else:
                raise
