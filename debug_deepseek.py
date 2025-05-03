#!/usr/bin/env python3
"""
Script to debug the DeepSeek LLM integration with detailed logging.
"""

import os
import sys
import json
import logging
from utils.llm_client import get_client, TextPrompt, ToolParam

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Debug the DeepSeek LLM integration with detailed logging."""
    # Set a dummy API key for testing
    os.environ["DEEPSEEK_API_KEY"] = "test_key"
    
    try:
        # Initialize the client
        logger.info("Initializing DeepSeek client...")
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
        logger.info("Attempting to generate a response from DeepSeek with tools...")
        response, metadata = client.generate(
            messages=messages,
            max_tokens=100,
            temperature=0.7,
            tools=tools
        )
        
        logger.info(f"Response: {response}")
        logger.info(f"Metadata: {metadata}")
        
        # Check if any tool calls were detected
        tool_calls = [item for item in response if hasattr(item, 'tool_name')]
        logger.info(f"Tool calls detected: {tool_calls}")
        
        # Log the raw response structure
        if 'raw_response' in metadata:
            logger.info(f"Raw response structure: {json.dumps(metadata['raw_response'], indent=2)}")
        
        return 0
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())