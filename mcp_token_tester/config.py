"""Configuration management for MCP servers."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""
    
    name: str = Field(..., description="Human-readable name for the server")
    server_type: str = Field(..., description="Type of server: 'stdio', 'http', or 'sse'")
    command: Optional[str] = Field(None, description="Command to run for stdio servers")
    path: Optional[str] = Field(None, description="Path to executable for stdio servers")
    args: List[str] = Field(default_factory=list, description="Arguments for the server")
    url: Optional[str] = Field(None, description="URL for HTTP servers")
    auto_start: bool = Field(True, description="Auto-start server when connecting")
    env_vars: Dict[str, str] = Field(default_factory=dict, description="Environment variables")


class MCPConfig(BaseModel):
    """Root configuration containing all MCP servers."""
    
    servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    default_server: Optional[str] = Field(None, description="Default server to use")
    token_overhead: int = Field(100, description="Default token overhead estimate")


class ConfigManager:
    """Manages MCP server configurations."""
    
    def __init__(self, config_path: Union[str, Path] = "mcp_config.json"):
        self.config_path = Path(config_path)
        self.config = MCPConfig()
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    self.config = MCPConfig(**data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"Error loading config: {e}")
                self.config = MCPConfig()
    
    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config.model_dump(), f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def add_server(self, server_config: MCPServerConfig) -> None:
        """Add a new server configuration."""
        self.config.servers[server_config.name] = server_config
        if not self.config.default_server:
            self.config.default_server = server_config.name
        self.save_config()
    
    def remove_server(self, name: str) -> bool:
        """Remove a server configuration."""
        if name in self.config.servers:
            del self.config.servers[name]
            if self.config.default_server == name:
                self.config.default_server = next(iter(self.config.servers.keys()), None)
            self.save_config()
            return True
        return False
    
    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by name."""
        return self.config.servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all configured server names."""
        return list(self.config.servers.keys())
    
    def get_default_server(self) -> Optional[MCPServerConfig]:
        """Get the default server configuration."""
        if self.config.default_server:
            return self.config.servers.get(self.config.default_server)
        return None
    
    def set_default_server(self, name: str) -> bool:
        """Set the default server."""
        if name in self.config.servers:
            self.config.default_server = name
            self.save_config()
            return True
        return False