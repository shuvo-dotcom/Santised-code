#!/usr/bin/env python3
"""
Entry script for NFG Analytics Orchestrator.
Starts the FastAPI server for the NFG Analytics API.
"""
import os
import sys
import uvicorn
import logging
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.getLevelName(os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting NFG Analytics API on port {port}")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("OPENAI_API_KEY environment variable not set. LLM functionality will be limited.")
    
    # Check if data folder exists
    data_folder = os.getenv("DATA_FOLDER", "./data")
    if not os.path.exists(data_folder):
        logger.warning(f"Data folder not found: {data_folder}. Creating empty directory.")
        os.makedirs(data_folder, exist_ok=True)
    
    # Start the FastAPI server
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENV", "production").lower() == "development"
    )
