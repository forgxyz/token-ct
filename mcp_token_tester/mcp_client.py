"""MCP client using the official MCP SDK."""

import asyncio
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.client.sse import sse_client
from mcp.shared.metadata_utils import get_display_name

from .config import MCPServerConfig


class MCPSDKClient:
    """MCP client using the official MCP SDK."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[types.Tool] = []
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the MCP server using the official SDK."""
        try:
            if self.config.server_type == "stdio":
                return await self._connect_stdio()
            elif self.config.server_type == "http":
                return await self._connect_http()
            elif self.config.server_type == "sse":
                return await self._connect_sse()
            else:
                print(f"Unsupported server type: {self.config.server_type}")
                return False
        except Exception as e:
            print(f"Error connecting to server: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Connect to stdio-based MCP server."""
        if not self.config.command and not self.config.path:
            print("No command or path specified for stdio server")
            return False
        
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=self.config.command or self.config.path,
                args=self.config.args,
                env=self.config.env_vars if self.config.env_vars else None
            )
            
            # Connect using stdio client following the official pattern
            transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = transport
            
            # Create session using the official pattern
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize connection
            await self.session.initialize()
            
            # List tools
            await self._list_tools()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to stdio server: {e}")
            await self.disconnect()
            return False
    
    async def _connect_http(self) -> bool:
        """Connect to HTTP-based MCP server using Streamable HTTP transport."""
        if not self.config.url:
            print("No URL specified for HTTP server")
            return False
        
        try:
            # Connect using streamable HTTP client following the official pattern
            transport = await self.exit_stack.enter_async_context(
                streamablehttp_client(self.config.url)
            )
            read_stream, write_stream, _ = transport
            
            # Create session using the official pattern
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize connection
            await self.session.initialize()
            
            # List tools
            await self._list_tools()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to HTTP server: {e}")
            await self.disconnect()
            return False
    
    async def _connect_sse(self) -> bool:
        """Connect to SSE-based MCP server using SSE transport."""
        if not self.config.url:
            print("No URL specified for SSE server")
            return False
        
        try:
            # Connect using SSE client following the official pattern
            transport = await self.exit_stack.enter_async_context(
                sse_client(self.config.url)
            )
            read_stream, write_stream = transport
            
            # Create session using the official pattern
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # Initialize connection
            await self.session.initialize()
            
            # List tools
            await self._list_tools()
            
            self.connected = True
            return True
            
        except Exception as e:
            print(f"Failed to connect to SSE server: {e}")
            await self.disconnect()
            return False
    
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        try:
            await self.exit_stack.aclose()
            self.session = None
            self.connected = False
            
        except Exception as e:
            print(f"Error disconnecting: {e}")
    
    async def _list_tools(self) -> None:
        """List available tools from the server."""
        if not self.session:
            return
        
        try:
            tools_response = await self.session.list_tools()
            self.tools = tools_response.tools
        except Exception as e:
            print(f"Error listing tools: {e}")
            self.tools = []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[types.CallToolResult]:
        """Call a tool on the MCP server."""
        if not self.connected:
            print("Not connected to server")
            return None
        
        if not self.session:
            print("No active session")
            return None
        
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return result
        except Exception as e:
            print(f"Error calling tool: {e}")
            return None
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools in a format compatible with the old client."""
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "inputSchema": tool.inputSchema or {}
            }
            for tool in self.tools
        ]
    
    def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific tool by name."""
        for tool in self.tools:
            if tool.name == name:
                return {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema or {}
                }
        return None
    
    def get_tool_display_names(self) -> List[str]:
        """Get display names for all tools."""
        return [get_display_name(tool) for tool in self.tools]