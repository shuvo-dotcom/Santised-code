"""
Dynamic pipeline to answer NFG analytics queries end-to-end.
No hardcoded dependencies - everything determined by LLM at runtime.
"""
import os
import logging
import time
from typing import Dict, Any, List, Optional

from semantic.intent_parser import IntentParser
from semantic.llm_provider import LLMProvider
from semantic.variable_catalog import VariableCatalog
from nfg_math.equations import EquationRegistry
# Use the new data_io module instead of io to avoid conflicts
from data_io.csv_store import CSVStore

logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, csv_folder: str, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize pipeline with components.
        
        Args:
            csv_folder: Path to folder containing CSV files
            api_key: Optional OpenAI API key (falls back to env var)
            model: Optional OpenAI model name (falls back to env var)
        """
        # Initialize LLM provider first
        self.llm_provider = LLMProvider(api_key=api_key, model=model)
        
        # Initialize other components and connect them to LLM provider
        self.intent_parser = IntentParser()
        self.intent_parser.set_llm_provider(self.llm_provider)
        
        self.equation_registry = EquationRegistry({})
        self.equation_registry.set_llm_provider(self.llm_provider)
        
        # Initialize variable catalog with LLM provider
        self.variable_catalog = VariableCatalog()
        self.variable_catalog.set_llm_provider(self.llm_provider)
        
        # Initialize CSV store for data access
        self.csv_store = CSVStore(csv_folder)

    def answer_query(self, text: str) -> Dict[str, Any]:
        """
        Answer query end-to-end using dynamic LLM-driven components.
        No hardcoded dependencies - all determined at runtime through LLM.
        
        Args:
            text: User query text
            
        Returns:
            Dict with answer, including result, method, inputs, and citations
        """
        # Track start time for performance logging
        start_time = time.time()
        
        # Step 1: Parse intent using LLM
        logger.info(f"Parsing intent for query: {text}")
        intent = self.intent_parser.parse(text)
        metric = intent.get("metric")
        
        if not metric:
            logger.warning("Could not determine metric from query")
            return {
                "error": "Could not determine metric from query",
                "scope": intent,
                "result": None,
                "citations": []
            }
            
        logger.info(f"Parsed intent: metric={metric}, tech={intent.get('tech')}, country={intent.get('country')}, year={intent.get('year')}")
            
        # Step 2: Get equation for metric from LLM
        equation = self.equation_registry.get_equation(metric)
        required_vars = equation.get('required', [])
        
        if not required_vars:
            return {
                "error": f"Could not determine equation for metric: {metric}",
                "metric": metric,
                "scope": intent,
                "result": None,
                "citations": []
            }
            
        logger.info(f"Required variables for {metric}: {required_vars}")
        
        # Step 3: Resolve variables from CSV data
        variables = {}
        citations = []
        
        # Get available properties from CSV store
        available_properties = self.csv_store.list_available_properties()
        
        # Convert intent to filters
        filters = {
            k: v for k, v in intent.items() 
            if k in ['country', 'tech', 'year', 'model', 'scenario'] and v is not None
        }
        
        # For each required variable, find mappings and query data
        for var_name in required_vars:
            # Get variable mapping using the variable catalog
            var_mappings_tuples = self.variable_catalog.get_mappings(var_name, available_properties)
            
            # Convert tuples to dict format for compatibility with existing code
            var_mappings = []
            for prop_name, unit_name, transform_fn in var_mappings_tuples:
                var_mappings.append({
                    'property_name': prop_name,
                    'unit_name': unit_name,
                    'transform': 'identity'  # Just for info, we'll use the function directly
                })
                
            # If no mappings found, use variable catalog for fallback values
            if not var_mappings:
                logger.warning(f"No mappings found for {var_name}, using fallback from variable catalog")
                fallback_value = self.variable_catalog.get_fallback_value(var_name, filters)
                variables[var_name] = fallback_value
                logger.info(f"Using fallback value for {var_name}: {fallback_value}")
                continue
                
            # For each mapping, try to find data in CSV
            for mapping in var_mappings:
                property_name = mapping.get('property_name')
                
                if not property_name:
                    continue
                    
                # Query CSV store for this property
                rows = self.csv_store.query(filters, properties=[property_name])
                
                if rows:
                    # Sum values for this variable
                    value_sum = sum(row.get('value', 0) for row in rows)
                    variables[var_name] = value_sum
                    
                    # Add citations
                    for row in rows:
                        citation = {
                            'csv': row.get('source_csv', 'unknown'),
                            'child_name': row.get('child_name', 'unknown'),
                            'property': property_name,
                            'year': row.get('date_string', 'unknown')
                        }
                        if citation not in citations:
                            citations.append(citation)
                            
                    # Found data, break out of mapping loop
                    break
                    
            # If we didn't find data, use variable catalog for fallback values
            if var_name not in variables:
                logger.warning(f"No data found for {var_name}, using fallback from variable catalog")
                fallback_value = self.variable_catalog.get_fallback_value(var_name, filters)
                variables[var_name] = fallback_value
                logger.info(f"Using fallback value for {var_name}: {fallback_value}")
        
        # Step 4: Calculate result
        result = self.equation_registry.evaluate(metric, variables)
        unit = self.equation_registry.generate_unit(metric)
        
        # Step 5: Return formatted answer
        return {
            "metric": metric,
            "unit": unit,
            "scope": intent,
            "result": result,
            "method": equation.get('formula', 'Unknown formula'),
            "inputs": variables,
            "citations": citations,
            "notes": "Pipeline with dynamic LLM-driven components"
        }