# Auto E-Way Bill Generation - Implementation Requirements

## 1. Additional Data Sources Needed

### A. Hub Pincode Mapping
Create `data/HubPincodes.csv`:
```csv
Location Name,Pincode
BLR_KSL,560001
BLR_KML,560002
BLR_HNU,560003
HOSUR_HUB,635109
```

### B. Transport Details
Create `data/TransportMaster.csv`:
```csv
Route,TransporterId,TransporterName,Distance,VehicleType
BLR_KSL-HOSUR_HUB,29TRANSPORT123,ABC Transport,40,R
```

### C. Enhanced Hub Constants
Update HUB_CONSTANTS in dc_template_generator.py:
```python
HUB_CONSTANTS = {
    'SOURCINGBEE': {
        'company_name': 'SourcingBee Private Limited',
        'sender_gstin': '29AAHCB1357R1Z1',
        'pincode': '562123',
        'state_code': '29',
        'address_line1': 'Survey.87/1,87/2,88/1,88/2,88/3,89/1,122',
        'address_line2': 'FC-Vikrant, Byranhalli, Village Kasaba',
        'place': 'Bengaluru'
    }
}
```

## 2. New Modules to Create

### A. eway_bill_generator.py
```python
class EWayBillGenerator:
    def __init__(self, environment='sandbox'):
        self.api_base = self.get_api_endpoint(environment)
        self.access_token = None
    
    def authenticate(self, username, password, gstin):
        # OAuth authentication with GSP
        pass
    
    def generate_eway_bill(self, dc_data):
        payload = self.build_payload(dc_data)
        return self.call_api("GENEWAYBILL", payload)
    
    def build_payload(self, dc_data):
        # Maps DC data to e-way bill JSON structure
        return {
            "supplyType": "O",
            "subSupplyType": "8",  # Stock Transfer
            "docType": "CHL",     # Delivery Challan
            "docNo": dc_data['serial_number'],
            "docDate": dc_data['date'].strftime('%d/%m/%Y'),
            "fromGstin": dc_data['sender_gstin'],
            "toGstin": dc_data['receiver_gstin'],
            "fromTrdName": dc_data['sender_name'],
            "toTrdName": dc_data['receiver_name'],
            "fromAddr1": dc_data['sender_address_line1'],
            "fromAddr2": dc_data['sender_address_line2'],
            "fromPlace": dc_data['sender_place'],
            "fromPincode": dc_data['sender_pincode'],
            "fromStateCode": dc_data['sender_state_code'],
            "toAddr1": dc_data['receiver_address_line1'],
            "toAddr2": dc_data['receiver_address_line2'],
            "toPlace": dc_data['receiver_place'],
            "toPincode": dc_data['receiver_pincode'],
            "toStateCode": dc_data['receiver_state_code'],
            "transactionType": 4,  # Stock Transfer
            "totalValue": dc_data['total_taxable_value'],
            "cgstValue": dc_data['total_cgst'],
            "sgstValue": dc_data['total_sgst'],
            "igstValue": 0,  # For intrastate, IGST = 0
            "cessValue": dc_data['total_cess'],
            "totInvValue": dc_data['grand_total'],
            "transporterId": dc_data.get('transporter_id', ''),
            "transporterName": dc_data.get('transporter_name', ''),
            "transMode": "1",  # By Road
            "transDistance": dc_data.get('distance', 0),
            "vehicleNo": dc_data.get('vehicle_no', ''),
            "vehicleType": "R",  # Regular
            "itemList": self.build_item_list(dc_data['products'])
        }
    
    def build_item_list(self, products):
        items = []
        for product in products:
            items.append({
                "productName": product['Description'][:30],  # Max 30 chars
                "productDesc": product['Description'][:100], # Max 100 chars
                "hsnCode": product['HSN'],
                "quantity": float(product['Quantity']),
                "qtyUnit": "NOS",  # Default unit
                "cgstRate": float(product['GST Rate']) / 2,
                "sgstRate": float(product['GST Rate']) / 2,
                "igstRate": 0,
                "cessRate": 0,
                "taxableAmount": float(product['Value'])
            })
        return items
```

### B. distance_calculator.py
```python
import requests
import math

class DistanceCalculator:
    def __init__(self, google_maps_api_key=None):
        self.api_key = google_maps_api_key
    
    def calculate_distance(self, from_pincode, to_pincode):
        if self.api_key:
            return self.get_google_maps_distance(from_pincode, to_pincode)
        else:
            return self.estimate_distance(from_pincode, to_pincode)
    
    def estimate_distance(self, from_pin, to_pin):
        # Fallback: Simple distance estimation
        # This is a basic implementation
        pin_distance_map = {
            ('560001', '635109'): 40,  # BLR to Hosur
            ('560002', '635109'): 45,
            # Add more mappings
        }
        return pin_distance_map.get((from_pin, to_pin), 50)  # Default 50km
```

### C. eway_integration.py
```python
from eway_bill_generator import EWayBillGenerator
from distance_calculator import DistanceCalculator

class EWayIntegration:
    def __init__(self, config):
        self.eway_generator = EWayBillGenerator(config['environment'])
        self.distance_calc = DistanceCalculator(config.get('google_api_key'))
        self.config = config
    
    def process_dc_for_eway(self, dc_data):
        # Enrich DC data with e-way bill requirements
        enriched_data = self.enrich_dc_data(dc_data)
        
        # Generate e-way bill
        eway_response = self.eway_generator.generate_eway_bill(enriched_data)
        
        return {
            'success': eway_response.get('success', False),
            'eway_bill_no': eway_response.get('ewayBillNo'),
            'valid_until': eway_response.get('validUpto'),
            'errors': eway_response.get('errors', [])
        }
    
    def enrich_dc_data(self, dc_data):
        # Add missing fields for e-way bill
        dc_data['distance'] = self.calculate_distance(dc_data)
        dc_data['transporter_id'] = self.get_transporter_id(dc_data)
        dc_data['vehicle_no'] = self.get_vehicle_number(dc_data)
        return dc_data
```

## 3. Integration Points

### A. Modify existing DC generator
Update `dc_template_generator.py`:
```python
from eway_integration import EWayIntegration

def create_dc_excel(dc_data_item, state, generate_eway=True):
    # Existing DC creation logic...
    
    if generate_eway:
        eway_integration = EWayIntegration(EWAY_CONFIG)
        eway_result = eway_integration.process_dc_for_eway(dc_data_item)
        
        if eway_result['success']:
            # Add e-way bill number to DC
            dc_data_item['eway_bill_no'] = eway_result['eway_bill_no']
            # Update DC template to include e-way bill number
            ws['J3'] = f"E-Way Bill No: {eway_result['eway_bill_no']}"
        else:
            print(f"❌ E-Way Bill generation failed: {eway_result['errors']}")
```

### B. Configuration
Create `eway_config.py`:
```python
EWAY_CONFIG = {
    'environment': 'sandbox',  # or 'production'
    'gsp_credentials': {
        'username': 'your_username',
        'password': 'your_password',
        'gstin': '29AAHCB1357R1Z1'
    },
    'api_endpoints': {
        'sandbox': 'https://api.mastergst.com/ewaybillapi/v1.03',
        'production': 'https://api.mastergst.com/ewaybillapi/v1.03'
    },
    'google_api_key': 'optional_for_distance_calculation'
}
```

## 4. Implementation Timeline

### Phase 1 (Week 1): Data Enhancement
- [ ] Create pincode mapping for all hubs
- [ ] Add transport details to data sources
- [ ] Update hub constants with detailed address info

### Phase 2 (Week 2): Core API Integration
- [ ] Implement EWayBillGenerator class
- [ ] Build payload mapping logic
- [ ] Add authentication handling

### Phase 3 (Week 3): Integration & Testing
- [ ] Integrate with existing DC generator
- [ ] Add distance calculation
- [ ] Implement error handling

### Phase 4 (Week 4): Production Ready
- [ ] Add logging and monitoring
- [ ] Implement retry mechanisms
- [ ] Add configuration management

## 5. Technical Considerations

### A. Authentication
- Register with GSP (GST Suvidha Provider)
- Obtain API credentials
- Implement OAuth token management

### B. Rate Limiting
- E-way bill API has rate limits
- Implement queuing for bulk generation
- Add retry logic for failed attempts

### C. Error Handling
- Validation errors from API
- Network connectivity issues
- Data mapping errors

### D. Compliance
- Ensure data accuracy
- Maintain audit logs
- Handle cancellations and updates

## 6. Cost Estimation

### A. Development Time
- **Total: 3-4 weeks** for a complete solution
- **Core functionality: 2 weeks** for basic integration

### B. External Dependencies
- GSP subscription: ₹5,000-15,000/month
- Google Maps API (optional): Pay per use
- SSL certificates for production

### C. Maintenance
- API version updates
- Regulation changes
- Error monitoring and fixes

## 7. Success Metrics

### A. Automation Rate
- Target: 95%+ of DCs automatically get e-way bills
- Fallback: Manual generation for edge cases

### B. Accuracy
- Zero compliance violations
- Minimal API rejections (<2%)

### C. Performance
- E-way bill generation within 30 seconds
- Batch processing capability

## 8. Risk Mitigation

### A. API Failures
- Fallback to manual generation
- Queue failed requests for retry
- Alert mechanisms

### B. Data Quality
- Validation before API calls
- Master data verification
- Regular data audits

### C. Compliance Changes
- Monitor GST rule updates
- Version control for API changes
- Regular testing with tax consultants 