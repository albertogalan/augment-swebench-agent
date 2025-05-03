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
    # Execution environment options
    execution_group = parser.add_argument_group("Execution Environment")

    # SWE-ReX options
    swerex_group = parser.add_argument_group("SWE-ReX options")
    swerex_group.add_argument(
        "--use-swerex",
        action="store_true",
        default=False,
        help="Use SWE-ReX for command execution",
    )
    swerex_group.add_argument(
        "--swerex-deployment",
        type=str,
        choices=["local", "docker", "fargate", "modal"],
        default="local",
        help="SWE-ReX deployment type",
    )
    swerex_group.add_argument(
        "--swerex-docker-image",
        type=str,
        default="python:3.11",
        help="Docker image to use with SWE-ReX Docker deployment",
    )

    # Legacy Docker options
    docker_group = parser.add_argument_group("Legacy Docker options (ignored if using SWE-ReX)")
    docker_group.add_argument(
        "--use-container-workspace",
        type=str,
        default=None,
        help="Path to the container workspace to run commands in",
    )
    docker_group.add_argument(
        "--docker-container-id",
        type=str,
        default=None,
        help="Docker container ID to run commands in",
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