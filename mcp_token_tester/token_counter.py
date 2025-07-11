"""Token counting functionality for various LLM providers."""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol

from anthropic import Anthropic
from anthropic.types import MessageParam


class TokenCounter(Protocol):
    """Protocol for token counting implementations."""
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in the given text."""
        ...
    
    def count_message_tokens(self, messages: list) -> int:
        """Count tokens in a list of messages."""
        ...


class AnthropicTokenCounter:
    """Token counter for Anthropic models."""
    
    def __init__(self, model: str = "claude-3-sonnet-20240229", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        if api_key:
            self.client = Anthropic(api_key=api_key)
        else:
            self.client = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using Anthropic's API."""
        if not self.client:
            print("Warning: Anthropic API key not provided. Token counting disabled.")
            return len(text.split()) * 1.3  # Rough estimate: ~1.3 tokens per word
        
        try:
            messages: list[MessageParam] = [{"role": "user", "content": text}]
            response = self.client.messages.count_tokens(
                model=self.model,
                messages=messages
            )
            return response.input_tokens
        except Exception as e:
            print(f"Error counting tokens: {e}")
            print("Tip: Set ANTHROPIC_API_KEY environment variable for accurate token counting")
            return len(text.split()) * 1.3  # Fallback to rough estimate
    
    def count_message_tokens(self, messages: list) -> int:
        """Count tokens in a list of messages."""
        if not self.client:
            print("Warning: Anthropic API key not provided. Token counting disabled.")
            # Rough estimate based on message content
            total_text = ""
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg:
                    total_text += str(msg["content"]) + " "
            return len(total_text.split()) * 1.3
        
        try:
            response = self.client.messages.count_tokens(
                model=self.model,
                messages=messages
            )
            return response.input_tokens
        except Exception as e:
            print(f"Error counting message tokens: {e}")
            print("Tip: Set ANTHROPIC_API_KEY environment variable for accurate token counting")
            # Fallback to rough estimate
            total_text = ""
            for msg in messages:
                if isinstance(msg, dict) and "content" in msg:
                    total_text += str(msg["content"]) + " "
            return len(total_text.split()) * 1.3


class TokenCounterFactory:
    """Factory for creating token counters."""
    
    # Model mapping for user-friendly names to API identifiers
    ANTHROPIC_MODELS = {
        'claude-opus-4': 'claude-opus-4-20250514',
        'claude-sonnet-4': 'claude-sonnet-4-20250514', 
        'claude-sonnet-3.7': 'claude-3-7-sonnet-20250219',
        'claude-sonnet-3.5': 'claude-3-5-sonnet-20241022',
        'claude-haiku-3.5': 'claude-3-5-haiku-20241022',
        'claude-haiku-3': 'claude-3-haiku-20240307',
        'claude-opus-3': 'claude-3-opus-20240229',
        # Direct API names are also supported
        'claude-opus-4-20250514': 'claude-opus-4-20250514',
        'claude-sonnet-4-20250514': 'claude-sonnet-4-20250514',
        'claude-3-7-sonnet-20250219': 'claude-3-7-sonnet-20250219',
        'claude-3-5-sonnet-20241022': 'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku-20241022': 'claude-3-5-haiku-20241022',
        'claude-3-haiku-20240307': 'claude-3-haiku-20240307',
        'claude-3-opus-20240229': 'claude-3-opus-20240229',
    }
    
    @staticmethod
    def create_counter(provider: str, model: str, api_key: Optional[str] = None) -> TokenCounter:
        """Create a token counter for the specified provider."""
        if provider.lower() == "anthropic":
            # Map user-friendly model names to API identifiers
            api_model = TokenCounterFactory.ANTHROPIC_MODELS.get(model.lower(), model)
            return AnthropicTokenCounter(model=api_model, api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")


class TokenAnalyzer:
    """Analyzes token costs for MCP tool calls."""
    
    def __init__(self, counter: TokenCounter, overhead_tokens: int = 100):
        self.counter = counter
        self.overhead_tokens = overhead_tokens
    
    def analyze_tool_call(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any], 
        tool_response: Dict[str, Any]
    ) -> Dict[str, int]:
        """Analyze token costs for a complete tool call."""
        
        # Count input tokens (tool name + arguments + overhead)
        input_text = f"Tool: {tool_name}\nArguments: {json.dumps(tool_args, indent=2)}"
        input_tokens = self.counter.count_tokens(input_text) + self.overhead_tokens
        
        # Count response tokens
        response_text = json.dumps(tool_response, indent=2)
        response_tokens = self.counter.count_tokens(response_text)
        
        # Calculate totals
        total_tokens = input_tokens + response_tokens
        
        return {
            "input_tokens": input_tokens,
            "response_tokens": response_tokens,
            "total_tokens": total_tokens,
            "overhead_tokens": self.overhead_tokens
        }
    
    def set_overhead(self, overhead: int) -> None:
        """Set the overhead token count."""
        self.overhead_tokens = overhead