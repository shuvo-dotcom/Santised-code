#!/usr/bin/env python
"""
Simple example to test the NFG Analytics pipeline with a query.
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import with clean path
from semantic.llm_provider import LLMProvider
from semantic.intent_parser import IntentParser

def main():
    """Run a simple example query"""
    # Get API key and model from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    
    # Initialize LLM provider
    llm = LLMProvider(api_key=api_key, model=model)
    
    # Initialize intent parser
    parser = IntentParser()
    parser.set_llm_provider(llm)
    
    # Example query
    query = "What is the LCOE for nuclear in Belgium in 2050?"
    
    logger.info(f"Parsing query: {query}")
    
    # Parse the query
    intent = parser.parse(query)
    
    logger.info(f"Parsed intent: {json.dumps(intent, indent=2)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
