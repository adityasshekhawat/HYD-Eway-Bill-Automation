#!/usr/bin/env python3
"""
Streamlit Frontend for Vehicle-Based DC Generation
"""

import streamlit as st
import pandas as pd
import os
import zipfile
from datetime import datetime
import json
import sys
from pathlib import Path
import time

# Add the project root to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import our custom modules
from src.core.vehicle_data_manager import VehicleDataManager
from src.core.vehicle_dc_generator import VehicleDCGenerator
from src.eway_bill.eway_bill_template_generator import EwayBillTemplateGenerator
from src.eway_bill.excel_dc_converter import ExcelDCConverter
from src.eway_bill.excel_generator import save_data_to_excel, save_eway_bill_to_excel

# Import migration constants for TaxMaster validation
from src.core.taxmaster_migration import CRITICAL_COLUMNS, TAXMASTER_COLUMN_MAPPING

# Page configuration
st.set_page_config(
    page_title="Vehicle DC Generator",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to help with file uploads
st.markdown("""
<style>
    .uploadedFile {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
    }
    .stFileUploader > div > div > div > div {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data_manager' not in st.session_state:
    st.session_state.data_manager = VehicleDataManager()
    st.session_state.data_loaded = False
    st.session_state.selected_route = None
    st.session_state.trips_data = []
    st.session_state.vehicle_assignments = []

def validate_taxmaster_format(df):
    """Validate TaxMaster file format (supports both old and new formats)"""
    # Check for new format first
    if 'Jpin' in df.columns and 'hsnCode' in df.columns and 'gstPercentage' in df.columns:
        return True, "new", "New TaxMaster format detected (Jpin, hsnCode, gstPercentage)"
    
    # Check for old format
    elif 'jpin' in df.columns and 'hsn_code' in df.columns and 'gst_percentage' in df.columns:
        return True, "old", "Old TaxMaster format detected (jpin, hsn_code, gst_percentage)"
    
    # Neither format
    else:
        missing_new = [col for col in ['Jpin', 'hsnCode', 'gstPercentage'] if col not in df.columns]
        missing_old = [col for col in ['jpin', 'hsn_code', 'gst_percentage'] if col not in df.columns]
        
        return False, "invalid", f"Invalid TaxMaster format. Missing columns - New format: {missing_new}, Old format: {missing_old}"

def main():
    """Main function for the Streamlit app"""
    # Add tabs for different functionalities
    tab1, tab2 = st.tabs(["🚛 Vehicle DC Generator", "⚙️ Settings"])
    
    with tab1:
        run_vehicle_dc_generator()
    
    with tab2:
        run_settings()
    
    # Add information about unified generation
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ About Complete Generation")
    st.sidebar.info("""
    **Enhanced Features**: The system now generates complete file packages!
    
    ✅ **What's Generated:**
    - **Excel DCs**: Editable spreadsheet format
    - **PDF DCs**: Print-ready landscape format
    - **E-Way Templates**: Ready for ClearTax upload
    - **Organized ZIP**: All files in structured folders
    
    **Benefits:**
    - No manual printing setup needed
    - Professional PDF output
    - Complete documentation package
    - Ready for compliance and courier use
    
    **Legacy Support:**
    - Existing DC files can be converted in Settings tab
    """)

def run_vehicle_dc_generator():
    """Run the vehicle DC generator UI with unified e-way generation and PDF support"""
    st.title("🚛 Vehicle-Based DC Generator")
    st.markdown("Generate complete document packages: **Excel DCs + Print-ready PDFs + E-Way Bill templates** grouped by vehicle")
    
    # Add unified generation callout
    st.success("🎉 **Complete Package Generation**: This system now automatically creates Excel DCs, print-ready PDFs, and E-Way Bill templates in one step!")
    
    # Sidebar for navigation
    with st.sidebar:
        st.header("📋 Navigation")
        page = st.radio(
            "Choose a step:",
            ["1️⃣ Upload Data", "2️⃣ Select Route", "3️⃣ Group Trips", "4️⃣ Generate Complete Package"],
            key="navigation"
        )
        
        # Add debugging and session management section
        st.markdown("---")
        st.header("🔧 Session Management")
        
        # Show session state info
        if st.session_state.get('trips_data'):
            trips_df = pd.DataFrame(st.session_state.trips_data)
            if not trips_df.empty:
                st.write(f"**Cached Trips:** {len(trips_df)}")
                st.write(f"**Columns:** {', '.join(trips_df.columns.tolist())}")
                
                # Check for field name issues
                if 'trip_id' in trips_df.columns and 'trip_ref_number' not in trips_df.columns:
                    st.error("⚠️ Old data format detected!")
                    st.write("Please clear session to fix.")
                elif 'trip_ref_number' in trips_df.columns:
                    st.success("✅ Current data format")
        
        # Clear session button
        if st.button("🔄 Clear Session", help="Reset all cached data and start fresh"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                if key not in ['navigation']:  # Keep navigation state
                    del st.session_state[key]
            
            # Reinitialize
            st.session_state.data_manager = VehicleDataManager()
            st.session_state.data_loaded = False
            st.session_state.selected_route = None
            st.session_state.trips_data = []
            st.session_state.vehicle_assignments = []
            
            st.success("🎉 Session cleared! Please re-upload data.")
            st.rerun()
    
    if page == "1️⃣ Upload Data":
        load_data_page()
    elif page == "2️⃣ Select Route":
        select_route_page()
    elif page == "3️⃣ Group Trips":
        group_trips_page()
    elif page == "4️⃣ Generate Complete Package":
        generate_dcs_page()

def load_data_page():
    st.header("📁 Step 1: Upload Data Files")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("📤 **Upload Required Data Files**: Please upload all required CSV files to proceed")
        
        # File upload section
        st.subheader("📊 Upload Data Files")
        
        # Required files list with updated TaxMaster description
        required_files = {
            'raw_dc': {'name': 'Raw_DC.csv', 'description': 'Main trip and product data'},
            'tax_master': {'name': 'TaxMaster.csv', 'description': 'Tax rates and HSN codes (supports both old and new formats)'},
            'org_names': {'name': 'Org_Names.csv', 'description': 'Organization details'},
            'hub_addresses': {'name': 'HubAddresses.csv', 'description': 'Hub location addresses'}
        }
        
        uploaded_files = {}
        
        # Create file uploaders for each required file
        for file_key, file_info in required_files.items():
            uploaded_file = st.file_uploader(
                f"📄 {file_info['name']} - {file_info['description']}", 
                type=['csv'],
                key=f"upload_{file_key}",
                help=f"Upload the {file_info['name']} file",
                accept_multiple_files=False
            )
            
            if uploaded_file is not None:
                # Add file validation
                try:
                    # Check file size (Streamlit default limit is 200MB)
                    file_size = len(uploaded_file.getvalue()) / (1024 * 1024)  # MB
                    if file_size > 50:  # 50MB limit
                        st.error(f"❌ {file_info['name']} is too large ({file_size:.1f}MB). Please use a file smaller than 50MB.")
                        continue
                    
                    # Try to read the file to validate it's a proper CSV
                    uploaded_file.seek(0)  # Reset file pointer
                    test_df = pd.read_csv(uploaded_file, nrows=5)  # Read first 5 rows to test
                    uploaded_file.seek(0)  # Reset file pointer again
                    
                    # Special validation for TaxMaster file
                    if file_key == 'tax_master':
                        is_valid, format_type, message = validate_taxmaster_format(test_df)
                        if is_valid:
                            st.success(f"✅ {file_info['name']} uploaded successfully ({file_size:.1f}MB, {len(test_df.columns)} columns)")
                            st.info(f"📋 {message}")
                        else:
                            st.error(f"❌ {file_info['name']} format validation failed: {message}")
                            continue
                    else:
                        st.success(f"✅ {file_info['name']} uploaded successfully ({file_size:.1f}MB, {len(test_df.columns)} columns)")
                    
                    uploaded_files[file_key] = uploaded_file
                    
                except Exception as e:
                    st.error(f"❌ Error reading {file_info['name']}: {str(e)}")
                    st.info("💡 Please ensure the file is a valid CSV with proper headers")
        
        # Show upload status
        st.subheader("📋 Upload Status")
        
        status_data = []
        for file_key, file_info in required_files.items():
            is_uploaded = file_key in uploaded_files
            status_data.append({
                'File': file_info['name'],
                'Description': file_info['description'],
                'Status': '✅ Uploaded' if is_uploaded else '❌ Not Uploaded'
            })
        
        status_df = pd.DataFrame(status_data)
        st.dataframe(status_df, use_container_width=True)
        
        # Load data button - only enabled if all files uploaded
        all_files_uploaded = len(uploaded_files) == len(required_files)
        
        if all_files_uploaded:
            if st.button("🔄 Process Uploaded Data", type="primary"):
                with st.spinner("Processing uploaded data files..."):
                    success = st.session_state.data_manager.load_data_from_uploads(uploaded_files)
                    
                    if success:
                        st.session_state.data_loaded = True
                        st.success("✅ Data processed successfully!")
                        st.balloons()
                        
                        # Show data summary
                        st.subheader("📈 Data Summary")
                        raw_data = st.session_state.data_manager.raw_data
                        
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("Total Rows", len(raw_data))
                        with col_b:
                            st.metric("Unique Trips", raw_data['trip_ref_number'].nunique())
                        with col_c:
                            st.metric("Origins", raw_data['name'].nunique())
                        with col_d:
                            st.metric("Destinations", raw_data['hub'].nunique())
                        
                        # Show sample data
                        st.subheader("📋 Sample Data Preview")
                        st.dataframe(raw_data.head(), use_container_width=True)
                        
                        st.info("✨ **Ready for next step!** Go to 'Select Route' to choose your route.")
                    else:
                        st.error("❌ Failed to process data. Please check the files and try again.")
        else:
            missing_count = len(required_files) - len(uploaded_files)
            st.warning(f"⚠️ Please upload {missing_count} more file(s) to proceed")
    
    with col2:
        st.subheader("📝 File Requirements")
        
        st.markdown("**Required columns per file:**")
        
        with st.expander("📄 Raw_DC.csv", expanded=False):
            st.markdown("""
            - jpin (Product identifier)
            - trip_ref_number (Trip reference)
            - taxable_amount (Product value)
            - planned_quantity (Quantity)
            - title (Product description)
            - hub (Destination hub)
            - delivery_date (Delivery date)
            - name (Origin location)
            - sender (Sender organization ID)
            """)
        
        with st.expander("📄 TaxMaster.csv", expanded=False):
            st.markdown("""
            **New Format (Recommended):**
            - Jpin (Product identifier)
            - hsnCode (HSN classification)
            - gstPercentage (GST rate)
            - cess (Cess amount)
            
            **Old Format (Legacy Support):**
            - jpin (Product identifier)  
            - hsn_code (HSN classification)
            - gst_percentage (GST rate)
            - cess (Cess amount)
            
            *Both formats are automatically detected and supported*
            """)
        
        with st.expander("📄 Org_Names.csv", expanded=False):
            st.markdown("""
            - org_profile_id (Organization ID)
            - org_name (Organization name)
            """)
        
        with st.expander("📄 HubAddresses.csv", expanded=False):
            st.markdown("""
            - Location Name (Hub name)
            - Location Address (Full address)
            """)
        
        st.markdown("---")
        
        st.subheader("🛠️ Troubleshooting")
        
        with st.expander("❌ Upload Issues", expanded=False):
            st.markdown("""
            **If uploads fail:**
            1. Check file size (max 50MB)
            2. Ensure CSV format with headers
            3. Verify required columns exist
            4. Try refreshing the page
            5. Use 'Clear Session' button to reset
            """)
            
            if st.button("🔄 Reset Upload Session", key="reset_upload"):
                # Clear only upload-related session state
                for key in list(st.session_state.keys()):
                    if 'upload_' in key or 'data_loaded' in key:
                        del st.session_state[key]
                st.success("Upload session reset!")
                st.rerun()

def select_route_page():
    st.header("🗺️ Step 2: Select Route")
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first (Step 1)")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Get available routes
        routes = st.session_state.data_manager.get_available_routes()
        
        if not routes:
            st.error("❌ No routes found in data")
            return
        
        st.subheader("🛣️ Available Routes")
        
        # Create route selection interface
        from_locations = sorted(list(set(route['from'] for route in routes)))
        to_locations = sorted(list(set(route['to'] for route in routes)))
        
        # Multi-select for origin facilities
        selected_from_locations = st.multiselect(
            "📍 From (Origin Facilities):", 
            from_locations, 
            default=[from_locations[0]] if from_locations else None,
            help="Select one or more origin facilities"
        )
        
        if not selected_from_locations:
            st.warning("⚠️ Please select at least one origin facility")
            return
        
        # Get all possible destinations for the selected origins
        available_destinations = set()
        for from_loc in selected_from_locations:
            for route in routes:
                if route['from'] == from_loc:
                    available_destinations.add(route['to'])
        
        # Convert to sorted list
        available_destinations = sorted(list(available_destinations))
        
        # Select destination
        selected_to = st.selectbox(
            "🎯 To (Destination):", 
            available_destinations, 
            key="to_select"
        )
        
        # Show route summary
        total_trips = 0
        for from_loc in selected_from_locations:
            selected_route = next(
                (r for r in routes if r['from'] == from_loc and r['to'] == selected_to), 
                None
            )
            if selected_route:
                total_trips += selected_route['trip_count']
        
        # Display summary of selected routes
        st.info(f"📊 **Selected Routes**: {', '.join(selected_from_locations)} → {selected_to} ({total_trips} total trips)")
            
        # Load trips button
        if st.button("🔍 Load Trips for Selected Routes", type="primary"):
            with st.spinner("Loading trips for selected routes..."):
                # Always use the multiple facilities method for consistency
                # This ensures uniform data structure regardless of facility count
                trips = st.session_state.data_manager.get_trips_for_multiple_facilities(selected_from_locations, selected_to)
                    
                if trips:
                    st.session_state.selected_route = {
                        'from': ', '.join(selected_from_locations),
                        'to': selected_to,
                        'trip_count': len(trips),
                        'facilities': selected_from_locations  # Store the list of facilities
                    }
                    st.session_state.trips_data = trips
                    
                    st.success(f"✅ Loaded {len(trips)} trips for selected routes")
                        
                    # Show trips summary
                    st.subheader("📋 Trips Summary")
                    
                    # Always show facility filter (even for single facility for consistency)
                    trips_df = pd.DataFrame(trips)
                    facility_filter = st.multiselect(
                        "Filter by Facility:", 
                        selected_from_locations,
                        default=selected_from_locations,
                        key="facility_filter"
                    )
                    
                    if facility_filter:
                        filtered_trips = trips_df[trips_df['from'].isin(facility_filter)]
                        st.dataframe(filtered_trips, use_container_width=True)
                    else:
                        st.dataframe(trips_df, use_container_width=True)
                        
                else:
                    st.error("❌ No trips found for selected routes")
    
    with col2:
        st.subheader("ℹ️ Route Information")
        if st.session_state.selected_route:
            route = st.session_state.selected_route
            st.success(f"**Selected Route:**")
            
            # Handle multiple facilities
            if 'facilities' in route and len(route['facilities']) > 1:
                st.write(f"📍 **From**: {len(route['facilities'])} facilities")
                with st.expander("View Facilities"):
                    for facility in route['facilities']:
                        st.write(f"- {facility}")
            else:
                st.write(f"📍 **From**: {route['from']}")
                
            st.write(f"🎯 **To**: {route['to']}")
            st.write(f"🔢 **Trips**: {route['trip_count']}")
        else:
            st.info("No route selected yet")
            
        st.markdown("""
        **Instructions:**
        1. Select one or more origin facilities
        2. Select destination location  
        3. Load trips for the routes
        4. Review trip details
        5. Proceed to trip grouping
        
        **💡 Multi-Facility Feature:**
        - Select multiple facilities to combine trips
        - Filter trips by facility after loading
        - Assign trips from different facilities to the same vehicle
        """)

def group_trips_page():
    st.header("📦 Step 3: Group Trips by Vehicle")
    
    if not st.session_state.trips_data:
        st.warning("⚠️ Please select a route and load trips first (Step 2)")
        return
    
    # Add information about enhanced trip handling
    trips_df = pd.DataFrame(st.session_state.trips_data)
    if 'composite_trip_id' in trips_df.columns:
        st.info("🎯 **Enhanced Trip Grouping**: This system now properly handles cases where the same trip reference number exists across multiple facilities. Each facility-specific trip is shown separately with clear facility identification in the 'Facility' column.")
    
    # Check if we have the raw data manager available
    has_data_manager = hasattr(st.session_state, 'data_manager') and st.session_state.data_manager is not None
    
    # Main content area - full width
    st.subheader(f"🚛 Available Trips: {st.session_state.selected_route['from']} → {st.session_state.selected_route['to']}")
    
    # Get already assigned trip refs to filter them out
    assigned_trip_refs = set()
    for assignment in st.session_state.vehicle_assignments:
        # Handle both old and new trip ID formats
        for trip_ref in assignment['trip_refs']:
            if 'composite_trip_id' in trip_ref if isinstance(trip_ref, dict) else False:
                assigned_trip_refs.add(trip_ref['composite_trip_id'])
            elif isinstance(trip_ref, dict) and 'trip_ref_number' in trip_ref:
                assigned_trip_refs.add(trip_ref['trip_ref_number'])
            else:
                assigned_trip_refs.add(str(trip_ref))
    
    # Store current state to detect changes
    if 'last_assigned_count' not in st.session_state:
        st.session_state.last_assigned_count = 0
    
    current_assigned_count = len(assigned_trip_refs)
    assignments_changed = current_assigned_count != st.session_state.last_assigned_count
    st.session_state.last_assigned_count = current_assigned_count
    
    # Show trips with selection - filter out already assigned trips
    # Always use composite_trip_id for consistency (unified data structure)
    trip_id_column = 'composite_trip_id' if 'composite_trip_id' in trips_df.columns else 'trip_ref_number'
    available_trips_df = trips_df[~trips_df[trip_id_column].isin(assigned_trip_refs)].copy()
    
    if len(assigned_trip_refs) > 0:
        st.info(f"ℹ️ {len(assigned_trip_refs)} trips already assigned to vehicles (hidden from selection)")
    
    # Use a container to stabilize the layout
    trips_container = st.container()
    
    with trips_container:
        if len(available_trips_df) == 0:
            st.success("🎉 All trips have been assigned to vehicles!")
            if assignments_changed:  # Only show balloons when assignments actually changed
                st.balloons()
        else:
            st.write(f"📋 **{len(available_trips_df)} unassigned trips available for selection:**")
            
            # Filter controls - we'll get all unique values from raw data
            all_facilities = st.session_state.selected_route['facilities']
            
            # Get unique parcel types and categories from raw data if available
            all_parcel_types = []
            all_categories = []
            
            if has_data_manager:
                try:
                    raw_data = st.session_state.data_manager.raw_data
                    if raw_data is not None:
                        # Filter raw data to selected route
                        route_data = raw_data[
                            (raw_data['name'].isin(all_facilities)) & 
                            (raw_data['hub'] == st.session_state.selected_route['to'])
                        ]
                        
                        # Get unique values
                        if 'parcel_type' in route_data.columns:
                            all_parcel_types = sorted(route_data['parcel_type'].dropna().unique().tolist())
                        if 'category' in route_data.columns:
                            all_categories = sorted(route_data['category'].dropna().unique().tolist())
                except Exception as e:
                    print(f"⚠️ Could not extract unique filter values: {e}")
            
            # Show filters
            if all_parcel_types and all_categories:
                filter_col1, filter_col2, filter_col3 = st.columns(3)
            elif all_parcel_types or all_categories:
                filter_col1, filter_col2 = st.columns(2)
                filter_col3 = None
            else:
                filter_col1 = st.columns(1)[0]
                filter_col2 = None
                filter_col3 = None
            
            with filter_col1:
                # Facility filter
                facility_filter = st.multiselect(
                    "Filter by Facility:", 
                    all_facilities,
                    default=all_facilities,
                    key="facility_filter_group"
                )
            
            # Parcel type filter
            if all_parcel_types and filter_col2:
                with filter_col2:
                    parcel_type_filter = st.multiselect(
                        "Filter by Parcel Type:",
                        all_parcel_types,
                        default=all_parcel_types,
                        key="parcel_type_filter"
                    )
            else:
                parcel_type_filter = None
            
            # Category filter
            if all_categories and filter_col3:
                with filter_col3:
                    category_filter = st.multiselect(
                        "Filter by Category:",
                        all_categories,
                        default=all_categories,
                        key="category_filter"
                    )
            else:
                category_filter = None
            
            # ALWAYS re-query trips with filters applied (Option B implementation)
            # This ensures totals are calculated from filtered data, not cached unfiltered data
            if has_data_manager:
                with st.spinner("🔍 Applying filters..."):
                    filtered_trips = st.session_state.data_manager.get_trips_for_multiple_facilities(
                        facility_filter if facility_filter else all_facilities,
                        st.session_state.selected_route['to'],
                        parcel_type_filter=parcel_type_filter if parcel_type_filter else None,
                        category_filter=category_filter if category_filter else None
                    )
                    
                    # Create new DataFrame with filtered trips
                    if filtered_trips:
                        filtered_trips_df = pd.DataFrame(filtered_trips)
                        # Use composite_trip_id for consistency
                        trip_id_column = 'composite_trip_id' if 'composite_trip_id' in filtered_trips_df.columns else 'trip_ref_number'
                        # Filter out already assigned trips
                        available_trips_df = filtered_trips_df[~filtered_trips_df[trip_id_column].isin(assigned_trip_refs)].copy()
                    else:
                        available_trips_df = pd.DataFrame()  # Empty dataframe
            else:
                # Fallback: No data manager - use cached data with facility filter
                if facility_filter and len(facility_filter) < len(all_facilities):
                    available_trips_df = available_trips_df[available_trips_df['from'].isin(facility_filter)]
            
            # Show filter summary
            filter_applied = False
            filter_parts = []
            
            if facility_filter and len(facility_filter) < len(all_facilities):
                filter_applied = True
                filter_parts.append(f"Facilities: {', '.join(facility_filter)}")
            
            if parcel_type_filter and len(parcel_type_filter) < len(all_parcel_types):
                filter_applied = True
                filter_parts.append(f"Parcel Types: {', '.join(parcel_type_filter)}")
            
            if category_filter and len(category_filter) < len(all_categories):
                filter_applied = True
                filter_parts.append(f"Categories: {', '.join(category_filter)}")
            
            if filter_applied:
                st.info(f"🔍 Filtered to {len(available_trips_df)} trips | {' | '.join(filter_parts)}")
            
            # Add selection column
            available_trips_df['Select'] = False
            
            # Use a stable key that reflects the current state
            editor_key = f"trip_selector_{len(available_trips_df)}_{current_assigned_count}"
            
            # Always show consistent columns - unified format (including new filters if available)
            display_columns = ['Select', 'from', 'trip_ref_number', 'hub']
            
            # Add optional columns if they exist
            if 'parcel_type' in available_trips_df.columns:
                display_columns.append('parcel_type')
            if 'category' in available_trips_df.columns:
                display_columns.append('category')
            
            # Add remaining standard columns
            display_columns.extend(['delivery_date', 'total_qty', 'total_value', 'product_count'])
            
            # Ensure trip_id_column is always available in display
            if trip_id_column not in display_columns and trip_id_column in available_trips_df.columns:
                # Add the trip_id_column to display_columns but don't show it to users
                # This ensures it's available for selection logic
                pass  # We'll handle this in the selection logic instead
            
            # Create trip selection interface
            edited_df = st.data_editor(
                available_trips_df[display_columns],
                column_config={
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select trips to assign to vehicle",
                        default=False,
                    ),
                    "from": st.column_config.TextColumn(
                        "Facility",
                        help="Origin facility for this trip",
                        width="medium"
                    ),
                    "trip_ref_number": st.column_config.TextColumn(
                        "Trip Ref #",
                        help="Trip reference number",
                        width="medium"
                    ),
                    "hub": st.column_config.TextColumn(
                        "Destination Hub",
                        help="Destination hub for this trip",
                        width="medium"
                    ),
                    "delivery_date": st.column_config.TextColumn(
                        "Delivery Date",
                        help="Scheduled delivery date"
                    ),
                    "total_qty": st.column_config.NumberColumn(
                        "Quantity",
                        help="Total quantity of products"
                    ),
                    "total_value": st.column_config.NumberColumn(
                        "Total Value",
                        format="₹%.2f"
                    ),
                    "product_count": st.column_config.NumberColumn(
                        "Products",
                        help="Number of different products"
                    )
                },
                disabled=[col for col in display_columns if col != "Select"],
                use_container_width=True,
                key=editor_key,
                hide_index=True
            )
        
        # Vehicle assignment section
        st.subheader("🚐 Vehicle Assignment")
        
        # Use a form to prevent constant re-renders
        with st.form("vehicle_assignment_form", clear_on_submit=True):
            # Single row layout for better alignment
            vehicle_col, button_col = st.columns([3, 1])
            
            with vehicle_col:
                vehicle_number = st.text_input(
                    "🚛 Vehicle Number:", 
                    placeholder="e.g., KA01AB1234",
                    help="Enter a valid vehicle registration number"
                )
            
            with button_col:
                # Add some spacing to align with text input
                st.write("")  # Empty line for spacing
                assign_button = st.form_submit_button(
                    "🚀 Assign to Vehicle", 
                    type="primary",
                    use_container_width=True
                )
            
            # Process the assignment
            if assign_button and vehicle_number:
                # Validate vehicle number
                if len(vehicle_number) < 5:
                    st.error("❌ Please enter a valid vehicle number")
                else:
                    # Get selected trips - access from original dataframe to ensure we have all columns
                    selected_indices = edited_df[edited_df['Select']].index
                    selected_trips = available_trips_df.loc[selected_indices, trip_id_column].tolist()
                    
                    if selected_trips:
                        # Get facilities for the selected trips (always available now)
                        trip_facilities = available_trips_df.loc[selected_indices, 'from'].unique().tolist()
                        
                        # Create assignment with enhanced trip information
                        assignment = {
                            'vehicle_number': vehicle_number,
                            'trip_refs': selected_trips,  # Contains composite IDs for unified format
                            'from_location': st.session_state.selected_route['from'],
                            'to_location': st.session_state.selected_route['to'],
                            'assignment_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'trip_count': len(selected_trips),
                            'trip_format': 'composite',  # Always composite now
                            'facilities': trip_facilities  # Always include facilities
                        }
                        
                        # Add detailed trip information for better tracking
                        selected_trip_details = []
                        for idx in selected_indices:
                            trip_info = available_trips_df.loc[idx]
                            selected_trip_details.append({
                                'composite_trip_id': trip_info[trip_id_column],
                                'trip_ref_number': trip_info.get('trip_ref_number', ''),
                                'hub': trip_info.get('hub', ''),
                                'facility': trip_info.get('from', ''),
                                'total_value': trip_info.get('total_value', 0),
                                'product_count': trip_info.get('product_count', 0)
                            })
                        assignment['trip_details'] = selected_trip_details
                        
                        # Add to session state
                        if 'vehicle_assignments' not in st.session_state:
                            st.session_state.vehicle_assignments = []
                        
                        st.session_state.vehicle_assignments.append(assignment)
                        
                        # Success message with enhanced information
                        unique_facilities = set(trip_facilities)
                        facility_info = f" from {len(unique_facilities)} facilities" if len(unique_facilities) > 1 else f" from {list(unique_facilities)[0]}"
                        st.success(f"✅ Assigned {len(selected_trips)} trips{facility_info} to vehicle {vehicle_number}")
                        
                        st.rerun()  # Refresh to update the UI
                    else:
                        st.warning("⚠️ Please select at least one trip to assign")
    
    # Show current assignments
    if st.session_state.vehicle_assignments:
        st.subheader("📋 Current Vehicle Assignments")
        
        for i, assignment in enumerate(st.session_state.vehicle_assignments):
            # Create an expanded view for better management
            with st.expander(f"🚛 {assignment['vehicle_number']} - {len(assignment['trip_refs'])} trips", expanded=True):
                # Vehicle info
                col_info, col_actions = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**Route**: {assignment['from_location']} → {assignment['to_location']}")
                    st.write(f"**Assigned**: {assignment['assignment_time']}")
                    
                    # Show trips in a more manageable format
                    st.write("**Trip Details:**")
                    
                    # Create a dataframe for trip management
                    trip_details = []
                    for trip_ref in assignment['trip_refs']:
                        # Initialize trip_data for each iteration to avoid scoping issues
                        trip_data = None
                        
                        # Handle both old and new trip formats
                        if assignment.get('trip_format') == 'composite' and 'trip_details' in assignment:
                            # Use enhanced trip details if available
                            for trip_detail in assignment['trip_details']:
                                if trip_detail['composite_trip_id'] == trip_ref:
                                    trip_details.append({
                                        'Facility': trip_detail['facility'],
                                        'Trip Ref #': trip_detail['trip_ref_number'],
                                        'Hub': trip_detail['hub'],
                                        'Value': f"₹{trip_detail['total_value']:.2f}",
                                        'Products': trip_detail['product_count']
                                    })
                                    break
                        else:
                            # Fallback to original trip data lookup
                            for t in st.session_state.trips_data:
                                trip_id_to_check = t.get('composite_trip_id', t.get('trip_ref_number'))
                                if str(trip_id_to_check) == str(trip_ref):
                                    trip_data = t
                                    break
                            
                        if trip_data:
                            # Determine display format based on available data
                            if 'composite_trip_id' in trip_data:
                                trip_details.append({
                                    'Facility': trip_data.get('from', 'N/A'),
                                    'Trip Ref #': trip_data['trip_ref_number'],
                                    'Hub': trip_data.get('hub', trip_data.get('to', 'N/A')),
                                    'Value': f"₹{trip_data['total_value']:.2f}",
                                    'Products': trip_data['product_count']
                                })
                            else:
                                # Legacy format
                                trip_details.append({
                                    'Trip Ref #': trip_data['trip_ref_number'],
                                    'Delivery Date': trip_data['delivery_date'],
                                    'Quantity': trip_data['total_qty'],
                                    'Value': f"₹{trip_data['total_value']:.2f}",
                                    'Products': trip_data['product_count']
                                })
                    
                    if trip_details:
                        trips_df = pd.DataFrame(trip_details)
                        st.dataframe(trips_df, use_container_width=True, hide_index=True)
                        
                        # Show summary statistics for composite trips
                        if assignment.get('trip_format') == 'composite':
                            unique_facilities = set()
                            unique_hubs = set()
                            total_value = 0
                            total_products = 0
                            
                            for detail in trip_details:
                                if 'Facility' in detail:
                                    unique_facilities.add(detail['Facility'])
                                if 'Hub' in detail:
                                    unique_hubs.add(detail['Hub'])
                                if 'Value' in detail:
                                    value_str = detail['Value'].replace('₹', '').replace(',', '')
                                    total_value += float(value_str)
                                if 'Products' in detail:
                                    total_products += detail['Products']
                            
                            col_stats1, col_stats2, col_stats3 = st.columns(3)
                            with col_stats1:
                                st.metric("Facilities", len(unique_facilities))
                            with col_stats2:
                                st.metric("Total Value", f"₹{total_value:,.2f}")
                            with col_stats3:
                                st.metric("Total Products", total_products)
                
                with col_actions:
                    st.write("**Actions:**")
                    
                    # Individual trip removal
                    if len(assignment['trip_refs']) > 1:
                        st.write("Remove individual trips:")
                        for j, trip_ref in enumerate(assignment['trip_refs']):
                            # Create display name for the button - use facility and trip ref
                            display_name = str(trip_ref)  # Default fallback
                            
                            if assignment.get('trip_format') == 'composite' and 'trip_details' in assignment:
                                # Use enhanced trip details for cleaner display
                                for trip_detail in assignment['trip_details']:
                                    if trip_detail.get('composite_trip_id') == trip_ref:
                                        facility = trip_detail.get('facility', 'Unknown')
                                        trip_num = trip_detail.get('trip_ref_number', 'Unknown')
                                        display_name = f"{facility} - {trip_num}"
                                        break
                            elif '@' in str(trip_ref):
                                # Parse composite ID for display
                                parts = str(trip_ref).split('@')
                                trip_num = parts[0]
                                facility = parts[2] if len(parts) > 2 else parts[1]
                                display_name = f"{facility} - {trip_num}"
                            
                            if st.button(f"❌ {display_name}", key=f"remove_trip_{i}_{j}", help=f"Remove trip {display_name} from vehicle"):
                                # Remove individual trip
                                assignment['trip_refs'].remove(trip_ref)
                                
                                # Also remove from trip_details if present
                                if 'trip_details' in assignment:
                                    assignment['trip_details'] = [
                                        detail for detail in assignment['trip_details'] 
                                        if detail.get('composite_trip_id') != trip_ref
                                    ]
                                
                                if not assignment['trip_refs']:  # If no trips left, remove vehicle
                                    st.session_state.vehicle_assignments.pop(i)
                                st.success(f"Removed trip {display_name} from vehicle {assignment['vehicle_number']}")
                                st.rerun()
                    
                    # Edit vehicle number
                    with st.form(f"edit_vehicle_{i}"):
                        new_vehicle_number = st.text_input(
                            "Edit Vehicle Number:", 
                            value=assignment['vehicle_number'],
                            key=f"edit_vehicle_input_{i}"
                        )
                        if st.form_submit_button("✏️ Update", help="Update vehicle number"):
                            if new_vehicle_number.strip():
                                assignment['vehicle_number'] = new_vehicle_number.strip().upper()
                                st.success(f"Updated vehicle number to {new_vehicle_number.strip().upper()}")
                                st.rerun()
                    
                    # Remove entire vehicle assignment
                    if st.button(f"🗑️ Remove Vehicle", key=f"remove_vehicle_{i}", type="secondary", help=f"Remove entire vehicle assignment"):
                        # Confirmation using dialog
                        if st.session_state.get(f'confirm_delete_{i}', False):
                            st.session_state.vehicle_assignments.pop(i)
                            st.session_state[f'confirm_delete_{i}'] = False
                            st.success(f"Removed vehicle {assignment['vehicle_number']} assignment")
                            st.rerun()
                        else:
                            st.session_state[f'confirm_delete_{i}'] = True
                            st.warning("⚠️ Click again to confirm deletion")
        
        # Enhanced clear all functionality
        st.markdown("---")
        col_clear1, col_clear2, col_clear3 = st.columns([1, 1, 1])
        
        with col_clear1:
            if st.button("🔄 Reset All Assignments", type="secondary", help="Clear all vehicle assignments"):
                if st.session_state.get('confirm_clear_all', False):
                    st.session_state.vehicle_assignments = []
                    st.session_state.confirm_clear_all = False
                    st.success("All assignments cleared!")
                    st.rerun()
                else:
                    st.session_state.confirm_clear_all = True
                    st.warning("⚠️ Click again to confirm clearing all assignments")
        
        with col_clear2:
            if st.button("📊 Assignment Summary", help="Show detailed assignment statistics"):
                st.session_state.show_summary = not st.session_state.get('show_summary', False)
        
        with col_clear3:
            total_assigned = sum(len(a['trip_refs']) for a in st.session_state.vehicle_assignments)
            remaining = len(st.session_state.trips_data) - total_assigned
            st.metric("Remaining Trips", remaining)
        
        # Show assignment summary if requested
        if st.session_state.get('show_summary', False):
            st.subheader("📈 Assignment Summary")
            
            summary_data = []
            for assignment in st.session_state.vehicle_assignments:
                # Calculate totals for this vehicle
                total_qty = 0
                total_value = 0.0
                
                for trip_ref_number in assignment['trip_refs']:
                    trip_data = next((t for t in st.session_state.trips_data if t['trip_ref_number'] == trip_ref_number), None)
                    if trip_data:
                        total_qty += trip_data['total_qty']
                        total_value += trip_data['total_value']
                
                summary_data.append({
                    'Vehicle': assignment['vehicle_number'],
                    'Trips': len(assignment['trip_refs']),
                    'Total Quantity': total_qty,
                    'Total Value': f"₹{total_value:.2f}",
                    'Route': f"{assignment['from_location']} → {assignment['to_location']}"
                })
            
            if summary_data:
                summary_df = pd.DataFrame(summary_data)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Overall totals
                col_total1, col_total2, col_total3 = st.columns(3)
                with col_total1:
                    st.metric("Total Vehicles", len(st.session_state.vehicle_assignments))
                with col_total2:
                    total_trips = sum(len(a['trip_refs']) for a in st.session_state.vehicle_assignments)
                    st.metric("Total Trips Assigned", total_trips)
                with col_total3:
                    remaining_trips = len(st.session_state.trips_data) - total_trips
                    st.metric("Trips Remaining", remaining_trips)
    
    # Instructions moved to bottom
    st.markdown("---")
    st.subheader("📋 How to Use")
    
    col_inst1, col_inst2 = st.columns(2)
    
    with col_inst1:
        st.markdown("""
        **Follow these steps:**
        
        1. **Select trips** using checkboxes above
        2. **Enter vehicle number** (e.g., KA01AB1234)
        3. **Click 'Assign to Vehicle'**
        4. **Repeat for more vehicles**
        5. **Proceed to DC generation**
        """)
    
    with col_inst2:
        st.markdown("""
        **💡 Tips:**
        
        - Select multiple trips for the same vehicle
        - Vehicle numbers should be valid formats
        - Review assignments in the main area above
        - All trips must be assigned before proceeding
        """)
        
        # Quick stats
        if st.session_state.trips_data:
            st.info(f"📊 **Total trips:** {len(st.session_state.trips_data)} | **Route:** {st.session_state.selected_route['from']} → {st.session_state.selected_route['to']}")

def generate_dcs_page():
    st.header("📄 Step 4: Generate DCs, PDFs & E-Way Templates")
    
    if not st.session_state.vehicle_assignments:
        st.warning("⚠️ Please assign trips to vehicles first (Step 3)")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚛 Vehicle Assignments Ready for Generation")
        
        # Show assignments summary
        for i, assignment in enumerate(st.session_state.vehicle_assignments):
            with st.expander(f"🚐 Vehicle: {assignment['vehicle_number']} ({len(assignment['trip_refs'])} trips)"):
                st.write(f"**Route**: {assignment['from_location']} → {assignment['to_location']}")
                
                # If we have facility information for the trips, show it
                if 'facilities' in assignment:
                    st.write(f"**Facilities**: {', '.join(assignment['facilities'])}")
                    
                st.write(f"**Trip Refs**: {', '.join(map(str, assignment['trip_refs']))}")
                st.write(f"**Assigned**: {assignment['assignment_time']}")
        
        # Generation options
        st.subheader("⚙️ Generation Options")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        with col_a:
            create_zip = st.checkbox("📦 Create ZIP file", value=True, help="Bundle all generated files into a ZIP file")
        
        with col_b:
            include_audit = st.checkbox("📋 Include audit trail", value=True, help="Include trip-to-vehicle mapping file")
        
        with col_c:
            generate_pdfs = st.checkbox("📄 Generate PDFs", value=True, help="Generate print-ready PDF versions of DCs")
        
        with col_d:
            consolidate_eway_bills = st.checkbox("🔗 Consolidate E-Way Bills", value=True, 
                                                 help="Consolidate e-way bill templates by seller (recommended)")
        
        # Info about generation modes
        if consolidate_eway_bills:
            st.info("📋 **E-Way Consolidation ON**: One file per seller (EWAY_BODEGA_Consolidated.xlsx, EWAY_AMOLAKCHAND_Consolidated.xlsx, etc.)")
        else:
            st.info("📋 **E-Way Consolidation OFF**: Individual file per DC (EWAY_BDDCAH000301_Vehicle.xlsx, etc.)")
        
        # Generate button
        if st.button("🚀 Generate Complete Package (Excel + PDF + E-Way)", type="primary", use_container_width=True):
            generate_vehicle_dcs(create_zip, include_audit, generate_pdfs, consolidate_eway_bills)
    
    with col2:
        st.subheader("📊 Generation Preview")
        
        if st.session_state.vehicle_assignments:
            total_vehicles = len(st.session_state.vehicle_assignments)
            # Each vehicle will have 3 file sets (Excel + PDF + E-Way template per seller)
            estimated_file_sets = total_vehicles * 3
            
            st.metric("🚛 Vehicles", total_vehicles)
            st.metric("📄 File Sets", estimated_file_sets, help="Each set contains Excel + PDF + E-Way template")
            st.metric("🏭 Sellers", 3, help="Amolakchand, SourcingBee, Bodega")
            
            st.info("Each vehicle generates 3 complete file sets (Excel + PDF + E-Way per seller)")
        
        st.markdown("""
        **Complete package includes:**
        - 📊 **Excel DCs** with vehicle number in cell I4
        - 📄 **Print-ready PDFs** (landscape, scale-to-fit)
        - 📋 **E-Way templates** ready for ClearTax upload
        - 🔄 Products consolidated by seller
        - ✂️ Auto-split if >250 line items
        - 📊 Audit trail mapping
        - 📦 ZIP bundle with organized folders
        """)

def generate_vehicle_dcs(create_zip=True, include_audit=True, generate_pdfs=True, consolidate_eway_bills=True):
    """Generate vehicle-based DCs with unified e-way template generation and PDF support"""
    
    progress_bar = st.progress(0, text="Starting unified DC + PDF + E-Way template generation...")
    
    try:
        # Initialize generator
        dc_generator = VehicleDCGenerator()
        all_results = []
        
        total_assignments = len(st.session_state.vehicle_assignments)
        
        # FIXED: Collect all vehicle DC data first for proper consolidation
        all_vehicle_dc_data = []
        
        for i, assignment in enumerate(st.session_state.vehicle_assignments):
            progress_bar.progress(
                (i * 0.3) / total_assignments, 
                text=f"Collecting data for vehicle {assignment['vehicle_number']}..."
            )
            
            # Get DC data for this vehicle
            try:
                vehicle_dc_data = st.session_state.data_manager.get_vehicle_dc_data(
                    assignment['trip_refs'], 
                    assignment['vehicle_number']
                )
                
                if vehicle_dc_data:
                    # Add to batch processing list
                    all_vehicle_dc_data.extend(vehicle_dc_data)
                    print(f"✅ Collected data for vehicle {assignment['vehicle_number']}: {len(vehicle_dc_data)} DCs")
                else:
                    error_msg = f"❌ Failed to process vehicle {assignment['vehicle_number']}: get_vehicle_dc_data returned None/empty"
                    print(error_msg)
                    st.error(error_msg)
                    st.warning(f"Check: Are trips selected properly? Trip refs: {assignment.get('trip_refs', [])[:3]}...")
            except Exception as e:
                error_msg = f"❌ Exception processing vehicle {assignment['vehicle_number']}: {str(e)}"
                print(error_msg)
                import traceback
                print(traceback.format_exc())
                st.error(error_msg)
                st.code(traceback.format_exc())
        
        if all_vehicle_dc_data:
            progress_bar.progress(0.5, text="Processing all vehicles with consolidation...")
            
            # FIXED: Process all vehicles in a single batch for proper consolidation
            all_results = dc_generator.generate_vehicle_dcs(
                all_vehicle_dc_data, 
                generate_eway_templates=True,
                generate_pdfs=generate_pdfs,
                consolidate_eway_bills=consolidate_eway_bills
            )
            
            print(f"✅ Batch processing completed: {len(all_results)} total DCs generated")
        
        progress_bar.progress(1.0, text="Finalizing and creating summary...")
        
        
        if all_results:
            # Filter out None results from failed generations
            all_results = [r for r in all_results if r is not None]
            
            if not all_results:
                st.error("❌ All DC generations failed")
                return
            
            # Calculate overall statistics including PDF
            total_dcs = len(all_results)
            total_eway_success = sum(1 for r in all_results if r.get('eway_template_status') == 'success')
            total_eway_failed = sum(1 for r in all_results if r.get('eway_template_status') == 'failed')
            total_pdf_success = sum(1 for r in all_results if r.get('pdf_status') == 'success')
            total_pdf_failed = sum(1 for r in all_results if r.get('pdf_status') == 'failed')
            unique_vehicles = len(set(r.get('vehicle_number', 'UNKNOWN') for r in all_results if r.get('vehicle_number')))
            
            # Create summary
            summary_file = dc_generator.create_generation_summary(all_results, st.session_state.vehicle_assignments)
            
            # Create audit trail
            audit_file = None
            if include_audit:
                audit_file = st.session_state.data_manager.create_audit_trail(st.session_state.vehicle_assignments)
            
            # Create ZIP file (now includes DCs, PDFs, and E-Way templates)
            zip_file = None
            if create_zip:
                zip_file = create_unified_zip_file(all_results, summary_file, audit_file, generate_pdfs)
            
            # Enhanced success message
            success_parts = [f"{total_dcs} DCs"]
            if generate_pdfs:
                success_parts.append(f"{total_pdf_success} PDFs")
            success_parts.append(f"{total_eway_success} E-Way templates")
            
            st.success(f"🎉 Successfully generated for {unique_vehicles} vehicles: " + " + ".join(success_parts))
            
            # Show per-vehicle breakdown
            vehicle_breakdown = {}
            for result in all_results:
                vehicle_num = result['vehicle_number']
                if vehicle_num not in vehicle_breakdown:
                    vehicle_breakdown[vehicle_num] = {'dcs': 0, 'sellers': set()}
                vehicle_breakdown[vehicle_num]['dcs'] += 1
                vehicle_breakdown[vehicle_num]['sellers'].add(result.get('hub_type', 'Unknown'))
            
            with st.expander("📊 Per-Vehicle Breakdown", expanded=True):
                for vehicle_num, stats in vehicle_breakdown.items():
                    sellers_list = ', '.join(sorted(stats['sellers']))
                    st.write(f"**Vehicle {vehicle_num}**: {stats['dcs']} DCs from {len(stats['sellers'])} sellers ({sellers_list})")
            
            # Enhanced statistics display
            if generate_pdfs:
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            else:
                col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("📄 Excel DCs", total_dcs)
            with col_stat2:
                if generate_pdfs:
                    if total_pdf_failed > 0:
                        st.metric("📄 PDFs", total_pdf_success, delta=f"{total_pdf_failed} failed")
                    else:
                        st.metric("📄 PDFs", total_pdf_success, delta="✅ All success")
                else:
                    st.metric("✅ E-Way Templates", total_eway_success, delta=f"{total_eway_success}/{total_dcs}")
            
            with col_stat3:
                if generate_pdfs:
                    st.metric("✅ E-Way Templates", total_eway_success, delta=f"{total_eway_success}/{total_dcs}")
                else:
                    if total_eway_failed > 0:
                        st.metric("❌ E-Way Failures", total_eway_failed, delta=f"Check logs")
                    else:
                        st.metric("🎯 Success Rate", "100%", delta="Perfect!")
            
            if generate_pdfs:
                with col_stat4:
                    total_failures = total_eway_failed + total_pdf_failed
                    if total_failures > 0:
                        st.metric("❌ Total Failures", total_failures, delta=f"Check logs")
                    else:
                        st.metric("🎯 Success Rate", "100%", delta="Perfect!")
            
            # Show any generation errors
            has_errors = total_eway_failed > 0 or (generate_pdfs and total_pdf_failed > 0)
            if has_errors:
                with st.expander("⚠️ Generation Issues", expanded=False):
                    # E-Way template errors
                    if total_eway_failed > 0:
                        st.subheader("E-Way Template Issues:")
                        failed_eway = [r for r in all_results if r.get('eway_template_status') == 'failed']
                        for failed in failed_eway:
                            st.error(f"**{failed['dc_number']}**: {failed.get('eway_error', 'Unknown error')}")
                    
                    # PDF generation errors
                    if generate_pdfs and total_pdf_failed > 0:
                        st.subheader("PDF Generation Issues:")
                        failed_pdf = [r for r in all_results if r.get('pdf_status') == 'failed']
                        for failed in failed_pdf:
                            st.error(f"**{failed['dc_number']}**: {failed.get('pdf_error', 'Unknown error')}")
            
            # Download options
            st.subheader("📥 Download Files")
            
            if zip_file and os.path.exists(zip_file):
                with open(zip_file, 'rb') as f:
                    zip_label = "📦 Download Complete Package (ZIP)"
                    if generate_pdfs:
                        zip_label += f" - Excel + PDF + E-Way"
                    else:
                        zip_label += f" - Excel + E-Way"
                    
                    st.download_button(
                        label=zip_label,
                        data=f.read(),
                        file_name=os.path.basename(zip_file),
                        mime="application/zip"
                    )
            
            # Individual file downloads with complete file sets
            with st.expander("📄 Individual Files by DC"):
                for result in all_results:
                    # Skip if result is None or missing required fields
                    if not result or not result.get('dc_number') or not result.get('file_path'):
                        continue
                        
                    st.write(f"**{result['dc_number']} - Vehicle {result['vehicle_number']}**")
                    
                    if generate_pdfs:
                        col_excel, col_pdf, col_eway = st.columns(3)
                    else:
                        col_excel, col_eway = st.columns(2)
                        col_pdf = None
                    
                    # Excel DC file download
                    with col_excel:
                        if result.get('file_path') and os.path.exists(result['file_path']):
                            with open(result['file_path'], 'rb') as f:
                                st.download_button(
                                        label=f"📊 Excel",
                                    data=f.read(),
                                    file_name=os.path.basename(result['file_path']),
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        key=f"excel_{result['dc_number']}"
                                )
        
                    # PDF file download
                    if generate_pdfs and col_pdf:
                        with col_pdf:
                            if result.get('pdf_path') and os.path.exists(result['pdf_path']):
                                with open(result['pdf_path'], 'rb') as f:
                                    st.download_button(
                                        label=f"📄 PDF",
                                        data=f.read(),
                                        file_name=os.path.basename(result['pdf_path']),
                                        mime="application/pdf",
                                        key=f"pdf_{result['dc_number']}"
                                    )
        
                    # E-Way template download
                    with col_eway:
                        if result.get('eway_template_path') and os.path.exists(result['eway_template_path']):
                            with open(result['eway_template_path'], 'rb') as f:
                                st.download_button(
                                    label=f"📋 E-Way",
                                    data=f.read(),
                                    file_name=os.path.basename(result['eway_template_path']),
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"eway_{result['dc_number']}"
                                )
                        else:
                            st.error(f"E-Way template not available")
                    
                    st.markdown("---")
        
        else:
            st.error("❌ No files were generated")
            
    except Exception as e:
        st.error(f"❌ Error during generation: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        progress_bar.empty()

def create_unified_zip_file(results, summary_file, audit_file, generate_pdfs):
    """Create a ZIP file containing all generated DC, PDF, and E-Way template files"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"vehicle_dc_complete_package_{timestamp}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add DC Excel files
            dc_count = 0
            for result in results:
                if result and result.get('file_path') and os.path.exists(result['file_path']):
                    zipf.write(result['file_path'], f"Excel_DCs/{os.path.basename(result['file_path'])}")
                    dc_count += 1
            
            # Add PDF files if generated
            pdf_count = 0
            if generate_pdfs:
                for result in results:
                    if result and result.get('pdf_path') and os.path.exists(result['pdf_path']):
                        zipf.write(result['pdf_path'], f"PDF_DCs/{os.path.basename(result['pdf_path'])}")
                        pdf_count += 1
            
            # Add E-Way template files
            eway_count = 0
            for result in results:
                if result and result.get('eway_template_path') and os.path.exists(result['eway_template_path']):
                    zipf.write(result['eway_template_path'], f"EWay_Templates/{os.path.basename(result['eway_template_path'])}")
                    eway_count += 1
            
            # Add summary file
            if summary_file and os.path.exists(summary_file):
                zipf.write(summary_file, f"Reports/{os.path.basename(summary_file)}")
            
            # Add audit file
            if audit_file and os.path.exists(audit_file):
                zipf.write(audit_file, f"Reports/{os.path.basename(audit_file)}")
        
            # Create a comprehensive README file
            readme_content = f"""# Vehicle DC Complete Package - {timestamp}

## Package Contents:
- Excel_DCs/: {dc_count} Delivery Challan Excel files
"""
            
            if generate_pdfs:
                readme_content += f"- PDF_DCs/: {pdf_count} Print-ready PDF versions of DCs\n"
            
            readme_content += f"""- EWay_Templates/: {eway_count} E-Way Bill template Excel files
- Reports/: Generation summary and audit trail

## File Usage:
1. **Excel DCs**: Use for internal documentation, compliance, and data processing
2. **PDF DCs**: Print-ready versions for physical documentation and courier packages
3. **E-Way Templates**: Upload to ClearTax for e-way bill generation
4. **Reports**: Detailed generation logs and vehicle-trip mappings

## Generation Statistics:
- Excel DCs Generated: {dc_count}
"""
            
            if generate_pdfs:
                readme_content += f"- PDF DCs Generated: {pdf_count}\n"
            
            readme_content += f"""- E-Way Templates Generated: {eway_count}
- Total Vehicles Processed: {len(set(r.get('vehicle_number', 'UNKNOWN') for r in results if r and r.get('vehicle_number')))}

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
System: Unified DC + PDF + E-Way Generation
"""
            zipf.writestr("README.txt", readme_content)
        
        # Enhanced logging
        log_parts = [f"{dc_count} Excel DCs"]
        if generate_pdfs:
            log_parts.append(f"{pdf_count} PDF DCs")
        log_parts.append(f"{eway_count} E-Way templates")
        
        print(f"✅ Created complete package ZIP: {zip_filename} ({' + '.join(log_parts)})")
        return zip_filename
        
    except Exception as e:
        st.error(f"❌ Error creating complete package ZIP: {str(e)}")
        return None

def run_settings():
    """Run the settings UI with legacy support for existing DC conversion"""
    st.title("⚙️ Settings & Configuration")
    
    # Create tabs for different settings
    settings_tab1, settings_tab2, settings_tab3 = st.tabs(["🏢 GSTIN Configuration", "🔄 Legacy DC Conversion", "🔧 System Diagnostics"])
    
    with settings_tab1:
        st.header("🏢 GSTIN Configuration")
        st.write("Configure GSTIN information for each facility")
        
        # Load existing GSTIN mapping
        gstin_mapping = {}
        gstin_file = "config/gstin_mapping.json"
        
        if os.path.exists(gstin_file):
            try:
                with open(gstin_file, "r") as f:
                    gstin_mapping = json.load(f)
                st.success("✅ Loaded existing GSTIN configuration")
            except Exception as e:
                st.error(f"Error loading GSTIN configuration: {str(e)}")
        else:
            st.info("ℹ️ No existing GSTIN configuration found. Creating new configuration.")
        
        # Edit GSTIN mapping
        st.subheader("Edit GSTIN Mapping")
        
        # Default facilities
        default_facilities = ["SOURCINGBEE", "AMOLAKCHAND", "BODEGA"]
        
        # Create input fields for each facility
        updated_mapping = {}
        for facility in default_facilities:
            current_gstin = gstin_mapping.get(facility, "")
            gstin_input = st.text_input(
                f"GSTIN for {facility}",
                value=current_gstin,
                key=f"gstin_{facility}",
                help=f"Enter 15-digit GSTIN for {facility}"
            )
            if gstin_input:
                updated_mapping[facility] = gstin_input
        
        # Add custom facility
        st.subheader("Add Custom Facility")
        col1, col2 = st.columns(2)
        with col1:
            custom_facility = st.text_input("Custom Facility Name")
        with col2:
            custom_gstin = st.text_input("Custom GSTIN")
        
        if custom_facility and custom_gstin:
            updated_mapping[custom_facility] = custom_gstin
        
        # Save button
        if st.button("💾 Save GSTIN Configuration"):
            try:
                # Ensure config directory exists
                os.makedirs("config", exist_ok=True)
                
                # Save updated mapping
                with open(gstin_file, "w") as f:
                    json.dump(updated_mapping, f, indent=4)
                
                st.success("✅ GSTIN configuration saved successfully!")
            except Exception as e:
                st.error(f"❌ Error saving GSTIN configuration: {str(e)}")
        
        # Show current mapping
        if updated_mapping:
            st.subheader("Current GSTIN Mapping")
            mapping_df = pd.DataFrame(list(updated_mapping.items()), columns=["Facility", "GSTIN"])
            st.dataframe(mapping_df, use_container_width=True, hide_index=True)
    
    with settings_tab2:
        st.header("🔄 Legacy DC Conversion")
        st.info("Convert existing DC files to E-Way Bill templates (for files generated before unified system)")
        
        # File upload for legacy conversion
        conversion_method = st.radio(
            "Select conversion method:",
            ["Single DC File (Excel)", "Multiple DC Files (Directory)"],
            index=0
        )
        
        if conversion_method == "Single DC File (Excel)":
            uploaded_dc = st.file_uploader("Upload existing DC Excel file", type=["xlsx", "xls"], key="legacy_dc")
            
            if uploaded_dc is not None:
                # Save the uploaded file temporarily
                temp_dc_path = "temp_legacy_dc.xlsx"
                with open(temp_dc_path, "wb") as f:
                    f.write(uploaded_dc.getbuffer())
                
                # Convert and generate e-way template
                with st.spinner("Converting DC to E-Way template..."):
                    try:
                        converter = ExcelDCConverter()
                        dc_data = converter.convert_excel_to_json(temp_dc_path)
                        
                        if dc_data:
                            # Generate e-way template
                            template_generator = EwayBillTemplateGenerator()
                            
                            # Load GSTIN mapping
                            if os.path.exists("config/gstin_mapping.json"):
                                with open("config/gstin_mapping.json", "r") as f:
                                    template_generator.facility_gstin_mapping = json.load(f)
                            
                            rows = template_generator.generate_template_from_dc(dc_data)
                            
                            # Generate output filename
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            output_file = f"legacy_eway_template_{timestamp}.xlsx"
                            template_generator.save_to_excel(rows, output_file)
                            
                            st.success(f"✅ Converted DC to E-Way template with {len(rows)} rows")
                            
                            # Provide download
                            if os.path.exists(output_file):
                                with open(output_file, "rb") as file:
                                    st.download_button(
                                        label="📋 Download E-Way Template",
                                        data=file,
                                        file_name=output_file,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                        else:
                            st.error("❌ Failed to convert DC file")
                    except Exception as e:
                        st.error(f"❌ Error converting DC: {str(e)}")
        
        elif conversion_method == "Multiple DC Files (Directory)":
            dc_directory = st.text_input("Directory containing DC Excel files", "generated_vehicle_dcs")
            
            if st.button("🔍 Scan Directory"):
                if os.path.exists(dc_directory):
                    dc_files = [f for f in os.listdir(dc_directory) if f.endswith(('.xlsx', '.xls'))]
                    
                    if dc_files:
                        st.success(f"✅ Found {len(dc_files)} DC files")
                        
                        selected_files = st.multiselect("Select DC files to convert:", dc_files)
                        
                        if selected_files and st.button("🔄 Convert Selected Files"):
                            with st.spinner(f"Converting {len(selected_files)} DC files..."):
                                try:
                                    converter = ExcelDCConverter()
                                    template_generator = EwayBillTemplateGenerator()
                                    
                                    # Load GSTIN mapping
                                    if os.path.exists("config/gstin_mapping.json"):
                                        with open("config/gstin_mapping.json", "r") as f:
                                            template_generator.facility_gstin_mapping = json.load(f)
                                    
                                    all_rows = []
                                    conversion_results = []
                                    
                                    for dc_file in selected_files:
                                        dc_path = os.path.join(dc_directory, dc_file)
                                        dc_data = converter.convert_excel_to_json(dc_path)
                                        
                                        if dc_data:
                                            rows = template_generator.generate_template_from_dc(dc_data)
                                            all_rows.extend(rows)
                                            conversion_results.append({"file": dc_file, "rows": len(rows), "status": "success"})
                                        else:
                                            conversion_results.append({"file": dc_file, "rows": 0, "status": "failed"})
                                    
                                    if all_rows:
                                        # Save combined e-way template
                                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                        output_file = f"legacy_eway_templates_combined_{timestamp}.xlsx"
                                        template_generator.save_to_excel(all_rows, output_file)
                                        
                                        successful_conversions = sum(1 for r in conversion_results if r["status"] == "success")
                                        st.success(f"✅ Converted {successful_conversions}/{len(selected_files)} files with {len(all_rows)} total rows")
                                        
                                        # Show conversion results
                                        results_df = pd.DataFrame(conversion_results)
                                        st.dataframe(results_df)
                                        
                                        # Provide download
                                        if os.path.exists(output_file):
                                            with open(output_file, "rb") as file:
                                                st.download_button(
                                                    label="📋 Download Combined E-Way Templates",
                                                    data=file,
                                                    file_name=output_file,
                                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                                )
                                    else:
                                        st.error("❌ No files were successfully converted")
                                        
                                except Exception as e:
                                    st.error(f"❌ Error during batch conversion: {str(e)}")
                    else:
                        st.warning("⚠️ No Excel files found in directory")
                else:
                    st.error("❌ Directory does not exist")
        
        # Information about unified system
        st.markdown("---")
        st.info("""
        **ℹ️ About Legacy Conversion:**
        
        This tool is for converting DC files that were generated **before** the unified system was implemented. 
        
        **For new DC generation**, use the main Vehicle DC Generator which automatically creates both DC and E-Way templates together.
        """)

    with settings_tab3:
        st.header("🔧 System Diagnostics")
        st.write("Debug and test system components, especially for cloud deployment issues")
        
        # Add diagnostic sections
        diag_tab1, diag_tab2, diag_tab3 = st.tabs(["🌐 Supabase Connection", "🔢 Sequence Status", "🚀 Test Generation"])
        
        with diag_tab1:
            st.subheader("🌐 Supabase Connection Diagnostics")
            st.info("This section helps debug Supabase connection issues, especially in Streamlit Cloud")
            
            if st.button("🔍 Test Supabase Connection"):
                with st.spinner("Testing Supabase connection..."):
                    try:
                        # Test environment detection
                        st.write("**Environment Detection:**")
                        env_supabase_url = os.getenv('SUPABASE_URL')
                        env_supabase_key = os.getenv('SUPABASE_KEY')
                        
                        st.write(f"- Environment SUPABASE_URL: {'✅ Found' if env_supabase_url else '❌ Missing'}")
                        st.write(f"- Environment SUPABASE_KEY: {'✅ Found' if env_supabase_key else '❌ Missing'}")
                        
                        # Test Streamlit secrets
                        st.write("\n**Streamlit Secrets:**")
                        try:
                            secrets_url = st.secrets.get('SUPABASE_URL')
                            secrets_key = st.secrets.get('SUPABASE_KEY')
                            st.write(f"- Streamlit secrets SUPABASE_URL: {'✅ Found' if secrets_url else '❌ Missing'}")
                            st.write(f"- Streamlit secrets SUPABASE_KEY: {'✅ Found' if secrets_key else '❌ Missing'}")
                        except Exception as e:
                            st.write(f"- ❌ Error accessing secrets: {e}")
                        
                        # Test Supabase service
                        st.write("\n**Supabase Service Test:**")
                        try:
                            from src.core.supabase_sequence_service import supabase_sequence_service
                            
                            st.write(f"- Service enabled: {'✅ Yes' if supabase_sequence_service.enabled else '❌ No'}")
                            
                            if supabase_sequence_service.enabled:
                                # Test health check
                                health = supabase_sequence_service.health_check()
                                st.write(f"- Health status: {health['status']}")
                                st.write(f"- Health message: {health['message']}")
                                
                                # Test getting sequences
                                success, sequences = supabase_sequence_service.get_current_sequences()
                                if success:
                                    st.write(f"- Current sequences: {sequences}")
                                else:
                                    st.write("- ❌ Failed to get sequences")
                                
                                # Test generating sequence
                                success, next_seq = supabase_sequence_service.get_next_sequence('TEST')
                                if success:
                                    st.write(f"- Test sequence generation: ✅ Success (TEST:{next_seq})")
                                else:
                                    st.write("- ❌ Failed to generate test sequence")
                            else:
                                st.write("- ❌ Service not enabled - check credentials")
                                
                        except Exception as e:
                            st.write(f"- ❌ Error testing service: {e}")
                            st.code(str(e))
                        
                        # Test cloud detection
                        st.write("\n**Cloud Environment Detection:**")
                        
                        # Enhanced cloud detection with multiple methods
                        cloud_indicators = {
                            'STREAMLIT_SHARING_MODE': bool(os.getenv('STREAMLIT_SHARING_MODE')),
                            'STREAMLIT_RUNTIME_CREDENTIALS': bool(os.getenv('STREAMLIT_RUNTIME_CREDENTIALS')),
                            'STREAMLIT_SERVER_HEADLESS': bool(os.getenv('STREAMLIT_SERVER_HEADLESS')),
                            'STREAMLIT_CLOUD': bool(os.getenv('STREAMLIT_CLOUD')),
                            'IS_STREAMLIT_CLOUD': bool(os.getenv('IS_STREAMLIT_CLOUD')),
                            'HOSTNAME_contains_streamlit': 'streamlit' in os.getenv('HOSTNAME', '').lower(),
                        }
                        
                        # Also check if we're in a cloud-like environment
                        try:
                            import socket
                            hostname = socket.gethostname()
                            cloud_indicators['hostname_check'] = 'streamlit' in hostname.lower() or 'share' in hostname.lower()
                        except:
                            cloud_indicators['hostname_check'] = False
                        
                        # Show all cloud detection methods
                        for method, detected in cloud_indicators.items():
                            status = "✅ Yes" if detected else "❌ No"
                            st.write(f"- {method}: {status}")
                        
                        # Overall cloud detection
                        is_cloud = any(cloud_indicators.values())
                        st.write(f"\n**🌐 Final Cloud Detection: {'✅ YES' if is_cloud else '❌ NO'}**")
                        
                        # If cloud detected, show which method(s) detected it
                        if is_cloud:
                            detected_methods = [method for method, detected in cloud_indicators.items() if detected]
                            st.write(f"- Detected via: {', '.join(detected_methods)}")
                        
                        # Show current environment info for debugging
                        st.write("\n**Environment Debug Info:**")
                        st.write(f"- Current working directory: {os.getcwd()}")
                        try:
                            import socket
                            st.write(f"- Hostname: {socket.gethostname()}")
                        except:
                            st.write("- Hostname: Unable to detect")
                        
                        # Show key environment variables for debugging
                        env_vars_to_check = ['HOSTNAME', 'USER', 'HOME', 'PATH']
                        for var in env_vars_to_check:
                            value = os.getenv(var, 'Not set')
                            # Truncate long values
                            if len(value) > 50:
                                value = value[:50] + "..."
                            st.write(f"- {var}: {value}")
                        
                        st.write(f"\n📊 **Summary**: Supabase connection is {'✅ WORKING' if supabase_sequence_service.enabled else '❌ FAILED'}")
                        if is_cloud:
                            st.write("☁️ **Cloud Environment**: Detected - should prioritize Supabase")
                        else:
                            st.write("🏠 **Local Environment**: Detected - but Supabase still available")
                        
                    except Exception as e:
                        st.error(f"❌ Diagnostic test failed: {e}")
        
        with diag_tab2:
            st.subheader("🔢 Sequence Status")
            st.info("Check current sequence numbers and identify sync issues")
            
            if st.button("📊 Check Sequence Status"):
                with st.spinner("Checking sequence status..."):
                    try:
                        # Import DC sequence manager
                        from src.core.dc_sequence_manager import dc_sequence_manager
                        
                        # Get health report
                        health_report = dc_sequence_manager.get_sequence_health_report()
                        
                        st.write("**Sequence Health Report:**")
                        st.write(f"- Health Status: {health_report['health_status']}")
                        st.write(f"- Local sequences: {health_report['local_sequences']}")
                        st.write(f"- Max sequence: {health_report['max_sequence']}")
                        st.write(f"- Min sequence: {health_report['min_sequence']}")
                        st.write(f"- Last updated: {health_report['last_updated']}")
                        
                        if health_report['warnings']:
                            st.write(f"- Warnings: {health_report['warnings']}")
                        
                        # Supabase health
                        if health_report['supabase_health']:
                            st.write(f"- Supabase status: {health_report['supabase_health']['status']}")
                            st.write(f"- Supabase sequences: {health_report['supabase_health'].get('sequences', {})}")
                        
                        # Show comparison
                        if health_report['supabase_health'] and health_report['supabase_health']['status'] == 'healthy':
                            st.write("\n**Local vs Supabase Comparison:**")
                            local_seqs = health_report['local_sequences']
                            supabase_seqs = health_report['supabase_health'].get('sequences', {})
                            
                            for prefix in local_seqs:
                                local_val = local_seqs[prefix]
                                supabase_val = supabase_seqs.get(prefix, 0)
                                status = "✅ Match" if local_val == supabase_val else "❌ Mismatch"
                                st.write(f"- {prefix}: Local={local_val}, Supabase={supabase_val} {status}")
                        
                    except Exception as e:
                        st.error(f"❌ Error checking sequence status: {e}")
        
        with diag_tab3:
            st.subheader("🚀 Test DC Generation")
            st.info("Test actual DC generation to identify issues")
            
            col1, col2 = st.columns(2)
            with col1:
                test_company = st.selectbox("Test Company", ["AMOLAKCHAND", "BODEGA", "SOURCINGBEE"])
            with col2:
                test_facility = st.selectbox("Test Facility", ["Arihant", "Sutlej/Gomati"])
            
            if st.button("🧪 Generate Test DC"):
                with st.spinner("Generating test DC..."):
                    try:
                        from src.core.dc_sequence_manager import dc_sequence_manager
                        
                        # Generate DC
                        dc_number = dc_sequence_manager.generate_dc_number(test_company, test_facility)
                        
                        st.success(f"✅ Generated test DC: {dc_number}")
                        
                        # Show updated sequences
                        sequences = dc_sequence_manager.get_current_sequences()
                        st.write(f"Current sequences after generation: {sequences}")
                        
                    except Exception as e:
                        st.error(f"❌ Error generating test DC: {e}")
                        st.code(str(e))
        
        # Warning message
        st.warning("⚠️ **Important**: The test generation will increment actual sequence numbers. Use with caution in production!")

if __name__ == "__main__":
    main() 