import asyncio
import sys

import click
from loguru import logger

from ask_gemini.client import GeminiClientWrapper
from ask_gemini.config import GeminiCookies

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
    "--new-chat",
    is_flag=True,
    default=False,
    help="Start a fresh conversation instead of resuming the latest web chat",
)
@click.option("--cookie-setup", is_flag=True, help="Print cookie setup instructions")
@click.version_option(version="0.1.0")
def main(prompt, model, stream, no_stream, chat, new_chat, cookie_setup):
    """Ask Gemini from the terminal."""
    if cookie_setup:
        print(GeminiCookies.setup_instructions())
        return

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

    client = GeminiClientWrapper()

    if chat:
        asyncio.run(_run_chat(client, model, stream, new_chat=new_chat))
    elif prompt:
        asyncio.run(_run(client, prompt, model, stream))
    else:
        click.echo("Usage: ask-gemini <your question>")
        click.echo("  ask-gemini --chat          Interactive chat mode")
        click.echo("  ask-gemini --help           Show all options")
        raise SystemExit(0)


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
                f"Chat mode (model: {model}). Resuming web conversation. Type 'exit' to leave, 'clear' for new chat, 'new' to start fresh.\n"
            )
        else:
            click.echo(
                f"Chat mode (model: {model}). No existing web conversations found, starting fresh. Type 'exit' to leave.\n"
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
