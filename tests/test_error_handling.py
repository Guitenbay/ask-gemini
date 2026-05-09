"""Unit tests for error handling — no network required."""

import pytest

from ask_gemini.client import (
    GeminiNetworkError,
    ProxyConfig,
    _is_network_error,
)


class TestIsNetworkError:
    @pytest.mark.parametrize(
        "err_text",
        [
            "curl_cffi.curl.CurlError: Connection reset by peer",
            "Recv failure: Connection reset",
            "ssl.SSLError: certificate verify failed",
            "broken pipe",
            "timed out after 30 seconds",
            "CURL (35) RECV FAILURE",
        ],
    )
    def test_detects_network(self, err_text):
        assert _is_network_error(Exception(err_text)) is True

    @pytest.mark.parametrize(
        "err_text",
        [
            "Gemini cookies not configured",
            "Unknown model: gemini-4-ultra",
            "Session not found",
            "KeyError: 'text_delta'",
            "403 Forbidden",
        ],
    )
    def test_non_network_errors(self, err_text):
        assert _is_network_error(Exception(err_text)) is False


class TestGeminiNetworkError:
    def test_user_message_includes_proxy_hint_when_unset(self):
        # Save and restore
        original = ProxyConfig.url
        try:
            ProxyConfig.url = ""
            err = GeminiNetworkError(Exception("connection reset"))
            msg = err.user_message()
            assert "Connection to Gemini failed" in msg
            assert "PROXY_URL is not configured" in msg
            assert "message may be too large" in msg
        finally:
            ProxyConfig.url = original

    def test_user_message_shows_proxy_when_set(self):
        original = ProxyConfig.url
        try:
            ProxyConfig.url = "http://127.0.0.1:7890"
            err = GeminiNetworkError(Exception("connection reset"))
            msg = err.user_message()
            assert "PROXY_URL is set to: http://127.0.0.1:7890" in msg
            assert "proxy is running" in msg
        finally:
            ProxyConfig.url = original

    def test_context_is_included(self):
        err = GeminiNetworkError(
            Exception("ssl error"),
            context="Session cid=abc123 may be out of sync.",
        )
        msg = err.user_message()
        assert "abc123" in msg
        assert "out of sync" in msg
