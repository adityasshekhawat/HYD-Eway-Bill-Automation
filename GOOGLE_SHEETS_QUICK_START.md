# ⚡ Google Sheets API - 5 Minute Quick Start

## 🎯 What You Need

1. **Service Account JSON** from Google Cloud
2. **Add to Streamlit Secrets**
3. **Share Spreadsheet** with service account

That's it! 🎉

---

## 📝 Step-by-Step (5 Minutes)

### 1️⃣ Create Service Account (2 min)

1. Go to: https://console.cloud.google.com/
2. Create new project: `DC-Sequence-Manager`
3. Enable APIs:
   - Google Sheets API
   - Google Drive API
4. Create Service Account:
   - Name: `dc-sequence-service`
   - Skip roles
   - Download JSON key

### 2️⃣ Add to Streamlit (1 min)

**Streamlit Cloud:**

App Settings → Secrets → Add:

```toml
GOOGLE_SHEETS_CREDENTIALS = '''
{paste your entire JSON file content here}
'''
```

**Local Development:**

Create `.streamlit/secrets.toml`:

```toml
GOOGLE_SHEETS_CREDENTIALS = '''
{paste JSON here}
'''
```

### 3️⃣ Share Spreadsheet (2 min)

1. Run your app once (creates spreadsheet automatically)
2. Find "DC_Sequences_Database" in Google Drive
3. Copy service account email from JSON: `client_email`
4. Share spreadsheet → Paste email → Give **Editor** access

---

## ✅ Test It

```python
# Just run your Streamlit app
# Check the logs for:
✅ Google Sheets sequence generator initialized successfully
```

---

## 📊 View Sequences

Open [Google Drive](https://drive.google.com) → "DC_Sequences_Database"

You'll see:
| Sequence Name | Current Value | Last Updated | Total Increments |
|--------------|---------------|--------------|------------------|
| akdchydnch_seq | 301 | 2025-12-04... | 1 |
| bddchydbal_seq | 302 | 2025-12-04... | 2 |

---

## 🔄 Fallback Chain

Your app tries in order:
1. **Google Sheets** (best for cloud) ⬅ **NEW!**
2. Supabase (if Google Sheets fails)
3. Local JSON (if both fail)

---

## 🎉 Done!

Your sequences are now:
- ✅ Cloud-based (works on Streamlit Cloud)
- ✅ Visible in Google Sheets
- ✅ Free forever (within limits)
- ✅ Reliable

Need detailed setup? See: `GOOGLE_SHEETS_SETUP.md`

