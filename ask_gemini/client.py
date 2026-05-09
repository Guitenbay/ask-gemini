from collections.abc import AsyncIterator

from gemini_webapi import GeminiClient
from loguru import logger

from ask_gemini.config import GeminiCookies, ProxyConfig


class _ChatSession:
    """Wraps a gemini-webapi ChatSession with model tracking."""

    def __init__(self, session, model: str):
        self.session = session
        self.model = model


class GeminiClientWrapper:
    def __init__(self):
        self._client: GeminiClient | None = None
        self._chat: _ChatSession | None = None

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

    async def start_chat(self, model: str) -> None:
        """Start or reset the chat session with the given model."""
        chat = self._client.start_chat(model=model)
        self._chat = _ChatSession(chat, model)
        logger.debug(f"Chat session started with model={model}")

    def has_chat(self) -> bool:
        return self._chat is not None

    async def chat(self, message: str, model: str) -> str:
        """Send a message in the active chat session."""
        if not self._chat:
            await self.start_chat(model)
        elif self._chat.model != model:
            await self.start_chat(model)

        resp = await self._chat.session.send_message(message)
        return resp.text

    async def chat_stream(self, message: str, model: str) -> AsyncIterator[str]:
        """Send a message with streaming in the active chat session."""
        if not self._chat:
            await self.start_chat(model)
        elif self._chat.model != model:
            await self.start_chat(model)

        session = self._chat.session
        async for chunk in session.send_message_stream(message):
            if chunk.text_delta:
                yield chunk.text_delta

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
