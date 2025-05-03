#!/usr/bin/env python3
"""
CLI interface for the Agent.

This script provides a command-line interface for interacting with the Agent.
It instantiates an Agent and prompts the user for input, which is then passed to the Agent.
"""

import os
import argparse
from pathlib import Path
import sys
import logging

from rich.console import Console
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

from tools.agent import Agent
from utils.workspace_manager import WorkspaceManager
from utils.llm_client import get_client
from prompts.instruction import INSTRUCTION_PROMPT

# Default token limits for different LLM providers
ANTHROPIC_MAX_TOKENS = 32768
DEEPSEEK_MAX_TOKENS = 8192
OPENAI_MAX_TOKENS = 4096
MAX_TURNS = 50


def main():
    """Main entry point for the CLI."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="CLI for interacting with the Agent")
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Path to the workspace",
    )

    # Problem statement group (mutually exclusive)
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

    # SWE-ReX options - avoid nesting argument groups
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

    # Legacy Docker options - avoid nesting argument groups
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
        help="Minimize the amount of logs printed to stdout",
        action="store_true",
        default=False,
    )

    # LLM options
    llm_group = parser.add_argument_group("Language Model")
    llm_group.add_argument(
        "--llm",
        type=str,
        default="anthropic",
        choices=["anthropic", "deepseek", "openai"],
        help="LLM provider to use (anthropic, deepseek, or openai)",
    )
    llm_group.add_argument(
        "--model",
        type=str,
        default=None,
        help="Specific model to use (overrides default for selected LLM provider)",
    )
    llm_group.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum number of tokens for model output (provider-specific default if not specified)",
    )

    args = parser.parse_args()

    # Set up logging
    if os.path.exists(args.logs_path):
        os.remove(args.logs_path)
    logger_for_agent_logs = logging.getLogger("agent_logs")
    logger_for_agent_logs.setLevel(logging.DEBUG)
    logger_for_agent_logs.addHandler(logging.FileHandler(args.logs_path))
    if not args.minimize_stdout_logs:
        logger_for_agent_logs.addHandler(logging.StreamHandler())
    else:
        logger_for_agent_logs.propagate = False

    # Check if appropriate API key is set based on LLM choice
    if args.llm == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it to your Anthropic API key.")
        sys.exit(1)
    elif args.llm == "deepseek" and "DEEPSEEK_API_KEY" not in os.environ:
        print("Error: DEEPSEEK_API_KEY environment variable is not set.")
        print("Please set it to your DeepSeek API key.")
        sys.exit(1)
    elif args.llm == "openai" and "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it to your OpenAI API key.")
        sys.exit(1)

    # Initialize console
    console = Console()

    # Set default model based on provider
    if args.model is None:
        if args.llm == "anthropic":
            model_name = "claude-3-7-sonnet-20250219"
        elif args.llm == "deepseek":
            model_name = "deepseek-coder"
        elif args.llm == "openai":
            model_name = "gpt-4o-2024-05-13"
        else:
            model_name = "claude-3-7-sonnet-20250219"  # Default fallback
    else:
        model_name = args.model

    # Set max tokens based on provider if not specified
    if args.max_tokens is None:
        if args.llm == "anthropic":
            max_tokens = ANTHROPIC_MAX_TOKENS
        elif args.llm == "deepseek":
            max_tokens = DEEPSEEK_MAX_TOKENS
        elif args.llm == "openai":
            max_tokens = OPENAI_MAX_TOKENS
        else:
            max_tokens = ANTHROPIC_MAX_TOKENS  # Default fallback
    else:
        max_tokens = args.max_tokens

    # Print welcome message with execution environment information
    env_info = f"LLM: {args.llm} (model: {model_name}, max tokens: {max_tokens})"
    if args.use_swerex:
        env_info += f"\nExecution: SWE-ReX ({args.swerex_deployment})"
        if args.swerex_deployment == "docker":
            env_info += f", image: {args.swerex_docker_image}"
    elif args.docker_container_id:
        env_info += f"\nExecution: Docker (container: {args.docker_container_id})"
    else:
        env_info += "\nExecution: Local"

    if not args.minimize_stdout_logs:
        console.print(
            Panel(
                f"[bold]Agent CLI[/bold]\n\n{env_info}\n\n"
                + "Type your instructions to the agent. Press Ctrl+C to exit.\n"
                + "Type 'exit' or 'quit' to end the session.",
                title="[bold blue]Agent CLI[/bold blue]",
                border_style="blue",
                padding=(1, 2),
            )
        )
    else:
        logger_for_agent_logs.info(
            f"Agent CLI started. {env_info}. "
            "Waiting for user input. Press Ctrl+C to exit. Type 'exit' or 'quit' to end the session."
        )

    # Initialize LLM client based on provider choice
    client = None
    if args.llm == "anthropic":
        client = get_client(
            "anthropic-direct",
            model_name=model_name,
            use_caching=True,
        )
    elif args.llm == "deepseek":
        try:
            # Try to import from the module if installed
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            try:
                from deepseek_client import get_deepseek_client
                client = get_deepseek_client(model_name=model_name)
                logger_for_agent_logs.info(f"Using DeepSeek model: {model_name}")
            except ImportError:
                # Fall back to local import
                import importlib.util
                spec = importlib.util.spec_from_file_location("deepseek_client", "deepseek_client.py")
                if spec is None or spec.loader is None:
                    raise ImportError("Could not find deepseek_client.py")
                deepseek_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(deepseek_module)
                client = deepseek_module.get_deepseek_client(model_name=model_name)
                logger_for_agent_logs.info(f"Using DeepSeek model from local file: {model_name}")
        except Exception as e:
            logger_for_agent_logs.error(f"DeepSeek API error: {str(e)}")
            console.print(f"[bold red]DeepSeek API error: {str(e)}[/bold red]")
            console.print("[yellow]Using mock response for testing[/yellow]")

            # Create a simple mock client for testing
            from utils.llm_client import LLMClient, TextResult

            class MockClient(LLMClient):
                def generate(self, messages, max_tokens, system_prompt=None, temperature=0.0, tools=[], tool_choice=None, thinking_tokens=None):
                    return [TextResult(text="This is a mock response for testing.")], {"tokens": 0}

            client = MockClient()
    elif args.llm == "openai":
        client = get_client(
            "openai-direct",
            model_name=model_name,
        )
    else:
        # Default fallback to Anthropic
        client = get_client(
            "anthropic-direct",
            model_name=model_name,
            use_caching=True,
        )

    if client is None:
        console.print(f"[bold red]Failed to initialize LLM client for {args.llm}[/bold red]")
        sys.exit(1)

    # Initialize workspace manager
    workspace_path = Path(args.workspace).resolve()

    # Set container_workspace to /workspace for SWE-ReX Docker deployment
    container_workspace = args.use_container_workspace
    if args.use_swerex and args.swerex_deployment == "docker":
        container_workspace = "/workspace"
        logger_for_agent_logs.info("Using /workspace as container workspace for SWE-ReX Docker deployment")

    workspace_manager = WorkspaceManager(
        root=workspace_path, container_workspace=container_workspace
    )

    # Initialize agent with SWE-ReX if specified
    agent = Agent(
        client=client,
        workspace_manager=workspace_manager,
        console=console,
        logger_for_agent_logs=logger_for_agent_logs,
        max_output_tokens_per_turn=max_tokens,
        max_turns=MAX_TURNS,
        ask_user_permission=args.needs_permission,
        # If using SWE-ReX, pass those parameters
        use_swerex=args.use_swerex,
        swerex_deployment_type=args.swerex_deployment,
        swerex_docker_image=args.swerex_docker_image,
        # Only use docker_container_id if SWE-ReX is not used
        docker_container_id=None if args.use_swerex else args.docker_container_id,
    )

    # Determine the problem statement
    problem_statement = None
    if args.problem_statement is not None:
        problem_statement = args.problem_statement
    elif args.problem_file is not None:
        try:
            problem_file_path = Path(args.problem_file)
            if not problem_file_path.exists():
                console.print(f"[bold red]Error: Problem file not found: {args.problem_file}[/bold red]")
                sys.exit(1)
            problem_statement = problem_file_path.read_text()
            console.print(f"[green]Successfully loaded problem statement from {args.problem_file}[/green]")
        except Exception as e:
            console.print(f"[bold red]Error reading problem file: {str(e)}[/bold red]")
            sys.exit(1)

    # Format the instruction if we have a problem statement
    if problem_statement is not None:
        instruction = INSTRUCTION_PROMPT.format(
            location=(
                workspace_path
                if args.use_container_workspace is None
                else args.use_container_workspace
            ),
            pr_description=problem_statement,
        )
    else:
        instruction = None

    history = InMemoryHistory()
    # Main interaction loop
    try:
        while True:
            # Get user input
            if instruction is None:
                user_input = prompt("User input: ", history=history)
                history.append_string(user_input)

                # Check for exit commands
                if user_input.lower() in ["exit", "quit"]:
                    console.print("[bold]Exiting...[/bold]")
                    logger_for_agent_logs.info("Exiting...")
                    break
            else:
                user_input = instruction
                logger_for_agent_logs.info(
                    f"User instruction:\n{user_input}\n-------------"
                )

            # Run the agent with the user input
            logger_for_agent_logs.info("\nAgent is thinking...")
            try:
                result = agent.run_agent(user_input, resume=True)
                logger_for_agent_logs.info(f"Agent: {result}")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                logger_for_agent_logs.error(error_msg)
                console.print(f"[bold red]{error_msg}[/bold red]")

            logger_for_agent_logs.info("\n" + "-" * 40 + "\n")

            if instruction is not None:
                break

    except KeyboardInterrupt:
        console.print("\n[bold]Session interrupted. Exiting...[/bold]")

    console.print("[bold]Goodbye![/bold]")


if __name__ == "__main__":
    main()
