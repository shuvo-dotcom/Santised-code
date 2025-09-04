#!/usr/bin/env python
"""
Test script to verify LLM parameter handling for different models
"""
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Import the LLM provider
from semantic.llm_provider import LLMProvider

def main():
    """Test the LLM provider with different models."""
    logger.info("Starting LLM parameter handling test")
    logger.info(f"Using OpenAI API key: {openai_api_key[:3]}{'*' * (len(openai_api_key) - 6)}{openai_api_key[-3:]}")
    
    # Create a provider instance
    logger.info("Creating LLM provider instance...")
    provider = LLMProvider()
    
    # Test with GPT-5-mini
    test_gpt5_parameters(provider)

def test_gpt5_parameters(provider):
    """Test specifically how GPT-5-mini parameters are handled."""
    # Set the model to GPT-5-mini
    provider.set_model("gpt-5-mini")
    logger.info(f"Set model to: {provider.model}")
    
    # Create test cases with different parameter combinations
    test_cases = [
        {
            "name": "default_params",
            "params": {}
        },
        {
            "name": "with_max_tokens",
            "params": {"max_tokens": 100}
        },
        {
            "name": "with_temperature",
            "params": {"temperature": 0.7}
        },
        {
            "name": "with_both_params",
            "params": {"max_tokens": 100, "temperature": 0.7}
        }
    ]
    
    # Test each case without actually making API calls
    for case in test_cases:
        try:
            logger.info(f"Testing case: {case['name']}")
            
            # Create a monkey-patched version of the API call to inspect parameters
            original_chat_completions_create = None
            
            # Store the parameters that would be sent to the API
            captured_params = {}
            
            # Define mock function
            def mock_chat_completions_create(*args, **kwargs):
                nonlocal captured_params
                captured_params = kwargs.copy()
                # Don't actually make the API call
                class MockResponse:
                    class MockChoice:
                        class MockMessage:
                            content = "Mock response"
                        message = MockMessage()
                    choices = [MockChoice()]
                return MockResponse()
            
            # Apply monkey patch based on API version
            if hasattr(provider, 'client') and hasattr(provider.client, 'chat'):
                # New OpenAI API
                original_chat_completions_create = provider.client.chat.completions.create
                provider.client.chat.completions.create = mock_chat_completions_create
            else:
                # Old OpenAI API
                original_chat_completions_create = provider.client.ChatCompletion.create
                provider.client.ChatCompletion.create = mock_chat_completions_create
            
            # Make the call
            prompt = "Test prompt"
            provider.complete(prompt, **case['params'])
            
            # Log the captured parameters
            logger.info(f"Parameters after processing: {captured_params}")
            
            # Verify parameter handling for GPT-5-mini
            if "max_tokens" in case['params'] and "max_completion_tokens" in captured_params:
                logger.info(f"✅ max_tokens correctly converted to max_completion_tokens: {captured_params['max_completion_tokens']}")
            elif "max_tokens" in case['params']:
                logger.info(f"❌ max_tokens NOT converted to max_completion_tokens")
                
            if "temperature" in case['params'] and "temperature" not in captured_params:
                logger.info(f"✅ temperature parameter correctly removed for GPT-5-mini")
            elif "temperature" in case['params']:
                logger.info(f"❌ temperature parameter was NOT removed for GPT-5-mini")
            
            # Restore original function
            if hasattr(provider, 'client') and hasattr(provider.client, 'chat'):
                provider.client.chat.completions.create = original_chat_completions_create
            else:
                provider.client.ChatCompletion.create = original_chat_completions_create
                
        except Exception as e:
            logger.error(f"Error in test case {case['name']}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    logger.info("GPT-5-mini parameter handling test completed")

if __name__ == "__main__":
    main()
