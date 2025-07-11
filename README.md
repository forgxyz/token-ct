# MCP Token Tester

A developer tool for testing Model Context Protocol (MCP) servers with comprehensive token cost analysis. Connect to MCP servers, execute tool calls, and analyze token costs using native LLM provider APIs to optimize your MCP tools for performance and cost-efficiency.

**Key Features:**
- Multi-server support (stdio, HTTP, SSE) using official MCP SDK
- Precise token counting with Anthropic's API
- Enhanced interactive CLI with session-based token analysis
- Flexible token cost calculation (inline and post-hoc)
- JSON configuration and fallback support

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd token-ct

# Install dependencies using uv
uv sync

# Copy environment template and set up API keys
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (required)
```

## Quickstart

```bash
# 1. Add an MCP server
uv run mcp-test add-server --name demo --type sse --url "https://demo-day.mcp.cloudflare.com/sse"

# 2. Connect and list available tools
uv run mcp-test connect --server demo

# 3. Call a tool with token analysis
uv run mcp-test call-tool --server demo --tool "search" --args '{"query": "test"}'

# 4. Start interactive session with token analysis
uv run mcp-test interactive --server demo
# > set auto_tokens on
# > call search {"query": "test"}
# > tokens  # Analyze previous response
```

## MCP Configuration

### CLI Configuration

**Add a server** (required fields: `--name`, `--type`):
```bash
# Stdio server
uv run mcp-test add-server --name github --type stdio --command npx --args "-y,@smithery/cli,run,@smithery-ai/github"

# HTTP/SSE server  
uv run mcp-test add-server --name demo --type sse --url "https://demo-day.mcp.cloudflare.com/sse"
```

**Manage servers:**
```bash
uv run mcp-test list-servers
uv run mcp-test remove-server SERVER_NAME
```

### JSON Configuration

Configuration is stored in `mcp_config.json`:
```json
{
  "servers": {
    "my-server": {
      "name": "my-server",
      "server_type": "stdio",
      "command": "python",
      "args": ["server.py"],
      "auto_start": true
    },
    "demo-server": {
      "name": "demo-server", 
      "server_type": "sse",
      "url": "https://demo-day.mcp.cloudflare.com/sse"
    }
  },
  "default_server": "my-server"
}
```

### Environment Variables

Required configuration in `.env`:
```bash
# Required - Anthropic token counting
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional - Default model for token counting
ANTHROPIC_MODEL=claude-sonnet-3.5
```

## Example Usage

**Connect and explore:**
```bash
# Connect to server and list tools
uv run mcp-test connect --server github

# Call a tool with token analysis
uv run mcp-test call-tool --server github --tool "search_repositories" --args '{"query": "MCP"}'

# Use different model for token counting
uv run mcp-test call-tool --tool "get_file" --args '{"path": "README.md"}' --model claude-opus-4

# Interactive session with token analysis
uv run mcp-test interactive --server github
```

**Interactive session examples:**
```bash
# Configure session for automatic token analysis
> set auto_tokens on
> set model claude-sonnet-4
> set overhead 150

# Call tool with automatic analysis
> call search_repositories {"query": "MCP"}

# Force token analysis on specific call
> call get_file {"path": "README.md"} --tokens

# Analyze previous response retrospectively
> tokens

# Show current configuration
> set
```

**Interactive mode commands:**
- `help`: Show available commands
- `list`: List available tools  
- `call <tool> [args] [--tokens] [--no-tokens]`: Call a tool with optional JSON arguments
- `tokens`: Analyze token count of the previous response
- `set [<key> <value>]`: Set session configuration or show all settings
- `exit` or `quit`: Exit the session

**Session configuration:**
- `provider`: Token provider (anthropic, openai) - default: anthropic
- `model`: Model name for token counting - default: claude-3-5-sonnet-20241022
- `overhead`: Token overhead estimate - default: 100
- `auto_tokens`: Auto-analyze tokens after each call (on/off) - default: off

## Command Reference

### Server Management

**`add-server`** - Add a new MCP server (required: `--name`, `--type`)
```bash
uv run mcp-test add-server --name NAME --type [stdio|http|sse] [OPTIONS]
```
Options: `--command`, `--args`, `--url`, `--auto-start`

**`list-servers`** - List all configured servers
**`remove-server`** - Remove a server configuration

### Tool Testing

**`connect`** - Connect to server and list tools
```bash
uv run mcp-test connect [--server NAME]
```

**`call-tool`** - Execute tool with token analysis (required: `--tool`)
```bash
uv run mcp-test call-tool --tool NAME [--args JSON] [--server NAME] [--model NAME] [--overhead INT]
```

**`interactive`** - Start interactive session
```bash
uv run mcp-test interactive [--server NAME]
```

### Token Analysis

**Token breakdown:**
- Input tokens: Tool name + arguments + overhead (default: 100)
- Response tokens: Actual MCP server response
- Total tokens: Complete cost estimation

**Supported models:** `claude-opus-4`, `claude-sonnet-4`, `claude-sonnet-3.7`, `claude-sonnet-3.5`, `claude-haiku-3.5`, `claude-haiku-3`, `claude-opus-3`

## Limitations

- Anthropic token counting only (free but rate-limited)
- Token overhead is estimated
- Some servers may not fully implement MCP protocol

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


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.