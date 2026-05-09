# ask-gemini

Call Gemini's web interface from the command line. Uses your browser's Gemini cookies to authenticate — no API key needed.

## When to use

Use this skill when the user needs to generate content via Gemini (free web interface) rather than other models. Good for:
- Getting a second opinion from Gemini on a topic
- Generating content that benefits from Gemini's specific capabilities
- Testing or comparing outputs across models

## Usage

### Single question (stateless)

Each call is independent — no context carried over between calls.

```bash
ask-gemini "your prompt here"
```

### Multi-turn conversation (stateful)

Use `--chat` to resume the latest web-side conversation. This shares the same conversation history as `gemini.google.com`.

```bash
# Pipe a sequence of messages to continue the conversation
printf "Question 1\nQuestion 2\nexit\n" | ask-gemini --chat -m gemini-3-flash
```

```bash
# Start a fresh conversation instead of resuming
ask-gemini --chat --new-chat <<< "Start of a new conversation"
```

### Named sessions (isolated conversations)

Use `--session <name>` to create or resume a named conversation. Each session is completely isolated — multiple agents using different session names will never interfere with each other.

```bash
# Create or resume a named session
ask-gemini --session code-review "Analyze this code: $(cat app.py)"

# Follow-up — same session, Gemini remembers context
ask-gemini --session code-review "Now rewrite it with better error handling"

# A different session, completely isolated
ask-gemini --session data-analysis "What is SQL?"
```

Sessions are persisted in `~/.ask-gemini/sessions.json` and map to real conversations on `gemini.google.com`.

```bash
# List all named sessions
ask-gemini --sessions

# Delete a session
ask-gemini --rm-session code-review
```

### Options

| Flag | Description |
|---|---|
| `-m, --model <name>` | Model to use: `gemini-3-pro` (default), `gemini-3-flash`, `gemini-3-flash-thinking` |
| `--no-stream` | Wait for full response instead of streaming |
| `--chat` | Resume the latest web-side conversation (stateful) |
| `--session <name>` | Use a named conversation session (isolated context) |
| `--sessions` | List all named sessions |
| `--rm-session <name>` | Delete a named session |
| `--new-chat` | Start a fresh conversation (use with `--chat`) |
| `--cookie-setup` | Show cookie setup instructions |

## Patterns for agents

### Pattern 1: Independent queries

```bash
ask-gemini "What is the difference between X and Y?"
```

Use for single, unrelated questions. No context preserved between calls.

### Pattern 2: Follow-up chain

When you need to build on a previous response (e.g., refine, debug, iterate):

```bash
# First exchange
ask-gemini --chat -m gemini-3-flash <<< "Analyze this code for bugs: $(cat file.py)"

# Follow-up — automatically resumes the same web conversation
ask-gemini --chat -m gemini-3-flash <<< "Now fix the issues you found and show the corrected code"
```

Each `--chat` call resumes the latest web-side conversation, so context is shared with the previous call.

### Pattern 3: Isolated agent sessions (recommended for multi-agent)

When multiple agents need independent conversations:

```bash
# Agent A: code review context
ask-gemini --session agent-a-review "Review this code..."
ask-gemini --session agent-a-review "Now suggest improvements..."

# Agent B: completely separate context
ask-gemini --session agent-b-creative "Write a documentation summary..."
```

Agent A and Agent B never share context — each `--session <name>` maintains its own isolated conversation history with Gemini.

### Pattern 4: New conversation boundary

When you want to isolate a topic from previous context:

```bash
ask-gemini --chat --new-chat <<< "Completely new topic: explain Docker networking"
```

### Pattern 5: Multi-turn in one call

```bash
printf "My name is Alex\nWhat's my name?\nexit\n" | ask-gemini --chat -m gemini-3-flash
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
