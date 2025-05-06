#!/usr/bin/env python3
"""
Test script for interactive environments in SWEReXWrapper.
"""

import os
import logging
from pathlib import Path
from utils.swerex_wrapper import SWEReXWrapper, DeploymentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_interactive_env")

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
    
    # Start an interactive Python environment
    logger.info("Starting interactive Python environment")
    result = wrapper.start_interactive_environment(environment_type="python")
    logger.info(f"Start result: {result}")
    
    # Send a command to the interactive environment
    logger.info("Sending command to interactive environment")
    result = wrapper.send_to_interactive_environment("print('Hello from interactive Python!')")
    logger.info(f"Command result: {result}")
    
    # Send another command
    logger.info("Sending another command")
    result = wrapper.send_to_interactive_environment("import sys; print(sys.version)")
    logger.info(f"Command result: {result}")
    
    # Quit the interactive environment
    logger.info("Quitting interactive environment")
    result = wrapper.quit_interactive_environment()
    logger.info(f"Quit result: {result}")
    
    # Try starting a different interactive environment
    logger.info("Starting interactive IPython environment")
    result = wrapper.start_interactive_environment(environment_type="ipython")
    if result["exit_code"] == 0:
        logger.info(f"IPython started successfully: {result}")
        
        # Send a command to IPython
        logger.info("Sending command to IPython")
        result = wrapper.send_to_interactive_environment("print('Hello from IPython!')")
        logger.info(f"Command result: {result}")
        
        # Quit IPython
        logger.info("Quitting IPython")
        result = wrapper.quit_interactive_environment()
        logger.info(f"Quit result: {result}")
    else:
        logger.warning(f"Failed to start IPython: {result}")
    
finally:
    # Shutdown the deployment
    logger.info("Shutting down deployment")
    wrapper.shutdown()
    logger.info("Deployment shut down successfully")

logger.info("Test completed successfully")