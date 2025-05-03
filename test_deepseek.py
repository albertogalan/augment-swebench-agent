#!/usr/bin/env python3
"""
Simple test script for DeepSeek client.

This script tests the DeepSeek client implementation without requiring any tools.
"""

import os
import sys
import logging
from deepseek_client import get_deepseek_client
from utils.llm_client import TextPrompt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_deepseek():
    """Test the DeepSeek client implementation."""
    # Check for DeepSeek API key
    if "DEEPSEEK_API_KEY" not in os.environ:
        logger.error("DEEPSEEK_API_KEY environment variable is not set.")
        print("Error: DEEPSEEK_API_KEY environment variable is not set.")
        print("Please set it to your DeepSeek API key.")
        sys.exit(1)

    # Initialize client
    client = get_deepseek_client(model_name="deepseek-chat")

    # Create a simple prompt
    messages = [[TextPrompt(text="Say hello in 5 different languages")]]

    # Generate a response
    try:
        logger.info("Sending request to DeepSeek API...")
        response, metadata = client.generate(
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )

        # Print the response
        logger.info("Response received from DeepSeek API")
        logger.info(f"Input tokens: {metadata['input_tokens']}")
        logger.info(f"Output tokens: {metadata['output_tokens']}")

        # Print each response message
        for msg in response:
            if hasattr(msg, 'text'):
                print(f"DeepSeek response: {msg.text}")
            else:
                print(f"DeepSeek response (non-text): {msg}")

        return True

    except Exception as e:
        logger.error(f"Error testing DeepSeek client: {str(e)}")
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_deepseek()
    if result:
        print("DeepSeek client test successful!")
    else:
        print("DeepSeek client test failed.")
        sys.exit(1)
