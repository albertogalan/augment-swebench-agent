#!/usr/bin/env python3
"""
Script to test the command-line arguments in cli.py.
"""

import os
import sys
import argparse

def main():
    """Test the command-line arguments in cli.py."""
    # Define the same arguments as in cli.py
    parser = argparse.ArgumentParser(description="CLI for interacting with the Agent")
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Path to the workspace",
    )

    # Create a mutually exclusive group for problem input
    problem_group = parser.add_mutually_exclusive_group()
    problem_group.add_argument(
        "--problem-statement",
        type=str,
        default=None,
        help="Problem statement to pass to the agent. Makes the agent non-interactive.",
    )
    problem_group.add_argument(
        "--problem-file",
        type=str,
        default=None,
        help="Path to a file containing the problem statement. Makes the agent non-interactive.",
    )

    parser.add_argument(
        "--logs-path",
        type=str,
        default="agent_logs.txt",
        help="Path to save logs",
    )
    parser.add_argument(
        "--needs-permission",
        "-p",
        help="Ask for permission before executing commands",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--use-container-workspace",
        type=str,
        default=None,
        help="(Optional) Path to the container workspace to run commands in.",
    )
    parser.add_argument(
        "--docker-container-id",
        type=str,
        default=None,
        help="(Optional) Docker container ID to run commands in.",
    )
    parser.add_argument(
        "--minimize-stdout-logs",
        help="Minimize the amount of logs printed to stdout.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--llm",
        type=str,
        choices=["claude", "openai", "deepseek"],
        default="claude",
        help="LLM to use (default: claude). Available options: claude, openai, deepseek",
    )
    parser.add_argument(
        "--no-caching",
        help="Disable caching of LLM requests",
        action="store_true",
        default=False,
    )

    # Parse the arguments
    args = parser.parse_args()
    
    # Print the parsed arguments
    print(f"Parsed arguments: {args}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())