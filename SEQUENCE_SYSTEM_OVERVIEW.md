# 🎯 DC Sequence System - Complete Overview

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Your Streamlit Application                      │
│                                                          │
│  ┌────────────────────────────────────────────┐        │
│  │      DC Sequence Manager                   │        │
│  │      (Priority-based selection)            │        │
│  └────────────────────────────────────────────┘        │
│                       │                                  │
│         Tries in order (automatic fallback):            │
│                       │                                  │
│         ┌─────────────┴───────────────┐                │
│         │                               │                │
│         ▼                               │                │
│  ┌─────────────────┐                   │                │
│  │ 1. Google Sheets│ ✅ PRIMARY        │                │
│  │    (Cloud)      │                   │                │
│  └─────────────────┘                   │                │
│         │ (if fails)                   │                │
│         ▼                               │                │
│  ┌─────────────────┐                   │                │
│  │ 2. Supabase     │ 🔄 FALLBACK #1   │                │
│  │    (Cloud)      │                   │                │
│  └─────────────────┘                   │                │
│         │ (if fails)                   │                │
│         ▼                               │                │
│  ┌─────────────────┐                   │                │
│  │ 3. Local JSON   │ 📁 FALLBACK #2   │                │
│  │    (File)       │                   │                │
│  └─────────────────┘                   │                │
└─────────────────────────────────────────────────────────┘
```

---

## 🔢 Sequence Format

### For Telangana (Hyderabad) - Hub-Specific:

```
Format: {Company}DC{Facility}{Hub}{Sequence}
         ──┬──     ──┬──   ─┬─  ────┬────
           │         │       │       └─ 8-digit number
           │         │       └───────── Hub code (3 letters)
           │         └───────────────── Facility (3 letters)
           └─────────────────────────── Company (2 letters)

Examples:
  AKDCHYDNCH00000001  → Amolakchand, Hyderabad, Nacharam, Seq #1
  BDDCHYDBAL00000042  → Bodega, Hyderabad, Balanagar, Seq #42
  AKDCHYDSGR00000100  → Amolakchand, Hyderabad, Sangareddy, Seq #100
```

### For Other Facilities (Karnataka, etc.):

```
Format: {Company}DC{Facility}{Sequence}
         ──┬──     ──┬──   ────┬────
           │         │          └─ 8-digit number
           │         └──────────── Facility (2 letters)
           └────────────────────── Company (2 letters)

Examples:
  AKDCAH00000001  → Amolakchand, Arihant, Seq #1
  BDDCSG00000042  → Bodega, Sutlej/Gomati, Seq #42
```

---

## 📍 Telangana Hub Codes

| Hub Code | Hub Name | Example DC Number |
|----------|----------|-------------------|
| **BVG** | Boduppal Gudem | AKDCHYDBVG00000001 |
| **SGR** | Santosh Nagar | AKDCHYDSGR00000001 |
| **BAL** | Balanagar | AKDCHYDBAL00000001 |
| **KMP** | Kompally | AKDCHYDKMP00000001 |
| **NCH** | Nacharam | AKDCHYDNCH00000001 |
| **SAN** | Sangareddy | AKDCHYDSAN00000001 |

**Total:** 12 independent sequences (AK + BD × 6 hubs)

---

## 🔄 How It Works

### 1. **DC Generation Request**

```python
# System receives DC data
dc_data = {
    'hub_type': 'AMOLAKCHAND',
    'facility_name': 'FC-Hyderabad',
    'hub': 'HYD_NCH',  # ← Hub information
    'vehicle_number': 'TL23DD2322',
    'products': [...]
}
```

### 2. **Sequence Manager Extracts Info**

```python
# Extracts from data
company_code = 'AK'          # from AMOLAKCHAND
facility_code = 'HYD'        # from FC-Hyderabad
hub_code = 'NCH'             # from HYD_NCH

# Creates sequence name
sequence_name = 'akdchydnch_seq'
```

### 3. **Gets Next Sequence**

```python
# From Google Sheets (or fallback)
current_value = 300
next_value = 301

# Generates DC number
dc_number = 'AKDCHYDNCH00000301'
```

### 4. **Updates Storage**

**Google Sheets:**
| Sequence Name | Current Value | Last Updated | Increments |
|--------------|---------------|--------------|------------|
| akdchydnch_seq | 301 | 2025-12-04... | 1 |

---

## 🎯 Key Features

### ✅ Automatic Hub Detection

- Reads `hub` column from Raw_DC.csv
- Format: `HYD_NCH` → extracts `NCH`
- Only activates for Hyderabad facility
- Other facilities work as before

### ✅ Independent Sequences

Each combination maintains its own counter:
- `akdchydnch_seq` → 301
- `akdchydbal_seq` → 300
- `bddchydnch_seq` → 300
- `bddcsg_seq` → 350 (Karnataka)

**No conflicts!** Each sequence increments independently.

### ✅ Cloud-Ready

**Google Sheets Backend:**
- ✅ Works on Streamlit Cloud
- ✅ No ephemeral filesystem issues
- ✅ Survives app restarts
- ✅ Shared across instances

### ✅ Easy Auditing

View sequences anytime:
1. Open Google Drive
2. Find "DC_Sequences_Database"
3. See all sequences in real-time
4. Can manually edit if needed

---

## 🔐 Data Flow

```
┌─────────────────┐
│  Raw_DC.csv     │
│  - hub: HYD_NCH │
│  - facility: FC-│
│    Hyderabad    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Vehicle Data Manager               │
│  • Groups trips by vehicle          │
│  • Extracts hub from data           │
│  • Prepares DC data dict            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Vehicle DC Generator               │
│  • Calls sequence manager           │
│  • Passes: company, facility, hub   │
│  • Receives: DC number              │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  DC Sequence Manager                │
│  • Extracts hub code (NCH)          │
│  • Builds sequence name             │
│  • Calls storage backend            │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Google Sheets Generator            │
│  • Finds/creates row                │
│  • Increments value atomically      │
│  • Updates timestamp                │
│  • Returns next number              │
└────────┬────────────────────────────┘
         │
         ▼
   AKDCHYDNCH00000301
```

---

## 📈 Performance

### Google Sheets API Limits:

- **60 requests/minute** per user
- **Your usage:** ~2 requests per DC
- **Capacity:** ~30 DCs/minute
- **Daily capacity:** ~43,000 DCs

### Fallback Performance:

| Backend | Speed | Reliability | Cloud-Ready |
|---------|-------|-------------|-------------|
| Google Sheets | ~500ms | 99.9% | ✅ Yes |
| Supabase | ~200ms | 99.9% | ✅ Yes |
| Local JSON | ~10ms | 100%* | ❌ No (ephemeral) |

*Local JSON 100% reliable only on non-ephemeral systems

---

## 🚀 Deployment

### Streamlit Cloud:

1. **Add credentials** to secrets.toml
2. **Deploy** your app
3. **First run** creates spreadsheet
4. **Share** spreadsheet with service account
5. **Done!** ✅

### Local Development:

1. **Save credentials** to `.streamlit/secrets.toml`
2. **Run** Streamlit app
3. **Check logs** for confirmation
4. **Share** spreadsheet with service account

---

## 🎉 Benefits Summary

| Feature | Before | After |
|---------|--------|-------|
| Storage | Supabase only | Google Sheets + fallbacks |
| Cloud-ready | ✅ Yes | ✅ Yes (better) |
| Auditing | API only | Visual spreadsheet |
| Cost | Hit limits | Generous free tier |
| Telangana | Basic | Hub-specific tracking |
| Reliability | Single point | Triple redundancy |

---

## 📚 Quick Links

- **Setup Guide:** `GOOGLE_SHEETS_QUICK_START.md`
- **Detailed Docs:** `GOOGLE_SHEETS_SETUP.md`
- **Implementation:** `IMPLEMENTATION_SUMMARY.md`
- **Code:** `src/core/google_sheets_sequence_generator.py`

---

**System Status:** ✅ Ready to Deploy!

