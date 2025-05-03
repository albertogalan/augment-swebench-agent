#!/usr/bin/env python3
"""
Test script for SWEReXWrapper with Docker deployment.
"""

import os
import logging
from pathlib import Path
from utils.swerex_wrapper import SWEReXWrapper, DeploymentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_swerex_wrapper")

# Create a test workspace
workspace_path = Path("./test_workspace")
os.makedirs(workspace_path, exist_ok=True)

# Initialize SWEReXWrapper with Docker deployment
logger.info("Initializing SWEReXWrapper with Docker deployment")
wrapper = SWEReXWrapper(
    deployment_type=DeploymentType.DOCKER,
    logger=logger,
    workspace_path=workspace_path,
)

try:
    # Initialize the deployment
    logger.info("Initializing deployment")
    wrapper.initialize()
    logger.info("Deployment initialized successfully")
    
    # Run a simple command to verify it works
    logger.info("Running command: ls -la /workspace")
    result = wrapper.run_command("ls -la /workspace")
    logger.info(f"Command output: {result['stdout']}")
    
    # Verify the exit code
    if result["exit_code"] == 0:
        logger.info("Command executed successfully")
    else:
        logger.error(f"Command failed with exit code {result['exit_code']}")
        logger.error(f"Error: {result['stderr']}")
    
finally:
    # Shutdown the deployment
    logger.info("Shutting down deployment")
    wrapper.shutdown()
    logger.info("Deployment shut down successfully")

logger.info("Test completed successfully")