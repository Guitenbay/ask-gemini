# ask-gemini

CLI tool to chat with Gemini's web interface from the terminal.

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

### 2. Configure cookies

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

### 3. Run

```bash
ask-gemini "What is Python?"
ask-gemini --model gemini-3-flash "Explain async/await"
ask-gemini --no-stream "Write a haiku about coding"
```

## Options

| Option | Description |
|---|---|
| `-m, --model` | Model to use (default: `gemini-3-pro`) |
| `-s, --stream` | Stream output as it arrives (default) |
| `--no-stream` | Wait for full response before printing |
| `--cookie-setup` | Print cookie setup instructions |
| `--version` | Print version |

## Available Models

| Model | Description |
|---|---|
| `gemini-3-pro` | Most capable (default) |
| `gemini-3-flash` | Fast |
| `gemini-3-flash-thinking` | Flash with chain-of-thought |

## Notes

- Uses the free Gemini web interface, not the paid API.
- Cookies expire. If requests fail, refresh Gemini in your browser or update cookies manually.
