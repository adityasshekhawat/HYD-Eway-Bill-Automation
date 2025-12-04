# TaxMaster Quick Reference Card

## 🚀 Quick Column Mapping (Copy-Paste Ready)

### Python Dictionary for Code
```python
TAXMASTER_COLUMN_MAPPING = {
    'jpin': 'Jpin',
    'hsn_code': 'hsnCode', 
    'gst_percentage': 'gstPercentage',
    'taxmasterid': 'TaxMasterID',
    'cess': 'cess',
    'cgst_component_share': 'cgstComponentShare',
    'sgst_component_share': 'sgstComponentShare',
    'igst_component_share': 'IgstComponentShare',
    'vatpercentage': 'vatPercentage',
    'sin_tax': 'sinTax'
}
```

### Critical Column Changes
```python
# BEFORE (OLD)          # AFTER (NEW)
df['jpin']         →     df['Jpin']
df['hsn_code']     →     df['hsnCode']
df['gst_percentage'] →   df['gstPercentage']
df['taxmasterid']  →     df['TaxMasterID']
```

### New Columns Available
- `Title` - Product description
- `ProductVerticalId` - Category ID
- `ProductVerticalName` - Category name
- `status` - Record status
- `Validity_Period_Start/End` - Tax validity dates

### Files to Update
1. `src/core/vehicle_data_manager.py` (Line ~214)
2. `src/core/local_data_manager.py`
3. Streamlit upload validation
4. Any hardcoded column references

### Test Command
```bash
python3 -c "
import pandas as pd
df = pd.read_csv('data/TaxMasterGstDump-20-06-2025-19-09-57.csv', nrows=5)
print('✅ Columns:', df[['Jpin', 'hsnCode', 'gstPercentage', 'cess']].columns.tolist())
"
```

---
*Reference: See `docs/analysis/TAXMASTER_MIGRATION_MAPPING.md` for complete details* 