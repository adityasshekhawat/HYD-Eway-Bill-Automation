#!/usr/bin/env python3
"""
E-Way Bill Template Generator Script
Generates e-way bill templates from existing DC data
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime
import argparse

# Add the project root to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.eway_bill.eway_bill_template_generator import EwayBillTemplateGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_dc_data(file_path):
    """
    Load DC data from a JSON file
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary with DC data
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading DC data from {file_path}: {str(e)}")
        return None

def find_dc_files(directory, pattern="*.json"):
    """
    Find all DC JSON files in a directory
    
    Args:
        directory: Directory to search in
        pattern: File pattern to match
        
    Returns:
        List of file paths
    """
    return glob.glob(os.path.join(directory, pattern))

def main():
    """Main function to generate e-way bill templates"""
    
    parser = argparse.ArgumentParser(description='Generate e-way bill templates from DC data')
    parser.add_argument('--input', '-i', help='Input directory or file with DC data', required=True)
    parser.add_argument('--output', '-o', help='Output file for the template', required=True)
    parser.add_argument('--batch', '-b', action='store_true', help='Process all files in the input directory')
    args = parser.parse_args()
    
    # Initialize template generator
    template_generator = EwayBillTemplateGenerator()
    
    # Generate timestamp for output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Process input
    if args.batch:
        # Process all files in directory
        dc_files = find_dc_files(args.input)
        if not dc_files:
            logger.error(f"No DC files found in {args.input}")
            return
            
        logger.info(f"Found {len(dc_files)} DC files to process")
        
        # Load all DC data
        dc_data_list = []
        for file_path in dc_files:
            dc_data = load_dc_data(file_path)
            if dc_data:
                dc_data_list.append(dc_data)
        
        # Generate output file name with timestamp
        output_file = args.output
        if not output_file.endswith('.csv'):
            output_file = f"{output_file}_{timestamp}.csv"
            
        # Generate template for all DCs
        template_generator.generate_template_for_multiple_dcs(dc_data_list, output_file)
        
        logger.info(f"✅ Generated e-way bill template for {len(dc_data_list)} DCs: {output_file}")
    else:
        # Process single file
        dc_data = load_dc_data(args.input)
        if not dc_data:
            logger.error(f"Failed to load DC data from {args.input}")
            return
            
        # Generate output file name with timestamp
        output_file = args.output
        if not output_file.endswith('.csv'):
            output_file = f"{output_file}_{timestamp}.csv"
            
        # Generate template
        rows = template_generator.generate_template_from_dc(dc_data)
        template_generator.save_to_csv(rows, output_file)
        
        logger.info(f"✅ Generated e-way bill template: {output_file}")

if __name__ == '__main__':
    main() 