"""
Generic CSV store for NFG analytics. Dynamically loads any CSV and supports generic queries.
No hardcoded dependencies - all filtering criteria determined at runtime.
"""
import pandas as pd
import os
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class CSVStore:
    def __init__(self, folder: str):
        """
        Initialize CSV store with a folder containing CSV files.
        
        Args:
            folder: Path to folder containing CSV files
        """
        self.folder = folder
        self.dfs = {}
        self._load_all_csvs()
    
    def _load_all_csvs(self):
        """
        Load all CSV files in the folder into dataframes.
        Files are accessed by their filename in self.dfs.
        """
        if not os.path.exists(self.folder):
            logger.warning(f"Folder not found: {self.folder}. Creating empty directory.")
            os.makedirs(self.folder, exist_ok=True)
            return
            
        for fname in os.listdir(self.folder):
            if fname.endswith(".csv"):
                try:
                    file_path = os.path.join(self.folder, fname)
                    self.dfs[fname] = pd.read_csv(file_path)
                    logger.info(f"Loaded {fname} with {len(self.dfs[fname])} rows")
                except Exception as e:
                    logger.error(f"Error loading {fname}: {str(e)}")
    
    def query(self, filters: Dict[str, Any], properties: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Generic query method that filters CSV data based on provided filters.
        No hardcoded dependencies - all filtering criteria determined at runtime.
        
        Args:
            filters: Dictionary of column:value pairs to filter on
            properties: Optional list of property names to filter on
            
        Returns:
            List of matching rows as dictionaries
        """
        results = []
        
        for fname, df in self.dfs.items():
            # Make a copy to avoid modifying the original
            df_filtered = df.copy()
            
            # First filter by properties if specified
            if properties and 'property_name' in df_filtered.columns:
                df_filtered = df_filtered[df_filtered['property_name'].isin(properties)]
            
            # Apply all other filters
            for col, value in filters.items():
                # Special case for country extraction from child_name
                if col == 'country' and 'child_name' in df_filtered.columns:
                    if isinstance(value, str) and len(value) == 2:
                        df_filtered = df_filtered[df_filtered['child_name'].str.startswith(value)]
                # Special case for tech extraction from category_name or child_name
                elif col == 'tech' and any(x in df_filtered.columns for x in ['category_name', 'child_name']):
                    if 'category_name' in df_filtered.columns:
                        tech_mask = df_filtered['category_name'].str.contains(value, case=False, na=False)
                        if 'child_name' in df_filtered.columns:
                            tech_mask = tech_mask | df_filtered['child_name'].str.contains(value, case=False, na=False)
                        df_filtered = df_filtered[tech_mask]
                # Standard column filtering
                elif col in df_filtered.columns:
                    df_filtered = df_filtered[df_filtered[col] == value]
            
            # If we found matches, add to results
            if not df_filtered.empty:
                for _, row in df_filtered.iterrows():
                    result_row = row.to_dict()
                    result_row['source_csv'] = fname
                    results.append(result_row)
        
        return results
    
    def list_available_properties(self) -> List[str]:
        """
        List all available property names across all CSVs.
        
        Returns:
            List of unique property names
        """
        properties = set()
        for df in self.dfs.values():
            if 'property_name' in df.columns:
                properties.update(df['property_name'].unique())
        return list(properties)
    
    def get_unique_values(self, column: str) -> List[Any]:
        """
        Get unique values for a column across all CSVs.
        
        Args:
            column: Column name to get unique values for
            
        Returns:
            List of unique values
        """
        values = set()
        for df in self.dfs.values():
            if column in df.columns:
                values.update(df[column].unique())
        return list(values)
