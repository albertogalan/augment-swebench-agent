#!/usr/bin/env python3
"""
Example script demonstrating how to use interactive environments with SWEReXWrapper.
"""

import os
import logging
from pathlib import Path
from utils.swerex_wrapper import SWEReXWrapper, DeploymentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("example_interactive_env")

def main():
    # Create a workspace
    workspace_path = Path("./workspace")
    os.makedirs(workspace_path, exist_ok=True)

    # Initialize SWEReXWrapper
    logger.info("Initializing SWEReXWrapper")
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
        
        # Send commands to the interactive environment
        commands = [
            "print('Hello from interactive Python!')",
            "import sys",
            "print(sys.version)",
            "a = 10",
            "b = 20",
            "print(f'a + b = {a + b}')"
        ]
        
        for cmd in commands:
            logger.info(f"Sending command: {cmd}")
            result = wrapper.send_to_interactive_environment(cmd)
            logger.info(f"Result: {result}")
        
        # Quit the interactive environment
        logger.info("Quitting interactive environment")
        result = wrapper.quit_interactive_environment()
        logger.info(f"Quit result: {result}")
        
        # Start a different interactive environment (IPython)
        logger.info("Starting interactive IPython environment")
        result = wrapper.start_interactive_environment(environment_type="ipython")
        if result["exit_code"] == 0:
            logger.info(f"IPython started successfully: {result}")
            
            # Send commands to IPython
            ipython_commands = [
                "%matplotlib inline",
                "import numpy as np",
                "np.random.rand(5)",
                "exit"  # This will exit IPython
            ]
            
            for cmd in ipython_commands:
                logger.info(f"Sending command to IPython: {cmd}")
                result = wrapper.send_to_interactive_environment(cmd)
                logger.info(f"Result: {result}")
        else:
            logger.warning(f"Failed to start IPython: {result}")
        
    finally:
        # Shutdown the deployment
        logger.info("Shutting down deployment")
        wrapper.shutdown()
        logger.info("Deployment shut down successfully")

if __name__ == "__main__":
    main()