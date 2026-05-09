import asyncio
import sys

import click
from loguru import logger

from ask_gemini.client import GeminiClientWrapper, _load_sessions, _save_sessions
from ask_gemini.config import GeminiCookies, RateLimitConfig

logger.remove()
logger.add(sys.stderr, level="WARNING", format="<level>{message}</level>")

AVAILABLE_MODELS = [
    "gemini-3-pro",
    "gemini-3-flash",
    "gemini-3-flash-thinking",
]

DEFAULT_MODEL = "gemini-3-pro"


@click.command()
@click.argument("prompt", required=False)
@click.option(
    "-m",
    "--model",
    default=None,
    help=f"Model to use. Options: {', '.join(AVAILABLE_MODELS)}",
)
@click.option(
    "-s",
    "--stream",
    is_flag=True,
    default=True,
    help="Stream output as it arrives (default)",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Wait for full response before printing",
)
@click.option(
    "--chat",
    is_flag=True,
    default=False,
    help="Enter interactive chat mode (resumes your latest web conversation)",
)
@click.option(
    "--session",
    "session_name",
    default=None,
    help="Use a named conversation session (creates one if it doesn't exist)",
)
@click.option(
    "--sessions",
    is_flag=True,
    default=False,
    help="List all named sessions",
)
@click.option(
    "--rm-session",
    default=None,
    help="Delete a named session",
)
@click.option(
    "--new-chat",
    is_flag=True,
    default=False,
    help="Start a fresh conversation instead of resuming the latest web chat",
)
@click.option(
    "--no-rate-limit",
    is_flag=True,
    default=False,
    help="Disable human-like typing/cooldown delays",
)
@click.option("--cookie-setup", is_flag=True, help="Print cookie setup instructions")
@click.version_option(version="0.1.0")
def main(
    prompt,
    model,
    stream,
    no_stream,
    chat,
    session_name,
    sessions,
    rm_session,
    new_chat,
    no_rate_limit,
    cookie_setup,
):
    """Ask Gemini from the terminal."""
    if cookie_setup:
        print(GeminiCookies.setup_instructions())
        return

    if sessions:
        _list_sessions()
        return

    if rm_session:
        asyncio.run(_remove_session(rm_session))
        return

    # Read prompt from stdin if not provided and input is piped
    if prompt is None and not sys.stdin.isatty():
        prompt = sys.stdin.read().strip()

    if no_stream:
        stream = False

    model = model or "gemini-3-pro"
    if model not in AVAILABLE_MODELS:
        click.echo(f"Unknown model: {model}")
        click.echo(f"Available models: {', '.join(AVAILABLE_MODELS)}")
        raise SystemExit(1)

    GeminiCookies.try_load_from_browser()

    if not GeminiCookies.is_configured():
        click.echo("Error: Gemini cookies not found.\n")
        click.echo(GeminiCookies.setup_instructions(), err=True)
        raise SystemExit(1)

    rate_limit = not no_rate_limit
    client = GeminiClientWrapper(rate_limit=rate_limit)

    if rate_limit:
        logger.info(
            f"Rate limit enabled: typing={RateLimitConfig.typing_speed}s/char, "
            f"min={RateLimitConfig.min_delay}s, max={RateLimitConfig.max_delay}s, "
            f"cooldown={RateLimitConfig.cooldown}s"
        )

    if session_name:
        asyncio.run(_run_session(client, session_name, prompt, model, stream))
    elif chat:
        asyncio.run(_run_chat(client, model, stream, new_chat=new_chat))
    elif prompt:
        asyncio.run(_run(client, prompt, model, stream))
    else:
        click.echo("Usage: ask-gemini <your question>")
        click.echo("  ask-gemini --chat              Interactive chat mode")
        click.echo("  ask-gemini --session <name>    Use a named session")
        click.echo("  ask-gemini --sessions          List saved sessions")
        click.echo("  ask-gemini --help              Show all options")
        raise SystemExit(0)


def _list_sessions():
    """List all named sessions."""
    sessions = _load_sessions()
    if not sessions:
        click.echo("No named sessions.")
        return
    for name, cid in sessions.items():
        click.echo(f"  {name:20s}  cid: {cid}")


async def _remove_session(name: str):
    """Delete a named session locally and from Gemini web."""
    sessions = _load_sessions()
    if name not in sessions:
        click.echo(f"Session '{name}' not found.")
        return

    cid = sessions[name]
    del sessions[name]
    _save_sessions(sessions)

    # Also delete the conversation from Gemini web
    GeminiCookies.try_load_from_browser()
    client = GeminiClientWrapper(rate_limit=False)
    try:
        await client.init()
        await client.delete_chat(cid)
        click.echo(f"Deleted session '{name}' from disk and Gemini web.")
    except Exception as e:
        click.echo(
            f"Deleted local session '{name}', but failed to delete from Gemini web: {e}",
            err=True,
        )


async def _run(client, prompt, model, stream):
    try:
        await client.init()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    if stream:
        first = True
        async for chunk in client.ask_stream(prompt, model):
            if first:
                first = False
            click.echo(chunk, nl=False)
        click.echo()
    else:
        resp = await client.ask(prompt, model)
        click.echo(resp)


async def _run_session(client, name, prompt, model, stream):
    """Named session: auto-create or resume, then send one message."""
    try:
        await client.init()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    existed = await client.resume_named_session(name, model)
    if existed:
        logger.info(f"Using existing session '{name}'")
    else:
        logger.info(f"Created new session '{name}'")

    if stream:
        first = True
        async for chunk in client.chat_stream(prompt, model):
            if first:
                first = False
            click.echo(chunk, nl=False)
        click.echo()
    else:
        resp = await client.chat(prompt, model)
        click.echo(resp)

    # Update the stored cid after the conversation was created
    if client._chat and client._chat.session.cid:
        sessions = _load_sessions()
        sessions[name] = client._chat.session.cid
        _save_sessions(sessions)


async def _run_chat(client, model, stream, new_chat=False):
    try:
        await client.init()
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1) from e

    if new_chat:
        await client.start_chat(model)
        click.echo(
            f"Chat mode (model: {model}). Type 'exit' or 'quit' to leave, 'clear' to reset history.\n"
        )
    else:
        resumed = await client.resume_latest_chat(model)
        if resumed:
            click.echo(
                f"Chat mode (model: {model}). Resuming web conversation. "
                f"Type 'exit' to leave, 'clear' for new chat, 'new' to start fresh.\n"
            )
        else:
            click.echo(
                f"Chat mode (model: {model}). No existing web conversations found, "
                f"starting fresh. Type 'exit' to leave.\n"
            )

    try:
        import readline  # noqa: F401 — enables line editing/history on macOS/Linux
    except ImportError:
        pass

    while True:
        try:
            text = input("You> ")
        except EOFError:
            click.echo()
            break

        text = text.strip()
        if not text:
            continue
        if text.lower() in ("exit", "quit"):
            break
        if text.lower() == "clear":
            await client.start_chat(model)
            click.echo("Started a new conversation.\n")
            continue
        if text.lower() == "new" and not new_chat:
            await client.start_chat(model)
            new_chat = True
            click.echo("Started a new conversation.\n")
            continue

        click.echo("Gemini> ", nl=False)

        if stream:
            first = True
            async for chunk in client.chat_stream(text, model):
                if first:
                    first = False
                click.echo(chunk, nl=False)
            click.echo("\n")
        else:
            resp = await client.chat(text, model)
            click.echo(f"{resp}\n")


if __name__ == "__main__":
    main()
