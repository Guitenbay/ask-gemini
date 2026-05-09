import os
from pathlib import Path

import browser_cookie3
from dotenv import load_dotenv
from loguru import logger

# Load .env from project dir or ~/.ask-gemini/
_env_paths = [
    Path(__file__).parent.parent / ".env",
    Path.home() / ".ask-gemini" / ".env",
]
for _p in _env_paths:
    if _p.exists():
        load_dotenv(_p)
        break


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


class GeminiCookies:
    PSID: str = _get("GEMINI_PSID")
    PSIDTS: str = _get("GEMINI_PSIDTS")

    @classmethod
    def try_load_from_browser(cls) -> bool:
        """Auto-detect cookies from Chrome/Edge/Firefox on macOS."""
        try:
            cj = browser_cookie3.chrome(domain_name=".google.com")
        except Exception:
            cj = None

        if cj:
            psid = psidts = ""
            for c in cj:
                if c.name == "__Secure-1PSID":
                    psid = c.value
                elif c.name == "__Secure-1PSIDTS":
                    psidts = c.value
            if psid and psidts:
                cls.PSID = psid
                cls.PSIDTS = psidts
                logger.debug("Loaded cookies from browser")
                return True

        # Fallback to .env
        return cls.is_configured()

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.PSID and cls.PSIDTS)

    @classmethod
    def setup_instructions(cls) -> str:
        return """\
Gemini cookies not found. To set them up:

1. Open Chrome/Edge and go to https://gemini.google.com (make sure you're logged in)
2. Open DevTools (F12 or Cmd+Option+I on Mac)
3. Go to Application tab → Cookies → https://gemini.google.com
4. Copy the value of __Secure-1PSID and __Secure-1PSIDTS
5. Create a .env file in ~/.ask-gemini/ or this project's root:

   GEMINI_PSID=<paste __Secure-1PSID value>
   GEMINI_PSIDTS=<paste __Secure-1PSIDTS value>

Alternatively, ask-gemini can auto-detect cookies from your browser.
Make sure you're logged into Gemini in Chrome or Edge.
"""


class ProxyConfig:
    url: str = _get("PROXY_URL")
