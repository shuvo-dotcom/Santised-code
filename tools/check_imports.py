#!/usr/bin/env python3
"""
Simple test to diagnose import issues
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
logger.info(f"Added {PROJECT_ROOT} to Python path")

def check_imports():
    """Check all imports to diagnose issues"""
    logger.info("Testing imports...")
    
    try:
        import semantic.llm_provider
        logger.info("✅ Successfully imported semantic.llm_provider")
    except ImportError as e:
        logger.error(f"❌ Failed to import semantic.llm_provider: {str(e)}")
    
    try:
        import semantic.intent_parser
        logger.info("✅ Successfully imported semantic.intent_parser")
    except ImportError as e:
        logger.error(f"❌ Failed to import semantic.intent_parser: {str(e)}")
    
    try:
        import nfg_math.equations
        logger.info("✅ Successfully imported nfg_math.equations")
    except ImportError as e:
        logger.error(f"❌ Failed to import nfg_math.equations: {str(e)}")
    
    try:
        from io import csv_store  # This will likely fail
        logger.info("✅ Successfully imported io.csv_store")
    except ImportError as e:
        logger.error(f"❌ Failed to import io.csv_store: {str(e)}")
        
        # Try with direct import
        try:
            sys.path.append(os.path.join(PROJECT_ROOT, "io"))
            import csv_store
            logger.info("✅ Successfully imported csv_store directly")
        except ImportError as e:
            logger.error(f"❌ Failed to import csv_store directly: {str(e)}")

    # Print Python path for debugging
    logger.info(f"Python path (sys.path): {sys.path}")
    
    # Check directory structure
    logger.info(f"Directory structure:")
    for root, dirs, files in os.walk(PROJECT_ROOT, topdown=True, followlinks=False):
        level = root.replace(PROJECT_ROOT, '').count(os.sep)
        indent = ' ' * 4 * (level)
        logger.info(f"{indent}{os.path.basename(root)}/")
        sub_indent = ' ' * 4 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                logger.info(f"{sub_indent}{file}")

if __name__ == "__main__":
    logger.info("Starting import diagnostics")
    check_imports()
    logger.info("Finished import diagnostics")
