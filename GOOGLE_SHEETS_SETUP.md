# 🔐 Google Sheets Sequence Generator Setup Guide

This guide will help you set up Google Sheets API for sequence management. **Works perfectly with Streamlit Cloud!**

---

## 📋 Prerequisites

- Google Account
- 10 minutes of your time

---

## 🚀 Quick Setup (Step-by-Step)

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Name it: `DC-Sequence-Manager`
4. Click **"Create"**

### Step 2: Enable Google Sheets API

1. In your project, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Sheets API"**
3. Click on it and press **"Enable"**
4. Also enable **"Google Drive API"** (same way)

### Step 3: Create Service Account

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"Service Account"**
3. Fill in details:
   - **Service account name**: `dc-sequence-service`
   - **Service account ID**: (auto-generated)
   - **Description**: "Service account for DC sequence management"
4. Click **"Create and Continue"**
5. **Skip** the optional steps (Role & Access)
6. Click **"Done"**

### Step 4: Generate Service Account Key

1. Click on the service account you just created
2. Go to **"Keys"** tab
3. Click **"Add Key"** → **"Create new key"**
4. Choose **JSON** format
5. Click **"Create"**
6. **Save the downloaded JSON file** - you'll need it!

### Step 5: Share Spreadsheet with Service Account

**IMPORTANT:** The service account needs permission to access the spreadsheet.

1. Open the downloaded JSON file
2. Copy the `client_email` value (looks like: `dc-sequence-service@project-name.iam.gserviceaccount.com`)
3. The system will auto-create a spreadsheet called **"DC_Sequences_Database"**
4. After first run, find it in your Google Drive
5. **Share** the spreadsheet with the service account email (give it **Editor** access)

---

## 🔧 Configure Your Application

### Option A: For Streamlit Cloud (Recommended)

1. Go to your Streamlit Cloud app settings
2. Click **"Secrets"** (🔐 icon)
3. Add this to your `secrets.toml`:

```toml
# Google Sheets API Credentials
GOOGLE_SHEETS_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYour-Private-Key-Here\\n-----END PRIVATE KEY-----\\n",
  "client_email": "dc-sequence-service@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your-cert-url"
}
'''
```

**Note:** Replace the content with your actual JSON file content. Make sure to:
- Keep it as a single line string (use `'''` triple quotes)
- Escape newlines in the private key with `\\n`

### Option B: For Local Development

**Method 1: Using secrets.toml (Recommended)**

Create `.streamlit/secrets.toml` in your project:

```toml
GOOGLE_SHEETS_CREDENTIALS = '''
{paste your JSON content here}
'''
```

**Method 2: Using JSON file**

1. Rename your downloaded JSON file to `google_sheets_credentials.json`
2. Place it in the project root directory
3. Add to `.gitignore`:
   ```
   google_sheets_credentials.json
   ```

**Method 3: Using Environment Variable**

```bash
export GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'
```

---

## ✅ Test Your Setup

Run this test script:

```python
from src.core.google_sheets_sequence_generator import GoogleSheetsSequenceGenerator

# Initialize
generator = GoogleSheetsSequenceGenerator()

# Test get current value
current = generator.get_current_sequence_value('test_seq')
print(f"Current value: {current}")

# Test increment
next_val = generator.get_next_sequence('test_seq')
print(f"Next value: {next_val}")

# View all sequences
all_seqs = generator.get_all_sequences()
print(f"All sequences: {all_seqs}")
```

If successful, you'll see:
- ✅ Messages indicating successful connection
- A new spreadsheet in your Google Drive: **"DC_Sequences_Database"**

---

## 📊 View Your Sequences

1. Go to [Google Drive](https://drive.google.com)
2. Look for **"DC_Sequences_Database"**
3. Open it to see all your DC sequences in real-time!

**Spreadsheet columns:**
- **Sequence Name**: `akdchydnch_seq`, `bddchydbal_seq`, etc.
- **Current Value**: Current sequence number
- **Last Updated**: Timestamp of last increment
- **Total Increments**: How many times it's been used

---

## 🔒 Security Best Practices

### ✅ DO:
- ✅ Keep credentials in Streamlit secrets or environment variables
- ✅ Add `google_sheets_credentials.json` to `.gitignore`
- ✅ Share spreadsheet only with your service account
- ✅ Use Editor permission (not Owner)

### ❌ DON'T:
- ❌ Commit credentials to Git
- ❌ Share credentials publicly
- ❌ Use personal Google account credentials

---

## 🐛 Troubleshooting

### Error: "Credentials not found"
**Solution:** Check that your credentials are properly set in secrets.toml or environment variable

### Error: "SpreadsheetNotFound"
**Solution:** 
1. Let the system create the spreadsheet automatically on first run
2. Find "DC_Sequences_Database" in your Google Drive
3. Share it with your service account email (from the JSON file)

### Error: "Insufficient permissions"
**Solution:** Make sure you shared the spreadsheet with **Editor** access, not just Viewer

### Error: "API not enabled"
**Solution:** 
1. Go to Google Cloud Console
2. Enable both "Google Sheets API" and "Google Drive API"

### Sequences resetting to 300
**Solution:** This is normal for new sequences. They start at 300 by default.

---

## 💡 Features

✅ **Cloud-based** - Works on Streamlit Cloud (no ephemeral filesystem issues)  
✅ **Easy to audit** - View/edit sequences directly in Google Sheets  
✅ **Thread-safe** - Automatic retry logic handles concurrent access  
✅ **Free** - Within Google's generous free tier limits  
✅ **Reliable** - Battle-tested Google infrastructure  

---

## 📈 Free Tier Limits

Google Sheets API free tier (more than enough for your use case):
- **60 requests per minute** per user
- **100 requests per 100 seconds** per user
- **Unlimited spreadsheets**

For your DC generation:
- Each DC generation = ~2 API calls
- You can generate **~30 DCs per minute**
- **~43,000 DCs per day** within free limits

---

## 🆘 Need Help?

If you encounter issues:

1. Check the [Google Sheets API docs](https://developers.google.com/sheets/api)
2. Verify your service account has Editor access to the spreadsheet
3. Check Streamlit Cloud logs for error messages
4. Ensure both Google Sheets API and Google Drive API are enabled

---

## 🎉 Next Steps

Once setup is complete:

1. Your application will automatically use Google Sheets for sequences
2. Fallback chain: Google Sheets → Supabase → Local JSON
3. Deploy to Streamlit Cloud with confidence!
4. Monitor sequences in real-time via Google Sheets

**Happy sequencing! 🚀**

