# DC Automation System

A comprehensive system for generating Delivery Challans (DCs) and E-Way Bills with both trip-based and vehicle-based grouping capabilities.

## 🏗️ Project Structure

```
├── src/                          # Source code
│   ├── core/                     # Core business logic
│   │   ├── dc_template_generator.py      # Original trip-based DC generation
│   │   ├── local_data_manager.py         # Trip-based data management
│   │   ├── vehicle_data_manager.py       # Vehicle-based data management
│   │   └── vehicle_dc_generator.py       # Vehicle-based DC generation
│   ├── eway_bill/                # E-Way Bill integration
│   │   ├── eway_bill_generator.py        # E-Way Bill data generation
│   │   ├── eway_integration.py           # Government API integration
    │   │   ├── eway_bill_template_generator.py # ClearTax template generator
│   │   └── excel_dc_converter.py         # Excel DC to JSON converter
│   └── web/                      # Web interface
│       └── streamlit_app.py              # Streamlit web application
├── data/                         # Data files
│   ├── Raw_DC.csv               # Main trip and product data
│   ├── TaxMaster.csv            # Tax rates and HSN codes
│   ├── Org_Names.csv            # Organization details
│   ├── HubAddresses.csv         # Hub location addresses
│   ├── E-Way Bill Dummy Data.csv # E-way bill sample data
│   └── guide-ewaybill.csv       # E-way bill field specifications
├── output/                       # Generated outputs
│   ├── trip_dcs/                # Trip-based DCs (original system)
│   ├── vehicle_dcs/             # Vehicle-based DCs
│   └── eway_bills/              # E-way bill templates and JSON files
├── config/                       # Configuration files
│   └── gstin_mapping.json       # GSTIN mapping for facilities
├── docs/                        # Documentation
│   ├── guides/                  # User guides and integration docs
│   └── analysis/                # Technical analysis documents
├── tests/                       # Test files
├── archive/                     # Archived development files
├── requirements.txt             # Python dependencies
├── run_app.py                  # Application launcher
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd "e-way bill"

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Web Application

```bash
# Option 1: Using the run script
python run_app.py

# Option 2: Direct streamlit command
streamlit run src/web/streamlit_app.py
```

The application will open at `http://localhost:8501`

### 3. Using the System

1. **Upload Data**: Upload your CSV files (Raw_DC.csv, TaxMaster.csv, etc.)
2. **Select Route**: Choose From/To locations for trip filtering
3. **Group Trips**: Select trips and assign them to vehicle numbers
4. **Generate DCs**: Create vehicle-based DCs with audit trail
5. **Generate E-Way Bill Templates**: Create ClearTax-compatible templates from DCs (Excel or JSON format)

## 📊 System Capabilities

### Vehicle-Based DC Generation
- **Multi-trip grouping**: Combine multiple trips per vehicle
- **Seller-wise DCs**: Generate separate DCs for each seller (Amolakchand, SourcingBee, Bodega)
- **250-item limit handling**: Automatic splitting when DCs exceed 250 line items
- **Vehicle number integration**: Vehicle numbers populated in Excel cell I4
- **Audit trail**: Complete tracking of trip-to-vehicle assignments

### Trip-Based DC Generation (Legacy)
- **Individual trip DCs**: Original system generating 3 DCs per trip
- **Preserved functionality**: Maintains all existing features
- **Independent operation**: Runs separately from vehicle system

### E-Way Bill Integration
- **Government API compliance**: 100% compliant with Official E-Way Bill API v1.03
- **Data validation**: Vehicle numbers, GSTIN, pincodes, distances
- **Tax calculations**: Automatic CGST/SGST vs IGST based on state codes
- **Batch processing**: Handle multiple vehicles simultaneously

### E-Way Bill Template Generation
- **ClearTax compatibility**: Generate templates in ClearTax format
- **Multiple input options**: Process single DC, multiple DCs, or vehicle summary
- **Tax calculation**: Automatic CGST/SGST or IGST based on states
- **Configurable GSTINs**: Manage facility-specific GSTIN information
- **Independent operation**: Works separately from DC generation process
- **Format flexibility**: Supports both JSON and Excel DC formats

### Excel DC Converter
- **Format bridging**: Converts Excel DCs to JSON format for e-way bill generation
- **Intelligent extraction**: Automatically identifies product table structure
- **Metadata mapping**: Extracts DC number, date, vehicle number from standard cells
- **Batch processing**: Converts multiple Excel files in one operation
- **Seamless integration**: Works directly with the e-way bill template generator

## 🔧 Configuration

### Data Files Required
- `Raw_DC.csv`: Trip and product data
- `TaxMaster.csv`: Tax rates (gst_percentage column)
- `Org_Names.csv`: Organization details
- `HubAddresses.csv`: Hub addresses

### Configuration Files
- `config/gstin_mapping.json`: GSTIN information for each facility

### Output Directories
- `output/trip_dcs/`: Original trip-based DCs
- `output/vehicle_dcs/`: New vehicle-based DCs
- `output/eway_bills/`: E-way bill templates and JSON files

## 🛠️ Development

### File Organization
- **src/core/**: Core business logic modules
- **src/eway_bill/**: E-way bill specific functionality
- **src/web/**: Web interface components
- **tests/**: Unit and integration tests
- **docs/**: Comprehensive documentation

### Key Features
- **Modular architecture**: Clean separation of concerns
- **Non-breaking changes**: Original system preserved
- **Scalable design**: Easy to extend and modify
- **Comprehensive logging**: Full audit trail and error tracking

## 📝 Usage Examples

### Running Vehicle DC Generation
```python
from src.core.vehicle_data_manager import VehicleDataManager
from src.core.vehicle_dc_generator import VehicleDCGenerator

# Initialize managers
data_manager = VehicleDataManager()
dc_generator = VehicleDCGenerator()

# Load data and generate DCs
data_manager.load_data()
# ... (see web interface for complete workflow)
```

### E-Way Bill Template Generation
```python
from src.eway_bill.eway_bill_template_generator import EwayBillTemplateGenerator

# Initialize template generator
template_generator = EwayBillTemplateGenerator()

# Generate template from DC data
dc_data = load_dc_data("path/to/dc.json")
rows = template_generator.generate_template_from_dc(dc_data)
template_generator.save_to_csv(rows, "output/eway_bills/template.csv")
```

### Excel DC Conversion
```python
from src.eway_bill.excel_dc_converter import ExcelDCConverter

# Initialize converter
converter = ExcelDCConverter()

# Convert Excel DC to JSON
dc_data = converter.convert_excel_to_json("path/to/dc.xlsx")
converter.save_json(dc_data, "output/vehicle_dcs/dc.json")

# Process multiple Excel files
excel_files = ["dc1.xlsx", "dc2.xlsx", "dc3.xlsx"]
dc_data_list = converter.convert_multiple_excel_files(excel_files)
```

### E-Way Bill API Integration
```python
from src.eway_bill.eway_integration import VehicleDCEWayIntegration

# Initialize integration
eway_integration = VehicleDCEWayIntegration()

# Generate e-way bills for vehicle DCs
results = eway_integration.generate_eway_for_multiple_vehicles(vehicle_dc_data)
```

## 🔍 Troubleshooting

### Common Issues
1. **Import errors**: Ensure you're running from the project root directory
2. **Data format issues**: Check CSV file headers match expected column names
3. **Missing dependencies**: Run `pip install -r requirements.txt`
4. **GSTIN configuration**: Verify GSTIN information in config/gstin_mapping.json
5. **Excel conversion**: Check Excel format matches expected structure

### Support
- Check `docs/guides/` for detailed documentation
- See `docs/guides/eway_bill_template_guide.md` for e-way bill template generation
- Review `archive/` for development history and analysis
- Examine test files in `tests/` for usage examples

## 📈 System Statistics

- **Original system**: 316 DCs from 112 trips (3 per trip)
- **New system**: Variable DCs based on vehicle assignments
- **E-way bill compliance**: Government API v1.03 specifications
- **Data processing**: Handles large datasets with efficient filtering
- **Format support**: Excel and JSON DC formats