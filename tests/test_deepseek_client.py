#!/usr/bin/env python3
"""
Script to test the DeepSeekDirectClient directly.
"""

import os
import sys
import json
from utils.llm_client import get_client, TextPrompt, ToolParam

def main():
    """Test the DeepSeekDirectClient directly."""
    # Set a dummy API key for testing and enable debug mode
    os.environ["DEEPSEEK_API_KEY"] = "test_key"
    os.environ["DEEPSEEK_DEBUG"] = "1"
    
    try:
        # Initialize the client
        print("Initializing DeepSeek client...")
        client = get_client("deepseek-direct", model_name="deepseek-coder-v2", use_caching=False)
        
        # Create a simple message
        messages = [[TextPrompt("Write a Python function to calculate factorial")]]
        
        # Create a simple tool
        tools = [
            ToolParam(
                name="bash",
                description="Run a bash command",
                input_schema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to run"
                        }
                    },
                    "required": ["command"]
                }
            )
        ]
        
        # Try to generate a response
        print("Attempting to generate a response from DeepSeek with tools...")
        response, metadata = client.generate(
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            tools=tools
        )
        
        print(f"Response: {response}")
        print(f"Metadata: {metadata}")
        
        # Check if any tool calls were detected
        tool_calls = [item for item in response if hasattr(item, 'tool_name')]
        print(f"Tool calls detected: {tool_calls}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())