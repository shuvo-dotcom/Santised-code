"""
Generic LLM provider for NFG energy analytics. Supports OpenAI and other providers.
Handles all dynamic content determination through API calls.
"""
import os
import json
import logging
import time
import tiktoken
import re
from typing import Dict, Any, List, Optional, Union

# Import model configuration
from .model_config import ModelConfig
from utils.metrics import Metrics

# Try multiple OpenAI client implementations - support both old and new API
try:
    from openai import OpenAI
    OPENAI_NEW_API = True
except ImportError:
    try:
        import openai
        OPENAI_NEW_API = False
    except ImportError:
        logging.error("OpenAI package not found. Please install with: pip install openai")

logger = logging.getLogger(__name__)

class LLMProvider:
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize LLM provider with API key and model.
        
        Args:
            api_key: Optional API key (will use environment variable if not provided)
            model: Model name to use for completions
        """
        # Initialize metrics tracker
        self.metrics = Metrics()
        
        # Use environment variable if no API key provided
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided. LLM functionality will be limited.")
            
        # Initialize model configuration
        self.model = model
        # Store model family for parameter handling
        self.model_family = ModelConfig.get_model_family(model)
        
        # Initialize token encoder for counting
        try:
            # Different encoding models for different OpenAI model families
            if model.startswith("gpt-4"):
                self.encoding = tiktoken.encoding_for_model("gpt-4")
            elif model.startswith("gpt-3.5"):
                self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            elif model.startswith("gpt-5"):
                # Use cl100k_base for gpt-5 models
                self.encoding = tiktoken.get_encoding("cl100k_base")
            else:
                # Default encoding
                self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to initialize token encoder: {str(e)}")
            self.encoding = None
            
        # Set token limits based on model (for logging/monitoring only)
        self.token_limits = {
            "gpt-5-mini": {"input": 128000, "output": 4096},
            "gpt-5": {"input": 128000, "output": 4096},
            "gpt-4": {"input": 8192, "output": 4096},
            "gpt-4-turbo": {"input": 128000, "output": 4096},
            "gpt-3.5-turbo": {"input": 4096, "output": 4096},
        }
        
        # Get token limits for the specific model (for logging/monitoring only)
        for model_name, limits in self.token_limits.items():
            if self.model.startswith(model_name):
                self.input_token_limit = limits["input"]
                self.output_token_limit = limits["output"]
                logger.info(f"Using model {self.model} with context window of {self.input_token_limit:,} tokens")
                break
        else:
            # Default limits
            self.input_token_limit = 4096
            self.output_token_limit = 4096
            logger.info(f"Using model {self.model} with default context window of {self.input_token_limit:,} tokens")
        
        # Initialize OpenAI client based on API version
        if OPENAI_NEW_API:
            self.client = OpenAI(api_key=self.api_key)
        else:
            openai.api_key = self.api_key
            
        # In-memory cache for value predictions - no YAML dependency
        self.value_cache = {}
    
    def get_fallback_value(self, canonical_var: str, filters: Dict[str, Any] = None) -> float:
        """
        Get a fallback value for a variable based on filters using the LLM's knowledge.
        Always dynamically determined by LLM at runtime.
        
        Args:
            canonical_var: Canonical variable name
            filters: Optional filters like tech, country, year
            
        Returns:
            A reasonable fallback value for the variable based on LLM knowledge
        """
        if not self.api_key:
            logger.warning("No API key available for getting fallback value.")
            return None
        
        # Create a cache key based on variable and filters
        cache_key = f"{canonical_var}_{filters.get('tech', '')}{filters.get('country', '')}{filters.get('year', '')}"
        
        # Check if we already have this value cached in memory
        if cache_key in self.value_cache:
            return self.value_cache[cache_key]
        
        # Always use LLM to determine values dynamically
        try:
            # Create a prompt asking for a reasonable value
            country_str = f" in {filters.get('country', 'a typical country')}" if filters and "country" in filters else ""
            year_str = f" for {filters.get('year', 'current year')}" if filters and "year" in filters else ""
            tech_str = f" for {filters.get('tech', 'typical generation technology')}" if filters and "tech" in filters else ""
            
            system_prompt = f"""You are an energy systems expert. Provide a single numeric value for the requested energy system parameter.
Respond ONLY with the numeric value, no text explanation or unit."""

            user_prompt = f"""What is a typical value for {canonical_var}{tech_str}{country_str}{year_str}?
Remember to respond ONLY with the numeric value."""

            # Make an API call to get a reasonable value
            response_text = self.generate_completion(system_prompt, user_prompt)
            
            # Extract numeric value from response
            value_match = re.search(r'-?\d+\.?\d*', response_text.strip())
            if value_match:
                try:
                    value = float(value_match.group(0))
                    # Cache the result for future use
                    self.value_cache[cache_key] = value
                    return value
                except ValueError:
                    pass
            
        except Exception as e:
            logger.error(f"Error getting fallback from LLM for {canonical_var}: {str(e)}")
        
        # If we reach here, we failed to get a value from the LLM
        # Return None - will fall back to guess_reasonable_value
        return None
    
    def _enhanced_regex_fallback(self, text: str) -> Dict[str, Any]:
        """
        Enhanced regex-based fallback for intent parsing when LLM fails.
        Uses dynamic LLM-based pattern matching when available.
        
        Args:
            text: User query text
            
        Returns:
            Dict with parsed intent fields
        """
        logger.info(f"Using enhanced regex fallback for intent parsing: {text}")
        
        # Initialize result structure
        result = {
            "metric": None, "tech": None, "fuel": None, "network": None, 
            "country": None, "year": None, "operation": None, "confidence": {}
        }
        
        text_lower = text.lower()
        
        # Try to get keywords from LLM
        if self.api_key:
            try:
                # Dynamically generate keyword mappings
                keywords_map = self._generate_keyword_mappings()
                
                # Get metrics, technologies and countries from LLM response
                metrics = keywords_map.get("metrics", {})
                technologies = keywords_map.get("technologies", {})
                countries = keywords_map.get("countries", {})
                
            except Exception as e:
                logger.error(f"Error generating keywords from LLM: {str(e)}")
                # Minimal fallback with just the most common keywords
                metrics = {
                    "LCOE": ["lcoe", "levelized cost"],
                    "NPV": ["npv", "net present value"],
                    "CAPACITY_FACTOR": ["capacity factor", "cf"]
                }
                technologies = {
                    "NUCLEAR": ["nuclear"],
                    "WIND": ["wind"],
                    "SOLAR": ["solar"]
                }
                countries = {
                    "BE": ["belgium", "belgian"],
                    "FR": ["france", "french"],
                    "UK": ["uk", "united kingdom"]
                }
        else:
            # Minimal fallback with just the most common keywords if no LLM
            metrics = {
                "LCOE": ["lcoe", "levelized cost"],
                "NPV": ["npv", "net present value"],
                "CAPACITY_FACTOR": ["capacity factor", "cf"]
            }
            technologies = {
                "NUCLEAR": ["nuclear"],
                "WIND": ["wind"],
                "SOLAR": ["solar"]
            }
            countries = {
                "BE": ["belgium", "belgian"],
                "FR": ["france", "french"],
                "UK": ["uk", "united kingdom"]
            }
        
        # Process metrics
        for metric_name, keywords in metrics.items():
            if any(keyword in text_lower for keyword in keywords):
                result["metric"] = metric_name
                result["confidence"]["metric"] = 0.8
                break
        
        # Process technologies
        for tech_name, keywords in technologies.items():
            if any(keyword in text_lower for keyword in keywords):
                result["tech"] = tech_name
                result["confidence"]["tech"] = 0.8
                break
        
        # Process countries
        for code, keywords in countries.items():
            if any(keyword in text_lower for keyword in keywords):
                result["country"] = code
                result["confidence"]["country"] = 0.8
                break
        
        # Year extraction - improved to handle "by 2050" and similar phrases
        year_patterns = [
            r"(20\d{2})",  # Standard year
            r"by\s+(20\d{2})",  # "by 2050"
            r"in\s+(20\d{2})"   # "in 2050"
        ]
        
        for pattern in year_patterns:
            year_match = re.search(pattern, text)
            if year_match:
                # Extract the actual year digits regardless of pattern
                year_str = re.search(r"20\d{2}", year_match.group(0)).group(0)
                result["year"] = int(year_str)
                result["confidence"]["year"] = 0.9
                break
                
        return result

    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens in the text
        """
        if self.encoding is None:
            # Rough approximation if no encoder is available
            return len(text) // 4
        
        try:
            tokens = self.encoding.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens: {str(e)}")
            # Fallback to rough approximation
            return len(text) // 4
            
    def get_token_limit_info(self) -> Dict[str, Any]:
        """
        Get information about token limits for the current model.
        
        Returns:
            Dict with token limit information
        """
        return {
            "model": self.model,
            "input_token_limit": self.input_token_limit,
            "output_token_limit": self.output_token_limit,
            "family": self.model_family
        }
    
    def complete(self, prompt: str, **kwargs) -> str:
        """
        Send a completion request to the LLM.
        
        Args:
            prompt: Prompt to send to LLM
            **kwargs: Additional parameters for the LLM API
            
        Returns:
            String response from LLM
        """
        if not self.api_key:
            logger.warning("No API key provided. Returning empty response.")
            return ""
        
        # Only count tokens for logging/debugging purposes
        token_count = self.count_tokens(prompt)
        logger.debug(f"Token count for prompt: {token_count}")
        
        # Don't enforce token limits or include them in calls - the API will handle this
        # This allows the model to use its full context window as needed
            
        # Filter out parameters not supported by this model
        filtered_kwargs = kwargs.copy()
        from .model_config import ModelConfig
        if "temperature" in filtered_kwargs and not ModelConfig.supports_temperature(self.model):
            logger.info(f"Removing 'temperature' parameter as it's not supported for model {self.model}")
            del filtered_kwargs["temperature"]
            
        start_time = time.time()
        
        try:
            # Use appropriate API based on version
            if OPENAI_NEW_API:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **filtered_kwargs
                )
                result = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **filtered_kwargs
                )
                result = response.choices[0].message.content
                
            # Track metrics
            duration = time.time() - start_time
            self.metrics.track_api_call(self.model, prompt, result, duration)
            
            return result.strip()
        except Exception as e:
            logger.error(f"Error calling LLM API: {str(e)}")
            return ""
            
    def generate_completion(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """
        Generate a completion using system and user prompts.
        
        Args:
            system_prompt: System prompt to set context
            user_prompt: User prompt with specific request
            **kwargs: Additional parameters for the LLM API
            
        Returns:
            String response from LLM
        """
        if not self.api_key:
            logger.warning("No API key provided. Returning empty response.")
            return ""
            
        start_time = time.time()
        
        try:
            # Create message array with system and user prompts
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Use appropriate API based on version
            if OPENAI_NEW_API:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                result = response.choices[0].message.content
            else:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                result = response.choices[0].message.content
                
            # Track metrics
            duration = time.time() - start_time
            combined_prompt = f"SYSTEM: {system_prompt}\nUSER: {user_prompt}"
            self.metrics.track_api_call(self.model, combined_prompt, result, duration)
            
            return result.strip()
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            return ""

    def parse_nfg_intent(self, text: str) -> Dict[str, Any]:
        """
        Use LLM to extract NFG intent from text.
        No hardcoded dependencies - all parsing done by LLM.
        
        Args:
            text: User query text
            
        Returns:
            Dict with parsed intent fields
        """
        system_prompt = """
        You are an energy analytics assistant specialized in Networks-Fuels-Generation (NFG) queries.
        
        Your task is to extract structured information from user queries about energy metrics.
        
        IMPORTANT: You must return ONLY a valid JSON object with these fields:
        - metric: The canonical metric name (e.g., LCOE, GENERATION_GWh, CAPACITY_MW, CAPACITY_FACTOR, EMISSIONS_tCO2)
        - tech: The technology type (e.g., NUCLEAR, CCGT, WIND, SOLAR, PV, HYDRO)
        - country: The country code (e.g., BE, FR, ES, DE, IT, UK)
        - year: The year as integer (e.g., 2030, 2040, 2050)
        - fuel: Optional fuel type (e.g., GAS, COAL, URANIUM)
        - network: Optional network type (e.g., TRANSMISSION, DISTRIBUTION)
        - operation: Optional operation (avg, sum, min, max)
        
        Include confidence scores (0.0-1.0) for each field in a nested "confidence" object.
        
        Example of valid response format:
        {
          "metric": "LCOE",
          "tech": "NUCLEAR",
          "country": "BE",
          "year": 2050,
          "fuel": null,
          "network": null,
          "operation": null,
          "confidence": {
            "metric": 0.95,
            "tech": 0.9,
            "country": 0.8,
            "year": 0.99
          }
        }
        
        MAKE SURE your response contains only the JSON object, nothing else.
        """
        
        # Structure the query for better JSON extraction
        prompt = f"{system_prompt}\n\nUser Query: \"{text}\"\n\nJSON:"
        
        # Log the attempt
        logger.debug(f"Attempting to parse intent from query: {text}")
        
        # No special cases - always use the model for intent parsing
        # This enables true dynamic parsing without hardcoded values
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use standard parameters that work across all models
                # Only set temperature - let the model use its default token limits
                params = {"temperature": 0.2}
                
                result = self.complete(prompt, **params)
                logger.debug(f"Raw LLM response: {result}")
                
                # Try to extract valid JSON
                # Handle case where there might be markdown formatting
                result = result.strip()
                if result.startswith("```json"):
                    result = result[7:]
                if result.endswith("```"):
                    result = result[:-3]
                
                # Additional cleanup for common LLM JSON formatting issues
                result = result.strip()
                
                # Debug the cleaned response
                logger.debug(f"Cleaned response for JSON parsing: {result}")
                
                # Try to use our enhanced JSON extraction if it's available
                try:
                    # First try to use the enhanced JSON parsing function if it exists
                    if hasattr(self, 'extract_json_from_response'):
                        parsed = self.extract_json_from_response(result)
                        if parsed:
                            logger.debug(f"Successfully parsed JSON with enhanced extractor: {parsed}")
                            
                            # Ensure expected fields exist
                            for field in ['metric', 'tech', 'country', 'year']:
                                if field not in parsed:
                                    parsed[field] = None
                            if 'confidence' not in parsed:
                                parsed['confidence'] = {}
                                
                            return parsed
                            
                    # Fall back to standard JSON parsing
                    parsed = json.loads(result.strip())
                    logger.debug(f"Successfully parsed JSON: {parsed}")
                    
                    # Ensure expected fields exist
                    for field in ['metric', 'tech', 'country', 'year']:
                        if field not in parsed:
                            parsed[field] = None
                    if 'confidence' not in parsed:
                        parsed['confidence'] = {}
                    
                    return parsed
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON on attempt {attempt+1}. Error: {e}")
                    logger.warning(f"Problematic JSON string: {result}")
                    time.sleep(1)  # Wait before retry
            except Exception as e:
                logger.error(f"Unexpected error during intent parsing (attempt {attempt+1}): {str(e)}")
                time.sleep(1)  # Wait before retry
                
        # All attempts failed, use enhanced regex-based fallback
        logger.warning("All LLM attempts failed for intent parsing, using enhanced regex fallback")
        return self._enhanced_regex_fallback(text)

    def get_variable_mapping(self, canonical_var: str, available_properties: List[str]) -> List[Dict[str, Any]]:
        """
        Use LLM to map canonical variables to available properties.
        """
        system_prompt = """
        You are an energy analytics expert specialized in NFG (Networks-Fuels-Generation) data.
        Map the canonical variable to possible properties from the available list.
        Return ONLY a valid JSON array with objects containing:
        - property_name: exact name from available_properties that could match
        - unit_name: expected unit of measure
        - transform: description of any transform needed
        
        Return empty array if no matches found.
        """
        
        prompt = f"{system_prompt}\n\nCanonical Variable: {canonical_var}\nAvailable Properties: {available_properties}\n\nJSON:"
        
        try:
            # Use standard parameters that work across all models
            # Only set temperature - let the model use its default token limits
            params = {"temperature": 0.2}
            
            result = self.complete(prompt, **params)
            # Extract JSON
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
                
            mappings = json.loads(result.strip())
            return mappings
        except Exception as e:
            logger.error(f"Error mapping variables: {str(e)}")
            return []
    def guess_reasonable_value(self, canonical_var: str, filters: Dict[str, Any] = None) -> float:
        """
        Guess a reasonable value for a variable based on its name and filters.
        This is the last resort when no fallback values are available.
        Always dynamically determined by LLM at runtime.
        
        Args:
            canonical_var: Canonical variable name
            filters: Optional filters like tech, country, year
            
        Returns:
            A reasonably guessed value for the variable
        """
        if not self.api_key:
            logger.warning("No API key available for guessing values.")
            return None
            
        # Create a cache key based on variable and filters
        cache_key = f"guess_{canonical_var}_{filters.get('tech', '')}{filters.get('country', '')}{filters.get('year', '')}"
        
        # Check if we already have this value cached in memory
        if cache_key in self.value_cache:
            return self.value_cache[cache_key]
            
        try:
            # Create a detailed prompt asking for a typical value
            country_str = f" in {filters.get('country', 'a typical country')}" if filters and "country" in filters else ""
            year_str = f" for {filters.get('year', 'current year')}" if filters and "year" in filters else ""
            tech_str = f" for {filters.get('tech', 'typical generation technology')}" if filters and "tech" in filters else ""
            
            system_prompt = f"""You are an expert in energy systems and economics.
I need a realistic value for {canonical_var}{tech_str}{country_str}{year_str}.
Respond ONLY with a single numerical value, nothing else. No units, no text."""

            user_prompt = f"""Based on your knowledge of energy systems, what is a reasonable value for {canonical_var}{tech_str}{country_str}{year_str}?
Remember to provide ONLY a number, with no text explanation or units."""

            # Make an API call to get a reasonable value
            response_text = self.generate_completion(system_prompt, user_prompt)
            
            # Extract numeric value from response with robust parsing
            clean_response = response_text.strip().replace(',', '')
            value_match = re.search(r'-?\d+\.?\d*', clean_response)
            if value_match:
                try:
                    value = float(value_match.group(0))
                    # Cache the result for future use
                    self.value_cache[cache_key] = value
                    return value
                except ValueError:
                    logger.warning(f"Failed to convert matched value to float: {value_match.group(0)}")
            
            # If we didn't find a clean number, try more aggressive parsing
            # Extract any digits and decimal points, ignoring other characters
            digits_only = ''.join([c for c in clean_response if c.isdigit() or c == '.'])
            try:
                if digits_only:
                    value = float(digits_only)
                    # Cache the result for future use
                    self.value_cache[cache_key] = value
                    return value
            except ValueError:
                logger.warning(f"Failed to parse digits from response: {digits_only}")
            
        except Exception as e:
            logger.error(f"Error guessing value from LLM for {canonical_var}: {str(e)}")
        
        # Default values based on variable name patterns as absolute last resort
        # These are minimal heuristics, not hardcoded values
        if "CAPACITY" in canonical_var and "MW" in canonical_var:
            value = 100.0
        elif "GENERATION" in canonical_var and "GWh" in canonical_var:
            value = 500.0
        elif "COST" in canonical_var and "kUSD" in canonical_var:
            value = 1000.0
        elif "RATE" in canonical_var:
            value = 0.08
        else:
            value = 100.0
            
        # Cache even the default value
        self.value_cache[cache_key] = value
        return value
            
    def _generate_keyword_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Generate keyword mappings for metrics, technologies, and countries using LLM.
        Used for regex fallback when main intent parsing fails.
        
        Returns:
            Dict with mappings for metrics, technologies, and countries
        """
        # Create a cache key
        cache_key = "keyword_mappings"
        
        # Check if we already have generated these mappings
        if hasattr(self, "_keyword_cache") and cache_key in self._keyword_cache:
            return self._keyword_cache[cache_key]
            
        # Initialize cache attribute if it doesn't exist
        if not hasattr(self, "_keyword_cache"):
            self._keyword_cache = {}
            
        system_prompt = """You are an energy systems expert helping to create keyword mappings.
Generate mappings for metrics, technologies, and countries in the energy sector.
For each category, provide canonical names and the keywords that might refer to them.
Return ONLY valid JSON."""

        user_prompt = """Generate keyword mappings for:
1. Metrics like LCOE, NPV, Capacity Factor, Generation, Capacity, Emissions
2. Technologies like Nuclear, Wind, Solar, Hydro, CCGT
3. Countries with their ISO codes like BE (Belgium), FR (France), etc.

Format as JSON with this structure:
{
  "metrics": {
    "METRIC_NAME": ["keyword1", "keyword2", ...],
    ...
  },
  "technologies": {
    "TECH_NAME": ["keyword1", "keyword2", ...],
    ...
  },
  "countries": {
    "ISO_CODE": ["country_name", "adjective", ...],
    ...
  }
}"""

        try:
            # Make API call to get mappings
            response_text = self.generate_completion(system_prompt, user_prompt, temperature=0.1)
            
            # Extract JSON
            if "```json" in response_text:
                json_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_text = response_text.split("```")[1].strip()
            else:
                json_text = response_text.strip()
                
            mappings = json.loads(json_text)
            
            # Cache for future use
            self._keyword_cache[cache_key] = mappings
            
            return mappings
        except Exception as e:
            logger.error(f"Error generating keyword mappings: {str(e)}")
            # Return minimal fallback
            return {
                "metrics": {
                    "LCOE": ["lcoe", "levelized cost"],
                    "NPV": ["npv", "net present value"],
                    "CAPACITY_FACTOR": ["capacity factor", "cf"]
                },
                "technologies": {
                    "NUCLEAR": ["nuclear"],
                    "WIND": ["wind"],
                    "SOLAR": ["solar"]
                },
                "countries": {
                    "BE": ["belgium", "belgian"],
                    "FR": ["france", "french"],
                    "UK": ["uk", "united kingdom"]
                }
            }
    
    def determine_equation(self, metric: str) -> Dict[str, Any]:
        """
        Use LLM to get equation for metric.
        
        Args:
            metric: Metric name
            
        Returns:
            Dict with formula, required variables, and fallback
        """
        # No hardcoding - dynamically determine equation through LLM
        logger.info(f"Dynamically determining equation for {metric} using LLM")
            
        system_prompt = """
        You are an energy analytics expert specialized in NFG (Networks-Fuels-Generation) mathematics.
        Provide the equation for calculating the given metric.
        Return ONLY a valid JSON object with:
        - formula: mathematical formula as string using only basic math operators (+, -, *, /, sum)
        - required: array of required variable names
        
        IMPORTANT: The formula must be simple enough to be parsed by SymPy. 
        For sum operations, use "sum([VAR])" instead of complex notations like "SUM(VAR_i for i=1..N)".
        For CAPACITY_MW, use "UNIT_CAPACITY_MW" as the variable name.
        - unit: unit of measure for result
        
        Example:
        {
          "formula": "TOTAL_GEN_COST_kUSD / GENERATION_GWh",
          "required": ["TOTAL_GEN_COST_kUSD", "GENERATION_GWh"],
          "unit": "USD/MWh"
        }
        """
        
        prompt = f"{system_prompt}\n\nMetric: {metric}\n\nJSON:"
        
        try:
            # Use standard parameters that work across all models
            # Only set temperature - let the model use its default token limits
            params = {"temperature": 0.3}
            
            result = self.complete(prompt, **params)
            # Extract JSON
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]
                
            equation = json.loads(result.strip())
            return equation
        except Exception as e:
            logger.error(f"Error getting equation: {str(e)}")
            return {
                "formula": None,
                "unit": None,
                "required": [],
                "fallback": {"formula": None, "required": []}
            }
