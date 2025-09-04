#!/usr/bin/env python
"""
Script to check available years in the data
"""
import os
import pandas as pd

# Load the CSV file
csv_path = os.path.join("data", "systemgenerators.csv")
df = pd.read_csv(csv_path)

# Get unique date strings
date_strings = df['date_string'].unique()
print(f"Available date_string values: {sorted(date_strings)}")

# Sample nuclear BE rows
nuclear_be_rows = df[(df['category_name'] == 'Nuclear') & 
                     (df['child_name'].str.startswith('BE'))]

# Get unique dates for nuclear BE
nuclear_be_dates = nuclear_be_rows['date_string'].unique()
print(f"\nAvailable date_string values for Nuclear+BE: {sorted(nuclear_be_dates)}")

# Check sample data for one of these dates
if len(nuclear_be_dates) > 0:
    sample_date = nuclear_be_dates[0]
    sample_rows = df[(df['category_name'] == 'Nuclear') & 
                     (df['child_name'].str.startswith('BE')) & 
                     (df['date_string'] == sample_date)]
    
    print(f"\nSample data for Nuclear + BE + {sample_date}:")
    
    # Get rows with Total Generation Cost
    gen_cost_rows = sample_rows[sample_rows['property_name'] == 'Total Generation Cost']
    if len(gen_cost_rows) > 0:
        print("\nTotal Generation Cost data:")
        print(gen_cost_rows[['property_name', 'value', 'unit_name', 'category_name', 'child_name']].head())
    else:
        print("No 'Total Generation Cost' rows found")
        
    # Get rows with Generation
    gen_rows = sample_rows[sample_rows['property_name'] == 'Generation']
    if len(gen_rows) > 0:
        print("\nGeneration data:")
        print(gen_rows[['property_name', 'value', 'unit_name', 'category_name', 'child_name']].head())
    else:
        print("No 'Generation' rows found")
