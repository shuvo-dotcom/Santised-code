#!/usr/bin/env python
"""
Enhanced pipeline implementation with improved data extraction and citation handling
Demonstrates the main concepts from the enhanced test pipeline
"""
import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set

from semantic.intent_parser import IntentParser
from semantic.llm_provider import LLMProvider
from semantic.variable_catalog import VariableCatalog
from nfg_math.equations import EquationRegistry
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
        
        # Tech mapping for different generator types
        self.tech_map = {
            "NUCLEAR": ["Nuclear"],
            "WIND": ["Wind", "onshore wind", "offshore wind"],
            "SOLAR": ["Solar", "PV", "photovoltaic"],
            "HYDRO": ["Hydro", "hydroelectric"],
            "CCGT": ["CCGT", "gas turbine", "combined cycle"]
        }
        
        # Country code mapping
        self.country_map = {
            "BE": "BE",
            "FR": "FR", 
            "DE": "DE",
            "UK": "UK",
            "ES": "ES",
            "IT": "IT"
        }

    def _extract_data_from_csv(self, df, filters: Dict[str, Any], property_name: str) -> List[Dict[str, Any]]:
        """
        Extract data from a CSV dataframe based on filters and property name.
        
        Args:
            df: Pandas DataFrame to extract data from
            filters: Dictionary of filter criteria
            property_name: Property name to extract
            
        Returns:
            List of dictionaries with extracted data
        """
        # Process tech filters
        tech_filter = None
        if "tech" in filters:
            tech = filters["tech"]
            if tech == "NUCLEAR":
                tech_filter = (df['category_name'] == 'Nuclear')
            elif tech in self.tech_map:
                tech_conditions = []
                for pattern in self.tech_map[tech]:
                    tech_conditions.append(df['category_name'].str.contains(pattern, case=False))
                if tech_conditions:
                    tech_filter = tech_conditions[0]
                    for condition in tech_conditions[1:]:
                        tech_filter |= condition
        
        # Process country filter
        country_filter = None
        if "country" in filters and filters["country"] in self.country_map:
            country_code = self.country_map[filters["country"]]
            country_filter = df['child_name'].str.match(f'^{country_code}[0-9]')
        
        # Process year filter - handle both string and integer date values
        year_filter = None
        if "year" in filters:
            year = filters["year"]
            try:
                year_int = int(year)
                year_filter = (df['date_string'] == year_int)
            except (ValueError, TypeError):
                year_filter = (df['date_string'] == str(year))
        
        # Process property name filter
        property_filter = (df['property_name'] == property_name)
        
        # Combine all filters
        combined_filter = property_filter
        if tech_filter is not None:
            combined_filter &= tech_filter
        if country_filter is not None:
            combined_filter &= country_filter
        if year_filter is not None:
            combined_filter &= year_filter
        
        # Apply the combined filter
        filtered_df = df[combined_filter]
        
        # Process results
        results = []
        for _, row in filtered_df.iterrows():
            if row['value'] not in [None, '']:
                try:
                    value = float(row['value'])
                except (ValueError, TypeError):
                    logger.warning(f"Could not convert value to float: {row['value']}")
                    continue
                    
                results.append({
                    "source": row.get('source_csv', 'systemgenerators.csv'),
                    "property": row['property_name'],
                    "value": value,
                    "unit": row['unit_name'],
                    "tech": row['category_name'],
                    "facility": row['child_name'],
                    "year": row['date_string']
                })
        
        return results
    
    def answer_query(self, text: str) -> Dict[str, Any]:
        """
        Answer query end-to-end using dynamic LLM-driven components.
        Data-driven approach using CSV data sources.
        
        Args:
            text: User query text
            
        Returns:
            Dict with answer, including result, method, inputs, and citations
        """
        # Step 1: Parse intent using LLM
        intent = self.intent_parser.parse(text)
        metric = intent.get("metric")
        
        if not metric:
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
        
        # Step 3: Setup filters from intent
        filters = {}
        
        # Extract tech filter
        if intent.get("tech") and intent.get("tech") in self.tech_map:
            filters["tech"] = intent["tech"]
        
        # Extract country filter
        if intent.get("country") and intent.get("country") in self.country_map:
            filters["country"] = intent["country"]
        
        # Extract year filter
        if intent.get("year"):
            filters["year"] = intent["year"]
            
        logger.info(f"Using filters: {filters}")
        
        # Step 4: Resolve variables from CSV data
        variables = {}
        citations = []
        
        # Get available CSV files
        csv_files = self.csv_store.dfs.keys()
        
        # Process each required variable
        for var_name in required_vars:
            var_data = []
            
            # Property mappings based on variable names
            property_mappings = {
                "TOTAL_GEN_COST_kUSD": ["Total Generation Cost"],
                "GENERATION_GWh": ["Generation"],
                "CAPACITY_MW": ["Installed Capacity", "Capacity"],
                "CAPEX_USD_per_kW": ["CAPEX", "Capital Cost"],
                "OPEX_FIXED_USD_per_kWyr": ["FO&M Cost", "Fixed O&M Cost"],
                "OPEX_VAR_USD_per_MWh": ["VO&M Cost", "Variable O&M Cost"],
                "EMISSIONS_tCO2": ["Emissions", "CO2 Emissions"],
                "REVENUE_ANNUAL": ["Pool Revenue", "Net Revenue"],
                "COST_ANNUAL": ["Total Generation Cost", "Fuel Cost", "VO&M Cost"],
                "CAPEX_INITIAL": ["Initial Investment", "Capital Investment", "CAPEX"],
                "DISCOUNT_RATE": ["Discount Rate", "WACC"]
            }
            
            # Get property names for this variable
            property_names = property_mappings.get(var_name, [var_name])
            
            # Look in systemgenerators.csv first
            if "systemgenerators.csv" in csv_files:
                df = self.csv_store.dfs["systemgenerators.csv"]
                
                for property_name in property_names:
                    property_data = self._extract_data_from_csv(df, filters, property_name)
                    if property_data:
                        var_data.extend(property_data)
                        break  # Found data for one property, stop looking
            
            # If no data found in systemgenerators.csv, try other CSV files
            if not var_data:
                for csv_name in [f for f in csv_files if f != "systemgenerators.csv"]:
                    df = self.csv_store.dfs[csv_name]
                    
                    for property_name in property_names:
                        property_data = self._extract_data_from_csv(df, filters, property_name)
                        if property_data:
                            var_data.extend(property_data)
                            break  # Found data for one property, stop looking
                    
                    if var_data:
                        break  # Found data in this CSV file, stop looking
            
            # Process the data if found
            if var_data:
                # Sum the values for this variable
                total_value = sum(item["value"] for item in var_data)
                variables[var_name] = total_value
                
                # Add citations
                for item in var_data:
                    citation = {
                        "source": item["source"],
                        "property": item["property"],
                        "value": item["value"],
                        "unit": item["unit"],
                    }
                    
                    # Add additional fields if available
                    for field in ["tech", "facility", "year"]:
                        if field in item and item[field] is not None:
                            citation[field] = item[field]
                            
                    citations.append(citation)
                    
                logger.info(f"Variable {var_name} = {total_value} (from {len(var_data)} data points)")
            else:
                # No data found, use data-driven fallback values
                logger.warning(f"No data found for {var_name}. Using data-driven fallback approach.")
                
                # Use the variable catalog to determine reasonable fallbacks
                # This uses the variable catalog which may be loaded from YAML or determined by LLM
                fallback_values = {
                    "TOTAL_GEN_COST_kUSD": self.variable_catalog.get_fallback_value("TOTAL_GEN_COST_kUSD", filters),
                    "GENERATION_GWh": self.variable_catalog.get_fallback_value("GENERATION_GWh", filters),
                    "CAPACITY_MW": self.variable_catalog.get_fallback_value("CAPACITY_MW", filters),
                    "CAPEX_USD_per_kW": self.variable_catalog.get_fallback_value("CAPEX_USD_per_kW", filters),
                    "OPEX_FIXED_USD_per_kWyr": self.variable_catalog.get_fallback_value("OPEX_FIXED_USD_per_kWyr", filters),
                    "OPEX_VAR_USD_per_MWh": self.variable_catalog.get_fallback_value("OPEX_VAR_USD_per_MWh", filters)
                }
                
                # Get fallback value from catalog or use a generic one
                variables[var_name] = fallback_values.get(var_name, self.variable_catalog.get_fallback_value(var_name, filters))
                
                # Add placeholder citation
                citations.append({
                    "source": "fallback_values",
                    "property": var_name,
                    "value": variables[var_name],
                    "unit": "fallback"
                })
        
        # Step 5: Calculate result
        result = self.equation_registry.evaluate(metric, variables)
        unit = self.equation_registry.generate_unit(metric)
        
        # Step 6: Remove duplicate citations
        unique_citations = []
        seen_citations = set()
        
        for citation in citations:
            # Create a unique key for this citation
            key_parts = []
            for field in ["source", "property", "tech", "facility", "year"]:
                if field in citation and citation[field] is not None:
                    key_parts.append(str(citation[field]))
                else:
                    key_parts.append("")
            
            citation_key = tuple(key_parts)
            
            if citation_key not in seen_citations:
                seen_citations.add(citation_key)
                unique_citations.append(citation)
        
        # Step 7: Create a more focused and precise answer
        
        # Format the result to appropriate precision based on metric type
        if metric in ["LCOE", "LCOS"]:
            formatted_result = f"{result:.2f}"  # 2 decimal places for costs
        elif "FACTOR" in metric:
            formatted_result = f"{result:.1%}"  # Percentage with 1 decimal for factors
        else:
            formatted_result = f"{result:.1f}"  # 1 decimal place for other metrics
        
        # Create a narrative summary for the result
        tech_name = filters.get("tech", "").title() if filters.get("tech") else "Unknown"
        country_name = filters.get("country", "") if filters.get("country") else "Unknown"
        year_value = filters.get("year", "") if filters.get("year") else "Unknown"
        
        # Get long country name if available
        country_names = {
            "BE": "Belgium",
            "DE": "Germany",
            "FR": "France",
            "UK": "United Kingdom",
            "ES": "Spain",
            "IT": "Italy"
        }
        country_long = country_names.get(country_name, country_name)
        
        # Get metric full name
        metric_names = {
            "LCOE": "Levelized Cost of Electricity",
            "CAPACITY_FACTOR": "Capacity Factor",
            "EMISSIONS_INTENSITY": "Emissions Intensity",
            "CAPEX": "Capital Expenditure",
            "OPEX": "Operational Expenditure",
            "NPV": "Net Present Value"
        }
        metric_full = metric_names.get(metric, metric)
        
        # Create summary statement
        summary = f"The {metric_full} for {tech_name} in {country_long} for {year_value} is {formatted_result} {unit}."
        
        # Include data source information
        if all(c.get("source", "").startswith("fallback") for c in unique_citations):
            data_source = "This result is based on typical values as no specific data was found."
        else:
            real_data_sources = [c.get("source") for c in unique_citations if not c.get("source", "").startswith("fallback")]
            data_source = f"This result is calculated from data in: {', '.join(set(real_data_sources))}."
        
        # Include methodology
        methodology = f"Calculated using: {equation.get('formula', 'Unknown formula')}"
        
        # Create a structured narrative response
        narrative = {
            "summary": summary,
            "data_source": data_source,
            "methodology": methodology
        }
        
        # Return complete structured answer with both raw data and narrative
        return {
            "metric": metric,
            "unit": unit,
            "scope": intent,
            "result": result,
            "formatted_result": formatted_result,
            "method": equation.get('formula', 'Unknown formula'),
            "inputs": variables,
            "citations": unique_citations,
            "narrative": narrative,
            "notes": f"Using data from CSV files with filters: {filters}"
        }
