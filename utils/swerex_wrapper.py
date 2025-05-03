"""
SWE-ReX integration wrapper for persistent shell environments.

This module provides integration with SWE-ReX to offer a unified approach to
executing commands in different environments (local, Docker, AWS Fargate, Modal).
"""

import asyncio
import logging
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple


# SWE-ReX imports
from swerex.deployment.abstract import AbstractDeployment
from swerex.deployment.local import LocalDeployment
from swerex.deployment.docker import DockerDeployment
from swerex.deployment.fargate import FargateDeployment
from swerex.deployment.modal import ModalDeployment
from swerex.runtime.abstract import CreateBashSessionRequest, BashAction, Command
from swerex.runtime.abstract import AbstractRuntime


class DeploymentType(Enum):
    """Supported deployment types for SWE-ReX."""
    LOCAL = "local"
    DOCKER = "docker"
    FARGATE = "fargate"
    MODAL = "modal"


class SWEReXWrapper:
    """
    Wrapper for SWE-ReX that provides a persistent shell execution environment.
    """

    def __init__(
        self,
        deployment_type: DeploymentType = DeploymentType.LOCAL,
        logger: Optional[logging.Logger] = None,
        docker_image: str = "python:3.11",
        docker_container_id: Optional[str] = None,
        workspace_path: Optional[Path] = None,
        timeout: int = 60,
    ):
        """
        Initialize the SWE-ReX wrapper.

        Args:
            deployment_type: The type of deployment to use
            logger: Optional logger for SWE-ReX operations
            docker_image: Docker image to use (for Docker deployment)
            docker_container_id: Existing Docker container ID to use (for Docker deployment)
            workspace_path: Path to the workspace (for mounting volumes)
            timeout: Command execution timeout in seconds
        """
        self.deployment_type = deployment_type
        self.logger = logger or logging.getLogger(__name__)
        self.docker_image = docker_image
        self.docker_container_id = docker_container_id
        self.workspace_path = workspace_path
        self.timeout = timeout

        self.deployment = None
        self.runtime = None
        self.default_session_id = "main"
        self.sessions = {}

        # For awaiting async operations in sync context
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def _run_async(self, coro):
        """Run an async function in the event loop."""
        return self.loop.run_until_complete(coro)

    def initialize(self) -> None:
        """Initialize the SWE-ReX deployment and runtime."""
        self.logger.info(f"Initializing SWE-ReX with deployment type: {self.deployment_type.value}")

        # Create the deployment based on the specified type
        if self.deployment_type == DeploymentType.LOCAL:
            self.deployment = LocalDeployment()
        elif self.deployment_type == DeploymentType.DOCKER:
            # Create a very basic Docker deployment with minimal parameters
            # to avoid validation errors with different SWE-ReX versions
            # Prepare docker args for volume mounts if workspace_path is provided
            docker_args = []
            if self.workspace_path:
                # Map local workspace to /workspace in the container using docker_args
                docker_args.extend(["-v", f"{self.workspace_path}:/workspace"])
                self.logger.info(f"Mounting local workspace {self.workspace_path} to /workspace in Docker container")
            
            if self.docker_container_id:
                self.deployment = DockerDeployment(
                    image=self.docker_image,
                    container_id=self.docker_container_id,
                    docker_args=docker_args
                )
            else:
                self.deployment = DockerDeployment(
                    image=self.docker_image,
                    docker_args=docker_args
                )
        elif self.deployment_type == DeploymentType.FARGATE:
            self.deployment = FargateDeployment()
        elif self.deployment_type == DeploymentType.MODAL:
            self.deployment = ModalDeployment()
        else:
            raise ValueError(f"Unsupported deployment type: {self.deployment_type}")

        # Start the deployment
        self._run_async(self.deployment.start())
        self.runtime = self.deployment.runtime

        # Initialize all sessions
        self.initialize_session(self.default_session_id)

        self.logger.info(f"SWE-ReX initialized with deployment type: {self.deployment_type.value}")

    def initialize_session(self, session_id: str) -> None:
        """
        Initialize a new shell session with the given ID.

        Args:
            session_id: ID for the new session
        """
        if session_id in self.sessions:
            return

        # Create a new bash session
        self._run_async(self.runtime.create_session(
            CreateBashSessionRequest(session_id=session_id)
        ))

        # Set up the session with appropriate environment
        # Set up a more consistent bash environment
        cmds = [
            "unset PROMPT_COMMAND",  # Remove any prompt command
            "stty -onlcr",  # Improve terminal handling
            "export PS1='SHELLPS1PREFIX'",  # Set a simple prompt for easier parsing
        ]

        # Execute the setup commands
        for cmd in cmds:
            self._run_async(self.runtime.run_in_session(
                BashAction(command=cmd, session_id=session_id)
            ))

        # Set the working directory - Check if it exists first
        if self.workspace_path:
            # For local deployment, use the actual path
            if self.deployment_type == DeploymentType.LOCAL:
                try:
                    self._run_async(self.runtime.run_in_session(
                        BashAction(command=f"cd {self.workspace_path}", session_id=session_id)
                    ))
                except Exception as e:
                    self.logger.warning(f"Failed to change directory to {self.workspace_path}: {e}")
            # For Docker deployment, use /workspace
            elif self.deployment_type == DeploymentType.DOCKER:
                try:
                    # Create /workspace directory if it doesn't exist
                    self._run_async(self.runtime.run_in_session(
                        BashAction(command="mkdir -p /workspace", session_id=session_id)
                    ))
                    self.logger.info("Created /workspace directory for Docker deployment")
                    
                    # Always use /workspace for Docker
                    self._run_async(self.runtime.run_in_session(
                        BashAction(command="cd /workspace", session_id=session_id)
                    ))
                    self.logger.info("Changed working directory to /workspace for Docker deployment")
                except Exception as e:
                    self.logger.warning(f"Failed to change directory to /workspace: {e}")
            # For other remote deployments, we can't assume a specific path exists
            # Instead, try to create a directory if needed
            else:
                try:
                    # Test if a default location like /workspace exists
                    result = self._run_async(self.runtime.run_in_session(
                        BashAction(command="[ -d /workspace ] && echo exists", session_id=session_id)
                    ))

                    if result.output.strip() == "exists":
                        self._run_async(self.runtime.run_in_session(
                            BashAction(command="cd /workspace", session_id=session_id)
                        ))
                    else:
                        # Try to create a workspace directory
                        self._run_async(self.runtime.run_in_session(
                            BashAction(command="mkdir -p ~/workspace && cd ~/workspace", session_id=session_id)
                        ))
                except Exception as e:
                    self.logger.warning(f"Failed to set workspace directory: {e}")

        self.sessions[session_id] = True

    def shutdown(self) -> None:
        """Stop the SWE-ReX deployment."""
        if self.deployment:
            try:
                self._run_async(self.deployment.stop())
                self.logger.info("SWE-ReX deployment stopped")
            except Exception as e:
                self.logger.warning(f"Error stopping SWE-ReX deployment: {e}")

    def run_command(
        self,
        command: str,
        session_id: str = "main",
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run a command in a persistent shell session.

        Args:
            command: The command to run
            session_id: The session ID to run the command in
            timeout: Optional timeout override

        Returns:
            Dictionary with stdout, stderr, and exit_code
        """
        if not self.runtime:
            raise RuntimeError("SWE-ReX runtime not initialized. Call initialize() first.")

        # Ensure the session exists
        if session_id not in self.sessions:
            self.initialize_session(session_id)

        # Set timeout for the operation
        actual_timeout = timeout or self.timeout

        try:
            # Run the command in the session
            result = self._run_async(self.runtime.run_in_session(
                BashAction(command=command, session_id=session_id, timeout=actual_timeout)
            ))

            # Match the expected output format of the original BashTool
            return {
                "stdout": result.output,
                "stderr": "",  # SWE-ReX combines stdout and stderr
                "exit_code": result.exit_code,
            }
        except asyncio.TimeoutError:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": 124,  # Standard timeout exit code
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "exit_code": 1,
            }

    def execute_one_off_command(
        self,
        command: List[str],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a one-off command (not in a persistent session).

        Args:
            command: The command to execute as a list of strings
            timeout: Optional timeout override

        Returns:
            Dictionary with stdout, stderr, and exit_code
        """
        if not self.runtime:
            raise RuntimeError("SWE-ReX runtime not initialized. Call initialize() first.")

        # Set timeout for the operation
        actual_timeout = timeout or self.timeout

        try:
            # Execute a one-off command
            result = self._run_async(self.runtime.execute(
                Command(command=command, timeout=actual_timeout)
            ))

            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
            }
        except asyncio.TimeoutError:
            return {
                "stdout": "",
                "stderr": "Command timed out",
                "exit_code": 124,  # Standard timeout exit code
            }
        except Exception as e:
            return {
                "stdout": "",
                "stderr": f"Error executing command: {str(e)}",
                "exit_code": 1,
            }

    def reset_session(self, session_id: str = "main") -> bool:
        """
        Reset a session to a clean state.

        Args:
            session_id: The session ID to reset

        Returns:
            True if reset was successful, False otherwise
        """
        if not self.runtime:
            return False

        try:
            # Delete the session if it exists
            if session_id in self.sessions:
                del self.sessions[session_id]

            # Create a new session with the same ID
            self.initialize_session(session_id)
            return True
        except Exception as e:
            self.logger.warning(f"Error resetting session {session_id}: {e}")
            return False

    def get_container_id(self) -> Optional[str]:
        """
        Get the ID of the Docker container that SWE-ReX is using.

        Returns:
            The container ID, or None if not applicable
        """
        if self.deployment_type == DeploymentType.DOCKER and self.deployment:
            # Access the container ID from the DockerDeployment
            if hasattr(self.deployment, 'container_id'):
                return self.deployment.container_id
        return None

    def read_file(self, file_path: Union[str, Path]) -> str:
        """
        Read a file from the deployment environment.

        Args:
            file_path: Path to the file to read

        Returns:
            The contents of the file as a string
        """
        path_str = str(file_path)
        file_content = self._run_async(self.runtime.read_file(path_str))
        return file_content.decode('utf-8')

    def write_file(self, file_path: Union[str, Path], content: str) -> None:
        """
        Write content to a file in the deployment environment.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file
        """
        path_str = str(file_path)
        self._run_async(self.runtime.write_file(path_str, content.encode('utf-8')))
