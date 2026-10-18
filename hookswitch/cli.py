"""Command line interface: ``hookswitch list|status|toggle|enable|disable|run|...``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .backup import DEFAULT_KEEP, backup_file, list_backups, restore_latest
from .config import ConfigError, ensure_config, load_config, render_config, write_text_atomic
from .diff import colorize, get_diff
from .formats import FORMATS, detect_format, has_server, list_servers, set_enabled
from .recipes import RecipeError, find_recipe, load_recipe_file, recipe_files

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_OFF = 3  # `check`: at least one named server is disabled

CONFIG_CANDIDATES = (".mcp.json", "mcp.json", "hookswitch.json")
DEFAULT_NEW_CONFIG = "hookswitch.json"
COLOR_CHOICES = ("auto", "always", "never")


class CliError(Exception):
    """A problem to report on stderr with exit status 1."""


# ---------------------------------------------------------------- helpers


def resolve_config_path(arg: str | None) -> tuple[Path, bool]:
    """Pick the config file. Returns ``(path, explicit)``.

    Order: ``--config``, ``$HOOKSWITCH_CONFIG``, the first of ``.mcp.json``,
    ``mcp.json``, ``hookswitch.json`` that exists in the current directory, and
    finally ``hookswitch.json`` (which is created on first use).
    """
    if arg:
        return Path(arg), True
    env = os.environ.get("HOOKSWITCH_CONFIG")
    if env:
        return Path(env), True
    for name in CONFIG_CANDIDATES:
        if Path(name).is_file():
            return Path(name), False
    return Path(DEFAULT_NEW_CONFIG), False


def recipe_dirs(arg: str | None) -> list[Path]:
    if arg:
        return [Path(arg)]
    env = os.environ.get("HOOKSWITCH_RECIPES")
    if env:
        return [Path(env)]
    return [Path(".hookswitch") / "recipes", Path.home() / ".config" / "hookswitch" / "recipes"]


def read_config(args: argparse.Namespace) -> tuple[Path, dict, str]:
    """Load the config named by the arguments, creating a default one when allowed."""
    path, explicit = resolve_config_path(args.config)
    if not path.exists():
        if explicit:
            raise CliError(f"config file not found: {path}")
        ensure_config(path)
        print(f"hookswitch: {path} did not exist; created an empty one", file=sys.stderr)
    config = load_config(path)
    text = path.read_text(encoding="utf-8")
    return path, config, text


def wants_color(mode: str) -> bool:
    if mode == "always":
        return True
    if mode == "never" or os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


def show_diff(old: str, new: str, path: Path, args: argparse.Namespace) -> None:
    diff = get_diff(old, new, fromfile=f"{path} (before)", tofile=f"{path} (after)")
    if wants_color(args.color):
        diff = colorize(diff)
    sys.stdout.write(diff)


def apply_changes(
    args: argparse.Namespace,
    path: Path,
    config: dict,
    old_text: str,
    wanted: list[tuple[str, bool]],
    skip_missing: bool = False,
) -> int:
    """Apply ``(server, enabled)`` toggles to the file at *path*: back up, write, show diff."""
    fmt = args.format
    missing = [name for name, _ in wanted if not has_server(config, name, fmt)]
    if missing and not skip_missing:
        known = ", ".join(name for name, _ in list_servers(config, fmt)) or "(none)"
        raise CliError(f"unknown server(s): {', '.join(missing)}; the config has: {known}")
    for name in missing:
        print(f"hookswitch: skipping {name}: not in {path}", file=sys.stderr)

    current = dict(list_servers(config, fmt))
    new_config = config
    changed: list[tuple[str, bool]] = []
    for name, enabled in wanted:
        if name in missing:
            continue
        new_config = set_enabled(new_config, name, enabled, fmt)
        if current.get(name) != enabled:
            changed.append((name, enabled))

    if new_config == config:
        if not args.quiet:
            print("no changes: everything is already in the requested state")
        return EXIT_OK

    new_text = render_config(new_config, old_text)
    if not args.quiet:
        for name, enabled in changed:
            print(f"{'enable' if enabled else 'disable'} {name}")
        show_diff(old_text, new_text, path, args)
    if args.dry_run:
        if not args.quiet:
            print("dry run: nothing written")
        return EXIT_OK

    backup = backup_file(path, keep=args.keep)
    write_text_atomic(new_text, path)
    if not args.quiet:
        print(f"backup: {backup.name}")
    return EXIT_OK


# ---------------------------------------------------------------- commands


def cmd_list(args: argparse.Namespace) -> int:
    path, config, _ = read_config(args)
    servers = list_servers(config, args.format)
    if args.json:
        payload = {
            "config": str(path),
            "format": args.format if args.format != "auto" else detect_format(config),
            "servers": [{"name": n, "enabled": e} for n, e in servers],
        }
        print(json.dumps(payload, indent=2))
        return EXIT_OK
    if not servers:
        print(f"no servers in {path}")
        return EXIT_OK
    width = max(len("NAME"), *(len(n) for n, _ in servers))
    print(f"{'NAME'.ljust(width)}  STATE")
    for name, enabled in servers:
        print(f"{name.ljust(width)}  {'on' if enabled else 'off'}")
    on = sum(1 for _, e in servers if e)
    print(f"\n{on} of {len(servers)} enabled ({path})")
    return EXIT_OK


def cmd_status(args: argparse.Namespace) -> int:
    _, config, _ = read_config(args)
    for name, enabled in list_servers(config, args.format):
        if enabled:
            print(name)
    return EXIT_OK


def cmd_check(args: argparse.Namespace) -> int:
    _, config, _ = read_config(args)
    state = dict(list_servers(config, args.format))
    unknown = [n for n in args.names if n not in state]
    if unknown:
        raise CliError(f"unknown server(s): {', '.join(unknown)}")
    off = [n for n in args.names if not state[n]]
    if off and not args.quiet:
        print(f"disabled: {', '.join(off)}", file=sys.stderr)
    return EXIT_OFF if off else EXIT_OK


def cmd_toggle(args: argparse.Namespace) -> int:
    path, config, text = read_config(args)
    state = dict(list_servers(config, args.format))
    wanted: list[tuple[str, bool]] = []
    for name in args.names:
        if args.on:
            wanted.append((name, True))
        elif args.off:
            wanted.append((name, False))
        else:
            # An unknown name is reported by apply_changes; the value here is irrelevant.
            wanted.append((name, not state.get(name, False)))
    return apply_changes(args, path, config, text, wanted)


def cmd_enable(args: argparse.Namespace) -> int:
    path, config, text = read_config(args)
    return apply_changes(args, path, config, text, [(n, True) for n in args.names])


def cmd_disable(args: argparse.Namespace) -> int:
    path, config, text = read_config(args)
    return apply_changes(args, path, config, text, [(n, False) for n in args.names])


def cmd_run(args: argparse.Namespace) -> int:
    recipe = find_recipe(args.recipe, recipe_dirs(args.recipes_dir))
    path, config, text = read_config(args)
    if not recipe.toggles:
        raise CliError(f"recipe {recipe.name!r} does not toggle any servers")
    return apply_changes(args, path, config, text, recipe.toggles, skip_missing=args.skip_missing)


def cmd_recipes(args: argparse.Namespace) -> int:
    found = 0
    for directory in recipe_dirs(args.recipes_dir):
        for file in recipe_files(directory):
            found += 1
            try:
                recipe = load_recipe_file(file)
            except RecipeError as exc:
                print(f"{file.stem}  [invalid] {exc}")
                continue
            on = [n for n, e in recipe.toggles if e]
            off = [n for n, e in recipe.toggles if not e]
            parts = []
            if on:
                parts.append("on: " + ", ".join(on))
            if off:
                parts.append("off: " + ", ".join(off))
            summary = "; ".join(parts) or "(empty)"
            note = f"  {recipe.description}" if recipe.description else ""
            print(f"{recipe.name}  {summary}{note}  [{file}]")
    if not found:
        dirs = ", ".join(str(d) for d in recipe_dirs(args.recipes_dir))
        print(f"no recipes found in {dirs}")
    return EXIT_OK


def cmd_backups(args: argparse.Namespace) -> int:
    path, _ = resolve_config_path(args.config)
    backups = list_backups(path)
    if not backups:
        print(f"no backups of {path}")
    for b in backups:
        print(b.name)
    return EXIT_OK


def cmd_undo(args: argparse.Namespace) -> int:
    path, _ = resolve_config_path(args.config)
    if not path.exists():
        raise CliError(f"config file not found: {path}")
    before = path.read_text(encoding="utf-8")
    try:
        used = restore_latest(path)
    except FileNotFoundError as exc:
        raise CliError(str(exc)) from exc
    after = path.read_text(encoding="utf-8")
    if not args.quiet:
        print(f"restored {path} from {used.name}")
        show_diff(before, after, path, args)
    return EXIT_OK


# ---------------------------------------------------------------- parser


def _add_color(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--color",
        nargs="?",
        const="always",
        default="auto",
        choices=COLOR_CHOICES,
        help="colour the diff (bare --color means always; default auto)",
    )


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        help=f"config file (default: $HOOKSWITCH_CONFIG, else the first of "
        f"{', '.join(CONFIG_CANDIDATES)} that exists)",
    )
    common.add_argument(
        "--format",
        choices=("auto", *FORMATS),
        default="auto",
        help="config layout (default: detect from the file)",
    )
    common.add_argument("-q", "--quiet", action="store_true", help="print nothing on success")

    edit = argparse.ArgumentParser(add_help=False)
    edit.add_argument(
        "-n", "--dry-run", action="store_true", help="show the diff but write nothing"
    )
    edit.add_argument(
        "--keep",
        type=int,
        default=DEFAULT_KEEP,
        metavar="N",
        help=f"backups to keep next to the file (default {DEFAULT_KEEP})",
    )
    _add_color(edit)

    parser = argparse.ArgumentParser(
        prog="hookswitch",
        description="Switch MCP servers on and off in a config file, with a backup and a diff.",
        epilog="exit status: 0 ok, 1 error, 2 bad usage, 3 `check` found a disabled server",
    )
    parser.add_argument("-V", "--version", action="version", version=f"hookswitch {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("list", parents=[common], help="show every server and whether it is on")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("status", parents=[common], help="print the enabled servers, one per line")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser(
        "check", parents=[common], help="exit 0 if all named servers are on, 3 if any is off"
    )
    p.add_argument("names", nargs="+", metavar="NAME")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser(
        "toggle", parents=[common, edit], help="flip servers (or force them with --on / --off)"
    )
    p.add_argument("names", nargs="+", metavar="NAME")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--on", action="store_true", help="switch the servers on")
    group.add_argument("--off", action="store_true", help="switch the servers off")
    p.set_defaults(func=cmd_toggle)

    p = sub.add_parser("enable", parents=[common, edit], help="switch servers on")
    p.add_argument("names", nargs="+", metavar="NAME")
    p.set_defaults(func=cmd_enable)

    p = sub.add_parser("disable", parents=[common, edit], help="switch servers off")
    p.add_argument("names", nargs="+", metavar="NAME")
    p.set_defaults(func=cmd_disable)

    p = sub.add_parser("run", parents=[common, edit], help="apply a recipe of toggles in one edit")
    p.add_argument("recipe", metavar="RECIPE", help="recipe name or path to a recipe file")
    p.add_argument(
        "--recipes-dir",
        metavar="DIR",
        help="where recipes live (default: .hookswitch/recipes, then ~/.config/hookswitch/recipes)",
    )
    p.add_argument(
        "--skip-missing",
        action="store_true",
        help="ignore recipe servers that are not in the config",
    )
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("recipes", help="list the available recipes")
    p.add_argument("--recipes-dir", metavar="DIR")
    p.set_defaults(func=cmd_recipes)

    p = sub.add_parser("backups", help="list the backups next to the config")
    p.add_argument("-c", "--config", metavar="FILE")
    p.set_defaults(func=cmd_backups)

    p = sub.add_parser("undo", help="restore the newest backup (repeat to go further back)")
    p.add_argument("-c", "--config", metavar="FILE")
    p.add_argument("-q", "--quiet", action="store_true")
    _add_color(p)
    p.set_defaults(func=cmd_undo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return EXIT_OK
    if getattr(args, "keep", DEFAULT_KEEP) < 1:
        parser.error("--keep must be at least 1")
    try:
        return args.func(args)
    except (CliError, ConfigError) as exc:
        print(f"hookswitch: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyError as exc:
        print(f"hookswitch: unknown server {exc.args[0]!r}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        detail = f" ({exc.filename})" if exc.filename else ""
        print(f"hookswitch: {exc.strerror or exc}{detail}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
