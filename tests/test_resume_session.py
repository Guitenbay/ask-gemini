"""Unit tests for session resume with rid/rcid recovery."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from ask_gemini.client import GeminiClientWrapper


class MockModelOutput:
    def __init__(self, cid, rcid):
        self.metadata = [cid, f"rid_{cid}", rcid]
        self.rcid = rcid


class MockChatTurn:
    def __init__(self, role, model_output=None):
        self.role = role
        self.model_output = model_output


class MockChatHistory:
    def __init__(self, turns):
        self.turns = turns


class TestResumeChatRecoversRidRcid:
    def test_resume_chat_recovers_rid_rcid(self):
        """resume_chat should fetch history and populate rid/rcid."""
        chat = MagicMock()
        chat.read_history = AsyncMock(
            return_value=MockChatHistory(
                [
                    MockChatTurn("model", MockModelOutput("c_abc123", "rcid_xyz")),
                    MockChatTurn("user"),
                ]
            )
        )

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.start_chat.return_value = chat

        asyncio.run(wrapper.resume_chat("c_abc123", "gemini-3-pro"))

        chat.read_history.assert_called_once_with(limit=5)
        assert wrapper._chat is not None
        assert chat.metadata[0] == "c_abc123"
        assert chat.metadata[1] == "rid_c_abc123"
        assert chat.metadata[2] == "rcid_xyz"
        assert chat.rcid == "rcid_xyz"

    def test_resume_chat_handles_no_history(self):
        """resume_chat should work when read_history returns None."""
        chat = MagicMock()
        chat.read_history = AsyncMock(return_value=None)

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.start_chat.return_value = chat

        asyncio.run(wrapper.resume_chat("c_new", "gemini-3-pro"))

        chat.read_history.assert_called_once_with(limit=5)
        assert wrapper._chat is not None

    def test_resume_chat_handles_empty_turns(self):
        """resume_chat should work when history has no turns."""
        chat = MagicMock()
        chat.read_history = AsyncMock(return_value=MockChatHistory([]))

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.start_chat.return_value = chat

        asyncio.run(wrapper.resume_chat("c_empty", "gemini-3-pro"))

        chat.read_history.assert_called_once_with(limit=5)
        assert wrapper._chat is not None

    def test_resume_chat_skips_user_turns(self):
        """resume_chat should only extract metadata from model turns."""
        chat = MagicMock()
        chat.read_history = AsyncMock(
            return_value=MockChatHistory(
                [
                    MockChatTurn("user"),
                    MockChatTurn("user"),
                    MockChatTurn("model", MockModelOutput("c_useronly", "rcid_user")),
                ]
            )
        )

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.start_chat.return_value = chat

        asyncio.run(wrapper.resume_chat("c_useronly", "gemini-3-pro"))

        assert chat.rcid == "rcid_user"
        assert chat.metadata[2] == "rcid_user"

    def test_resume_latest_chat_recovers_rid_rcid(self):
        """resume_latest_chat should fetch history and populate rid/rcid."""
        mock_chat_info = MagicMock()
        mock_chat_info.cid = "c_latest"
        mock_chat_info.title = "Test Chat"

        chat = MagicMock()
        chat.read_history = AsyncMock(
            return_value=MockChatHistory(
                [
                    MockChatTurn("model", MockModelOutput("c_latest", "rcid_latest")),
                ]
            )
        )

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.list_chats.return_value = [mock_chat_info]
        wrapper._client.start_chat.return_value = chat

        result = asyncio.run(wrapper.resume_latest_chat("gemini-3-pro"))

        assert result is True
        chat.read_history.assert_called_once_with(limit=5)
        assert chat.rcid == "rcid_latest"

    def test_resume_latest_chat_no_chats(self):
        """resume_latest_chat should return False when no chats exist."""
        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.list_chats.return_value = []

        result = asyncio.run(wrapper.resume_latest_chat("gemini-3-pro"))

        assert result is False

    def test_resume_latest_chat_no_model_turns(self):
        """resume_latest_chat should handle case where no model turns exist."""
        mock_chat_info = MagicMock()
        mock_chat_info.cid = "c_nomodel"
        mock_chat_info.title = "Empty Chat"

        chat = MagicMock()
        chat.read_history = AsyncMock(
            return_value=MockChatHistory(
                [
                    MockChatTurn("user"),
                ]
            )
        )

        wrapper = GeminiClientWrapper(rate_limit=False)
        wrapper._client = MagicMock()
        wrapper._client.list_chats.return_value = [mock_chat_info]
        wrapper._client.start_chat.return_value = chat

        result = asyncio.run(wrapper.resume_latest_chat("gemini-3-pro"))

        assert result is True
        chat.read_history.assert_called_once_with(limit=5)
        # Should not crash, just no rid/rcid recovered
