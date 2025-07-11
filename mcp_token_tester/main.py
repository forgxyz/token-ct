"""Main CLI interface for MCP Token Tester."""

import asyncio
import json
import os
import click
from dotenv import load_dotenv

from .config import ConfigManager, MCPServerConfig
from .mcp_client import MCPSDKClient
from .token_counter import TokenCounterFactory, TokenAnalyzer

# Load environment variables
load_dotenv()


@click.group()
@click.pass_context
def cli(ctx):
    """MCP Token Tester - Test MCP servers with token cost analysis."""
    ctx.ensure_object(dict)
    ctx.obj['config_manager'] = ConfigManager()


@cli.command()
@click.option('--name', required=True, help='Server name')
@click.option('--type', 'server_type', required=True, type=click.Choice(['stdio', 'http', 'sse']), help='Server type')
@click.option('--command', help='Command to run (for stdio)')
@click.option('--path', help='Path to executable (for stdio)')
@click.option('--args', help='Arguments (comma-separated)')
@click.option('--url', help='URL (for HTTP/SSE servers)')
@click.option('--auto-start/--no-auto-start', default=True, help='Auto-start server')
@click.pass_context
def add_server(ctx, name, server_type, command, path, args, url, auto_start):
    """Add a new MCP server configuration."""
    config_manager = ctx.obj['config_manager']
    
    # Parse arguments
    args_list = [arg.strip() for arg in args.split(',')] if args else []
    
    # Create server config
    server_config = MCPServerConfig(
        name=name,
        server_type=server_type,
        command=command,
        path=path,
        args=args_list,
        url=url,
        auto_start=auto_start
    )
    
    config_manager.add_server(server_config)
    click.echo(f"Added server '{name}' successfully!")


@cli.command()
@click.pass_context
def list_servers(ctx):
    """List all configured MCP servers."""
    config_manager = ctx.obj['config_manager']
    servers = config_manager.list_servers()
    
    if not servers:
        click.echo("No servers configured.")
        return
    
    click.echo("Configured servers:")
    for server_name in servers:
        server = config_manager.get_server(server_name)
        is_default = server_name == config_manager.config.default_server
        status = " (default)" if is_default else ""
        click.echo(f"  • {server_name} ({server.server_type}){status}")


@cli.command()
@click.argument('name')
@click.pass_context
def remove_server(ctx, name):
    """Remove a server configuration."""
    config_manager = ctx.obj['config_manager']
    
    if config_manager.remove_server(name):
        click.echo(f"Removed server '{name}' successfully!")
    else:
        click.echo(f"Server '{name}' not found.")


@cli.command()
@click.option('--server', help='Server name to connect to')
@click.pass_context
def connect(ctx, server):
    """Connect to an MCP server and list its tools."""
    config_manager = ctx.obj['config_manager']
    
    # Get server config
    if server:
        server_config = config_manager.get_server(server)
    else:
        server_config = config_manager.get_default_server()
    
    if not server_config:
        click.echo("No server configuration found.")
        return
    
    async def _connect():
        client = MCPSDKClient(server_config)
        
        try:
            click.echo(f"Connecting to {server_config.name}...")
            if await client.connect():
                click.echo("Connected successfully!")
                
                tools = client.get_tools()
                if tools:
                    click.echo(f"\nAvailable tools ({len(tools)}):")
                    for tool in tools:
                        click.echo(f"  • {tool['name']}: {tool['description']}")
                else:
                    click.echo("No tools available.")
                    
            else:
                click.echo("Failed to connect.")
                
        except Exception as e:
            click.echo(f"Error: {e}")
        finally:
            await client.disconnect()
    
    asyncio.run(_connect())


@cli.command()
@click.option('--server', help='Server name to use')
@click.option('--tool', required=True, help='Tool name to call')
@click.option('--args', help='Tool arguments as JSON string')
@click.option('--provider', default='anthropic', help='LLM provider for token counting')
@click.option('--model', default=lambda: os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'), help='Model for token counting')
@click.option('--overhead', default=100, help='Token overhead estimate')
@click.pass_context
def call_tool(ctx, server, tool, args, provider, model, overhead):
    """Call a tool and analyze token costs."""
    config_manager = ctx.obj['config_manager']
    
    # Get server config
    if server:
        server_config = config_manager.get_server(server)
    else:
        server_config = config_manager.get_default_server()
    
    if not server_config:
        click.echo("No server configuration found.")
        return
    
    # Parse arguments
    try:
        tool_args = json.loads(args) if args else {}
    except json.JSONDecodeError:
        click.echo("Invalid JSON in arguments.")
        return
    
    # Get API key (optional for Anthropic token counting)
    api_key = None
    if provider.lower() == 'anthropic':
        api_key = os.getenv('ANTHROPIC_API_KEY')
        # Note: API key is optional for token counting (free to use)
    
    async def _call_tool():
        client = MCPSDKClient(server_config)
        
        try:
            click.echo(f"Connecting to {server_config.name}...")
            if not await client.connect():
                click.echo("Failed to connect.")
                return
            
            # Check if tool exists
            tool_obj = client.get_tool(tool)
            if not tool_obj:
                click.echo(f"Tool '{tool}' not found.")
                available_tools = [t['name'] for t in client.get_tools()]
                if available_tools:
                    click.echo(f"Available tools: {', '.join(available_tools)}")
                return
            
            click.echo(f"Calling tool '{tool}'...")
            
            # Call the tool
            response = await client.call_tool(tool, tool_args)
            
            if response:
                # Convert MCP response to dict for analysis
                # Use model_dump() to serialize MCP content objects properly
                serialized_content = []
                for content_item in response.content:
                    if hasattr(content_item, 'model_dump'):
                        serialized_content.append(content_item.model_dump())
                    else:
                        serialized_content.append(content_item)
                
                response_dict = {
                    "content": serialized_content,
                    "isError": response.isError or False
                }
                
                click.echo("\n--- Tool Response ---")
                click.echo(json.dumps(response_dict, indent=2, default=str))
                
                # Analyze token costs
                try:
                    counter = TokenCounterFactory.create_counter(provider, model, api_key)
                    analyzer = TokenAnalyzer(counter, overhead)
                    
                    analysis = analyzer.analyze_tool_call(tool, tool_args, response_dict)
                    
                    click.echo(f"\n--- Token Analysis ({provider} {model}) ---")
                    click.echo(f"Input tokens (estimated): {analysis['input_tokens']}")
                    click.echo(f"Response tokens (actual): {analysis['response_tokens']}")
                    click.echo(f"Total tokens: {analysis['total_tokens']}")
                    click.echo(f"Overhead tokens: {analysis['overhead_tokens']}")
                    
                except Exception as e:
                    click.echo(f"Error analyzing tokens: {e}")
            else:
                click.echo("Tool call failed.")
                
        except Exception as e:
            click.echo(f"Error: {e}")
        finally:
            await client.disconnect()
    
    asyncio.run(_call_tool())


@cli.command()
@click.option('--server', help='Server name to use')
@click.pass_context
def interactive(ctx, server):
    """Start interactive session with an MCP server."""
    config_manager = ctx.obj['config_manager']
    
    # Get server config
    if server:
        server_config = config_manager.get_server(server)
    else:
        server_config = config_manager.get_default_server()
    
    if not server_config:
        click.echo("No server configuration found.")
        return
    
    async def _interactive():
        client = MCPSDKClient(server_config)
        
        # Session configuration
        session_config = {
            'provider': 'anthropic',
            'model': os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022'),
            'overhead': 100,
            'auto_tokens': False
        }
        
        # Store last response for tokens command
        last_response = None
        last_tool_name = None
        last_tool_args = None
        
        def parse_command_with_flags(command_str):
            """Parse command and extract flags"""
            # First, extract flags from the end
            flags = []
            remaining_command = command_str
            
            # Look for flags at the end of the command
            while True:
                flag_match = False
                for flag in ['--tokens', '--no-tokens']:
                    if remaining_command.endswith(' ' + flag):
                        flags.append(flag[2:])  # Remove --
                        remaining_command = remaining_command[:-len(flag)-1].strip()
                        flag_match = True
                        break
                if not flag_match:
                    break
            
            # Now parse the remaining command (without flags)
            parts = remaining_command.split(None, 2)  # Split into at most 3 parts
            
            return parts, flags
        
        def display_token_analysis(tool_name, tool_args, response_dict):
            """Display token analysis for a tool call"""
            try:
                # Get API key (optional for Anthropic token counting)
                api_key = None
                if session_config['provider'].lower() == 'anthropic':
                    api_key = os.getenv('ANTHROPIC_API_KEY')
                
                counter = TokenCounterFactory.create_counter(
                    session_config['provider'], 
                    session_config['model'], 
                    api_key
                )
                analyzer = TokenAnalyzer(counter, session_config['overhead'])
                
                analysis = analyzer.analyze_tool_call(tool_name, tool_args, response_dict)
                
                click.echo(f"\n--- Token Analysis ({session_config['provider']} {session_config['model']}) ---")
                click.echo(f"Input tokens (estimated): {analysis['input_tokens']}")
                click.echo(f"Response tokens (actual): {analysis['response_tokens']}")
                click.echo(f"Total tokens: {analysis['total_tokens']}")
                click.echo(f"Overhead tokens: {analysis['overhead_tokens']}")
                
            except Exception as e:
                click.echo(f"Error analyzing tokens: {e}")
        
        try:
            click.echo(f"Connecting to {server_config.name}...")
            if not await client.connect():
                click.echo("Failed to connect.")
                return
            
            click.echo("Connected! Type 'help' for commands, 'exit' to quit.")
            
            while True:
                try:
                    command = input("\n> ").strip()
                    
                    if command.lower() in ['exit', 'quit']:
                        break
                    elif command.lower() == 'help':
                        click.echo("Commands:")
                        click.echo("  list - List available tools")
                        click.echo("  call <tool> [args] [--tokens] [--no-tokens] - Call a tool")
                        click.echo("  tokens - Analyze token count of previous response")
                        click.echo("  set [<key> <value>] - Set session config or show all config")
                        click.echo("  exit - Exit interactive session")
                        click.echo("\nConfiguration keys:")
                        click.echo("  provider - Token provider (anthropic, openai)")
                        click.echo("  model - Model name for token counting")
                        click.echo("  overhead - Token overhead estimate (integer)")
                        click.echo("  auto_tokens - Auto-analyze tokens (on/off)")
                    elif command.lower() == 'list':
                        tools = client.get_tools()
                        if tools:
                            click.echo("Available tools:")
                            for tool in tools:
                                click.echo(f"  • {tool['name']}: {tool['description']}")
                        else:
                            click.echo("No tools available.")
                    elif command.startswith('set'):
                        parts = command.split(None, 2)
                        if len(parts) == 1:
                            # Show all config
                            click.echo("Current session configuration:")
                            for key, value in session_config.items():
                                click.echo(f"  {key}: {value}")
                        elif len(parts) == 3:
                            # Set config
                            key, value = parts[1], parts[2]
                            if key in session_config:
                                # Type conversion
                                if key == 'overhead':
                                    try:
                                        session_config[key] = int(value)
                                    except ValueError:
                                        click.echo(f"Invalid value for {key}: must be an integer")
                                        continue
                                elif key == 'auto_tokens':
                                    if value.lower() in ['on', 'true', '1']:
                                        session_config[key] = True
                                    elif value.lower() in ['off', 'false', '0']:
                                        session_config[key] = False
                                    else:
                                        click.echo(f"Invalid value for {key}: use 'on' or 'off'")
                                        continue
                                else:
                                    session_config[key] = value
                                click.echo(f"Set {key} to {session_config[key]}")
                            else:
                                click.echo(f"Unknown configuration key: {key}")
                        else:
                            click.echo("Usage: set [<key> <value>]")
                    elif command.lower() == 'tokens':
                        if last_response is None:
                            click.echo("No previous response to analyze. Use 'call' to make a request first.")
                        else:
                            display_token_analysis(last_tool_name, last_tool_args, last_response)
                    elif command.startswith('call '):
                        args, flags = parse_command_with_flags(command)
                        
                        if len(args) < 2:
                            click.echo("Usage: call <tool> [args] [--tokens] [--no-tokens]")
                            continue
                        
                        tool_name = args[1]
                        args_str = args[2] if len(args) > 2 else "{}"
                        
                        # Parse flags
                        force_tokens = 'tokens' in flags
                        no_tokens = 'no-tokens' in flags
                        
                        try:
                            tool_args = json.loads(args_str)
                        except json.JSONDecodeError:
                            click.echo("Invalid JSON in arguments.")
                            continue
                        
                        response = await client.call_tool(tool_name, tool_args)
                        if response:
                            # Convert MCP response to dict for analysis
                            # Use model_dump() to serialize MCP content objects properly
                            serialized_content = []
                            for content_item in response.content:
                                if hasattr(content_item, 'model_dump'):
                                    serialized_content.append(content_item.model_dump())
                                else:
                                    serialized_content.append(content_item)
                            
                            response_dict = {
                                "content": serialized_content,
                                "isError": response.isError or False
                            }
                            
                            # Store for tokens command
                            last_response = response_dict
                            last_tool_name = tool_name
                            last_tool_args = tool_args
                            
                            click.echo(json.dumps(response_dict, indent=2, default=str))
                            
                            # Token analysis logic
                            should_analyze = False
                            if force_tokens:
                                should_analyze = True
                            elif not no_tokens and session_config['auto_tokens']:
                                should_analyze = True
                            
                            if should_analyze:
                                display_token_analysis(tool_name, tool_args, response_dict)
                        else:
                            click.echo("Tool call failed.")
                    else:
                        click.echo("Unknown command. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    break
                except EOFError:
                    break
                    
        except Exception as e:
            click.echo(f"Error: {e}")
        finally:
            await client.disconnect()
    
    asyncio.run(_interactive())


if __name__ == '__main__':
    cli()