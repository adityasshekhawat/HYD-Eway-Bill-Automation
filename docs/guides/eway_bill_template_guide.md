# E-Way Bill Template Generator Guide

This guide explains how to use the E-Way Bill Template Generator to create templates compatible with ClearTax.

## Overview

The E-Way Bill Template Generator creates CSV files in the format required by ClearTax for e-way bill generation. This allows you to generate e-way bills without directly accessing the government API.

## Prerequisites

1. Delivery Challans (DCs) in either JSON or Excel format
2. Correct GSTIN information for your facilities
3. Python environment with required dependencies

## Using the Streamlit UI

The easiest way to generate e-way bill templates is through the Streamlit UI:

1. **Launch the Streamlit app**:
   ```
   python run_app.py
   ```

2. **Navigate to the E-Way Bill Template Generator tab**

3. **Select Input Method**:
   - **Single DC File (JSON)**: Upload a single DC JSON file
   - **Single DC File (Excel)**: Upload a single DC Excel file (will be converted to JSON)
   - **Multiple DC Files**: Select multiple DC files from a directory (both JSON and Excel supported)
   - **Vehicle Summary File**: Use a vehicle summary file that references multiple DCs

4. **Configure Output Options**:
   - Specify the output directory for the generated template

5. **Generate Template**:
   - Click the "Generate E-Way Bill Template" button
   - The app will process the DC data and create a CSV file
   - You can preview and download the generated template

## Excel DC Support

The system now supports Excel DC files directly:

1. **Excel-to-JSON Conversion**:
   - Excel DCs are automatically converted to JSON format
   - The converter extracts metadata from standard cells (DC number, date, vehicle number)
   - Products are extracted from the product table in the Excel file
   - The system intelligently identifies column headers and maps them to required fields

2. **Excel Format Requirements**:
   - DC number should be in cell C4
   - Date should be in cell C5
   - Vehicle number should be in cell I4
   - Sender name should be in cell C8
   - Receiver name should be in cell C12
   - Product table should start between rows 15-30
   - Product table should have columns for Description, HSN, Quantity, Value, and GST Rate

## Command Line Usage

You can also generate templates using the command line:

### For JSON DC Files:
```bash
# Generate template from a single DC file
python src/eway_bill/generate_eway_templates.py --input path/to/dc_file.json --output output/eway_bills/template.csv

# Generate template from multiple DC files in a directory
python src/eway_bill/generate_eway_templates.py --input output/vehicle_dcs/generated_vehicle_dcs --output output/eway_bills/template.csv --batch
```

### For Excel DC Files:
```bash
# Convert Excel DC to JSON
python src/eway_bill/excel_dc_converter.py --input path/to/dc_file.xlsx --output path/to/dc_file.json

# Convert multiple Excel DCs to JSON
python src/eway_bill/excel_dc_converter.py --input directory_with_excel_files --output output_json_directory --batch

# Generate template from converted JSON
python src/eway_bill/generate_eway_templates.py --input path/to/dc_file.json --output output/eway_bills/template.csv
```

## Configuration

### GSTIN Settings

Configure GSTIN information for each facility in the Settings tab of the Streamlit app or by editing the `config/gstin_mapping.json` file directly:

```json
{
    "SOURCINGBEE": "29AAWCS7485C1ZJ",
    "AMOLAKCHAND": "29AAPCA1708D1ZS",
    "BODEGA": "29AAKCB1234D1ZX"
}
```

## Template Format

The generated template follows the ClearTax format with the following structure:

1. **Header rows** indicating mandatory, optional, and conditional fields
2. **Column headers** with field names
3. **Data rows** with one row per product in each DC

## Uploading to ClearTax

After generating the template:

1. Log in to your ClearTax account
2. Navigate to the e-way bill section
3. Upload the generated CSV file
4. Review and confirm the e-way bill details
5. Submit for processing

## Troubleshooting

### Common Issues

1. **Missing GSTIN**: Ensure all facilities have correct GSTIN information in the settings
2. **Invalid Address Format**: Make sure addresses in DCs include pincode and state information
3. **Tax Calculation Errors**: Verify HSN codes and GST rates in the DC data
4. **Excel Conversion Issues**: If Excel conversion fails, check the Excel file structure matches expected format
5. **Column Mapping**: If product data is not extracted correctly, check the column headers in the Excel file

### Excel Conversion Troubleshooting

If Excel conversion fails or extracts incorrect data:

1. **Check Cell Positions**: Verify metadata is in the expected cells (DC number in C4, etc.)
2. **Verify Product Table**: Make sure product table has clear headers and starts between rows 15-30
3. **Column Names**: Ensure product table has columns for Description, HSN, Quantity, Value, and GST Rate
4. **Data Types**: Check that numeric values are properly formatted as numbers in Excel

### Error Logs

Check the application logs for detailed error messages if you encounter issues during template generation. 