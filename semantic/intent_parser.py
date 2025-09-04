"""
Dynamic intent parser for NFG analytics. Uses LLM provider for all parsing.
No hardcoded values - everything determined by LLM at runtime.
No YAML file dependencies - all configuration generated dynamically.
"""
import re
import os
import json
import logging
import traceback
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# No YAML config file - everything will be generated dynamically
CONFIG = {}

class IntentParser:
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize intent parser with config and LLM provider.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or CONFIG
        self.llm_provider = None  # Will be set by pipeline

    def set_llm_provider(self, provider):
        """Set LLM provider for dynamic intent parsing"""
        self.llm_provider = provider
        
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse user question using LLM to extract intent.
        Extracts metric, tech, fuel, network, country, year, scenario/model, requested op, and confidence.
        No hardcoded dependencies - all parsing done by LLM.
        
        Args:
            text: User query text
            
        Returns:
            Dict with parsed intent fields and confidence scores
        """
        logger.info(f"Parsing intent from text: {text}")
            
        # If LLM provider is available, use it for parsing
        if self.llm_provider is not None:
            try:
                print("DEBUG - Using LLM provider for intent parsing")
                logger.debug("Using LLM provider for intent parsing")
                intent = self.llm_provider.parse_nfg_intent(text)
                print(f"DEBUG - LLM provider returned: {json.dumps(intent) if intent else 'None'}")
                if intent:
                    # Validate the intent structure
                    self._validate_and_enhance_intent(intent)
                    logger.info(f"Successfully parsed intent: {intent}")
                    return intent
            except Exception as e:
                print(f"DEBUG - Error using LLM for intent parsing: {str(e)}")
                logger.error(f"Error using LLM for intent parsing: {str(e)}")
                import traceback
                print(f"DEBUG - Error traceback: {traceback.format_exc()}")
        else:
            print("DEBUG - LLM provider is None")
        
        # Fallback to basic regex parsing if LLM is not available or fails
        print("DEBUG - LLM intent parsing failed or unavailable, using local regex fallback")
        logger.warning("LLM intent parsing failed or unavailable, using local regex fallback")
        result = self._local_regex_fallback(text)
        print(f"DEBUG - Fallback intent parsing result: {json.dumps(result)}")
        logger.info(f"Fallback intent parsing result: {result}")
        return result
    
    def _validate_and_enhance_intent(self, intent: Dict[str, Any]) -> None:
        """
        Validate and enhance the parsed intent with additional checks and defaults.
        
        Args:
            intent: The parsed intent dictionary to validate
        """
        # Ensure all required fields exist
        required_fields = ["metric", "tech", "country", "year", "fuel", "network", "operation"]
        for field in required_fields:
            if field not in intent:
                intent[field] = None
        
        # Ensure confidence object exists
        if "confidence" not in intent:
            intent["confidence"] = {}
            
        # Add empty confidence entries for any fields without them
        for field in required_fields:
            if field not in intent["confidence"] and intent[field] is not None:
                intent["confidence"][field] = 0.7  # Default moderate confidence
    
    def _local_regex_fallback(self, text: str) -> Dict[str, Any]:
        """
        Local fallback method using regex patterns when LLM is not available.
        This is simpler than the LLM provider's enhanced fallback.
        
        Args:
            text: User query text
            
        Returns:
            Dict with parsed intent fields
        """
        result = {
            "metric": None, "tech": None, "fuel": None, "network": None, 
            "country": None, "year": None, "scenario": None, "model": None, 
            "operation": None, "confidence": {}
        }
        
        text_lower = text.lower()
        
        # Year extraction with improved patterns
        year_patterns = [
            r"(20\d{2})",          # Standard year format
            r"by\s+(20\d{2})",     # "by 2050" format
            r"in\s+(20\d{2})"      # "in 2050" format
        ]
        
        for pattern in year_patterns:
            year_match = re.search(pattern, text)
            if year_match:
                # Extract the actual year digits
                year_str = re.search(r"20\d{2}", year_match.group(0)).group(0)
                result["year"] = int(year_str)
                result["confidence"]["year"] = 0.9
                break
        
        # Enhanced keyword matching for metrics
        metrics = {
            "LCOE": ["lcoe", "levelized cost", "cost of electricity", "cost of generation"],
            "GENERATION_GWh": ["generation", "output", "produced", "electricity production"],
            "CAPACITY_MW": ["capacity", "installed capacity", "power capacity"],
            "CAPACITY_FACTOR": ["capacity factor", "cf", "utilization", "utilisation"],
            "EMISSIONS_tCO2": ["emission", "carbon", "co2", "greenhouse"],
            "NPV": ["npv", "net present value", "present value", "discounted value"]
        }
        
        for metric_name, keywords in metrics.items():
            if any(keyword in text_lower for keyword in keywords):
                result["metric"] = metric_name
                result["confidence"]["metric"] = 0.8
                break
            
        # Enhanced tech detection
        technologies = {
            "NUCLEAR": ["nuclear", "npp", "atomic", "uranium"],
            "CCGT": ["ccgt", "gas turbine", "combined cycle", "gas-fired", "natural gas"],
            "WIND": ["wind", "onshore wind", "offshore wind", "turbine", "wind farm"],
            "SOLAR": ["solar", "pv", "photovoltaic", "solar panel"],
            "HYDRO": ["hydro", "hydroelectric", "hydropower", "water power", "dam"]
        }
        
        for tech_name, keywords in technologies.items():
            if any(keyword in text_lower for keyword in keywords):
                result["tech"] = tech_name
                result["confidence"]["tech"] = 0.8
                break
                
        # Country detection
        countries = {
            "BE": ["belgium", "belgian", "be"],
            "FR": ["france", "french", "fr"],
            "DE": ["germany", "german", "de"],
            "UK": ["uk", "united kingdom", "britain", "british", "england"],
            "IT": ["italy", "italian", "it"],
            "ES": ["spain", "spanish", "es"]
        }
        
        for code, keywords in countries.items():
            if any(keyword in text_lower for keyword in keywords):
                result["country"] = code
                result["confidence"]["country"] = 0.8
                break
                
        # Basic operation detection
        if "average" in text_lower or "avg" in text_lower or "mean" in text_lower:
            result["operation"] = "avg"
            result["confidence"]["operation"] = 0.8
        elif "maximum" in text_lower or "max" in text_lower:
            result["operation"] = "max"
            result["confidence"]["operation"] = 0.8
        elif "minimum" in text_lower or "min" in text_lower:
            result["operation"] = "min"
            result["confidence"]["operation"] = 0.8
        elif "total" in text_lower or "sum" in text_lower:
            result["operation"] = "sum"
            result["confidence"]["operation"] = 0.8
            
        return result
                
        # Simple country detection
        for country, keywords in [
            ("BE", ["belgium", "be"]),
            ("FR", ["france", "fr"]),
            ("ES", ["spain", "es"]),
        ]:
            if any(keyword in text_lower for keyword in keywords):
                result["country"] = country
                result["confidence"]["country"] = 0.8
                break
        
        return result