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
@click.option("--cookie-setup", is_flag=True, help="Print cookie setup instructions")
@click.version_option(version="0.1.0")
def main(prompt, model, stream, no_stream, cookie_setup):
    """Ask Gemini from the terminal."""
    if cookie_setup:
        print(GeminiCookies.setup_instructions())
        return

    if not prompt:
        click.echo("Usage: ask-gemini <your question>")
        click.echo("Run `ask-gemini --help` for options.")
        return

    if no_stream:
        stream = False

    model = model or "gemini-3-pro"
    if model not in AVAILABLE_MODELS:
        click.echo(f"Unknown model: {model}")
        click.echo(f"Available models: {', '.join(AVAILABLE_MODELS)}")
        raise SystemExit(1)

    # Try loading cookies from browser first
    GeminiCookies.try_load_from_browser()

    if not GeminiCookies.is_configured():
        click.echo("Error: Gemini cookies not found.\n")
        click.echo(GeminiCookies.setup_instructions(), err=True)
        raise SystemExit(1)

    client = GeminiClientWrapper()
    asyncio.run(_run(client, prompt, model, stream))


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


if __name__ == "__main__":
    main()
