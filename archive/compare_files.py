#!/usr/bin/env python3
"""
Compare original and processed data files to verify calculations
"""

import pandas as pd
from decimal import Decimal
import json

def load_file(file_path: str) -> pd.DataFrame:
    """Load CSV file and clean numeric columns"""
    df = pd.read_csv(file_path)
    
    # Clean column names
    df.columns = [col.strip().lower() for col in df.columns]
    
    # Clean numeric columns
    numeric_columns = ['taxable_amount', 'gst', 'cgst', 'sgst', 'cess', 'total_amount']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
    
    return df

def compare_files():
    """Compare original and processed files"""
    print("🔍 Comparing files...")
    
    # Load both files
    original = load_file('input_data/Mys-V1 - Paste Query Data Over Here.csv')
    processed = load_file('input_data/processed_data.csv')
    
    print("\n=== Basic Comparison ===")
    print(f"Original rows: {len(original)}")
    print(f"Processed rows: {len(processed)}")
    
    # Compare columns
    original_cols = set(original.columns)
    processed_cols = set(processed.columns)
    
    print("\n=== Column Comparison ===")
    print("Original columns:", sorted(original_cols))
    print("Processed columns:", sorted(processed_cols))
    print("\nNew columns in processed:", sorted(processed_cols - original_cols))
    print("Columns only in original:", sorted(original_cols - processed_cols))
    
    # Compare key numeric columns
    print("\n=== Value Comparison ===")
    numeric_cols = ['taxable_amount', 'gst', 'cgst', 'sgst', 'cess']
    
    for col in numeric_cols:
        if col in original.columns and col in processed.columns:
            print(f"\n{col.upper()} Comparison:")
            original_sum = original[col].sum()
            processed_sum = processed[col].sum()
            
            print(f"Original sum: {original_sum:,.2f}")
            print(f"Processed sum: {processed_sum:,.2f}")
            
            if abs(original_sum - processed_sum) < 0.01:
                print("✅ Values match")
            else:
                print(f"❌ Difference: {abs(original_sum - processed_sum):,.2f}")
                
                # Show sample of differences
                diff_mask = abs(original[col] - processed[col]) > 0.01
                if diff_mask.any():
                    print("\nSample differences:")
                    diff_df = pd.DataFrame({
                        'JPIN': original.loc[diff_mask, 'jpin'],
                        'Original': original.loc[diff_mask, col],
                        'Processed': processed.loc[diff_mask, col],
                        'Difference': original.loc[diff_mask, col] - processed.loc[diff_mask, col]
                    }).head()
                    print(diff_df.to_string())

if __name__ == "__main__":
    compare_files() 