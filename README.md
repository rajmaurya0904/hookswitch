# hookswitch

**Flip MCP servers on and off in a JSON config file without losing the file to a bad write — every edit is backed up first and shown to you as a diff.**

**Status: early and incomplete.** The three library pieces work and are tested:
config load/save/toggle, timestamped backups with rotation, and unified diffs.
There is **no CLI yet** — no `hookswitch` command and no `python -m hookswitch`.
You call it from Python (or a hook script) as shown below.

## The problem

Every MCP server you leave switched on eats context before you have typed a word.
Turning them off per project means hand-editing a JSON config, which is exactly the
kind of file you do not want to corrupt from inside a pre-session hook at 2am.
hookswitch does the boring safety part: copy the file, flip the flag, show you what
changed.

## Real output

A three-server config, with two of them switched off:

```console
$ cat mcp.json
{
  "servers": {
    "github": {"enabled": true},
    "postgres": {"enabled": true},
    "puppeteer": {"enabled": true}
  }
}

$ python off.py
backup: mcp.json.bak.20261011141544113500
---
+++
@@ -1,7 +1,13 @@
 {
   "servers": {
-    "github": {"enabled": true},
-    "postgres": {"enabled": true},
-    "puppeteer": {"enabled": true}
+    "github": {
+      "enabled": true
+    },
+    "postgres": {
+      "enabled": false
+    },
+    "puppeteer": {
+      "enabled": false
+    }
   }
-}
+}
```

`off.py` is the whole of it — this is the script that produced the output above:

```python
from hookswitch.backup import backup_file
from hookswitch.config import load_config, save_config, toggle_server
from hookswitch.diff import get_diff

PATH = "mcp.json"
before = open(PATH).read()

print("backup:", backup_file(PATH, keep=3).name)

cfg = load_config(PATH)
for name in ("postgres", "puppeteer"):
    cfg = toggle_server(cfg, name, False)
save_config(cfg, PATH)

print(get_diff(before, open(PATH).read()))
```

## Install

Not on PyPI. Clone it and install from the working tree:

```bash
pip install -e ".[dev]"
```

## Usage

There is no command-line interface. The public surface is five functions:

```python
load_config(path)                      # dict, or {} if the file is absent
toggle_server(config, name, enabled)   # new dict; raises KeyError on unknown name
save_config(config, path)              # writes JSON, creating parent dirs
backup_file(path, keep=3)              # <path>.bak.<timestamp>, prunes older ones
get_diff(old_text, new_text)           # unified diff string, "" if identical
```

`docs/example_recipe.yaml` sketches the recipe format the eventual CLI is meant to
read. Nothing in the package parses it today.

## How it works

- **Config** is plain JSON with a top-level `servers` object, each entry carrying an
  `enabled` boolean. Nothing else is inspected.
- **`toggle_server`** deep-copies through `json.dumps`/`json.loads`, so your input
  dict is never mutated. An unknown server name is a `KeyError`, not a silent insert.
- **`backup_file`** copies with `shutil.copy2` to `<name>.bak.<YYYYMMDDHHMMSSffffff>`,
  then globs `<name>.bak.*`, sorts by mtime and deletes the oldest until `keep` remain.
- **`get_diff`** is `difflib.unified_diff` over `splitlines(keepends=True)`.
- **Backups live next to the file**, not in a `.hookswitch/` directory.

## Limitations

- No CLI, no `hookswitch diff`, no hook installer. Those are the parts that would
  make this a tool rather than three helpers.
- JSON only. The YAML recipe file in `docs/` is documentation, not an input.
- `save_config` rewrites the whole file with `indent=2`, so your original formatting
  and any comments are gone — see the diff above, where untouched lines got reflowed.
- Nothing validates that the config is really an MCP config, or that the server names
  mean anything to your client.
- `get_diff` emits bare `---`/`+++` headers with no filenames or timestamps.
- Backup rotation ranks by mtime. Two backups written within the same filesystem tick
  can be pruned in an arbitrary order.

## Development

```bash
pip install -e ".[dev]"
pytest -q        # 19 tests
ruff check .
```

MIT — see [LICENSE](LICENSE).
