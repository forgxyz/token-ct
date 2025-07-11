# MCP Token Tester

A developer tool for testing Model Context Protocol (MCP) servers with comprehensive token cost analysis.

## Overview

MCP Token Tester enables developers to:
- Configure and connect to MCP servers (stdio and HTTP)
- Execute tool calls and analyze responses
- Calculate accurate token costs using native LLM provider APIs
- Optimize MCP tools for performance and cost-efficiency

## Features

- **Official MCP SDK**: Uses the official MCP Python SDK for reliable connections
- **Multi-server Support**: Connect to multiple MCP servers via stdio, HTTP, or SSE
- **Token Cost Analysis**: Precise token counting using Anthropic's API
- **Interactive CLI**: User-friendly command-line interface
- **JSON Configuration**: Version-controllable server configurations
- **Fallback Support**: Handles non-standard MCP servers with graceful fallbacks

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd token-ct

# Install dependencies using uv
uv sync

# Copy environment template
cp .env.example .env
```

### Configuration

1. **Set up API keys and model preferences** in `.env`:
   ```
   # Required - Anthropic token counting requires an API key
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   
   # Optional - Default model for token counting (see supported models table)
   ANTHROPIC_MODEL=claude-sonnet-3.5
   ```

2. **Add an MCP server**:
   ```bash
   # For stdio servers
   uv run mcp-test add-server --name my-server --type stdio --command python --args "server.py"
   
   # For HTTP servers
   uv run mcp-test add-server --name http-server --type http --url "http://localhost:8080"
   
   # For SSE servers
   uv run mcp-test add-server --name sse-server --type sse --url "http://localhost:8080"
   
   # Example: Demo SSE server
   uv run mcp-test add-server --name demo-server --type sse --url "https://demo-day.mcp.cloudflare.com/sse"
   ```

3. **List configured servers**:
   ```bash
   uv run mcp-test list-servers
   ```

### Usage

#### Connect and List Tools
```bash
uv run mcp-test connect --server my-server
```

#### Call a Tool with Token Analysis
```bash
uv run mcp-test call-tool --tool "search" --args '{"query": "test"}' --provider anthropic
```

#### Interactive Session
```bash
uv run mcp-test interactive --server my-server
```

## Commands

### Server Management

#### `add-server`
Add a new MCP server configuration.

```bash
uv run mcp-test add-server [OPTIONS]
```

**Options:**
- `--name TEXT` **(required)**: Server name for identification
- `--type [stdio|http|sse]` **(required)**: Server transport type
- `--command TEXT`: Command to run (for stdio servers)
- `--path TEXT`: Path to executable (for stdio servers)
- `--args TEXT`: Arguments (comma-separated)
- `--url TEXT`: Server URL (for HTTP/SSE servers)
- `--auto-start / --no-auto-start`: Auto-start server (default: enabled)

**Examples:**
```bash
# Add stdio server
uv run mcp-test add-server --name github --type stdio --command npx --args "-y,@smithery/cli,run,@smithery-ai/github"

# Add HTTP server
uv run mcp-test add-server --name api-server --type http --url "http://localhost:8080"

# Add SSE server
uv run mcp-test add-server --name demo-server --type sse --url "https://demo-day.mcp.cloudflare.com/sse"
```

#### `list-servers`
List all configured MCP servers.

```bash
uv run mcp-test list-servers
```

#### `remove-server`
Remove a server configuration.

```bash
uv run mcp-test remove-server SERVER_NAME
```

### Testing and Analysis

#### `connect`
Connect to a server and list available tools.

```bash
uv run mcp-test connect [OPTIONS]
```

**Options:**
- `--server TEXT`: Server name to connect to (uses default if not specified)

**Example:**
```bash
uv run mcp-test connect --server github
```

#### `call-tool`
Execute a tool call with comprehensive token cost analysis.

```bash
uv run mcp-test call-tool [OPTIONS]
```

**Options:**
- `--server TEXT`: Server name to use (uses default if not specified)
- `--tool TEXT` **(required)**: Tool name to call
- `--args TEXT`: Tool arguments as JSON string (default: "{}")
- `--provider TEXT`: LLM provider for token counting (default: "anthropic")
- `--model TEXT`: Model for token counting (default: from ANTHROPIC_MODEL env var or "claude-3-5-sonnet-20241022", see supported models table)
- `--overhead INTEGER`: Token overhead estimate (default: 100)

**Examples:**
```bash
# Simple tool call
uv run mcp-test call-tool --tool "search_repositories" --args '{"query": "MCP"}'

# With specific server and model
uv run mcp-test call-tool --server github --tool "get_file" --args '{"path": "README.md"}' --model claude-3-opus-20240229

# With custom overhead
uv run mcp-test call-tool --tool "complex_analysis" --args '{"data": "large_dataset"}' --overhead 200
```

#### `interactive`
Start an interactive session with a server.

```bash
uv run mcp-test interactive [OPTIONS]
```

**Options:**
- `--server TEXT`: Server name to use (uses default if not specified)

**Example:**
```bash
uv run mcp-test interactive --server github
```

**Interactive Commands:**
- `help`: Show available commands
- `list`: List available tools
- `call <tool> [args]`: Call a tool with optional JSON arguments
- `exit` or `quit`: Exit the session

## Configuration Format

Server configurations are stored in `mcp_config.json`:

```json
{
  "servers": {
    "my-server": {
      "name": "my-server",
      "server_type": "stdio",
      "command": "python",
      "args": ["server.py"],
      "auto_start": true,
      "env_vars": {}
    },
    "http-server": {
      "name": "http-server",
      "server_type": "http",
      "url": "http://localhost:8080",
      "auto_start": false,
      "env_vars": {}
    },
    "sse-server": {
      "name": "sse-server", 
      "server_type": "sse",
      "url": "http://localhost:8080",
      "auto_start": false,
      "env_vars": {}
    }
  },
  "default_server": "my-server",
  "token_overhead": 100
}
```

## Token Analysis

The tool provides detailed token breakdowns:
- **Input tokens**: Tool name + arguments + configurable overhead
- **Response tokens**: Actual response from MCP server
- **Total tokens**: Complete cost estimation for the tool call

### Supported Models

The following Anthropic Claude models are supported for token counting:

| Model Name | User-Friendly Name | API Identifier |
|------------|-------------------|----------------|
| Claude Opus 4 | `claude-opus-4` | `claude-opus-4-20250514` |
| Claude Sonnet 4 | `claude-sonnet-4` | `claude-sonnet-4-20250514` |
| Claude Sonnet 3.7 | `claude-sonnet-3.7` | `claude-3-7-sonnet-20250219` |
| Claude Sonnet 3.5 | `claude-sonnet-3.5` | `claude-3-5-sonnet-20241022` |
| Claude Haiku 3.5 | `claude-haiku-3.5` | `claude-3-5-haiku-20241022` |
| Claude Haiku 3 | `claude-haiku-3` | `claude-3-haiku-20240307` |
| Claude Opus 3 | `claude-opus-3` | `claude-3-opus-20240229` |

**Usage**: You can use either the user-friendly name or the API identifier when specifying models:

```bash
# Using user-friendly name
uv run mcp-test call-tool --tool "search" --model claude-sonnet-4

# Using API identifier
uv run mcp-test call-tool --tool "search" --model claude-sonnet-4-20250514

# Set default model in .env file
ANTHROPIC_MODEL=claude-sonnet-3.5
```

## Best Practices

1. **Use specific tool arguments** to get accurate token counts
2. **Adjust token overhead** based on your LLM integration complexity
3. **Test with representative data** to understand real-world costs
4. **Monitor token usage** to optimize tool performance
5. **For SSE servers**: Be patient with responses as they may be processed asynchronously

## Limitations

- Currently supports Anthropic token counting only
- Token overhead is estimated, not precisely calculated
- Anthropic token counting is free but subject to rate limits
- Limited to MCP protocol 2024-11-05
- Some servers may not fully implement the MCP protocol (fallback support provided)
- Non-standard MCP servers may only support tool discovery, not execution

## Development

### Project Structure
```
mcp_token_tester/
├── __init__.py
├── main.py          # CLI interface
├── config.py        # Configuration management
├── mcp_client.py     # MCP SDK client with fallbacks
└── token_counter.py # Token counting logic
```

### Adding New LLM Providers

1. Implement `TokenCounter` protocol in `token_counter.py`
2. Add provider to `TokenCounterFactory`
3. Update environment variables and documentation

### Dependencies

- `mcp`: Official MCP Python SDK (>=1.0.0)
- `httpx`: HTTP client for MCP servers
- `click`: CLI framework
- `pydantic`: Data validation
- `anthropic`: Anthropic API client
- `python-dotenv`: Environment variable management

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.