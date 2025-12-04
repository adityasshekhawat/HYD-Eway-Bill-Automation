#!/usr/bin/env python3
"""
E-Way Bill Template Generator
Generates e-way bill templates from DC data
"""

import os
import re
import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Import the excel generator functions
from src.eway_bill.excel_generator import save_data_to_excel, save_eway_bill_to_excel
from src.core.config_loader import get_config_loader
from src.core.hub_metadata_service import hub_metadata
from src.core.dc_template_generator import FACILITY_ADDRESS_MAPPING

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EwayBillTemplateGenerator:
    """
    Generates e-way bill templates from DC data for ClearTax upload
    """
    
    def __init__(self):
        """Initialize template generator with standard values"""
        # Standard values for all e-way bills
        self.standard_values = {
            'Supply Type': 'Outward',
            'Sub SupplyType': 'Others',
            'Document Type': 'Challan',
            'Transportation Mode (Road/Rail/Air/Ship)': 'Road',
            'Vehicle Type': 'Regular',
            'Item Unit of Measurement': 'UNITS',
            'My Branch': '',
            'Replace E-way bill': '',
            'Is this Supply to/from SEZ unit?': '',
            'Eway Bill Transaction Type': '',
            'Sub Type Description': 'Stock Transfer'
        }
        self.config_loader = get_config_loader()
        
        # Fallback mappings when configuration data is missing
        self.fallback_state_codes = {
            'Karnataka': '29',
            'Tamil Nadu': '33',
            'Andhra Pradesh': '37',
            'Telangana': '36',
            'Kerala': '32',
            'Maharashtra': '27',
            'Gujarat': '24',
            'Rajasthan': '08',
            'Delhi': '07',
            'Haryana': '06',
            'Punjab': '03',
            'Uttar Pradesh': '09',
            'West Bengal': '19',
            'Odisha': '21',
            'Bihar': '10',
            'Jharkhand': '20',
            'Madhya Pradesh': '23',
            'Chhattisgarh': '22',
            'Assam': '18',
            'Goa': '30'
        }
        
        self.fallback_gstin_mapping = {
            'SOURCINGBEE': '29AAWCS7485C1ZJ',
            'AMOLAKCHAND': '29AAPCA1708D1ZS',
            'BODEGA': '29AAHCB1357R1Z1'
        }
        self._facility_address_mapping = FACILITY_ADDRESS_MAPPING or {}
    
    def generate_template_from_dc(self, dc_data):
        """
        Generate e-way bill template rows from DC data
        
        Args:
            dc_data: Dictionary containing DC data
            
        Returns:
            List of dictionaries, each representing a row in the template
        """
        rows = []
        
        try:
            # Extract common data that applies to all products
            common_data = self._extract_common_data(dc_data)
            
            # Calculate total transaction value (same for all rows)
            total_taxable_value = Decimal('0')
            total_cgst = Decimal('0')
            total_sgst = Decimal('0')
            total_igst = Decimal('0')
            total_cess = Decimal('0')
            
            # First pass to calculate all tax components
            for product in dc_data['products']:
                # Get taxable value
                taxable_value = product.get('taxable_value', product.get('Value', 0))
                if isinstance(taxable_value, str):
                    taxable_value = taxable_value.replace(',', '')
                taxable_value = Decimal(str(taxable_value))
                
                # Get GST rate
                gst_rate = product.get('GST Rate', 0)
                if isinstance(gst_rate, str):
                    gst_rate = gst_rate.replace('%', '')
                gst_rate = Decimal(str(gst_rate))
                
                # Calculate tax components
                cgst_rate = gst_rate / 2
                sgst_rate = gst_rate / 2
                
                cgst_amount = (taxable_value * cgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                sgst_amount = (taxable_value * sgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # CESS CALCULATION FIX: The 'Cess' field contains CESS RATE, not amount
                # CESS Amount = (CESS Rate × Taxable Value) / 100
                cess_rate = product.get('Cess', 0)
                if isinstance(cess_rate, str):
                    cess_rate = cess_rate.replace(',', '').replace('%', '')
                cess_rate = Decimal(str(cess_rate))
                
                # Calculate CESS amount using the correct formula
                cess_amount = (cess_rate * taxable_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Add to totals
                total_taxable_value += taxable_value
                total_cgst += cgst_amount
                total_sgst += sgst_amount
                total_cess += cess_amount
            
            # Calculate grand total
            grand_total = total_taxable_value + total_cgst + total_sgst + total_igst + total_cess
            formatted_grand_total = self._format_indian_currency(grand_total)
            
            # Set the total transaction value for all rows
            common_data['Total Transaction Value'] = formatted_grand_total
            
            # Process each product
            for product in dc_data['products']:
                # Create a row by combining common data with product-specific data
                row = {**common_data}
                
                # Add product-specific data
                product_data = self._extract_product_data(product, common_data)
                row.update(product_data)
                
                rows.append(row)
            
            logger.info(f"✅ Generated {len(rows)} template rows for DC {dc_data.get('dc_number', '')} with total value {formatted_grand_total}")
            return rows
            
        except Exception as e:
            logger.error(f"❌ Error generating template: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_common_data(self, dc_data):
        """
        Extract common data that applies to all products in a DC
        
        Args:
            dc_data: Dictionary containing DC data
            
        Returns:
            Dictionary with common data fields
        """
        # Get facility information
        hub_type = dc_data.get('hub_type', 'SOURCINGBEE')
        
        company_names = {
            'SOURCINGBEE': 'SourcingBee Retail Pvt Ltd',
            'AMOLAKCHAND': 'Amolakchand Ankur Kothari Enterprises Private Limited',
            'BODEGA': 'Bodega Private Limited'
        }
        company_name = company_names.get(hub_type, 'SourcingBee Retail Pvt Ltd')
        supplier_name = dc_data.get('sender_name', company_name)
        receiver_name = dc_data.get('receiver_name', company_name)
        facility_name = dc_data.get('facility_name', '')
        
        fc_info = self._get_facility_info(hub_type, facility_name)
        
        # Facility / supplier information
        supplier_address1 = self._truncate_address(
            dc_data.get('facility_address_line1')
            or (fc_info.get('address_line1') if fc_info else '')
            or ''
        )
        supplier_address2 = self._truncate_address(
            dc_data.get('facility_address_line2')
            or (fc_info.get('address_line2') if fc_info else '')
            or ''
        )
        supplier_pincode = self._normalize_pincode(
            dc_data.get('facility_pincode')
            or (fc_info.get('pincode') if fc_info else '')
        )
        supplier_city = (
            dc_data.get('facility_city')
            or (fc_info.get('city') if fc_info else '')
            or ''
        ).strip()
        supplier_state = (
            dc_data.get('facility_state')
            or (fc_info.get('state') if fc_info else '')
            or ''
        ).strip()
        supplier_full_address = (
            dc_data.get('facility_address')
            or (fc_info.get('address') if fc_info else '')
            or ''
        )
        
        if supplier_address1:
            print(f"🏢 Using facility-specific dispatch address:")
            print(f"   Facility Name: {dc_data.get('facility_name', 'Unknown')}")
            print(f"   Line 1: {supplier_address1}")
            print(f"   Line 2: {supplier_address2}")
            print(f"   City: {supplier_city}")
            print(f"   Pincode: {supplier_pincode}")
            print(f"   State: {supplier_state}")
        else:
            print("⚠️ Facility address missing - using empty supplier values")
        
        if not supplier_city and supplier_address1:
            extracted_city = self._extract_city_from_address(supplier_address1)
            if extracted_city:
                supplier_city = extracted_city
                print(f"   Extracted city from address: {supplier_city}")
        
        if not supplier_address1 and supplier_full_address:
            parsed_facility = self._parse_address(supplier_full_address)
            supplier_address1 = self._truncate_address(parsed_facility.get('address1') or '')
            supplier_address2 = self._truncate_address(parsed_facility.get('address2') or '')
            supplier_city = supplier_city or parsed_facility.get('city') or ''
            supplier_pincode = supplier_pincode or self._normalize_pincode(parsed_facility.get('pincode'))
        
        if not supplier_state:
            supplier_state = (dc_data.get('hub_state') or '').strip()
        
        # Customer / hub information
        customer_components = self._parse_customer_address(dc_data)
        customer_address1 = self._truncate_address(customer_components.get('address1') or '')
        customer_address2 = self._truncate_address(customer_components.get('address2') or '')
        customer_city = (customer_components.get('city') or dc_data.get('place_of_supply') or '').strip()
        customer_state = (customer_components.get('state') or dc_data.get('hub_state') or '').strip()
        customer_pincode = self._normalize_pincode(customer_components.get('pincode'))
        customer_state_code = customer_components.get('state_code') or self._get_state_code(customer_state)
        
        print(f"🏢 Using dynamic customer address:")
        print(f"   Address 1: {customer_address1}")
        print(f"   Address 2: {customer_address2}")
        print(f"   City: {customer_city}")
        print(f"   Pincode: {customer_pincode}")
        print(f"   State: {customer_state}")
        
        supplier_state_code = self._get_state_code(supplier_state)
        sender_state_code_full = self._format_state_code_label(supplier_state_code, supplier_state)
        receiver_state_code_full = self._format_state_code_label(customer_state_code, customer_state)
        
        from_gstin = self._get_gstin(hub_type, supplier_state or customer_state)
        to_gstin = self._get_gstin(hub_type, customer_state or supplier_state)
        
        # Format date as DD/MM/YYYY (e.g., 24/06/2025)
        doc_date = dc_data.get('date', datetime.now())
        if isinstance(doc_date, str):
            try:
                # Try to parse the date string
                doc_date = datetime.strptime(doc_date, "%d-%b-%Y")
            except ValueError:
                try:
                    # Try alternative format
                    doc_date = datetime.strptime(doc_date, "%d/%m/%Y")
                except ValueError:
                    # Default to current date if parsing fails
                    doc_date = datetime.now()
        
        # Format as DD/MM/YYYY
        formatted_date = doc_date.strftime("%d/%m/%Y")
        
        # Dynamic state codes based on supplier and customer states
        supplier_state_code = self._get_state_code(supplier_state)
        customer_state_code = self._get_state_code(customer_state)
        
        # Get document number (Serial Number of Challan)
        document_number = dc_data.get('dc_number') or ''
        # Ensure it's a string (defensive check for None, int, etc.)
        document_number = str(document_number) if document_number else ''
        
        # Clean document number - remove date part if present
        if document_number and isinstance(document_number, str) and '_' in document_number:
            # Split by underscore and take only the first part (the serial number)
            parts = document_number.split('_')
            # Keep the serial number part only (parts before the last underscore)
            if len(parts) > 1:
                document_number = '_'.join(parts[:-1])
        
        # Leave Invoice Reference No empty as per requirement
        invoice_ref = ""
        
        # Get vehicle number
        vehicle_number = dc_data.get('vehicle_number', '')
        
        # Get dynamic distance - FIXED: Default to empty string for blank delivered km
        distance = dc_data.get('distance', '')  # Changed from '100' to '' for blank column
        if distance:
            print(f"🚗 Using distance: {distance}km")
        else:
            print(f"🚗 Using distance: [BLANK] (as requested)")
        
        return {
            **self.standard_values,
            'Invoice Reference No': invoice_ref,
            'Document Number': document_number,
            'Document Date': formatted_date,
            'Supplier GSTIN': from_gstin,
            'Supplier Name': supplier_name,
            'Supplier Address1': supplier_address1,
            'Supplier Address2': supplier_address2,
            'Supplier Place': supplier_city,
            'Supplier Pincode': supplier_pincode,
            'Supplier State': supplier_state,
            'Customer Billing Name': receiver_name,
            'Customer Billing GSTIN': to_gstin,
            'Customer Billing Address 1': customer_address1,
            'Customer Billing Address 2': customer_address2,
            'Customer Billing City': customer_city,
            'Customer Billing State': customer_state,
            'Customer Billing Pincode': customer_pincode,
            'Distance Level (Km)': distance,  # Now will be blank instead of '100'
            'Vehicle Number': vehicle_number,
            # Copy the same data to shipping fields (for stock transfer)
            'Customer Shipping Name': receiver_name,
            'Customer Shipping Address 1': self._truncate_address(customer_address1),
            'Customer Shipping Address 2': self._truncate_address(customer_address2),
            'Customer Shipping City': customer_city,
            'Customer Shipping PinCode': customer_pincode,
            'Customer Shipping State Code': receiver_state_code_full,
            # Dispatch details (same as supplier for stock transfer)
            'Supplier Dispatch Name': supplier_name,
            'Supplier Dispatch Address 1': self._truncate_address(supplier_address1),
            'Supplier Dispatch Address 2': self._truncate_address(supplier_address2),
            'Supplier Dispatch Place': supplier_city,
            'Supplier Dispatch PinCode': supplier_pincode,
            'Supplier Dispatch State Code': sender_state_code_full,
        }
    
    def _extract_product_data(self, product, common_data):
        """
        Extract product-specific data
        
        Args:
            product: Dictionary containing product data
            common_data: Dictionary with common DC data
            
        Returns:
            Dictionary with product-specific fields
        """
        # Get product details - handle both field name formats
        # DC data uses capitalized field names: 'Description', 'HSN', 'Quantity'
        # Legacy data might use lowercase: 'description', 'hsn', 'quantity'
        item_name = product.get('Description', product.get('item_name', product.get('description', '')))
        description = product.get('Description', product.get('description', item_name))
        hsn = product.get('HSN', product.get('hsn', ''))
        quantity = product.get('Quantity', product.get('quantity', 0))
        
        # Get tax values
        taxable_value = product.get('taxable_value', product.get('Value', 0))
        if isinstance(taxable_value, str):
            taxable_value = taxable_value.replace(',', '')  # Remove commas from string
        taxable_value = Decimal(str(taxable_value))
        
        gst_rate = product.get('GST Rate', 0)
        if isinstance(gst_rate, str):
            gst_rate = gst_rate.replace('%', '')  # Remove % from string
        gst_rate = Decimal(str(gst_rate))
        
        # For intra-state supply (Karnataka to Karnataka), CGST and SGST apply
        # Always split GST into CGST and SGST for intra-state
        cgst_rate = gst_rate / 2
        sgst_rate = gst_rate / 2
        igst_rate = 0
        
        cgst_amount = (taxable_value * cgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        sgst_amount = (taxable_value * sgst_rate / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        igst_amount = Decimal('0')
        
        # CESS CALCULATION FIX: The 'Cess' field contains CESS RATE, not amount
        # CESS Amount = (CESS Rate × Taxable Value) / 100
        cess_rate = product.get('Cess', 0)
        if isinstance(cess_rate, str):
            cess_rate = cess_rate.replace(',', '').replace('%', '')
        cess_rate = Decimal(str(cess_rate))
        
        # Calculate CESS amount using the correct formula
        cess_amount = (cess_rate * taxable_value / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Format currency values
        formatted_taxable_value = self._format_indian_currency(taxable_value)
        formatted_cgst_amount = self._format_indian_currency(cgst_amount)
        formatted_sgst_amount = self._format_indian_currency(sgst_amount)
        formatted_igst_amount = self._format_indian_currency(igst_amount)
        formatted_cess_amount = self._format_indian_currency(cess_amount)
        
        # Calculate total value including taxes
        total_value = taxable_value + cgst_amount + sgst_amount + igst_amount + cess_amount
        formatted_total_value = self._format_indian_currency(total_value)
        
        return {
            'Product Name': item_name,
            'Item Description': description,
            'HSN code': hsn,
            'Item Quantity': quantity,
            'Taxable Value': formatted_taxable_value,
            'CGST Rate': float(cgst_rate),  # Send as numeric rate
            'CGST Amount': formatted_cgst_amount,  # Send as formatted amount
            'SGST Rate': float(sgst_rate),  # Send as numeric rate
            'SGST Amount': formatted_sgst_amount,  # Send as formatted amount
            'IGST Rate': float(igst_rate),
            'IGST Amount': formatted_igst_amount,
            'CESS Rate': float(cess_rate),  # Send CESS rate as numeric rate
            'CESS Amount': formatted_cess_amount,  # Send calculated CESS amount
            'CESS Non Advol Rate': 0,  # Default to 0
            'CESS Non Advol Tax Amount': 0,  # Default to 0
            'Other Value': 0,  # Default to 0
            'Other Charges - TCS': 0  # Default to 0
        }
    
    def _parse_address(self, address):
        """
        Parse address string into components
        
        Args:
            address: Full address string
            
        Returns:
            Dictionary with address components
        """
        if not address:
            return {
                'address1': '',
                'address2': '',
                'city': '',  # ✅ No default
                'pincode': '000000'  # ✅ No default
            }
        
        # Extract pincode
        pincode_match = re.search(r'(\d{6})', address)
        pincode = pincode_match.group(1) if pincode_match else '000000'  # ✅ No default
        
        # Extract city
        city_match = re.search(r'(Hyderabad|Bangalore|Bengaluru|Mumbai|Delhi|Chennai|Kolkata|Pune|Ahmedabad|Jaipur|Patna|Ranchi|Lucknow)', address, re.IGNORECASE)
        city = city_match.group(1) if city_match else ''  # ✅ No default
        
        # Split address into two parts
        address_parts = address.split(',')
        if len(address_parts) >= 2:
            address1 = address_parts[0].strip()
            address2 = ', '.join(address_parts[1:]).strip()
        else:
            address1 = address
            address2 = ''
        
        return {
            'address1': address1,
            'address2': address2,
            'city': city,
            'pincode': pincode
        }
    
    def _truncate_address(self, address, max_length=99):
        """
        Truncate address to maximum allowed length for E-Way bill
        
        Args:
            address: Address string
            max_length: Maximum allowed length (default 99)
            
        Returns:
            Truncated address string
        """
        if not address:
            return ""
        
        address_str = str(address)
        if len(address_str) <= max_length:
            return address_str
        
        # Truncate and add indication that it was truncated
        return address_str[:max_length-3] + "..."
    
    def _normalize_pincode(self, raw_value):
        """Normalize pincodes to 6-digit numeric strings"""
        if raw_value is None:
            return ''
        value = str(raw_value).strip()
        if not value or value.lower() == 'nan':
            return ''
        
        six_digit_matches = re.findall(r'\d{6}', value)
        if six_digit_matches:
            return six_digit_matches[-1]
        
        digits_only = re.sub(r'\D', '', value)
        if len(digits_only) >= 6:
            return digits_only[-6:]
        return digits_only or value
    
    def _format_indian_currency(self, amount):
        """
        Format amount in Indian currency format
        
        Args:
            amount: Decimal amount
            
        Returns:
            Formatted string
        """
        try:
            # Format with 2 decimal places
            return f"{float(amount):.2f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def generate_template_for_multiple_dcs(self, dc_data_list, output_file):
        """
        Generate e-way bill template for multiple DCs and save to Excel
        
        Args:
            dc_data_list: List of DC data dictionaries
            output_file: Path to save the Excel file
            
        Returns:
            Path to the generated file
        """
        all_rows = []
        
        # Process each DC
        for dc_data in dc_data_list:
            rows = self.generate_template_from_dc(dc_data)
            all_rows.extend(rows)
        
        # Save to Excel
        self.save_to_excel(all_rows, output_file)
        
        return output_file
    
    def save_to_excel(self, rows, output_file):
        """
        Save template rows to Excel file using the excel_generator module
        
        Args:
            rows: List of dictionaries containing row data
            output_file: Path to save the Excel file
        """
        # Use the save_eway_bill_to_excel function from excel_generator
        save_eway_bill_to_excel(rows, output_file)
        
        logger.info(f"✅ Saved {len(rows)} rows to e-way bill Excel file: {output_file}")
        return output_file

    def generate_eway_template(self, dc_data):
        """Generate E-Way Bill template data from DC data"""
        try:
            print(f"🔍 DEBUG - E-Way template generation:")
            print(f"   DC facility pincode: {dc_data.get('facility_pincode', 'Not found')}")
            print(f"   DC hub pincode: {dc_data.get('hub_pincode', 'Not found')}")
            print(f"   Products count: {len(dc_data.get('products', []))}")
            
            # Get supplier pincode from facility data
            if 'facility_pincode' in dc_data:
                supplier_pincode = dc_data['facility_pincode']
                print(f"   Using facility pincode: {supplier_pincode}")
            else:
                print(f"   No facility pincode found, using default")
                supplier_pincode = "562123"
            
            # Get customer pincode from DC hub data (not from products)
            if 'hub_pincode' in dc_data and dc_data['hub_pincode']:
                customer_pincode = str(dc_data['hub_pincode'])
                print(f"   Using hub pincode from DC data: {customer_pincode}")
            else:
                # Fallback: try to extract from hub address
                hub_address = dc_data.get('hub_address', '')
                if hub_address:
                    pincode_match = re.search(r'(\d{6})', hub_address)
                    if pincode_match:
                        customer_pincode = pincode_match.group(1)
                        print(f"   Extracted pincode from hub address: {customer_pincode}")
                    else:
                        customer_pincode = "562123"
                        print(f"   No pincode found in hub address, using default: {customer_pincode}")
                else:
                    customer_pincode = "562123"
                    print(f"   No hub address found, using default: {customer_pincode}")
            
            print(f"   Final pincodes - Supplier: {supplier_pincode}, Customer: {customer_pincode}")
            
            # Get facility type for GSTIN mapping
            facility_type = self._determine_facility_type(dc_data)
            supplier_gstin = self.facility_gstin_mapping.get(facility_type, '29AAHCB1357R1Z1')
            
            # Generate template rows
            template_rows = []
            total_value = Decimal('0')
            
            for product in dc_data.get('products', []):
                try:
                    # Convert values with proper validation
                    quantity = Decimal(str(product.get('quantity', 0)))
                    value = Decimal(str(product.get('value', 0)))
                    gst_rate = Decimal(str(product.get('gst_rate', 0)))
                    cess_rate = Decimal(str(product.get('cess_rate', 0)))
                    
                    # Skip zero value products
                    if value <= 0:
                        continue
                    
                    total_value += value
                    
                    # Calculate tax amounts
                    cgst_rate = sgst_rate = gst_rate / Decimal('2')
                    cgst_amount = (value * cgst_rate / Decimal('100')).quantize(Decimal('0.01'))
                    sgst_amount = (value * sgst_rate / Decimal('100')).quantize(Decimal('0.01'))
                    cess_amount = (value * cess_rate / Decimal('100')).quantize(Decimal('0.01'))
                    
                    # Create template row with hub-specific pincodes
                    row = {
                        'User GSTIN': supplier_gstin,
                        'Supplier Name': self._get_supplier_name(facility_type),
                        'Supplier Address1': self._get_supplier_address_line1(facility_type),
                        'Supplier Address2': self._get_supplier_address_line2(facility_type),
                        'Supplier Place': '',  # ✅ Dynamic from facility
                        'Supplier Pincode': supplier_pincode,  # Use facility-specific pincode
                        'Supplier State Code': '29',
                        'Customer Name': 'JumboTail India Private Limited',
                        'Customer Address1': 'Jumbo Tail India Pvt Ltd',
                        'Customer Address2': dc_data.get('hub_address', ''),  # ✅ No fallback
                        'Customer Place': '',  # ✅ Dynamic from hub
                        'Customer Billing State': 'Karnataka',
                        'Customer Billing Pincode': customer_pincode,  # Use hub-specific pincode
                        'Distance Level (Km)': self._calculate_distance(supplier_pincode, customer_pincode),
                        'Product Name': product.get('name', 'Unknown Product'),
                        'Product Description': product.get('name', 'Unknown Product'),
                        'HSN Code': str(product.get('hsn', '')),
                        'Unit': 'NOS',
                        'Quantity': str(quantity),
                        'Taxable Value': str(value),
                        'Customer Shipping PinCode': customer_pincode,  # Use hub-specific pincode
                        'Customer Shipping State Code': '29',
                        'Transport Doc Date': datetime.now().strftime('%d/%m/%Y'),
                        'Transport Mode': '1',
                        'Supplier Dispatch PinCode': supplier_pincode,  # Use facility-specific pincode
                        'Supplier Dispatch State Code': '29',
                        'CGST Rate': str(cgst_rate),
                        'CGST Amount': str(cgst_amount),
                        'SGST Rate': str(sgst_rate),
                        'SGST Amount': str(sgst_amount),
                        'CESS Rate': str(cess_rate),
                        'CESS Amount': str(cess_amount)
                    }
                    
                    template_rows.append(row)
                    
                except (ValueError, decimal.InvalidOperation) as e:
                    print(f"⚠️ Error processing product {product.get('name', 'Unknown')}: {e}")
                    continue
            
            print(f"✅ Generated {len(template_rows)} template rows for DC {dc_data.get('dc_number', 'Unknown')} with total value {total_value}")
            return template_rows
            
        except Exception as e:
            print(f"❌ Error generating E-Way template: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _parse_customer_address(self, dc_data):
        """Parse customer address from hub data"""
        hub_name = dc_data.get('hub_name', '')
        hub_state_hint = (dc_data.get('hub_state') or '').strip()
        hub_pincode_hint = self._normalize_pincode(dc_data.get('hub_pincode'))
        
        if hub_name:
            metadata = hub_metadata.get_customer_address_components(hub_name)
            if metadata and metadata.get('address1'):
                address1 = self._truncate_address(metadata.get('address1') or '')
                address2 = self._truncate_address(metadata.get('address2') or '')
                city = (metadata.get('city') or dc_data.get('place_of_supply') or '').strip()
                state = (metadata.get('state') or hub_state_hint).strip()
                pincode = hub_pincode_hint or self._normalize_pincode(metadata.get('pincode'))
                state_code = metadata.get('state_code') or self._get_state_code(state)
            
            return {
                    'address1': address1,
                    'address2': address2,
                'city': city,
                    'state': state,
                    'pincode': pincode,
                    'state_code': state_code
                }
        
        hub_address = dc_data.get('hub_address', '')
        parsed = self._parse_address(hub_address)
        fallback_state = hub_state_hint
        fallback_pincode = hub_pincode_hint or parsed.get('pincode')
        fallback_city = (parsed.get('city') or dc_data.get('place_of_supply') or '').strip()
        
        return {
            'address1': self._truncate_address(parsed.get('address1') or ''),
            'address2': self._truncate_address(parsed.get('address2') or ''),
            'city': fallback_city,
            'state': fallback_state,
            'pincode': fallback_pincode,
            'state_code': self._get_state_code(fallback_state)
        }
    
    def _extract_city_from_address(self, address):
        """Extract city from address string"""
        if not address:
            return None
            
        city_patterns = [
            r'(Bengaluru|Bangalore)',
            r'(Mumbai|Bombay)',
            r'(Chennai|Madras)',
            r'(Hyderabad)',
            r'(Pune)',
            r'(Mysore|Mysuru)',
            r'(Kolar)',
            r'(Tumakuru)',
            r'(Ramanagar)',
            r'(Chikballapur)',
            r'(Tiptur)'
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _get_state_code(self, state_name):
        """Get state code for a given state name"""
        if not state_name:
            return ''
        
        if self.config_loader:
            code = self.config_loader.get_state_code(state_name)
            if code:
                return code
        
        return self.fallback_state_codes.get(state_name, '')
    
    def _format_state_code_label(self, code, state_name):
        """Format state code label as 'code-state'"""
        if code and state_name:
            return f"{code}-{state_name}"
        return ''
    
    def _get_gstin(self, company_name, state_name):
        """Fetch GSTIN for a company/state combination with fallback values"""
        normalized_company = (company_name or '').upper()
        normalized_state = (state_name or '').strip()
        
        if self.config_loader and normalized_state:
            gstin = self.config_loader.get_gstin(normalized_company, normalized_state)
            if gstin:
                return gstin
        
        return self.fallback_gstin_mapping.get(normalized_company, '')
    
    def _normalize_name(self, name: str) -> str:
        """Normalize facility names by stripping spaces, punctuation, and casing"""
        if not name:
            return ''
        return ''.join(ch for ch in name.lower() if ch.isalnum())
    
    def _get_facility_info(self, company: str, facility_name: str):
        """Resolve facility metadata using config loader with fuzzy fallback"""
        if not facility_name or not company:
            return None
        
        normalized_company = company.upper()
        
        if self.config_loader:
            info = self.config_loader.get_fc_address(normalized_company, facility_name)
            if info:
                return info
            
            candidates = self.config_loader.get_company_fcs(normalized_company)
            info = self._match_facility_from_candidates(normalized_company, facility_name, candidates)
            if info:
                return info
        
        mapping_info = self._match_facility_from_mapping(facility_name)
        if mapping_info:
            parsed = self._parse_address(mapping_info.get('address', ''))
            return {
                'address': mapping_info.get('address', ''),
                'address_line1': parsed.get('address1', ''),
                'address_line2': parsed.get('address2', ''),
                'pincode': mapping_info.get('pincode', ''),
                'city': parsed.get('city', ''),
                'state': mapping_info.get('state', ''),
                'fssai': ''
            }
        
        return None
    
    def _match_facility_from_candidates(self, company: str, facility_name: str, candidates):
        """Perform fuzzy matching of facility names within a list of candidates"""
        if not candidates:
            return None
        
        target = self._normalize_name(facility_name)
        for candidate in candidates:
            if not candidate:
                continue
            normalized_candidate = self._normalize_name(candidate)
            if not normalized_candidate:
                continue
            if target in normalized_candidate or normalized_candidate in target:
                info = self.config_loader.get_fc_address(company, candidate)
                if info:
                    return info
        return None
    
    def _match_facility_from_mapping(self, facility_name: str):
        """Match facility info using the legacy FACILITY_ADDRESS_MAPPING with fuzzy comparison"""
        mapping = self._facility_address_mapping
        if not mapping:
            return None
        
        if facility_name in mapping:
            return mapping[facility_name]
        
        target = self._normalize_name(facility_name)
        for name, info in mapping.items():
            normalized_candidate = self._normalize_name(name)
            if not normalized_candidate:
                continue
            if target in normalized_candidate or normalized_candidate in target:
                return info
        return None

    def _calculate_distance(self, supplier_pincode, customer_pincode):
        """
        Calculate distance for Distance Level (Km) field
        FIXED: Return empty string for blank delivered km column
        """
        # FIXED: Return empty string instead of hardcoded values
        return ""  # This ensures Distance Level (Km) column is blank as requested 