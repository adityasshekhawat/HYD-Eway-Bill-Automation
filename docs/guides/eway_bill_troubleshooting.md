# E-Way Bill Template Generator Troubleshooting Guide

This guide provides solutions for common issues encountered when using the E-Way Bill Template Generator.

## Common Errors and Solutions

### 1. "No such file or directory" Error

**Error Message:**
```
Error generating template: [Errno 2] No such file or directory: 'output/eway_bills/eway_bill_template_YYYYMMDD_HHMMSS.csv'
```

**Solution:**
- The output directory doesn't exist. Click the "Create Output Directory Now" button before generating the template.
- Alternatively, you can manually create the directory using:
  ```bash
  mkdir -p output/eway_bills
  ```
- The latest version automatically creates the directory when needed.

### 2. Excel Conversion Issues

**Error Message:**
```
Error converting Excel file: [various error messages]
```

**Solution:**
- Verify the Excel file structure matches the expected format:
  - DC number should be in cell C4
  - Date should be in cell C5
  - Vehicle number should be in cell I4
  - Product table should start between rows 15-30
- Check that the Excel file is not corrupted or password-protected
- Try opening and resaving the Excel file with a different name

### 3. "Please upload and convert an Excel file first" Error

**Solution:**
- Make sure you've uploaded an Excel file and it has been successfully converted
- The conversion process should show success messages and display the extracted data
- If conversion failed, check the error messages for specific issues

### 4. Empty or Incorrect Template Generated

**Solution:**
- Verify the source data has all required fields (HSN codes, GST rates, etc.)
- Check that products were correctly extracted from the Excel file
- Ensure GSTIN information is configured correctly in Settings tab
- Try using the test script to debug the conversion process:
  ```bash
  python test_excel_converter.py path/to/your/excel_file.xlsx
  ```

## Directory Structure Issues

If you encounter directory-related issues:

1. **Check directory permissions**:
   - Ensure you have write permissions to the output directory
   - Try using an output directory in your user space if needed

2. **Verify directory paths**:
   - Avoid special characters or spaces in directory paths
   - Use forward slashes (/) even on Windows
   - Keep paths relatively short

3. **Create directories manually**:
   ```bash
   mkdir -p output/eway_bills
   mkdir -p output/test_data
   ```

## Testing the Excel Converter

To test the Excel converter independently:

```bash
# Test with a specific Excel file
python test_excel_converter.py path/to/excel_file.xlsx

# Convert Excel to JSON using the command line
python src/eway_bill/excel_dc_converter.py --input path/to/excel_file.xlsx --output output/test_data/converted.json
```

## Debugging Steps

If you continue to encounter issues:

1. **Enable detailed logging**:
   - Set logging level to DEBUG in the Python files
   - Check the logs for specific error messages

2. **Inspect intermediate files**:
   - Look at the JSON files generated during Excel conversion
   - Check the CSV template structure

3. **Try with sample data**:
   - Use the sample DC file provided in the test directory
   - Compare your Excel files with the sample to identify differences

4. **Check dependencies**:
   - Ensure all required Python packages are installed:
     ```bash
     pip install openpyxl pandas
     ```

5. **Restart the application**:
   - Sometimes restarting the Streamlit app can resolve issues
   - Clear browser cache if using the web interface

## Getting Help

If you've tried the solutions above and still encounter issues:

1. Check the documentation in the `docs/guides/` directory
2. Examine the implementation code for specific requirements
3. Create a detailed issue report with:
   - Exact error messages
   - Steps to reproduce the issue
   - Sample data files (with sensitive information removed) 