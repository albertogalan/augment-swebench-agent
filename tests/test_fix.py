#!/usr/bin/env python3
"""
Script to test the fix for the Docker workspace issue.
"""

import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the fixed modules
from utils.swerex_wrapper import SWEReXWrapper, DeploymentType
from utils.file_transfer import FileTransfer

def test_file_transfer_init():
    """Test that FileTransfer initializes correctly with DeploymentType."""
    try:
        # Create a mock SWEReXWrapper
        wrapper = SWEReXWrapper(deployment_type=DeploymentType.DOCKER)
        
        # Initialize FileTransfer with the wrapper
        file_transfer = FileTransfer(swerex_wrapper=wrapper, logger=logger)
        
        logger.info("FileTransfer initialized successfully with DeploymentType")
        return True
    except Exception as e:
        logger.error(f"Error initializing FileTransfer: {e}")
        return False

def main():
    """Run the tests."""
    logger.info("Testing the fix for the Docker workspace issue")
    
    # Test FileTransfer initialization
    if test_file_transfer_init():
        logger.info("✅ FileTransfer initialization test passed")
    else:
        logger.error("❌ FileTransfer initialization test failed")
        return 1
    
    logger.info("All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())