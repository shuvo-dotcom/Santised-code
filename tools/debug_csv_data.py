#!/usr/bin/env python
"""
Script to directly examine CSV data and debug extraction issues
"""
import os
import pandas as pd

# Load the CSV file
csv_path = os.path.join("data", "systemgenerators.csv")
df = pd.read_csv(csv_path)

# Print basic info
print(f"CSV file has {len(df)} rows and {len(df.columns)} columns")
print(f"Column names: {list(df.columns)}")

# Count nuclear rows
nuclear_rows = df[df['category_name'] == 'Nuclear']
print(f"Found {len(nuclear_rows)} rows with category_name = 'Nuclear'")

# Count Belgium rows
be_rows = df[df['child_name'].str.startswith('BE')]
print(f"Found {len(be_rows)} rows with child_name starting with 'BE'")

# Count rows for both nuclear and Belgium
nuclear_be_rows = df[(df['category_name'] == 'Nuclear') & (df['child_name'].str.startswith('BE'))]
print(f"Found {len(nuclear_be_rows)} rows with category_name = 'Nuclear' AND child_name starting with 'BE'")

# Count rows for 2050
year_2050_rows = df[df['date_string'] == '2050']
print(f"Found {len(year_2050_rows)} rows with date_string = '2050'")

# Count rows for all three filters combined
combined_rows = df[(df['category_name'] == 'Nuclear') & 
                   (df['child_name'].str.startswith('BE')) & 
                   (df['date_string'] == '2050')]
print(f"Found {len(combined_rows)} rows matching all three filters")

# Sample combined rows
if len(combined_rows) > 0:
    print("\nSample data for Nuclear + BE + 2050:")
    # Get 5 rows with Total Generation Cost
    gen_cost_rows = combined_rows[combined_rows['property_name'] == 'Total Generation Cost']
    if len(gen_cost_rows) > 0:
        print("\nTotal Generation Cost data:")
        print(gen_cost_rows[['property_name', 'value', 'unit_name', 'category_name', 'child_name']].head())
    else:
        print("No 'Total Generation Cost' rows found")
        
    # Get 5 rows with Generation
    gen_rows = combined_rows[combined_rows['property_name'] == 'Generation']
    if len(gen_rows) > 0:
        print("\nGeneration data:")
        print(gen_rows[['property_name', 'value', 'unit_name', 'category_name', 'child_name']].head())
    else:
        print("No 'Generation' rows found")
else:
    print("No rows match all three filters")
