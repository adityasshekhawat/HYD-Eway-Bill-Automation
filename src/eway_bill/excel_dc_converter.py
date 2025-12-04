#!/usr/bin/env python3
"""
Excel DC to JSON Converter
Converts Excel-format DCs to JSON format for e-way bill template generation
"""

import os
import json
import pandas as pd
import re
import logging
from datetime import datetime
from openpyxl import load_workbook

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExcelDCConverter:
    """
    Converts Excel DC files to JSON format for e-way bill template generation
    """
    
    def __init__(self):
        """Initialize converter with standard mappings"""
        # Excel cell mappings for DC metadata based on dc_template_generator
        self.metadata_mappings = {
            'dc_number': 'C3',        # Serial no. of Challan
            'date': 'C4',             # Date of Challan
            'vehicle_number': 'F4',   # Vehicle number
            'sender_name': 'B8',      # Name (from dispatch)
            'receiver_name': 'F8',    # Name (of receiver)
            'from_facility': 'B8',    # Same as sender name
            'to_facility': 'F8',      # Same as receiver name
            'place_of_supply': 'C5',  # Place of Supply
            'state': 'C6',            # State
            'sender_address': 'B9',   # Address (from dispatch)
            'receiver_address': 'F9', # Address (of receiver)
            'sender_gstin': 'B10',    # GSTIN (from dispatch)
            'receiver_gstin': 'F10',  # GSTIN (of receiver)
            'sender_state': 'B12',    # State (from dispatch)
            'sender_state_code': 'D12', # State Code (from dispatch)
            'receiver_state': 'F12',  # State (of receiver)
            'receiver_state_code': 'H12' # State Code (of receiver)
        }
        
        # Product table start row (based on dc_template_generator)
        self.product_table_start_row = 14
        
        # Column mappings for product data
        self.product_columns = {
            'S.No.': 'A',             # Serial Number
            'Description': 'B',       # Product Description
            'HSN': 'C',               # HSN Code
            'Quantity': 'D',          # Quantity
            'Taxable Value': 'E',     # Taxable Value
            'GST Rate': 'F',          # GST Rate
            'CGST Amount': 'G',       # CGST Amount
            'SGST Amount': 'H',       # SGST Amount
            'Cess': 'I'               # Cess
        }
    
    def convert_excel_to_json(self, excel_file):
        """
        Convert Excel DC file to JSON format
        
        Args:
            excel_file: Path to Excel DC file
            
        Returns:
            Dictionary with DC data in JSON format
        """
        try:
            logger.info(f"Converting Excel DC: {excel_file}")
            
            # Load workbook
            wb = load_workbook(excel_file, data_only=True)
            sheet = wb.active
            
            # Extract metadata
            dc_data = {}
            for key, cell in self.metadata_mappings.items():
                value = sheet[cell].value
                if key == 'date' and isinstance(value, datetime):
                    value = value.strftime('%d-%b-%Y')  # Format date as DD-MMM-YYYY
                dc_data[key] = str(value) if value is not None else ''
            
            # Extract hub type from the file name or sender name
            dc_data['hub_type'] = self._extract_hub_type(excel_file, dc_data['sender_name'])
            
            # Use the extracted addresses directly from the DC
            dc_data['hub_address'] = dc_data.get('receiver_address', '')
            
            # Add distance (default to 100 km for intra-state)
            dc_data['distance'] = ''
            
            # Add from_facility and to_facility if not already extracted
            if 'from_facility' not in dc_data:
                dc_data['from_facility'] = dc_data.get('sender_name', '')
            if 'to_facility' not in dc_data:
                dc_data['to_facility'] = dc_data.get('receiver_name', '')
                
            # Extract products data
            products = self._extract_products(sheet)
            dc_data['products'] = products
            
            # Format dc_number to match expected format
            if 'dc_number' in dc_data:
                # If it doesn't already have a date format, add the date
                if not re.search(r'\d{1,2}-[A-Za-z]{3}-\d{4}', dc_data['dc_number']):
                    dc_data['dc_number'] = f"{dc_data['dc_number']}_{dc_data['date']}"
            
            logger.info(f"✅ Successfully converted DC {dc_data.get('dc_number', '')}")
            return dc_data
            
        except Exception as e:
            logger.error(f"❌ Error converting Excel DC: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_hub_type(self, file_path, sender_name):
        """
        Extract hub type from file name or sender name
        
        Args:
            file_path: Path to Excel file
            sender_name: Sender name from DC
            
        Returns:
            Hub type string (SOURCINGBEE, AMOLAKCHAND, etc.)
        """
        file_name = os.path.basename(file_path).upper()
        
        # Try to extract from file name
        if 'SOURCINGBEE' in file_name:
            return 'SOURCINGBEE'
        elif 'AMOLAKCHAND' in file_name:
            return 'AMOLAKCHAND'
        elif 'BODEGA' in file_name:
            return 'BODEGA'
        
        # Try to extract from sender name
        if sender_name:
            sender_name = sender_name.upper()
            if 'SOURCINGBEE' in sender_name:
                return 'SOURCINGBEE'
            elif 'AMOLAKCHAND' in sender_name:
                return 'AMOLAKCHAND'
            elif 'BODEGA' in sender_name:
                return 'BODEGA'
        
        # Default
        return 'SOURCINGBEE'
    
    def _extract_address(self, sheet):
        """
        Extract address from Excel sheet
        
        Args:
            sheet: Excel worksheet
            
        Returns:
            Address string
        """
        # Try to extract from standard cells
        address_parts = []
        
        # Sender address cells
        for row in range(9, 11):
            cell_value = sheet[f'C{row}'].value
            if cell_value:
                address_parts.append(str(cell_value).strip())
        
        # Extract pincode if available
        pincode = None
        address_text = ' '.join(address_parts)
        pincode_match = re.search(r'(\d{6})', address_text)
        if pincode_match:
            pincode = pincode_match.group(1)
        else:
            # Try to find pincode in other cells
            for row in range(9, 15):
                cell_value = str(sheet[f'C{row}'].value or '')
                pincode_match = re.search(r'(\d{6})', cell_value)
                if pincode_match:
                    pincode = pincode_match.group(1)
                    break
        
        # Extract state
        state = None
        state_patterns = [
            r'(Karnataka|Tamil Nadu|Maharashtra|Delhi|Telangana|Andhra Pradesh|Kerala|Uttar Pradesh|Gujarat|Haryana)',
            r'(KA|TN|MH|DL|TS|AP|KL|UP|GJ|HR)'  # State codes
        ]
        
        for pattern in state_patterns:
            for row in range(9, 15):
                cell_value = str(sheet[f'C{row}'].value or '')
                state_match = re.search(pattern, cell_value, re.IGNORECASE)
                if state_match:
                    state = state_match.group(1)
                    break
            if state:
                break
        
        # Map state codes to full names if needed
        state_code_mapping = {
            'KA': 'Karnataka',
            'TN': 'Tamil Nadu',
            'MH': 'Maharashtra',
            'DL': 'Delhi',
            'TS': 'Telangana',
            'AP': 'Andhra Pradesh',
            'KL': 'Kerala',
            'UP': 'Uttar Pradesh',
            'GJ': 'Gujarat',
            'HR': 'Haryana'
        }
        
        if state in state_code_mapping:
            state = state_code_mapping[state]
        
        # Default state if not found
        if not state:
            state = 'Karnataka'
        
        # Combine address with state and pincode
        if address_parts:
            address = ', '.join(address_parts)
            if state and state not in address:
                address += f', {state}'
            if pincode and pincode not in address:
                address += f' {pincode}'
        else:
            # Default address with state and pincode
            address = f"Bangalore, {state} {pincode or '560001'}"
        
        return address
    
    def _extract_products(self, sheet):
        """
        Extract products data from Excel sheet
        
        Args:
            sheet: Excel worksheet
            
        Returns:
            List of product dictionaries
        """
        products = []
        
        # Start from the product table start row (defined in __init__)
        start_row = self.product_table_start_row
        
        # Start from the row after header
        row = start_row + 1
        
        # Extract products until we hit a row with no description or "Total"
        while True:
            # Check if we've reached the end of the table
            description_cell = sheet[f"{self.product_columns['Description']}{row}"].value
            sno_cell = sheet[f"{self.product_columns['S.No.']}{row}"].value
            
            # Stop if we've reached the end (empty row or "Total" row)
            if not description_cell or (isinstance(sno_cell, str) and "total" in sno_cell.lower()) or row > 500:
                break
            
            # Extract product data
            product = {
                'item_name': str(sheet[f"{self.product_columns['Description']}{row}"].value or ''),
                'description': str(sheet[f"{self.product_columns['Description']}{row}"].value or ''),
                'hsn': str(sheet[f"{self.product_columns['HSN']}{row}"].value or ''),
                'quantity': self._get_numeric_value(sheet[f"{self.product_columns['Quantity']}{row}"].value),
                'unit': 'PCS',  # Default unit
                'unit_price': 0,  # Will be calculated if not available
                'taxable_value': self._get_numeric_value(sheet[f"{self.product_columns['Taxable Value']}{row}"].value),
                'GST Rate': self._get_numeric_value(sheet[f"{self.product_columns['GST Rate']}{row}"].value),
                'cgst_rate': self._get_numeric_value(sheet[f"{self.product_columns['GST Rate']}{row}"].value) / 2,
                'sgst_rate': self._get_numeric_value(sheet[f"{self.product_columns['GST Rate']}{row}"].value) / 2,
                'igst_rate': 0,  # For intra-state, IGST is 0
                'cgst_amount': self._get_numeric_value(sheet[f"{self.product_columns['CGST Amount']}{row}"].value),
                'sgst_amount': self._get_numeric_value(sheet[f"{self.product_columns['SGST Amount']}{row}"].value),
                'cess_rate': 0,
                'Cess': self._get_numeric_value(sheet[f"{self.product_columns['Cess']}{row}"].value),
                'Value': self._get_numeric_value(sheet[f"{self.product_columns['Taxable Value']}{row}"].value)
            }
            
            # Calculate unit price if not available
            if product['quantity'] > 0 and product['taxable_value'] > 0:
                product['unit_price'] = product['taxable_value'] / product['quantity']
            
            # Only add products with a description
            if product['description']:
                products.append(product)
            
            row += 1
        
        logger.info(f"Extracted {len(products)} products")
        return products
    
    def _get_numeric_value(self, value):
        """
        Convert a cell value to a numeric value
        
        Args:
            value: Cell value from Excel
            
        Returns:
            Numeric value (float)
        """
        try:
            # Handle percentage strings
            if isinstance(value, str) and '%' in value:
                return float(value.replace('%', ''))
            # Handle currency strings
            elif isinstance(value, str) and ('₹' in value or 'Rs.' in value):
                return float(re.sub(r'[^\d.]', '', value))
            # Handle other numeric values
            elif value is not None:
                return float(value)
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def convert_multiple_excel_files(self, excel_files):
        """
        Convert multiple Excel DC files to JSON
        
        Args:
            excel_files: List of paths to Excel DC files
            
        Returns:
            List of DC data dictionaries
        """
        dc_data_list = []
        
        for file_path in excel_files:
            dc_data = self.convert_excel_to_json(file_path)
            if dc_data:
                dc_data_list.append(dc_data)
        
        return dc_data_list
    
    def save_json(self, dc_data, output_file):
        """
        Save DC data to JSON file
        
        Args:
            dc_data: Dictionary with DC data
            output_file: Path to save the JSON file
            
        Returns:
            Path to the saved file
        """
        try:
            # Check if output file path is provided
            if not output_file:
                logger.warning("No output file path provided, skipping save")
                return None
                
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:  # Only create directory if path has a directory component
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"Ensuring output directory exists: {output_dir}")
            
            # Save to JSON
            with open(output_file, 'w') as f:
                json.dump(dc_data, f, indent=4)
            
            logger.info(f"✅ Saved DC data to {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error saving JSON: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert Excel DC files to JSON format')
    parser.add_argument('--input', '-i', help='Input Excel file or directory', required=True)
    parser.add_argument('--output', '-o', help='Output JSON file or directory', required=True)
    parser.add_argument('--batch', '-b', action='store_true', help='Process all Excel files in the input directory')
    args = parser.parse_args()
    
    converter = ExcelDCConverter()
    
    if args.batch:
        # Process all Excel files in directory
        if not os.path.isdir(args.input):
            logger.error(f"Input must be a directory when using batch mode")
            exit(1)
            
        # Find all Excel files
        excel_files = []
        for file in os.listdir(args.input):
            if file.endswith('.xlsx') or file.endswith('.xls'):
                excel_files.append(os.path.join(args.input, file))
        
        if not excel_files:
            logger.error(f"No Excel files found in {args.input}")
            exit(1)
            
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Convert each file
        for excel_file in excel_files:
            dc_data = converter.convert_excel_to_json(excel_file)
            if dc_data:
                # Generate output file name
                base_name = os.path.splitext(os.path.basename(excel_file))[0]
                output_file = os.path.join(args.output, f"{base_name}.json")
                converter.save_json(dc_data, output_file)
    else:
        # Process single file
        if not os.path.isfile(args.input):
            logger.error(f"Input file {args.input} not found")
            exit(1)
            
        dc_data = converter.convert_excel_to_json(args.input)
        if dc_data:
            converter.save_json(dc_data, args.output) 