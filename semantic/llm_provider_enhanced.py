"""
Add enhanced methods to the LLMProvider class to support the enhanced pipeline v2.
These methods provide dynamic information for tech mappings, country mappings,
metric information, and property mappings.
"""
import logging
import json
import re
import sys
from typing import Dict, Any, List, Optional, Union

# Configure basic logging to stdout for debugging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    stream=sys.stdout)

# Import the LLMProvider
from semantic.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

def extract_json_from_response(response_text: str) -> Union[Dict, List, None]:
    """
    Extract JSON from an LLM response with robust error handling.
    
    Args:
        response_text: The raw text response from the LLM
        
    Returns:
        Parsed JSON object or None if parsing failed
    """
    # Clean the response text
    text = response_text.strip()
    
    # Try to find JSON with code block markers
    if "```json" in text:
        # Extract content between ```json and ```
        match = re.search(r'```json\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1).strip()
    elif "```" in text:
        # Extract content between ``` and ```
        match = re.search(r'```\s*([\s\S]*?)\s*```', text)
        if match:
            text = match.group(1).strip()
    
    # Try to find a JSON object in the text
    object_match = re.search(r'(\{[\s\S]*\})', text)
    array_match = re.search(r'(\[[\s\S]*\])', text)
    
    json_str = None
    if object_match:
        json_str = object_match.group(1)
    elif array_match:
        json_str = array_match.group(1)
    
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON: {e}")
            
            # Try to fix common JSON formatting issues
            try:
                # Replace single quotes with double quotes
                fixed_str = json_str.replace("'", '"')
                return json.loads(fixed_str)
            except json.JSONDecodeError:
                pass
                
            # Try more aggressive fixes
            try:
                # Fix unquoted keys
                fixed_str = re.sub(r'([{,])\s*(\w+):', r'\1"\2":', json_str)
                return json.loads(fixed_str)
            except json.JSONDecodeError:
                logger.warning("Failed to fix and parse JSON after multiple attempts")
    
    logger.warning(f"No valid JSON found in response: {response_text[:100]}...")
    return None

def get_tech_mappings(self) -> Dict[str, List[str]]:
    """
    Get technology mappings from LLM knowledge.
    
    Returns:
        Dictionary mapping canonical tech names to patterns in CSV
    """
    if not self.api_key:
        logger.warning("No API key available for getting tech mappings.")
        return {}
    
    try:
        system_prompt = """You are an energy systems expert. 
Provide mappings between canonical technology names and patterns that might appear in CSV files.
Respond with a JSON dictionary where keys are canonical names and values are lists of pattern strings."""

        user_prompt = """Please provide mappings between these canonical technology names and patterns:
- NUCLEAR
- WIND
- SOLAR
- HYDRO
- CCGT
- COAL
- OIL
- BIOMASS
- GEOTHERMAL

For example, "NUCLEAR" might map to ["Nuclear", "nuclear power", "nuclear energy"].
Respond with ONLY a JSON dictionary, no explanation."""

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = self.complete(combined_prompt)
        
        # Extract and parse JSON using our robust extraction function
        tech_map = extract_json_from_response(response_text)
        if tech_map:
            return tech_map
        else:
            logger.warning("Could not extract tech mappings JSON from LLM response")
                
    except Exception as e:
        logger.error(f"Error getting tech mappings from LLM: {str(e)}")
    
    # Return empty dictionary if failed
    return {}

def get_country_mappings(self) -> Dict[str, str]:
    """
    Get country code mappings from LLM knowledge.
    
    Returns:
        Dictionary mapping canonical country codes to codes in CSV
    """
    if not self.api_key:
        logger.warning("No API key available for getting country mappings.")
        return {}
    
    try:
        system_prompt = """You are an energy systems expert. 
Provide mappings between canonical country codes and codes that might appear in CSV files.
Respond with a JSON dictionary where keys are canonical codes and values are codes in CSV."""

        user_prompt = """Please provide mappings between these canonical country codes and codes in CSV:
- BE (Belgium)
- FR (France)
- DE (Germany)
- UK (United Kingdom)
- ES (Spain)
- IT (Italy)
- NL (Netherlands)
- PL (Poland)
- PT (Portugal)
- NO (Norway)

Respond with ONLY a JSON dictionary, no explanation."""

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = self.complete(combined_prompt)
        
        # Extract and parse JSON using our robust extraction function
        country_map = extract_json_from_response(response_text)
        if country_map:
            return country_map
        else:
            logger.warning("Could not extract country mappings JSON from LLM response")
                
    except Exception as e:
        logger.error(f"Error getting country mappings from LLM: {str(e)}")
    
    # Return empty dictionary if failed
    return {}

def get_metric_info(self) -> Dict[str, Dict[str, Any]]:
    """
    Get metric information including full names and formatting specifications.
    
    Returns:
        Dictionary with metric information
    """
    if not self.api_key:
        logger.warning("No API key available for getting metric information.")
        return {}
    
    try:
        system_prompt = """You are an energy systems expert. 
Provide information about energy system metrics including full names, formatting specifications, and descriptions.
Respond with a JSON dictionary where keys are metric names and values are dictionaries with full_name, format, and description."""

        user_prompt = """Please provide information about these metrics:
- LCOE
- CAPACITY_FACTOR
- EMISSIONS_INTENSITY
- CAPEX
- OPEX
- TOTAL_GEN_COST
- CAPACITY_VALUE

Each metric should have:
1. full_name: The full name of the metric
2. format: A Python format string like "{:.2f}" for 2 decimal places or "{:.1%}" for percentage
3. description: A brief description of what the metric means

Respond with ONLY a JSON dictionary, no explanation."""

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = self.complete(combined_prompt)
        
        # Extract and parse JSON using our robust extraction function
        metric_info = extract_json_from_response(response_text)
        if metric_info:
            return metric_info
        else:
            logger.warning("Could not extract metric info JSON from LLM response")
                
    except Exception as e:
        logger.error(f"Error getting metric info from LLM: {str(e)}")
    
    # Return empty dictionary if failed
    return {}

def get_property_mappings(self) -> Dict[str, List[str]]:
    """
    Get property mappings for variables from LLM knowledge.
    
    Returns:
        Dictionary mapping canonical variables to property names in CSV
    """
    if not self.api_key:
        logger.warning("No API key available for getting property mappings.")
        return {}
    
    try:
        system_prompt = """You are an energy systems expert. 
Provide mappings between canonical variable names and property names that might appear in CSV files.
Respond with a JSON dictionary where keys are canonical variable names and values are lists of property names."""

        user_prompt = """Please provide mappings between these canonical variable names and property names in CSV:
- TOTAL_GEN_COST_kUSD
- GENERATION_GWh
- CAPACITY_MW
- CAPEX_USD_per_kW
- OPEX_FIXED_USD_per_kWyr
- OPEX_VAR_USD_per_MWh
- EMISSIONS_tCO2
- HEAT_RATE_BTU_per_kWh
- FUEL_PRICE_USD_per_MMBTU
- CF_PERCENT

For example, "TOTAL_GEN_COST_kUSD" might map to ["Total Generation Cost", "Generation Cost", "Total Cost"].
Respond with ONLY a JSON dictionary, no explanation."""

        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        response_text = self.complete(combined_prompt)
        
        # Extract and parse JSON using our robust extraction function
        property_mappings = extract_json_from_response(response_text)
        if property_mappings:
            return property_mappings
        else:
            logger.warning("Could not extract property mappings JSON from LLM response")
                
    except Exception as e:
        logger.error(f"Error getting property mappings from LLM: {str(e)}")
    
    # Return empty dictionary if failed
    return {}

# Add the helper function and new methods to the LLMProvider class
LLMProvider.extract_json_from_response = extract_json_from_response
LLMProvider.get_tech_mappings = get_tech_mappings
LLMProvider.get_country_mappings = get_country_mappings
LLMProvider.get_metric_info = get_metric_info
LLMProvider.get_property_mappings = get_property_mappings
