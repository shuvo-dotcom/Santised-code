#!/usr/bin/env python
"""
Tool to check token limits for different models.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project directory to Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Import modules with absolute paths to avoid conflicts
from semantic.llm_provider import LLMProvider

def main():
    """Test token counting for different models"""
    try:
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        models = [
            "gpt-5-mini",
            "gpt-5",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ]
        
        print("Token limits for different models:")
        print("=" * 50)
        
        for model in models:
            provider = LLMProvider(api_key=api_key, model=model)
            limits = provider.get_token_limit_info()
            
            print(f"Model: {limits['model']}")
            print(f"  - Input token limit: {limits['input_token_limit']:,}")
            print(f"  - Output token limit: {limits['output_token_limit']:,}")
            print(f"  - Model family: {limits['family']}")
            print("-" * 50)
        
        # Test token counting
        test_provider = LLMProvider(api_key=api_key, model="gpt-5-mini")
        
        sample_texts = [
            "This is a short test.",
            "This is a slightly longer test with multiple sentences. It contains more words and should use more tokens.",
            "A" * 1000,  # 1000 character string
            "A" * 10000,  # 10,000 character string
        ]
        
        print("\nToken counting examples:")
        print("=" * 50)
        
        for i, text in enumerate(sample_texts):
            token_count = test_provider.count_tokens(text)
            char_count = len(text)
            ratio = token_count / char_count if char_count > 0 else 0
            
            print(f"Sample {i+1} ({char_count} chars):")
            print(f"  - Token count: {token_count}")
            print(f"  - Tokens per character: {ratio:.2f}")
            print("-" * 50)
            
        return True
        
    except Exception as e:
        logger.error(f"Error testing token counting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting token count test")
    success = main()
    
    if success:
        logger.info("Token count test completed successfully")
        sys.exit(0)
    else:
        logger.error("Token count test failed")
        sys.exit(1)
