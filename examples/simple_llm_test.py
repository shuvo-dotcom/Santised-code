#!/usr/bin/env python
"""
Simple test of the LLM provider.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

# Import the LLM provider
from semantic.llm_provider import LLMProvider

def main():
    """Simple LLM test"""
    try:
        logger.info("Starting simple LLM test")
        logger.info(f"Using model: {model}")
        
        # Initialize the LLM provider
        provider = LLMProvider(model=model)
        logger.info("Provider initialized successfully")
        
        # Make a simple API call
        prompt = "What is the capital of France?"
        logger.info(f"Making API call with prompt: {prompt}")
        
        response = provider.complete(prompt)
        
        # Save response to a file
        with open("llm_test_output.txt", "w") as f:
            f.write(f"Response from {model}:\n\n{response}")
            
        logger.info(f"Received response (first 50 chars): {response[:50]}...")
        logger.info(f"Full response saved to llm_test_output.txt")
        logger.info("Test completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
