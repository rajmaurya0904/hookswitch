# hookswitch

**Switch MCP servers on and off in a config file from the command line or a hook, with a backup and a diff for every edit.**

## The problem

Every MCP server you leave switched on spends context before you have typed a word, and `.mcp.json` has no on/off switch: to turn the Postgres server off for a docs session you delete a block, then paste it back next week. Doing that from a script means rewriting a JSON file you care about. hookswitch does the rewrite carefully (atomic write, timestamped backup, diff of what changed) and lets a named recipe flip several servers in one go.

## Real output

A `.mcp.json` with three servers, and a recipe called `lean` that keeps GitHub and drops the other two:

```console
$ hookswitch list
NAME       STATE
github     on
postgres   on
puppeteer  on

3 of 3 enabled (.mcp.json)

$ hookswitch run lean
disable postgres
disable puppeteer
--- .mcp.json (before)
+++ .mcp.json (after)
@@ -1,6 +1,8 @@
 {
   "mcpServers": {
-    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
+    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
+  },
+  "hookswitchDisabled": {
     "postgres": {"command": "uvx", "args": ["mcp-server-postgres"]},
     "puppeteer": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]}
   }
backup: .mcp.json.bak.20261018093541554634

$ hookswitch status
github

$ hookswitch undo
restored .mcp.json from .mcp.json.bak.20261018093541554634
--- .mcp.json (before)
+++ .mcp.json (after)
@@ -1,8 +1,6 @@
 {
   "mcpServers": {
-    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]}
-  },
-  "hookswitchDisabled": {
+    "github": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"]},
     "postgres": {"command": "uvx", "args": ["mcp-server-postgres"]},
     "puppeteer": {"command": "npx", "args": ["-y", "@modelcontextprotocol/server-puppeteer"]}
   }
```

The disabled servers are not deleted: they are moved, unchanged, under `hookswitchDisabled`, and `undo` (or `enable`) puts them back.

## Install

Not on PyPI yet. Clone the repo and install from the working tree (Python 3.11 or newer):

```bash
pip install -e .
```

## Usage

```bash
hookswitch list                          # every server and whether it is on (--json for scripts)
hookswitch disable postgres puppeteer    # switch off; `enable` and `toggle [--on|--off]` also work
hookswitch run lean                      # apply a recipe: one backup, one diff
hookswitch check postgres || echo off    # exit 0 if on, 3 if off, 1 on error; for hooks
```

Add `--dry-run` to any edit to see the diff without writing, `--quiet` to print nothing, and `--color` to colour the diff (it is plain when output is not a terminal). `hookswitch recipes` lists recipes, `hookswitch backups` lists the backups, and `hookswitch undo` restores the newest one, repeatedly if you keep going.

**Which file?** `--config FILE`, else `$HOOKSWITCH_CONFIG`, else the first of `.mcp.json`, `mcp.json`, `hookswitch.json` in the current directory. If none exist, `hookswitch.json` is created with an empty `{"servers": {}}`. A path you name explicitly must already exist.

**Recipes** are small YAML or JSON files named after the recipe, looked up in `.hookswitch/recipes/` and then `~/.config/hookswitch/recipes/` (or `--recipes-dir`). See [docs/recipes](docs/recipes):

```yaml
description: Docs work, no database or browser
enable: [github]
disable: [postgres, puppeteer]
```

`servers:` (`name: true/false`) and `toggles:` (`- {server: x, enabled: false}`) are also accepted. A recipe naming a server that is not in the config fails without touching the file, unless you pass `--skip-missing`.

**As a hook.** [docs/example_hook_settings.json](docs/example_hook_settings.json) shows a Claude Code `SessionStart` hook that runs `hookswitch run lean --quiet`. See Limitations before relying on it.

## How it works

- It reads the file as JSON and picks a layout from its shape. `servers.<name>.enabled` is flipped in place. For `mcpServers` (`.mcp.json`, Claude Desktop), which has no switch, a disabled server is moved to a top-level `hookswitchDisabled` object. For a Claude Code settings file, names move between `enabledMcpjsonServers` and `disabledMcpjsonServers`. `--format` overrides the guess.
- Before writing, it copies the file to `<name>.bak.<timestamp>` next to it and keeps the newest 3 (`--keep N`). Only files with exactly that name pattern are ever pruned.
- The new content goes to a temp file in the same directory and replaces the original with `os.replace`, so a crash cannot leave half a file.
- It re-uses the original indentation, final newline and one-line `{...}` objects, so the diff shows only the servers that moved.
- Setting a server to the state it is already in changes nothing and makes no backup.

## Limitations

- It edits a file; it does not talk to a running MCP client. Whether and when a client re-reads the file is up to the client. I have not verified that a `SessionStart` hook edit takes effect in the same Claude Code session; running hookswitch before the client starts (an alias or wrapper script) is the dependable way.
- `hookswitchDisabled` is a key hookswitch invented. I have not checked that every client tolerates an unknown top-level key; if one does not, use the `servers`/`enabled` layout or the settings layout.
- JSON only. Comments (JSONC) are rejected as invalid JSON. Formatting is preserved by heuristic, so an unusually formatted file can be reflowed on its first edit; `--dry-run` shows you before it happens.
- A server re-enabled from `hookswitchDisabled` is appended after the others, so key order can change.
- The settings layout cannot know which names are real servers, so it accepts any name.
- No file locking: two hookswitch runs (or a hook plus an editor) writing at once can overwrite each other.
- Config discovery looks only in the current directory; there is no search up the tree and no user-level default.

## Development

```bash
pip install -e ".[dev]"
pytest -q        # 178 tests
ruff check .
```

MIT, see [LICENSE](LICENSE).
