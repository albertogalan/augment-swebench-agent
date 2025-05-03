#!/usr/bin/env python3
"""
Script to test workspace path handling with Docker deployment.
"""

import os
from pathlib import Path
from utils.workspace_manager import WorkspaceManager

def main():
    """Test workspace path handling with Docker deployment."""
    # Test with local workspace
    local_workspace = Path("/Users/agalan/data/src/wk/augment-improved").resolve()
    print(f"Local workspace: {local_workspace}")
    
    # Test with container workspace set to /workspace (Docker)
    container_workspace = "/workspace"
    
    # Initialize workspace manager
    workspace_manager = WorkspaceManager(
        root=local_workspace, container_workspace=container_workspace
    )
    
    # Test path translations
    test_paths = [
        Path("file.txt"),  # Relative path
        Path("/Users/agalan/data/src/wk/augment-improved/file.txt"),  # Absolute path in local workspace
        Path("/other/path/file.txt"),  # Absolute path outside local workspace
    ]
    
    print("\nPath translations:")
    for path in test_paths:
        local_path = workspace_manager.workspace_path(path)
        container_path = workspace_manager.container_path(path)
        print(f"Original: {path}")
        print(f"  Local: {local_path}")
        print(f"  Container: {container_path}")
        print()
    
    return 0

if __name__ == "__main__":
    main()