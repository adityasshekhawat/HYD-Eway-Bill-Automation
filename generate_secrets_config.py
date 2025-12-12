#!/usr/bin/env python3
"""
Generate Streamlit Secrets Configuration
Converts CSV files into TOML format for Streamlit Secrets
"""

import pandas as pd
import json
from io import StringIO

print("=" * 70)
print("Streamlit Secrets Configuration Generator")
print("=" * 70)

# Read the sensitive CSV file
print("\n📖 Reading final_address_updated.csv...")
try:
    df = pd.read_csv('data/final_address_updated.csv')
    print(f"✅ Loaded {len(df)} rows")
except FileNotFoundError:
    print("❌ Error: data/final_address_updated.csv not found!")
    exit(1)

# Option 1: Generate as CSV string (simpler, easier to manage)
print("\n" + "=" * 70)
print("OPTION 1: CSV String Format (Recommended)")
print("=" * 70)
print("\nCopy this ENTIRE block to your Streamlit Secrets:\n")

print('[secrets]')
print('final_address_csv = """')
# Read the actual CSV file as string to preserve exact format
with open('data/final_address_updated.csv', 'r') as f:
    csv_content = f.read()
print(csv_content.rstrip())
print('"""')

# Option 2: Generate as JSON (more programmatic)
print("\n" + "=" * 70)
print("OPTION 2: JSON Format (Alternative)")
print("=" * 70)
print("\nOr use this if you prefer JSON:\n")

print('[final_address_data]')
# Convert DataFrame to JSON with proper escaping
json_data = df.to_json(orient='records', indent=2)
# Escape the JSON for TOML
json_escaped = json_data.replace('\\', '\\\\').replace('"', '\\"')
print(f'data = "{json_escaped}"')

# Generate hub addresses mapping
print("\n" + "=" * 70)
print("Hub Addresses Mapping")
print("=" * 70)
print("\n[hub_addresses]")

# Extract unique hub addresses
for _, row in df.iterrows():
    hub_name = row['Hub Name']
    address_line1 = row['HUB Buyers Address 1']
    address_line2 = row['HUB Buyers Address 1.1']
    pincode = row['HUB Buyers Pin code']
    
    full_address = f"{address_line1}, {address_line2}, {pincode}"
    # Escape quotes in address
    full_address_escaped = full_address.replace('"', '\\"')
    
    print(f'{hub_name} = "{full_address_escaped}"')

# Instructions
print("\n" + "=" * 70)
print("📋 NEXT STEPS:")
print("=" * 70)
print("""
1. Go to your Streamlit Cloud dashboard:
   https://share.streamlit.io/

2. Click on your app → ⚙️ Settings → Secrets

3. Copy OPTION 1 (CSV String Format) - it's the entire block above

4. Paste it into the Secrets text area

5. Click "Save"

6. Your app will automatically restart with the new secrets

7. The sensitive data files will now be loaded from Secrets in production
   and from local files in development

NOTE: Make sure to copy the ENTIRE block including:
- [secrets]
- final_address_csv = \"\"\"
- All the CSV data
- The closing \"\"\"
""")

print("\n✅ Configuration generated successfully!")
print("=" * 70)
