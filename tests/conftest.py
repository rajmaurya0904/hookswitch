"""Shared fixtures: a scratch project with a compact flag-style config."""

import json

import pytest

from hookswitch.cli import main

FLAG_TEXT = (
    "{\n"
    '  "servers": {\n'
    '    "github": {"enabled": true},\n'
    '    "postgres": {"enabled": true},\n'
    '    "puppeteer": {"enabled": false}\n'
    "  }\n"
    "}\n"
)

STASH_TEXT = (
    "{\n"
    '  "mcpServers": {\n'
    '    "github": {"command": "npx", "args": ["-y", "gh"]},\n'
    '    "postgres": {"command": "uvx", "args": ["pg"]}\n'
    "  }\n"
    "}\n"
)


@pytest.fixture
def project(tmp_path, monkeypatch):
    """A temp working directory containing mcp.json (flag layout)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("HOOKSWITCH_CONFIG", raising=False)
    monkeypatch.delenv("HOOKSWITCH_RECIPES", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)
    (tmp_path / "mcp.json").write_text(FLAG_TEXT, encoding="utf-8")
    return tmp_path


@pytest.fixture
def hs(capsys):
    """Run the CLI in-process and return (exit_code, stdout, stderr)."""

    def run(*argv):
        code = main(list(argv))
        out = capsys.readouterr()
        return code, out.out, out.err

    return run


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def enabled_map(path):
    return {n: v["enabled"] for n, v in read_json(path)["servers"].items()}
