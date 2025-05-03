#!/usr/bin/env python3
"""
Mock script to test the fix for the Docker workspace issue without requiring the swerex package.
"""

import os
import sys
from pathlib import Path
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock the DeploymentType enum
class MockDeploymentType(Enum):
    LOCAL = "local"
    DOCKER = "docker"
    FARGATE = "fargate"
    MODAL = "modal"

# Mock SWEReXWrapper class
class MockSWEReXWrapper:
    def __init__(self, deployment_type=MockDeploymentType.LOCAL):
        self.deployment_type = deployment_type

def test_file_transfer_import():
    """Test that the DeploymentType import is present in file_transfer.py."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), "utils", "file_transfer.py")
        with open(file_path, "r") as f:
            content = f.read()
        
        if "from utils.swerex_wrapper import SWEReXWrapper, DeploymentType" in content:
            logger.info("✅ DeploymentType import found in file_transfer.py")
            return True
        else:
            logger.error("❌ DeploymentType import not found in file_transfer.py")
            return False
    except Exception as e:
        logger.error(f"Error reading file_transfer.py: {e}")
        return False

def test_docker_workspace_creation():
    """Test that the Docker workspace creation code is present in swerex_wrapper.py."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), "utils", "swerex_wrapper.py")
        with open(file_path, "r") as f:
            content = f.read()
        
        if "mkdir -p /workspace" in content:
            logger.info("✅ Docker workspace creation code found in swerex_wrapper.py")
            return True
        else:
            logger.error("❌ Docker workspace creation code not found in swerex_wrapper.py")
            return False
    except Exception as e:
        logger.error(f"Error reading swerex_wrapper.py: {e}")
        return False

def test_docker_volume_mounting():
    """Test that the Docker volume mounting code is present in swerex_wrapper.py."""
    try:
        file_path = os.path.join(os.path.dirname(__file__), "utils", "swerex_wrapper.py")
        with open(file_path, "r") as f:
            content = f.read()
        
        if "volumes[str(self.workspace_path)] = \"/workspace\"" in content:
            logger.info("✅ Docker volume mounting code found in swerex_wrapper.py")
            return True
        else:
            logger.error("❌ Docker volume mounting code not found in swerex_wrapper.py")
            return False
    except Exception as e:
        logger.error(f"Error reading swerex_wrapper.py: {e}")
        return False

def main():
    """Run the tests."""
    logger.info("Testing the fix for the Docker workspace issue")
    
    # Test DeploymentType import
    test_file_transfer_import()
    
    # Test Docker workspace creation
    test_docker_workspace_creation()
    
    # Test Docker volume mounting
    test_docker_volume_mounting()
    
    logger.info("All tests completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())