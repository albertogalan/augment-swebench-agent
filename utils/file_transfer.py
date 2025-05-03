"""
File transfer utility for SWE-ReX environments.

This module provides functionality to transfer local directories to remote environments
while maintaining the directory structure.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Set, Union

from utils.swerex_wrapper import SWEReXWrapper, DeploymentType


class FileTransfer:
    """
    Utility class for transferring files between local and remote environments.
    """

    def __init__(
        self,
        swerex_wrapper: SWEReXWrapper,
        logger: Optional[logging.Logger] = None,
        remote_base_dir: Optional[str] = None,
        ignore_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize the file transfer utility.

        Args:
            swerex_wrapper: The SWE-ReX wrapper to use for file operations
            logger: Optional logger for file transfer operations
            remote_base_dir: Base directory in the remote environment to write files to
            ignore_patterns: Optional list of patterns to ignore (e.g., '.git', '*.pyc')
        """
        self.swerex_wrapper = swerex_wrapper
        self.logger = logger or logging.getLogger(__name__)
        
        # Set the remote base directory based on the deployment type
        if remote_base_dir is None:
            if swerex_wrapper.deployment_type == DeploymentType.DOCKER:
                self.remote_base_dir = "/workspace"
                self.logger.info("Using /workspace as remote base directory for Docker deployment")
            else:
                self.remote_base_dir = "~/workspace"
        else:
            self.remote_base_dir = remote_base_dir
            
        self.ignore_patterns = ignore_patterns or [
            ".git",
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
            ".env",
            ".venv",
            "venv",
            "env",
            "node_modules",
            ".idea",
            ".vscode",
        ]

        # Ensure remote base directory exists
        self._ensure_remote_dir_exists(self.remote_base_dir)

    def _should_ignore(self, path: str) -> bool:
        """
        Check if a path should be ignored based on ignore patterns.

        Args:
            path: Path to check against ignore patterns

        Returns:
            True if the path should be ignored, False otherwise
        """
        path_obj = Path(path)

        # Check if any part of the path matches an ignore pattern
        for pattern in self.ignore_patterns:
            # Simple exact match for directory/file names
            if pattern in path_obj.parts:
                return True

            # Wildcard pattern matching
            if pattern.startswith("*") and path_obj.suffix == pattern[1:]:
                return True

        return False

    def _ensure_remote_dir_exists(self, directory: str) -> None:
        """
        Ensure that a directory exists in the remote environment.

        Args:
            directory: Path to the directory to ensure exists
        """
        try:
            # Expand home directory to make sure we have the full path
            if directory.startswith("~"):
                # Get the home directory on the remote system
                home_dir_result = self.swerex_wrapper.run_command("echo $HOME")
                if home_dir_result["exit_code"] == 0:
                    home_dir = home_dir_result["stdout"].strip()
                    directory = directory.replace("~", home_dir, 1)

            # Create the directory if it doesn't exist
            self.swerex_wrapper.run_command(f"mkdir -p {directory}")
            self.logger.info(f"Ensured remote directory exists: {directory}")
        except Exception as e:
            self.logger.error(f"Failed to create remote directory {directory}: {e}")
            raise

    def transfer_directory(
        self, local_dir: Union[str, Path], remote_subdir: Optional[str] = None
    ) -> int:
        """
        Transfer a local directory to the remote environment.

        Args:
            local_dir: Path to the local directory to transfer
            remote_subdir: Optional subdirectory within the remote base directory

        Returns:
            The number of files transferred
        """
        local_dir_path = Path(local_dir).resolve()
        if not local_dir_path.exists() or not local_dir_path.is_dir():
            raise ValueError(f"Local directory {local_dir_path} does not exist or is not a directory")

        # Determine the remote base directory
        remote_dir = self.remote_base_dir
        if remote_subdir:
            remote_dir = os.path.join(remote_dir, remote_subdir)
            self._ensure_remote_dir_exists(remote_dir)
        elif remote_subdir is None:
            # If remote_subdir is explicitly None (not just empty), use the remote_base_dir directly
            # This is used for Docker deployments where we want to use /workspace directly
            remote_dir = self.remote_base_dir
            self._ensure_remote_dir_exists(remote_dir)

        files_transferred = 0
        self.logger.info(f"Starting transfer of {local_dir_path} to {remote_dir}")

        # Walk through the local directory
        for root, dirs, files in os.walk(local_dir_path):
            # Filter out directories to ignore
            dirs[:] = [d for d in dirs if not self._should_ignore(os.path.join(root, d))]

            # Calculate the relative path from the local base directory
            rel_path = os.path.relpath(root, local_dir_path)
            if rel_path == ".":
                rel_path = ""

            # Create the corresponding remote directory
            remote_path = os.path.join(remote_dir, rel_path) if rel_path else remote_dir
            if rel_path:
                self._ensure_remote_dir_exists(remote_path)

            # Transfer each file
            for file in files:
                if self._should_ignore(os.path.join(root, file)):
                    continue

                local_file_path = os.path.join(root, file)
                remote_file_path = os.path.join(remote_path, file)

                try:
                    # Read local file
                    with open(local_file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    # Write to remote file
                    self.swerex_wrapper.write_file(remote_file_path, content)
                    files_transferred += 1

                    if files_transferred % 10 == 0:
                        self.logger.info(f"Transferred {files_transferred} files so far...")

                except Exception as e:
                    self.logger.warning(f"Failed to transfer {local_file_path}: {e}")
                    # Continue with other files even if one fails

        self.logger.info(f"Transfer complete. {files_transferred} files transferred to {remote_dir}")
        return files_transferred

    def transfer_file(self, local_file: Union[str, Path], remote_file: str) -> bool:
        """
        Transfer a single local file to the remote environment.

        Args:
            local_file: Path to the local file to transfer
            remote_file: Path to the remote file (absolute or relative to remote base directory)

        Returns:
            True if the transfer was successful, False otherwise
        """
        local_file_path = Path(local_file).resolve()
        if not local_file_path.exists() or not local_file_path.is_file():
            raise ValueError(f"Local file {local_file_path} does not exist or is not a file")

        # If remote_file is not an absolute path, make it relative to the remote base directory
        if not remote_file.startswith("/") and not remote_file.startswith("~"):
            remote_file = os.path.join(self.remote_base_dir, remote_file)

        # Ensure the remote directory exists
        remote_dir = os.path.dirname(remote_file)
        self._ensure_remote_dir_exists(remote_dir)

        try:
            # Read local file
            with open(local_file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Write to remote file
            self.swerex_wrapper.write_file(remote_file, content)
            self.logger.info(f"Successfully transferred {local_file_path} to {remote_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to transfer {local_file_path} to {remote_file}: {e}")
            return False

    def list_remote_files(self, directory: Optional[str] = None) -> List[str]:
        """
        List files in a remote directory.

        Args:
            directory: Optional directory within the remote base directory to list

        Returns:
            List of files in the specified directory
        """
        remote_dir = self.remote_base_dir
        if directory:
            remote_dir = os.path.join(remote_dir, directory)

        try:
            result = self.swerex_wrapper.run_command(f"find {remote_dir} -type f | sort")
            if result["exit_code"] == 0:
                return result["stdout"].splitlines()
            else:
                self.logger.warning(f"Failed to list remote files: {result['stderr']}")
                return []
        except Exception as e:
            self.logger.error(f"Error listing remote files: {e}")
            return []
