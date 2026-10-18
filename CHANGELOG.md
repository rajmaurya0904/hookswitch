# Changelog

## 0.1.0

- `hookswitch` command with `list`, `status`, `check`, `toggle`, `enable`, `disable`,
  `run`, `recipes`, `backups` and `undo`.
- Three config layouts: `servers.<name>.enabled` flags, `.mcp.json` / Claude Desktop
  `mcpServers` (disabled servers are parked under `hookswitchDisabled`), and Claude Code
  settings arrays (`enabledMcpjsonServers` / `disabledMcpjsonServers`).
- Every write is atomic, preceded by a timestamped backup (newest 3 kept), and followed
  by a unified diff. `--dry-run`, `--quiet` and `--color` are available on edits.
- Recipes in YAML or JSON apply several toggles as a single edit.
- Rewrites keep the file's indentation, final newline and one-line `{...}` objects.
