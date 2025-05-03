#!/usr/bin/env python3
"""
Script to test the Agent with DeepSeek LLM.
"""

import os
import sys
from rich.console import Console
import logging
from utils.llm_client import get_client
from utils.workspace_manager import WorkspaceManager
from tools.agent import Agent

def main():
    """Test the Agent with DeepSeek LLM."""
    # Set a dummy API key for testing and enable debug mode
    os.environ["DEEPSEEK_API_KEY"] = "test_key"
    os.environ["DEEPSEEK_DEBUG"] = "1"
    
    try:
        # Initialize console
        console = Console()
        
        # Set up logging
        logger = logging.getLogger("agent_logs")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())
        
        # Initialize the client
        print("Initializing DeepSeek client...")
        client = get_client("deepseek-direct", model_name="deepseek-coder-v2", use_caching=False)
        
        # Initialize workspace manager
        workspace_manager = WorkspaceManager(root=".")
        
        # Initialize agent
        agent = Agent(
            client=client,
            workspace_manager=workspace_manager,
            console=console,
            logger_for_agent_logs=logger,
            max_output_tokens_per_turn=32768,
            max_turns=200,
        )
        
        # Run the agent
        print("Running agent with DeepSeek LLM...")
        result = agent.run_agent("Write a simple Python function to calculate the factorial of a number")
        
        print(f"Agent result: {result}")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())