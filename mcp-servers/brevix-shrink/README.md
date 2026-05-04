# brevix-shrink

> MCP middleware proxy that compresses tool/prompt/resource descriptions to save tokens.

`brevix-shrink` sits between an MCP client (Claude Desktop, Claude Code, Cursor, etc.) and an upstream MCP server. It intercepts `tools/list`, `prompts/list`, `resources/list`, and `resources/templates/list` responses, then runs Brevix's compression rules on description-style fields. Code, URLs, identifiers, and error quotes are preserved.

Why: MCP servers ship verbose descriptions for every tool. Those descriptions are loaded into the model's input on every session. Compressing them once at the proxy saves input tokens for the whole session lifetime.

## Install

```bash
npm install -g brevix-shrink
# or run on demand
npx brevix-shrink <upstream> [args...]
```

## Usage

Wrap any MCP server command:

```bash
brevix-shrink npx -y @modelcontextprotocol/server-filesystem /tmp
```

Register in Claude Desktop / Claude Code config:

```json
{
  "mcpServers": {
    "fs-shrunk": {
      "command": "npx",
      "args": ["-y", "brevix-shrink", "npx", "-y",
               "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

## Configuration

| Env var | Default | Effect |
|---------|---------|--------|
| `BREVIX_SHRINK_FIELDS` | `description,prompt,instructions` | Comma-separated field names to compress |
| `BREVIX_SHRINK_DEBUG` | unset | Log proxy events to stderr |

## License

MIT
