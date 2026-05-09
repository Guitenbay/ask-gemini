# ask-gemini

[![CI](https://github.com/Guitenbay/ask-gemini/actions/workflows/ci.yml/badge.svg)](https://github.com/Guitenbay/ask-gemini/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![GitHub stars](https://img.shields.io/github/stars/Guitenbay/ask-gemini?style=social)](https://github.com/Guitenbay/ask-gemini)

CLI tool to chat with Gemini's web interface from the terminal. No API key needed — uses your browser cookies.

## Setup

### Option A: Standalone executable (recommended)

Build a single binary that runs without Python installed:

```bash
cd ask-gemini
pip install pyinstaller
bash build.sh
```

The executable is at `dist/ask-gemini` (~21MB). You can copy it anywhere and run it directly.

### Option B: Install as Python package

```bash
cd ask-gemini
pip install -e .
```

## Configure cookies

**Option A: Auto-detect from browser**

If you're logged into Gemini in Chrome or Edge, ask-gemini will auto-detect your cookies. Just run:

```bash
ask-gemini "Hello!"
```

**Option B: Manual setup**

```bash
ask-gemini --cookie-setup
```

Follow the instructions to copy `__Secure-1PSID` and `__Secure-1PSIDTS` from your browser, then save them in a `.env` file.

## Usage

### Single question

```bash
ask-gemini "What is Python?"
ask-gemini --model gemini-3-flash "Explain async/await"
ask-gemini --no-stream "Write a haiku about coding"
```

### Chat mode

Enter an interactive conversation that resumes your latest web-side chat:

```bash
ask-gemini --chat
```

This automatically picks up where you left off on [gemini.google.com](https://gemini.google.com).
Type your message, and Gemini responds. Useful commands while in chat:

| Command | Action |
|---|---|
| `exit` / `quit` | Leave chat mode |
| `new` | Start a fresh conversation |
| `clear` | Same as `new` |

To always start a fresh conversation instead of resuming:

```bash
ask-gemini --chat --new-chat
```

### Chat mode internals

- The same `cid` (conversation ID) is used as the web interface, so history is shared between CLI and browser
- Multiple CLI sessions in a row will keep using the same web conversation
- Switching models in an existing chat starts a new session on the web side

## Options

| Option | Description |
|---|---|
| `-m, --model` | Model to use (default: `gemini-3-pro`) |
| `-s, --stream` | Stream output as it arrives (default) |
| `--no-stream` | Wait for full response before printing |
| `--chat` | Enter interactive chat mode (resumes web conversation) |
| `--new-chat` | Start a fresh conversation instead of resuming |
| `--cookie-setup` | Print cookie setup instructions |
| `--version` | Print version |

## Available Models

| Model | Description |
|---|---|
| `gemini-3-pro` | Most capable (default) |
| `gemini-3-flash` | Fast |
| `gemini-3-flash-thinking` | Flash with chain-of-thought |

## Configuration

All configuration via environment variables in `.env` (project root or `~/.ask-gemini/.env`):

| Variable | Description | Default |
|---|---|---|
| `GEMINI_PSID` | `__Secure-1PSID` cookie | (auto-detect from browser) |
| `GEMINI_PSIDTS` | `__Secure-1PSIDTS` cookie | (auto-detect from browser) |
| `PROXY_URL` | HTTP proxy URL | (empty) |
| `MODEL` | Default model | `gemini-3-pro` |

## Notes

- Uses the free Gemini web interface, not the paid API.
- Cookies expire. If requests fail, refresh Gemini in your browser or update cookies manually.
- Automated access may violate Google's Terms of Service. Use at your own risk.
