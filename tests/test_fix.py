#!/usr/bin/env python3
"""
Script to test the fix for DeepSeek LLM integration in cli.py.
"""

import os
import subprocess
import sys

def main():
    """Test the fix for DeepSeek LLM integration."""
    # Set a dummy API key for testing and enable debug mode
    os.environ["DEEPSEEK_API_KEY"] = "test_key"
    os.environ["DEEPSEEK_DEBUG"] = "1"
    
    # Run the CLI with DeepSeek LLM
    cmd = ["python", "cli.py", "--llm", "deepseek", "--problem-statement", "Write a simple Python function to calculate the factorial of a number"]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("\nSTDOUT:")
    print(result.stdout)
    
    print("\nSTDERR:")
    print(result.stderr)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())