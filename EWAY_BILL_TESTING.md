# E-Way Bill API Testing Guide

This guide explains how to test the e-way bill API integration before implementing the full system.

## Prerequisites

1. **Test Credentials**: You need test credentials from a GST Suvidha Provider (GSP) or the government e-way bill portal.
2. **Python Environment**: Make sure all required packages are installed.

## Setup Instructions

1. **Configure Credentials**:
   - Copy `credentials_template.json` to `credentials.json`
   - Fill in your test credentials in the `eway_test` section
   ```json
   {
       "eway_test": {
           "username": "YOUR_TEST_USERNAME",
           "password": "YOUR_TEST_PASSWORD",
           "client_id": "YOUR_TEST_CLIENT_ID",
           "client_secret": "YOUR_TEST_CLIENT_SECRET",
           "gstin": "YOUR_TEST_GSTIN"
       },
       "api_environment": "test"
   }
   ```

2. **Run the Test Script**:
   ```bash
   python test_eway_api.py
   ```

## Test Stages

The test script will check:

1. **Authentication**: Verifies if you can successfully authenticate with the e-way bill API.
2. **Data Generation**: Tests if your code can generate valid e-way bill JSON data.
3. **Data Validation**: Checks if the generated data passes all validation rules.
4. **Integration Module**: Tests if the integration module correctly prepares vehicle DC data for e-way bill generation.

## Getting Test Credentials

To obtain test credentials:

1. Register on the e-way bill portal (https://ewaybillgst.gov.in)
2. Request test/sandbox access
3. Contact your GSP provider for API access credentials

## Common Issues

- **Authentication Failures**: Verify your credentials are correct and not expired.
- **Validation Errors**: Check that your data meets all the format requirements.
- **API Connectivity**: Ensure your network allows connections to the API endpoints.

## Next Steps

Once the tests pass successfully:

1. **Enable API Submission**: Uncomment the API submission line in the test script to actually submit a test e-way bill.
2. **Verify Response**: Check if you receive a valid e-way bill number in the response.
3. **Proceed to UI Integration**: Begin integrating with your Streamlit UI for the full workflow.

## Support Resources

- [Official E-way Bill API Documentation](https://docs.ewaybillgst.gov.in/html/APIIntegrationSpecification.pdf)
- [GST Developer Portal](https://developer.gst.gov.in)
- [E-way Bill Portal Help](https://ewaybillgst.gov.in/help) 