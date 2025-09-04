#!/usr/bin/env python
"""
Full pipeline test for the NFG Analytics Orchestrator
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
project_id = os.getenv("OPENAI_PROJECT_ID")

# Import components
from semantic.llm_provider import LLMProvider
from engine.pipeline import Pipeline

def main():
    """Full pipeline test"""
    try:
        logger.info("Starting full pipeline test")
        logger.info(f"Using OpenAI API key: {openai_api_key[:3]}{'*' * (len(openai_api_key) - 6)}{openai_api_key[-3:]}")
        logger.info(f"Using model: {model}")
        logger.info(f"Using project ID: {project_id}")
        
        # Initialize the pipeline
        try:
            logger.info("Initializing Pipeline...")
            
            # Check that the data directory exists
            csv_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            logger.info(f"Data folder path: {csv_folder}")
            if os.path.exists(csv_folder):
                logger.info(f"Data folder exists, contains: {os.listdir(csv_folder)}")
            else:
                logger.error(f"Data folder does not exist: {csv_folder}")
                raise FileNotFoundError(f"Data folder does not exist: {csv_folder}")
            
            # Initialize the LLM provider
            logger.info("Initializing LLM provider...")
            provider = LLMProvider(model=model)
            logger.info(f"LLM provider initialized with model: {provider.model}")
            
            # Initialize the pipeline
            logger.info("Initializing Analytics Pipeline...")
            pipeline = Pipeline(csv_folder=csv_folder, api_key=openai_api_key, model=model)
            logger.info("Pipeline initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        
        # Example query
        query = "calculate LCOE for nuclear generations in Belgium 2030"
        logger.info(f"Running query: {query!r}")
        
        # Run the query
        try:
            logger.info("Calling answer_query...")
            result = pipeline.answer_query(query)
            
            # Save result to a file
            with open("pipeline_test_output.json", "w") as f:
                json.dump(result, f, indent=2)
            
            # Pretty print the result
            logger.info("Query result:")
            logger.info(f"Result saved to pipeline_test_output.json")
        except Exception as e:
            logger.error(f"Failed to run query: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        print(f"Exiting with code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Unhandled exception: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
