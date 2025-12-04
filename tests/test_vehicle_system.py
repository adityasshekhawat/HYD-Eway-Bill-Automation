#!/usr/bin/env python3
"""
Test script for vehicle-based DC generation system
Quick test without the Streamlit frontend
"""

from vehicle_data_manager import VehicleDataManager
from vehicle_dc_generator import VehicleDCGenerator

def test_vehicle_system():
    print("🧪 Testing Vehicle-Based DC Generation System")
    print("=" * 50)
    
    # Initialize data manager
    print("1️⃣ Initializing data manager...")
    data_manager = VehicleDataManager()
    
    # Load data
    print("2️⃣ Loading data...")
    success = data_manager.load_data()
    if not success:
        print("❌ Failed to load data")
        return
    
    # Get routes
    print("3️⃣ Getting available routes...")
    routes = data_manager.get_available_routes()
    print(f"✅ Found {len(routes)} routes")
    
    if not routes:
        print("❌ No routes found")
        return
    
    # Show first few routes
    print("\n📍 Sample routes:")
    for i, route in enumerate(routes[:3]):
        print(f"   {i+1}. {route['from']} → {route['to']} ({route['trip_count']} trips)")
    
    # Select first route for testing
    test_route = routes[0]
    print(f"\n4️⃣ Testing with route: {test_route['from']} → {test_route['to']}")
    
    # Get trips for route
    trips = data_manager.get_trips_for_route(test_route['from'], test_route['to'])
    print(f"✅ Found {len(trips)} trips for route")
    
    if not trips:
        print("❌ No trips found for route")
        return
    
    # Select first few trips for testing
    test_trips = [trip['trip_id'] for trip in trips[:3]]  # Take first 3 trips
    test_vehicle = "TEST001"
    
    print(f"5️⃣ Testing with {len(test_trips)} trips assigned to vehicle {test_vehicle}")
    print(f"   Trip IDs: {test_trips}")
    
    # Generate vehicle DC data
    print("6️⃣ Generating vehicle DC data...")
    vehicle_dc_data = data_manager.get_vehicle_dc_data(test_trips, test_vehicle)
    
    if not vehicle_dc_data:
        print("❌ Failed to generate vehicle DC data")
        return
    
    print(f"✅ Generated DC data for {len(vehicle_dc_data)} sellers")
    
    # Generate DCs
    print("7️⃣ Generating Excel DCs...")
    dc_generator = VehicleDCGenerator()
    results = dc_generator.generate_vehicle_dcs(vehicle_dc_data)
    
    if results:
        print(f"✅ Successfully generated {len(results)} vehicle DCs!")
        print("\n📄 Generated files:")
        for result in results:
            print(f"   - {result['dc_number']}: {result['file_path']}")
        
        # Create audit trail
        test_assignments = [{
            'vehicle_number': test_vehicle,
            'trip_ids': test_trips,
            'from_location': test_route['from'],
            'to_location': test_route['to'],
            'dc_count': len(results)
        }]
        
        audit_file = data_manager.create_audit_trail(test_assignments)
        if audit_file:
            print(f"✅ Audit trail: {audit_file}")
        
        print("\n🎉 Vehicle system test completed successfully!")
        print("✅ All components working correctly")
        
    else:
        print("❌ Failed to generate DCs")

if __name__ == "__main__":
    test_vehicle_system() 