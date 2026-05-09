# ask-gemini

Call Gemini's web interface from the command line. Uses your browser's Gemini cookies to authenticate — no API key needed.

## When to use

Use this skill when the user needs to generate content via Gemini (free web interface) rather than other models. Good for:
- Getting a second opinion from Gemini on a topic
- Generating content that benefits from Gemini's specific capabilities
- Testing or comparing outputs across models

## Usage

```bash
ask-gemini "your prompt here"
```

### Options

| Flag | Description |
|---|---|
| `-m, --model <name>` | Model to use: `gemini-3-pro` (default), `gemini-3-flash`, `gemini-3-flash-thinking` |
| `--no-stream` | Wait for full response instead of streaming |
| `--cookie-setup` | Show cookie setup instructions |

### Examples

```bash
# Simple question
ask-gemini "What are the tradeoffs between REST and GraphQL?"

# Different model
ask-gemini -m gemini-3-flash "Summarize this code: $(cat file.py)"

# Non-streaming (wait for complete response)
ask-gemini --no-stream "Write a short bash script that..."

# Long prompt from stdin
cat prompt.txt | ask-gemini "$(cat)"
```

## Setup requirements

Before using, ensure:
1. The user is logged into Gemini in Chrome or Edge (cookies auto-detected)
2. Or a `.env` file exists with `GEMINI_PSID` and `GEMINI_PSIDTS`
3. Proxy is configured if needed (`PROXY_URL` in `.env`)

If cookies are not found, run `ask-gemini --cookie-setup` and follow instructions.

## Output

- **Streaming mode (default)**: Response prints word-by-word as it arrives
- **Non-streaming**: Response prints all at once after completion
- Exit code 0 on success, 1 on error (with error message on stderr)
