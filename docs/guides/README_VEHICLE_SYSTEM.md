# 🚛 Vehicle-Based DC Generation System

A modern web interface for generating Delivery Challans (DCs) grouped by vehicle instead of individual trips.

## 🎯 Key Features

- **Vehicle-Based Grouping**: Group multiple trips into single vehicle for consolidated DC generation
- **Interactive Frontend**: Modern Streamlit interface with step-by-step workflow
- **Route Filtering**: Filter trips by From/To locations before grouping
- **Smart Consolidation**: Automatically consolidate products by seller while respecting 250-line limits
- **Audit Trail**: Track which trips are assigned to which vehicles
- **Bulk Download**: ZIP file with all generated DCs and supporting files

## 🔄 System Architecture

### Current Trip-Based System (Preserved)
- `dc_template_generator.py` - Original trip-based DC generation
- `local_data_manager.py` - Original data processing logic
- Both systems work independently and can be used simultaneously

### New Vehicle-Based System
- `streamlit_app.py` - Main web interface
- `vehicle_data_manager.py` - Vehicle-based data processing
- `vehicle_dc_generator.py` - Vehicle-based DC creation
- `requirements_streamlit.txt` - Dependencies

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements_streamlit.txt
```

### Launch Application
```bash
streamlit run streamlit_app.py
```

### Data Requirements
Ensure these files exist in `/data` directory:
- `Raw_DC.csv` - Main trip data
- `TaxMaster.csv` - Tax information  
- `Org_Names.csv` - Organization details

## 📋 Workflow

### Step 1: Load Data
- Automatically loads data from `/data` directory
- Validates file existence and format
- Shows data summary and sample

### Step 2: Select Route  
- Choose From (Origin) location
- Choose To (Destination) location
- Load trips for selected route

### Step 3: Group Trips by Vehicle
- Select trips using checkboxes
- Assign vehicle number
- Track vehicle assignments
- Clear and reassign as needed

### Step 4: Generate DCs
- Review vehicle assignments
- Generate DCs (3 per vehicle - one per seller)
- Download individual files or ZIP bundle
- Includes audit trail mapping

## 🎛️ Key Differences from Trip-Based System

| Feature | Trip-Based | Vehicle-Based |
|---------|------------|---------------|
| **Grouping** | By `(trip_id, sender)` | By `(vehicle_number, seller)` |
| **Output** | 316 DCs (112 trips × 3 sellers) | Variable (depends on vehicles) |
| **Interface** | Command line | Web interface |
| **Selection** | Automatic | User-controlled |
| **File Naming** | `DC_XXX_TripYYY.xlsx` | `DC_XXX_VehicleYYY.xlsx` |
| **Vehicle Info** | Empty cell I4 | Vehicle number in I4 |

## 📊 Business Logic

### Product Consolidation
- Products from multiple trips are consolidated by seller
- Each vehicle generates 3 DCs (Amolakchand, SourcingBee, Bodega)
- Automatic splitting if >250 line items per DC

### Route Constraints
- Only trips with same From/To can be grouped
- Prevents mixing different routes in same vehicle

### DC Numbering
- Vehicle-based prefixes: `SBVHDCMYR`, `AKVHDCMYR`, `BDVHDCMYR`
- Sequential numbering with auto-splitting (`_01`, `_02` etc.)

## 🔧 File Outputs

### Generated Files
- **DCs**: `DC_SBVHDCMYR0001_VehicleKA01AB1234_3trips.xlsx`
- **Summary**: `vehicle_generation_summary_YYYYMMDD_HHMMSS.json`
- **Audit**: `vehicle_audit_YYYYMMDD_HHMMSS.json`
- **ZIP Bundle**: `vehicle_dcs_YYYYMMDD_HHMMSS.zip`

### Directory Structure
```
/
├── data/                          # Input data files
├── generated_dcs/                 # Trip-based DCs (original)
├── generated_vehicle_dcs/         # Vehicle-based DCs (new)
├── dc_template_generator.py       # Original system
├── local_data_manager.py          # Original system  
├── streamlit_app.py               # New web interface
├── vehicle_data_manager.py        # New data processor
└── vehicle_dc_generator.py        # New DC generator
```

## 🎨 User Experience

### Intuitive Workflow
1. **Visual Data Loading**: See file status and data summary
2. **Route Selection**: Dropdown menus with trip counts
3. **Interactive Trip Selection**: Checkbox-based selection table
4. **Vehicle Assignment**: Simple input with validation
5. **Progress Tracking**: Real-time generation progress
6. **Easy Downloads**: One-click ZIP download or individual files

### Error Handling
- File validation and clear error messages
- Data integrity checks
- Graceful handling of edge cases
- Detailed error reporting for debugging

## 🔒 Data Safety

### Non-Breaking Design
- Original trip-based system remains untouched
- Separate output directories prevent conflicts
- Independent state management

### Audit Trail
- Complete mapping of trips to vehicles
- Timestamp tracking for assignments
- Generation summary with detailed metadata

## 🚀 Future Enhancements

### Planned Features
- **Multi-route support**: Handle multiple From/To in single session
- **Weight/volume validation**: Add load constraints
- **Template customization**: User-configurable DC templates
- **Batch processing**: Upload multiple route files
- **E-way bill integration**: Direct API integration for e-way bills

### Scalability
- Designed to handle PAN India expansion
- Modular architecture for easy feature addition
- Performance optimizations for large datasets

---

## 📞 Support

For questions or issues:
1. Check the workflow steps in the web interface
2. Verify data file formats match requirements
3. Review error messages for specific guidance
4. Both trip-based and vehicle-based systems work independently 