# Connecting AI clients

dotTide speaks MCP (Model Context Protocol), the open standard most AI coding tools and assistants use to call outside tools. Any client that can start a local MCP server over stdio can use it. Each one only needs the same command:

```
uvx dottide
```

`uvx` comes with [uv](https://docs.astral.sh/uv/). It downloads dotTide the first time and starts it from its cache after that. Desktop apps often start without your shell's `PATH`, so if a client says it can't find `uvx`, use its full path instead. `which uvx` prints it, usually `/opt/homebrew/bin/uvx`.

Config file names and keys change between versions, so check your client's MCP docs if a snippet below doesn't match what you see.

## Claude Code

```
claude mcp add --scope user dottide -- uvx dottide
```

`--scope user` makes it available in every project. Check it with `claude mcp get dottide`.

## Claude Desktop

Open Settings, then Developer, then Edit Config, and add dotTide to `mcpServers` in `claude_desktop_config.json`:

```
{
  "mcpServers": {
    "dottide": {
      "command": "/opt/homebrew/bin/uvx",
      "args": ["dottide"]
    }
  }
}
```

Restart Claude Desktop afterwards.

## Cursor

Add the same `mcpServers` block to `~/.cursor/mcp.json` for every project, or to `.cursor/mcp.json` inside one project.

dotTide is also listed on [cursor.directory](https://cursor.directory/plugins/dottide), with the same setup.

## Windsurf

Add the same `mcpServers` block to `~/.codeium/windsurf/mcp_config.json`, then refresh the MCP list in Windsurf's settings.

## VS Code with GitHub Copilot

Create `.vscode/mcp.json` in your project. VS Code uses `servers`, not `mcpServers`:

```
{
  "servers": {
    "dottide": {
      "type": "stdio",
      "command": "/opt/homebrew/bin/uvx",
      "args": ["dottide"]
    }
  }
}
```

Then pick the dotTide tools in Copilot Chat's agent mode.

## OpenAI Codex CLI

Add a table to `~/.codex/config.toml`:

```
[mcp_servers.dottide]
command = "/opt/homebrew/bin/uvx"
args = ["dottide"]
```

## Gemini CLI

Add dotTide to `mcpServers` in `~/.gemini/settings.json`, using the same block as Claude Desktop.

## Grok

The Grok Build CLI reads the MCP servers already set up for Claude and Cursor, so if dotTide works in either one, Grok finds it too.

## Web chat apps

ChatGPT, grok.com and claude.ai in the browser connect to MCP servers by URL, over the internet. dotTide runs on your computer and keeps its Google key in your system's secret store on purpose, so it has no public URL, and those apps can't reach it. Use a desktop app or a command-line client instead.

## Agents without MCP

Anything that can run a command or read a file can still use dotTide:

- **Commands:** every tool is also a command that prints JSON, for example `uvx dottide search_queries example.com --compare`. See [Using dotTide](usage.md).
- **Files:** the weekly snapshot writes one JSON file per profile. Point a script or an agent at the folder. The file format is in [Using dotTide](usage.md#the-weekly-snapshot).

## Check that it works

Ask your client: "Use dotTide to list my sites and tell me whether each one has access." It should call `sites` and answer from the result. For more to ask, see [Asking an AI agent for your numbers](examples.md). If the tools don't show up, run `uvx dottide sites` in a terminal first: if that fails, the client will too, and the message tells you why.
