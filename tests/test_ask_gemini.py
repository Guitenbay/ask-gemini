import json
import os
import subprocess
from pathlib import Path

import pytest

CLI = "ask-gemini"
SESSIONS_FILE = Path.home() / ".ask-gemini" / "sessions.json"

TEST_SESSION_PREFIX = "_test_"

pytestmark = pytest.mark.integration


def _run(*args, timeout: int = 120) -> subprocess.CompletedProcess:
    """Run the ask-gemini CLI and return the result."""
    env = os.environ.copy()
    return subprocess.run(
        [CLI, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )


def _load_sessions() -> dict:
    if SESSIONS_FILE.exists():
        try:
            return json.loads(SESSIONS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _clean_test_sessions():
    """Remove all test-prefixed sessions from disk."""
    sessions = _load_sessions()
    to_remove = [k for k in sessions if k.startswith(TEST_SESSION_PREFIX)]
    for name in to_remove:
        del sessions[name]
    if to_remove:
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSIONS_FILE.write_text(json.dumps(sessions, indent=2) + "\n")


@pytest.fixture(autouse=True)
def cleanup():
    """Clean up test sessions after each test."""
    yield
    _clean_test_sessions()


# --- Single question tests ---


def test_single_question():
    """Basic single question should return a response."""
    result = _run("What is 1+1? Please answer with just the number.")
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "2" in result.stdout


def test_single_question_model_flag():
    """Specifying a model should work."""
    result = _run("-m", "gemini-3-flash", "What color is the sky on a clear day?")
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert result.stdout  # non-empty response


def test_single_question_no_stream():
    """Non-streaming mode should return a complete response."""
    result = _run("--no-stream", "Say 'hello world' and nothing else.")
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "hello" in result.stdout.lower() or "world" in result.stdout.lower()


# --- Named session tests ---


def test_named_session_create():
    """Creating a named session should work."""
    session = f"{TEST_SESSION_PREFIX}create-test"
    result = _run("--session", session, "Say 'session created' and stop.")
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    assert "created" in result.stdout.lower()


def test_named_session_context_memory():
    """Named session should preserve context across calls."""
    session = f"{TEST_SESSION_PREFIX}memory-test"

    # First call: establish context
    result1 = _run("--session", session, "My secret word is BLOOM. Remember it.")
    assert result1.returncode == 0, f"First call failed: {result1.stderr}"

    # Second call: ask about the context
    result2 = _run("--session", session, "What was my secret word?")
    assert result2.returncode == 0, f"Second call failed: {result2.stderr}"
    assert "bloom" in result2.stdout.lower(), (
        f"Context not remembered. Response: {result2.stdout}"
    )


def test_named_session_isolation():
    """Two named sessions should have independent contexts."""
    session_a = f"{TEST_SESSION_PREFIX}isolation-a"
    session_b = f"{TEST_SESSION_PREFIX}isolation-b"

    # Set different contexts
    _run("--session", session_a, "My color is RED. Remember it.")
    _run("--session", session_b, "My color is BLUE. Remember it.")

    # Ask each session — they should give different answers
    result_a = _run("--session", session_a, "What color did I say?")
    result_b = _run("--session", session_b, "What color did I say?")

    assert "red" in result_a.stdout.lower(), (
        f"Session A lost context. Response: {result_a.stdout}"
    )
    assert "blue" in result_b.stdout.lower(), (
        f"Session B lost context. Response: {result_b.stdout}"
    )


# --- Session management tests ---


def test_list_sessions_empty():
    """Listing sessions when none exist should show empty message."""
    _clean_test_sessions()
    result = _run("--sessions")
    assert result.returncode == 0
    assert "no named" in result.stdout.lower() or not result.stdout.strip()


def test_list_sessions_has_entry():
    """Listing sessions should show saved sessions."""
    session = f"{TEST_SESSION_PREFIX}list-test"
    _run("--session", session, "Hi")
    result = _run("--sessions")
    assert result.returncode == 0
    assert session in result.stdout


def test_delete_session():
    """Deleting a session should remove it."""
    session = f"{TEST_SESSION_PREFIX}delete-test"
    _run("--session", session, "Hi")

    # Should exist
    list_result = _run("--sessions")
    assert session in list_result.stdout

    # Delete it
    result = _run("--rm-session", session)
    assert result.returncode == 0
    assert "deleted" in result.stdout.lower()

    # Should be gone
    list_result = _run("--sessions")
    assert session not in list_result.stdout


def test_delete_nonexistent_session():
    """Deleting a session that doesn't exist should show error."""
    result = _run("--rm-session", f"{TEST_SESSION_PREFIX}does-not-exist-xyz")
    assert "not found" in result.stdout.lower()


# --- Chat mode internals test ---


def test_chat_mode_stdin():
    """Chat mode should work with piped stdin."""
    result = _run(
        "--chat", "-m", "gemini-3-flash",
        input="I am a test user. Type 'exit'.\nexit\n",
    )
    assert result.returncode == 0, f"Chat mode failed: {result.stderr}"
    assert "gemini>" in result.stdout.lower() or "test user" in result.stdout.lower()


# --- Help and version ---


def test_help():
    """Help should list all options."""
    result = _run("--help")
    assert result.returncode == 0
    assert "--session" in result.stdout
    assert "--chat" in result.stdout
    assert "--no-rate-limit" in result.stdout


def test_version():
    """Version flag should work."""
    result = _run("--version")
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


# --- Cookie setup ---


def test_cookie_setup():
    """Cookie setup instructions should print."""
    result = _run("--cookie-setup")
    assert result.returncode == 0
    assert "__Secure-1PSID" in result.stdout
