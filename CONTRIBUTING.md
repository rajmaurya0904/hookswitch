# Contributing to hookswitch

## Setup

```bash
git clone https://github.com/rajmaurya0904/hookswitch.git
cd hookswitch
python -m venv .venv
.venv/bin/pip install -e ".[dev]"        # Windows: .venv\Scripts\pip
```

## Testing

```bash
pytest -q
ruff check .
```

Tests run the CLI in-process against a temporary directory, so they never touch
a real MCP config. Keep it that way: any new test that edits a file should work
inside `tmp_path`.

## Submitting changes

Open a pull request against `main` with a short description of what changed and
why. New behaviour needs a test; a bug fix needs a test that fails without it.
