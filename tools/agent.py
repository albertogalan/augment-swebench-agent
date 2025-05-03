"""
Agent implementation with integrated file transfer capability for remote environments.

This implementation extends the Agent class with file transfer capabilities
using SWE-ReX for remote execution.
"""

from copy import deepcopy
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
import os

from tools.bash_tool import create_bash_tool, create_docker_bash_tool, create_swerex_bash_tool
from utils.common import (
    DialogMessages,
    LLMTool,
    ToolImplOutput,
)
from utils.llm_client import LLMClient, TextResult
from utils.workspace_manager import WorkspaceManager
from utils.swerex_wrapper import SWEReXWrapper, DeploymentType
from utils.file_transfer import FileTransfer
from tools.complete_tool import CompleteTool
from prompts.system_prompt import SYSTEM_PROMPT
from tools.str_replace_tool import StrReplaceEditorTool
from tools.sequential_thinking_tool import SequentialThinkingTool
from termcolor import colored
from rich.console import Console
import logging


class Agent(LLMTool):
    """Agent with file transfer capability for remote environments."""

    name = "general_agent"
    description = """\
A general agent that can accomplish tasks and answer questions.

If you are faced with a task that involves more than a few steps, or if the task is complex, or if the instructions are very long,
try breaking down the task into smaller steps and call this tool multiple times.
"""
    input_schema = {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "The instruction to the agent.",
            },
        },
        "required": ["instruction"],
    }

    def _get_system_prompt(self):
        """Get the system prompt, including any pending messages.

        Returns:
            The system prompt with messages prepended if any
        """

        return SYSTEM_PROMPT.format(
            workspace_root=self.workspace_manager.root,
        )

    def __init__(
        self,
        client: LLMClient,
        workspace_manager: WorkspaceManager,
        console: Console,
        logger_for_agent_logs: logging.Logger,
        max_output_tokens_per_turn: int = 8192,
        max_turns: int = 10,
        use_prompt_budgeting: bool = True,
        ask_user_permission: bool = False,
        docker_container_id: Optional[str] = None,
        use_swerex: bool = False,
        swerex_deployment_type: str = "local",
        swerex_docker_image: str = "python:3.11",
        auto_transfer_workspace: bool = True,
    ):
        """Initialize the agent.

        Args:
            client: The LLM client to use
            workspace_manager: Workspace manager for taking snapshots
            console: Console for output
            logger_for_agent_logs: Logger for agent logs
            max_output_tokens_per_turn: Maximum tokens per turn
            max_turns: Maximum number of turns
            use_prompt_budgeting: Whether to use prompt budgeting
            ask_user_permission: Whether to ask user permission before executing commands
            docker_container_id: Docker container ID to use (legacy approach)
            use_swerex: Whether to use SWE-ReX for command execution
            swerex_deployment_type: SWE-ReX deployment type (local, docker, fargate, modal)
            swerex_docker_image: Docker image to use (for SWE-ReX Docker deployment)
            auto_transfer_workspace: Automatically transfer workspace to remote environment
        """
        super().__init__()
        self.client = client
        self.console = console
        self.logger_for_agent_logs = logger_for_agent_logs
        self.max_output_tokens = max_output_tokens_per_turn
        self.max_turns = max_turns
        self.workspace_manager = workspace_manager
        self.interrupted = False
        self.dialog = DialogMessages(
            logger_for_agent_logs=logger_for_agent_logs,
            use_prompt_budgeting=use_prompt_budgeting,
        )
        self.auto_transfer_workspace = auto_transfer_workspace

        # Create and store the complete tool
        self.complete_tool = CompleteTool()

        # Initialize SWE-ReX if requested
        self.use_swerex = use_swerex
        self.swerex_wrapper = None
        self.file_transfer = None

        bash_tool = None
        if use_swerex:
            # Convert string deployment type to enum
            try:
                deployment_type = DeploymentType(swerex_deployment_type)
            except ValueError:
                deployment_type = DeploymentType.LOCAL
                logger_for_agent_logs.warning(
                    f"Invalid SWE-ReX deployment type: {swerex_deployment_type}. Using LOCAL instead."
                )

            # Initialize SWE-ReX wrapper
            self.swerex_wrapper = SWEReXWrapper(
                deployment_type=deployment_type,
                logger=logger_for_agent_logs,
                docker_image=swerex_docker_image,
                docker_container_id=docker_container_id,
                workspace_path=workspace_manager.root,
            )

            # Initialize SWE-ReX deployment
            self.swerex_wrapper.initialize()

            # Set up file transfer utility
            self.file_transfer = FileTransfer(
                swerex_wrapper=self.swerex_wrapper,
                logger=logger_for_agent_logs,
            )

            # Automatically transfer workspace if requested
            if auto_transfer_workspace and workspace_manager.root:
                self._transfer_workspace()

            # Use SWE-ReX bash tool
            bash_tool = create_swerex_bash_tool(
                self.swerex_wrapper,
                ask_user_permission=ask_user_permission,
                cwd=workspace_manager.root,
            )
            logger_for_agent_logs.info(
                f"Initialized SWE-ReX with deployment type: {deployment_type.value}"
            )

            # If using Docker deployment, get the container ID for compatibility
            if deployment_type == DeploymentType.DOCKER:
                self.docker_container_id = self.swerex_wrapper.get_container_id()
                logger_for_agent_logs.info(
                    f"SWE-ReX Docker container ID: {self.docker_container_id}"
                )
            else:
                self.docker_container_id = None
        elif docker_container_id is not None:
            # Legacy Docker approach (using command filter)
            print(
                colored(
                    f"Enabling docker bash tool with container {docker_container_id}",
                    "blue",
                )
            )
            self.logger_for_agent_logs.info(
                f"Enabling docker bash tool with container {docker_container_id}"
            )
            bash_tool = create_docker_bash_tool(
                container=docker_container_id,
                ask_user_permission=ask_user_permission,
                cwd=workspace_manager.root,
            )
            self.docker_container_id = docker_container_id
        else:
            # Local bash tool (default)
            bash_tool = create_bash_tool(
                ask_user_permission=ask_user_permission,
                cwd=workspace_manager.root,
            )
            self.docker_container_id = None

        # Initialize tools
        self.tools = [
            bash_tool,
            StrReplaceEditorTool(workspace_manager=workspace_manager),
            SequentialThinkingTool(),
            self.complete_tool,
        ]

    def _transfer_workspace(self) -> None:
        """
        Transfer the workspace to the remote environment.
        """
        if not self.file_transfer or not self.workspace_manager.root:
            return

        try:
            self.logger_for_agent_logs.info(
                f"Transferring workspace {self.workspace_manager.root} to remote environment..."
            )

            # Create a remote directory for the workspace
            remote_workspace_name = os.path.basename(self.workspace_manager.root)
            if not remote_workspace_name or remote_workspace_name == ".":
                remote_workspace_name = "workspace"

            # Determine the remote workspace path based on deployment type
            if self.swerex_wrapper and self.swerex_wrapper.deployment_type == DeploymentType.DOCKER:
                # For Docker, use /workspace
                remote_workspace_path = "/workspace"
                remote_subdir = None  # No subdirectory needed
                self.logger_for_agent_logs.info(
                    f"Using Docker deployment with workspace at {remote_workspace_path}"
                )
            else:
                # For other deployments, use ~/workspace/remote_workspace_name
                remote_workspace_path = os.path.join("~/workspace", remote_workspace_name)
                remote_subdir = remote_workspace_name

            # Transfer the directory
            files_transferred = self.file_transfer.transfer_directory(
                self.workspace_manager.root,
                remote_subdir=remote_subdir
            )

            self.logger_for_agent_logs.info(
                f"Workspace transfer complete. {files_transferred} files transferred."
            )

            # Update the path in the SWE-ReX bash sessions to point to the transferred workspace
            if self.swerex_wrapper:
                self.swerex_wrapper.run_command(f"cd {remote_workspace_path}")
                self.logger_for_agent_logs.info(
                    f"Changed remote working directory to {remote_workspace_path}"
                )

        except Exception as e:
            self.logger_for_agent_logs.error(f"Failed to transfer workspace: {e}")

    def transfer_files(self, local_paths: List[Union[str, Path]], remote_dir: Optional[str] = None) -> int:
        """
        Transfer files to the remote environment.

        Args:
            local_paths: List of local files or directories to transfer
            remote_dir: Optional remote directory to transfer to

        Returns:
            Number of files transferred
        """
        if not self.file_transfer:
            raise RuntimeError("File transfer is not available. Agent must be initialized with use_swerex=True.")

        total_files = 0
        for path in local_paths:
            path_obj = Path(path)
            if path_obj.is_dir():
                files = self.file_transfer.transfer_directory(path, remote_dir)
                total_files += files
            elif path_obj.is_file():
                remote_path = os.path.join(remote_dir or "~/workspace", path_obj.name) if remote_dir else path_obj.name
                success = self.file_transfer.transfer_file(path, remote_path)
                if success:
                    total_files += 1

        return total_files

    def run_impl(
        self,
        tool_input: Dict[str, Any],
        dialog_messages: Optional[DialogMessages] = None,
    ) -> ToolImplOutput:
        instruction = tool_input["instruction"]

        user_input_delimiter = "-" * 45 + " USER INPUT " + "-" * 45 + "\n" + instruction
        self.logger_for_agent_logs.info(f"\n{user_input_delimiter}\n")

        # print("Agent starting with instruction:", instruction)

        # Add instruction to dialog before getting mode
        self.dialog.add_user_prompt(instruction)
        self.interrupted = False

        remaining_turns = self.max_turns
        while remaining_turns > 0:
            remaining_turns -= 1

            delimiter = "-" * 45 + " NEW TURN " + "-" * 45
            self.logger_for_agent_logs.info(f"\n{delimiter}\n")

            if self.dialog.use_prompt_budgeting:
                current_tok_count = self.dialog.count_tokens()
                self.logger_for_agent_logs.info(
                    f"(Current token count: {current_tok_count})\n"
                )

            # Get tool parameters for available tools
            tool_params = [tool.get_tool_param() for tool in self.tools]

            # Check for duplicate tool names
            tool_names = [param.name for param in tool_params]
            sorted_names = sorted(tool_names)
            for i in range(len(sorted_names) - 1):
                if sorted_names[i] == sorted_names[i + 1]:
                    raise ValueError(f"Tool {sorted_names[i]} is duplicated")

            try:
                model_response, metadata = self.client.generate(
                    messages=self.dialog.get_messages_for_llm_client(),
                    max_tokens=self.max_output_tokens,
                    tools=tool_params,
                    system_prompt=self._get_system_prompt(),
                )
                self.dialog.add_model_response(model_response)

                # Handle tool calls
                pending_tool_calls = self.dialog.get_pending_tool_calls()

                if len(pending_tool_calls) == 0:
                    # No tools were called, so assume the task is complete
                    self.logger_for_agent_logs.info("[no tools were called]")
                    return ToolImplOutput(
                        tool_output=self.dialog.get_last_model_text_response(),
                        tool_result_message="Task completed",
                    )

                if len(pending_tool_calls) > 1:
                    raise ValueError("Only one tool call per turn is supported")

                assert len(pending_tool_calls) == 1
                tool_call = pending_tool_calls[0]

                text_results = [
                    item for item in model_response if isinstance(item, TextResult)
                ]
                if len(text_results) > 0:
                    text_result = text_results[0]
                    self.logger_for_agent_logs.info(
                        f"Top-level agent planning next step: {text_result.text}\n",
                    )

                try:
                    tool = next(t for t in self.tools if t.name == tool_call.tool_name)
                except StopIteration as exc:
                    raise ValueError(
                        f"Tool with name {tool_call.tool_name} not found"
                    ) from exc

                try:
                    result = tool.run(tool_call.tool_input, deepcopy(self.dialog))

                    tool_input_str = "\n".join(
                        [f" - {k}: {v}" for k, v in tool_call.tool_input.items()]
                    )
                    log_message = f"Calling tool {tool_call.tool_name} with input:\n{tool_input_str}"
                    log_message += f"\nTool output: \n{result}\n\n"
                    self.logger_for_agent_logs.info(log_message)

                    # Handle both ToolResult objects and tuples
                    if isinstance(result, tuple):
                        tool_result, _ = result
                    else:
                        tool_result = result

                    self.dialog.add_tool_call_result(tool_call, tool_result)

                    if self.complete_tool.should_stop:
                        # Add a fake model response, so the next turn is the user's
                        # turn in case they want to resume
                        self.dialog.add_model_response(
                            [TextResult(text="Completed the task.")]
                        )
                        return ToolImplOutput(
                            tool_output=self.complete_tool.answer,
                            tool_result_message="Task completed",
                        )
                except KeyboardInterrupt:
                    # Handle interruption during tool execution
                    self.interrupted = True
                    interrupt_message = "Tool execution was interrupted by user."
                    self.dialog.add_tool_call_result(tool_call, interrupt_message)
                    self.dialog.add_model_response(
                        [
                            TextResult(
                                text="Tool execution interrupted by user. You can resume by providing a new instruction."
                            )
                        ]
                    )
                    return ToolImplOutput(
                        tool_output=interrupt_message,
                        tool_result_message=interrupt_message,
                    )

            except KeyboardInterrupt:
                # Handle interruption during model generation or other operations
                self.interrupted = True
                self.dialog.add_model_response(
                    [
                        TextResult(
                            text="Agent interrupted by user. You can resume by providing a new instruction."
                        )
                    ]
                )
                return ToolImplOutput(
                    tool_output="Agent interrupted by user",
                    tool_result_message="Agent interrupted by user",
                )

        agent_answer = "Agent did not complete after max turns"
        return ToolImplOutput(
            tool_output=agent_answer, tool_result_message=agent_answer
        )

    def get_tool_start_message(self, tool_input: Dict[str, Any]) -> str:
        return f"Agent started with instruction: {tool_input['instruction']}"

    def run_agent(
        self,
        instruction: str,
        resume: bool = False,
        orientation_instruction: Optional[str] = None,
    ) -> str:
        """Start a new agent run.

        Args:
            instruction: The instruction to the agent.
            resume: Whether to resume the agent from the previous state,
                continuing the dialog.
            orientation_instruction: Optional orientation instruction.

        Returns:
            A tuple of (result, message).
        """
        self.complete_tool.reset()
        if resume:
            assert self.dialog.is_user_turn()
        else:
            self.dialog.clear()
            self.interrupted = False

        tool_input = {
            "instruction": instruction,
        }
        if orientation_instruction:
            tool_input["orientation_instruction"] = orientation_instruction
        return self.run(tool_input, self.dialog)

    def clear(self):
        self.dialog.clear()
        self.interrupted = False

    def __del__(self):
        """Cleanup SWE-ReX resources when the agent is destroyed."""
        if hasattr(self, 'swerex_wrapper') and self.swerex_wrapper is not None:
            try:
                self.swerex_wrapper.shutdown()
            except Exception as e:
                if hasattr(self, 'logger_for_agent_logs'):
                    self.logger_for_agent_logs.warning(f"Error shutting down SWE-ReX: {e}")
