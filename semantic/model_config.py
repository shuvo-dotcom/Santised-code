"""
Model configuration management for the NFG Analytics Orchestrator.
Contains configuration for different LLM models including parameter support.
"""
from typing import Dict, List, Any, Set

class ModelConfig:
    """Configuration for LLM models"""
    
    # Model families and their characteristics
    MODEL_FAMILIES = {
        "gpt-5": {
            "supports_temperature": False,
            "token_param": "max_completion_tokens",
        },
        "gpt-4": {
            "supports_temperature": True,
            "token_param": "max_tokens",
        },
        "gpt-3.5": {
            "supports_temperature": True, 
            "token_param": "max_tokens",
        },
        "claude": {
            "supports_temperature": True,
            "token_param": "max_tokens",
        }
    }
    
    @classmethod
    def get_model_family(cls, model_name: str) -> str:
        """Determine the model family from the model name"""
        for family in cls.MODEL_FAMILIES:
            if model_name.startswith(family):
                return family
        return "default"
    
    @classmethod
    def supports_temperature(cls, model_name: str) -> bool:
        """Check if the model supports temperature parameter"""
        family = cls.get_model_family(model_name)
        return cls.MODEL_FAMILIES.get(family, {}).get("supports_temperature", True)
    
    @classmethod
    def get_token_param(cls, model_name: str) -> str:
        """Get the appropriate token parameter name for the model"""
        family = cls.get_model_family(model_name)
        return cls.MODEL_FAMILIES.get(family, {}).get("token_param", "max_tokens")
    
    @classmethod
    def transform_params(cls, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Transform parameters to be compatible with the specified model"""
        # Create a copy to avoid modifying the original
        transformed = params.copy()
        
        # Handle token parameter
        token_param = cls.get_token_param(model_name)
        if token_param != "max_tokens" and "max_tokens" in transformed:
            transformed[token_param] = transformed.pop("max_tokens")
        
        # Handle temperature parameter
        if not cls.supports_temperature(model_name) and "temperature" in transformed:
            transformed.pop("temperature")
            
        return transformed
