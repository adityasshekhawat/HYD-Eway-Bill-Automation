# Field Mapping: final_address.csv → E-Way Bill Template

This document provides a comprehensive mapping between the columns in `final_address.csv` and the fields in the E-Way Bill template generated for ClearTax upload.

---

## CSV Structure: `final_address.csv`

| Column # | Column Name | Description | Example |
|----------|-------------|-------------|---------|
| 1 | Slno | Serial number | 1, 2, 3... |
| 2 | State | State name/abbreviation | Bihar, UP, MH |
| 3 | Entity name | Full legal company name | AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED |
| 4 | GST No | State-specific GSTIN | 10AAPCA1708D1ZB |
| 5 | FC Data | FC indicator | FC |
| 6 | FC Name | Fulfillment Center name | FC-Patna, FC-Lucknow |
| 7 | FC Seller Address 1 | FC address line 1 | Tauzi No. - 5225/14851, Survey No -1... |
| 8 | FC Seller Address 1.1 | FC address line 2 | 96/1691, 95/1692, Mauza Lakhani Bigha... |
| 9 | Seller Pin code | FC pincode | 801105 |
| 10 | Location Status | Active/Inactive status | Active |
| 11 | HUB/FC | Type indicator | HUB |
| 12 | Hub Name | Hub code | BH_PTN_DDJ, 3P_PTN_SMP, LKO_SDG |
| 13 | Name | Hub display name/city | Didarganj, Samastipur, Lucknow |
| 14 | Fssai | FSSAI number | 1.04E+13 |
| 15 | Address | Full hub address | Full address string |
| 16 | HUB Buyers Address 1 | Hub address line 1 | Khata no.157 & 227 (part)... |
| 17 | HUB Buyers Address 1.1 | Hub address line 2 | at Adbul Rehman Pur Katra Bazar... |
| 18 | HUB Buyers Pin code | Hub pincode | 800008 |

---

## Supplier/Dispatch Details (FC Data)

These fields represent the **source/dispatch location** (Fulfillment Center).

| CSV Column | E-Way Bill Field | Code Reference | Notes |
|------------|------------------|----------------|-------|
| **Entity name** | `Supplier Name` | Line 323 | Full legal company name |
| **Entity name** | `Supplier Dispatch Name` | Line 346 | Same as Supplier Name |
| **GST No** | `Supplier GSTIN` | Line 322 | State-specific GSTIN (e.g., 09AAPCA1708D1ZU for UP) |
| **FC Seller Address 1** | `Supplier Address1` | Line 324 | FC address line 1 (truncated to 99 chars) |
| **FC Seller Address 1** | `Supplier Dispatch Address 1` | Line 347 | Same as above |
| **FC Seller Address 1.1** | `Supplier Address2` | Line 325 | FC address line 2 (truncated to 99 chars) |
| **FC Seller Address 1.1** | `Supplier Dispatch Address 2` | Line 348 | Same as above |
| **Seller Pin code** | `Supplier Pincode` | Line 327 | FC 6-digit pincode |
| **Seller Pin code** | `Supplier Dispatch PinCode` | Line 350 | Same as above |
| **State** | `Supplier State` | Line 328 | Normalized full state name |
| **State** | `Supplier Dispatch State Code` | Line 351 | Format: `{code}-{state}` (e.g., "09-Uttar Pradesh") |
| *(extracted)* | `Supplier Place` | Line 326 | City extracted from FC address |
| *(extracted)* | `Supplier Dispatch Place` | Line 349 | Same as above |

---

## Customer/Billing/Shipping Details (Hub Data)

These fields represent the **destination location** (Hub). For stock transfers, customer = same company.

| CSV Column | E-Way Bill Field | Code Reference | Notes |
|------------|------------------|----------------|-------|
| **Entity name** | `Customer Billing Name` | Line 329 | Same company (stock transfer) |
| **Entity name** | `Customer Shipping Name` | Line 339 | Same company (stock transfer) |
| **GST No** | `Customer Billing GSTIN` | Line 330 | Same GSTIN (intra-state stock transfer) |
| **HUB Buyers Address 1** | `Customer Billing Address 1` | Line 331 | Hub address line 1 |
| **HUB Buyers Address 1** | `Customer Shipping Address 1` | Line 340 | Same (truncated to 99 chars) |
| **HUB Buyers Address 1.1** | `Customer Billing Address 2` | Line 332 | Hub address line 2 |
| **HUB Buyers Address 1.1** | `Customer Shipping Address 2` | Line 341 | Same (truncated to 99 chars) |
| **HUB Buyers Pin code** | `Customer Billing Pincode` | Line 335 | Hub 6-digit pincode |
| **HUB Buyers Pin code** | `Customer Shipping PinCode` | Line 343 | Same as above |
| **State** | `Customer Billing State` | Line 334 | Normalized full state name |
| **State** | `Customer Shipping State Code` | Line 344 | Format: `{code}-{state}` (e.g., "09-Uttar Pradesh") |
| **Name** | `Customer Billing City` | Line 333 | Hub city/location name |
| **Name** | `Customer Shipping City` | Line 342 | Same as above |

---

## State Code Mapping

The system normalizes state abbreviations to full names and assigns correct state codes.

| CSV State Value | Normalized Name | State Code | E-Way Bill Format |
|-----------------|-----------------|------------|-------------------|
| UP | Uttar Pradesh | 09 | `09-Uttar Pradesh` |
| MH | Maharashtra | 27 | `27-Maharashtra` |
| KA / Karnataka | Karnataka | 29 | `29-Karnataka` |
| TN | Tamil Nadu | 33 | `33-Tamil Nadu` |
| AP | Andhra Pradesh | 37 | `37-Andhra Pradesh` |
| TS / TG | Telangana | 36 | `36-Telangana` |
| Bihar | Bihar | 10 | `10-Bihar` |
| Jharkhand | Jharkhand | 20 | `20-Jharkhand` |
| GJ | Gujarat | 24 | `24-Gujarat` |
| RJ | Rajasthan | 08 | `08-Rajasthan` |
| DL | Delhi | 07 | `07-Delhi` |
| HR | Haryana | 06 | `06-Haryana` |
| PB | Punjab | 03 | `03-Punjab` |
| WB | West Bengal | 19 | `19-West Bengal` |
| OR | Odisha | 21 | `21-Odisha` |
| MP | Madhya Pradesh | 23 | `23-Madhya Pradesh` |
| CG | Chhattisgarh | 22 | `22-Chhattisgarh` |
| AS | Assam | 18 | `18-Assam` |
| GA | Goa | 30 | `30-Goa` |
| KL | Kerala | 32 | `32-Kerala` |

---

## Standard/Static Values

These values are constant for all e-way bills and not derived from CSV.

| E-Way Bill Field | Static Value | Description |
|------------------|--------------|-------------|
| `Supply Type` | Outward | Direction of supply |
| `Sub SupplyType` | Others | Sub-category |
| `Document Type` | Challan | Document type for stock transfer |
| `Sub Type Description` | Stock Transfer | Nature of transaction |
| `Transportation Mode (Road/Rail/Air/Ship)` | Road | Mode of transport |
| `Vehicle Type` | Regular | Vehicle classification |
| `Item Unit of Measurement` | UNITS | Default UOM |
| `My Branch` | *(empty)* | Not applicable |
| `Replace E-way bill` | *(empty)* | Not a replacement |
| `Is this Supply to/from SEZ unit?` | *(empty)* | Not SEZ |
| `Eway Bill Transaction Type` | *(empty)* | Default |
| `Distance Level (Km)` | *(blank)* | Left empty as requested |

---

## Product/Tax Fields

These fields come from **DC Data** and **TaxMaster.csv**, not from `final_address.csv`.

| Source | E-Way Bill Field | Description |
|--------|------------------|-------------|
| DC Data | `Document Number` | DC serial number |
| DC Data | `Document Date` | DC date (DD/MM/YYYY format) |
| DC Data | `Vehicle Number` | Vehicle registration |
| DC Data / TaxMaster | `Product Name` | Product description |
| DC Data / TaxMaster | `Item Description` | Same as Product Name |
| TaxMaster.csv | `HSN code` | HSN code for the product |
| DC Data | `Item Quantity` | Quantity of items |
| DC Data | `Taxable Value` | Value before tax |
| TaxMaster.csv | `CGST Rate` | Central GST rate (GST/2) |
| Calculated | `CGST Amount` | (Taxable Value × CGST Rate) / 100 |
| TaxMaster.csv | `SGST Rate` | State GST rate (GST/2) |
| Calculated | `SGST Amount` | (Taxable Value × SGST Rate) / 100 |
| TaxMaster.csv | `IGST Rate` | Inter-state GST (0 for intra-state) |
| Calculated | `IGST Amount` | (Taxable Value × IGST Rate) / 100 |
| TaxMaster.csv | `CESS Rate` | Compensation cess rate |
| Calculated | `CESS Amount` | (Taxable Value × CESS Rate) / 100 |
| Calculated | `Total Transaction Value` | Sum of all values + taxes |

---

## Visual Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           final_address.csv                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────┐    ┌─────────────────────────────────┐│
│  │     FC DATA (Supplier)          │    │     HUB DATA (Customer)          ││
│  ├─────────────────────────────────┤    ├─────────────────────────────────┤│
│  │ Entity name                     │    │ Entity name                      ││
│  │ GST No                          │    │ GST No (same for stock transfer) ││
│  │ FC Seller Address 1             │    │ HUB Buyers Address 1             ││
│  │ FC Seller Address 1.1           │    │ HUB Buyers Address 1.1           ││
│  │ Seller Pin code                 │    │ HUB Buyers Pin code              ││
│  │ State                           │    │ State                            ││
│  │ FC Name (internal key)          │    │ Hub Name (internal key)          ││
│  └─────────────────────────────────┘    │ Name (city)                      ││
│                                         └─────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────┘
                    │                                    │
                    ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        E-WAY BILL TEMPLATE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  SUPPLIER FIELDS                        CUSTOMER FIELDS                     │
│  ────────────────                       ───────────────                     │
│  Supplier Name                          Customer Billing Name               │
│  Supplier GSTIN                         Customer Billing GSTIN              │
│  Supplier Address1                      Customer Billing Address 1          │
│  Supplier Address2                      Customer Billing Address 2          │
│  Supplier Pincode                       Customer Billing Pincode            │
│  Supplier State                         Customer Billing State              │
│  Supplier Place                         Customer Billing City               │
│                                                                             │
│  DISPATCH FIELDS                        SHIPPING FIELDS                     │
│  ──────────────                         ───────────────                     │
│  Supplier Dispatch Name                 Customer Shipping Name              │
│  Supplier Dispatch Address 1            Customer Shipping Address 1         │
│  Supplier Dispatch Address 2            Customer Shipping Address 2         │
│  Supplier Dispatch PinCode              Customer Shipping PinCode           │
│  Supplier Dispatch State Code           Customer Shipping State Code        │
│  Supplier Dispatch Place                Customer Shipping City              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Code References

- **Address Resolution:** `src/core/address_resolver.py`
- **E-Way Template Generation:** `src/eway_bill/eway_bill_template_generator.py`
- **State Code Normalization:** `_normalize_state_name()` and `_get_state_code()` methods

---

## Important Notes

1. **State Abbreviation Handling:** The system automatically converts state abbreviations (UP, MH, etc.) to full names (Uttar Pradesh, Maharashtra, etc.) for proper display.

2. **Address Truncation:** All address fields are truncated to 99 characters maximum (E-Way bill requirement).

3. **Stock Transfer:** For stock transfers, Supplier and Customer use the same company name and GSTIN (intra-company movement).

4. **FSSAI:** The FSSAI field from CSV is currently not used in e-way bill generation (kept blank per requirement).

5. **Hub Code:** The `Hub Name` column (e.g., `3P_PTN_SMP`, `LKO_SDG`) is used as an internal key for address lookup, not displayed in the e-way bill.

---

*Last Updated: December 2025*

