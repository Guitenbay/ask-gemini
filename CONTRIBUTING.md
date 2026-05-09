# Contributing to ask-gemini

Thanks for your interest in contributing! Here are a few guidelines to help get you started.

## Development setup

```bash
git clone https://github.com/Guitenbay/ask-gemini.git
cd ask-gemini
pip install -e .
pip install ruff pyinstaller  # for linting and building executables
```

## Code style

This project uses [ruff](https://github.com/astral-sh/ruff) for linting and formatting.
All code passes CI checks — make sure your changes pass before opening a PR:

```bash
ruff check ask_gemini/
ruff format ask_gemini/
```

## Running locally

You need Gemini cookies configured. Either:
- Be logged into Gemini in Chrome/Edge (auto-detected)
- Or set `GEMINI_PSID` and `GEMINI_PSIDTS` in `.env`

```bash
ask-gemini "Hello from dev mode!"
```

## Pull requests

- Keep PRs focused — one change per PR
- Follow the existing code style
- Update README.md if your change adds or modifies user-facing behavior
- No need to bump version numbers — maintainers handle releases

## Adding new providers or models

The provider architecture in `ask_gemini/client.py` is designed to be extensible.
If you're adding support for a new model variant, simply add it to the
`AVAILABLE_MODELS` list in `ask_gemini/main.py`.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
