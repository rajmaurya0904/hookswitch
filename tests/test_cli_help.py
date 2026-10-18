"""The command is installed, runs, and documents itself."""

import subprocess
import sys
from pathlib import Path

import pytest

import hookswitch


def run_module(*args):
    return subprocess.run(
        [sys.executable, "-m", "hookswitch", *args], capture_output=True, text=True, timeout=60
    )


def test_python_dash_m_help_lists_subcommands():
    proc = run_module("--help")
    assert proc.returncode == 0
    for word in ("list", "status", "toggle", "enable", "disable", "run", "recipes", "undo"):
        assert word in proc.stdout


def test_no_arguments_prints_help_and_exits_zero():
    proc = run_module()
    assert proc.returncode == 0
    assert "usage: hookswitch" in proc.stdout


def test_version_flag():
    proc = run_module("--version")
    assert proc.returncode == 0
    assert proc.stdout.strip() == f"hookswitch {hookswitch.__version__}"


def test_unknown_command_is_usage_error():
    proc = run_module("frobnicate")
    assert proc.returncode == 2
    assert "invalid choice" in proc.stderr


def test_subcommand_help_mentions_its_options():
    proc = run_module("toggle", "--help")
    assert proc.returncode == 0
    assert "--on" in proc.stdout and "--dry-run" in proc.stdout and "--color" in proc.stdout


def test_missing_required_argument_is_usage_error():
    assert run_module("toggle").returncode == 2


def test_console_script_is_installed():
    scripts = Path(sys.executable).parent
    candidates = [scripts / "hookswitch", scripts / "hookswitch.exe"]
    exe = next((c for c in candidates if c.exists()), None)
    if exe is None:
        pytest.skip("console script not found next to the interpreter (not an installed env)")
    proc = subprocess.run([str(exe), "--help"], capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0
    assert "Switch MCP servers" in proc.stdout
