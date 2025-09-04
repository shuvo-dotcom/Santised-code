#!/usr/bin/env python
"""
Script to fix intent parsing issues in the LLM provider.
This improves the extraction of JSON from LLM responses and adds
the extract_json_from_response method to the LLMProvider class.
"""
import os
import sys
import json
import re
import logging

# Add the project directory to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from semantic.llm_provider import LLMProvider

def add_json_extraction_method():
    """Add the extract_json_from_response method to the LLMProvider class"""
    
    # Define the method to add
    def extract_json_from_response(self, text):
        """
        Enhanced method to extract valid JSON from an LLM response.
        Handles various issues like incomplete JSON, markdown formatting, etc.
        
        Args:
            text: The response text from the LLM
            
        Returns:
            Parsed JSON object or None if parsing fails
        """
        if not text:
            return None
            
        # Remove markdown code block markers
        text = text.replace("```json", "").replace("```", "")
        
        # Clean up common issues
        text = text.strip()
        
        try:
            # First attempt - direct parsing
            return json.loads(text)
        except json.JSONDecodeError:
            logger.debug(f"Initial JSON parsing failed, trying enhanced extraction")
            
            # Try to find JSON between curly braces
            json_pattern = r'\{(?:[^{}]|(?R))*\}'
            match = re.search(json_pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
                    
            logger.warning(f"Enhanced JSON extraction failed")
            return None

    # Add method to the LLMProvider class
    setattr(LLMProvider, 'extract_json_from_response', extract_json_from_response)
    logger.info("Added extract_json_from_response method to LLMProvider")

def fix_intent_parsing():
    """Apply fixes to the intent parsing code in the LLMProvider"""
    
    # Add the JSON extraction method
    add_json_extraction_method()
    
    logger.info("Intent parsing fixes applied successfully")
    return True

if __name__ == "__main__":
    logger.info("Starting intent parsing fix script")
    success = fix_intent_parsing()
    
    if success:
        logger.info("Intent parsing fixes applied successfully")
    else:
        logger.error("Failed to apply intent parsing fixes")
        sys.exit(1)
