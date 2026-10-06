# Hookswitch

Small CLI plus hook recipes to toggle MCP servers per project or per session by editing config safely (with backup and diff). Lets scripts and hooks control which servers are active to save context.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

TODO: fill in as the build loop lands the core feature.

## Example

TODO.

## FAQ

**Where are backups stored?**
Backups are stored in the `.hookswitch/backups` directory within your project.

**Where are recipe files located?**
Recipe files are located in the `.hookswitch/recipes` directory within your project.

**I'm having issues with hookswitch not toggling servers. What should I check?**
Ensure that the hookswitch configuration file (`.hookswitch/config.yaml`) is correctly formatted and that the MCP server names match those in your config. You can run `hookswitch diff` to see what changes would be made.

## License

MIT -- see [LICENSE](LICENSE).
