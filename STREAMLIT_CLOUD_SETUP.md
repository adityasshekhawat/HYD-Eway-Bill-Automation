# 🚀 Streamlit Cloud Deployment Guide

## Quick Setup Checklist

- [ ] Google Sheets API credentials
- [ ] Streamlit Cloud account connected
- [ ] Repository connected
- [ ] Secrets configured
- [ ] App deployed

---

## Step 1: Create Google Sheets Service Account (5 min)

### 1.1 Create Google Cloud Project

1. Go to: https://console.cloud.google.com/
2. Click **"New Project"**
3. Name: `DC-Sequence-Manager`
4. Click **"Create"**

### 1.2 Enable APIs

1. In your project, go to **"APIs & Services" → "Library"**
2. Search and enable:
   - ✅ **Google Sheets API**
   - ✅ **Google Drive API**

### 1.3 Create Service Account

1. Go to **"APIs & Services" → "Credentials"**
2. Click **"Create Credentials" → "Service Account"**
3. Fill in:
   - **Name**: `dc-sequence-service`
   - Click **"Create and Continue"**
   - **Skip** optional steps → Click **"Done"**

### 1.4 Generate JSON Key

1. Click on the service account you just created
2. Go to **"Keys"** tab
3. Click **"Add Key" → "Create new key"**
4. Choose **JSON** format
5. Click **"Create"**
6. **Save the downloaded JSON file** ⬇️

### 1.5 Copy Service Account Email

Open the JSON file and copy the `client_email` value:
```
dc-sequence-service@your-project.iam.gserviceaccount.com
```

You'll need this later to share the spreadsheet!

---

## Step 2: Deploy to Streamlit Cloud

### 2.1 Connect GitHub

1. Go to: https://share.streamlit.io/
2. Click **"New app"**
3. Connect your GitHub account: **adityasshekhawat**
4. Select repository: **HYD-Eway-Bill-Automation**
5. Main file path: `src/web/streamlit_app.py`

### 2.2 Configure Secrets

Click **"Advanced settings"** → **"Secrets"**

Paste this (replace with your actual JSON content):

```toml
# Google Sheets API Credentials
GOOGLE_SHEETS_CREDENTIALS = '''
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\nYour-Key-Here\n-----END PRIVATE KEY-----\n",
  "client_email": "dc-sequence-service@your-project.iam.gserviceaccount.com",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your-cert-url"
}
'''
```

**⚠️ Important:**
- Copy the ENTIRE content from your downloaded JSON file
- Keep it within the triple quotes `'''`
- Make sure the private key has `\n` for newlines

### 2.3 Deploy

Click **"Deploy"** and wait ~2 minutes ⏱️

---

## Step 3: Share Spreadsheet with Service Account

### 3.1 Run App Once

After deployment, run your app once. It will automatically create a spreadsheet called:
**"DC_Sequences_Database"**

### 3.2 Find the Spreadsheet

1. Go to: https://drive.google.com
2. Search for: `DC_Sequences_Database`
3. Open the spreadsheet

### 3.3 Share It

1. Click **"Share"** button
2. Paste the service account email:
   ```
   dc-sequence-service@your-project.iam.gserviceaccount.com
   ```
3. Give it **"Editor"** permission
4. Click **"Send"**

✅ Done! Your sequences will now persist in Google Sheets!

---

## Step 4: Verify Setup

### Check Streamlit Logs

Look for these messages in your app logs:

```
✅ Google Sheets sequence generator initialized successfully
✅ Google Sheets connection test successful: akdcah_seq = 300
```

### Check Google Sheets

Open the spreadsheet and you should see:

| Sequence Name | Current Value | Last Updated | Total Increments |
|--------------|---------------|--------------|------------------|
| akdchydnch_seq | 300 | 2025-12-04... | 0 |

---

## 🐛 Troubleshooting

### Error: "Credentials not found"

**Problem:** Secrets not configured correctly

**Solution:**
1. Check Streamlit Cloud → App Settings → Secrets
2. Make sure the format matches exactly (triple quotes)
3. Verify no extra spaces or line breaks

### Error: "SpreadsheetNotFound"

**Problem:** Spreadsheet not shared with service account

**Solution:**
1. Find the spreadsheet in Google Drive
2. Share it with the service account email
3. Give Editor permission

### Error: "Permission denied"

**Problem:** Service account doesn't have access

**Solution:**
1. Check the email is correct
2. Make sure you gave "Editor" not just "Viewer"
3. Try re-sharing

### Sequences resetting

**Problem:** Google Sheets not connected

**Solution:**
1. Check logs for "Using local sequence generator"
2. This means Google Sheets failed
3. Review credentials setup

---

## 📊 Expected Behavior

### Fallback Chain

Your app tries in order:
1. **Google Sheets** (primary) ← Set this up!
2. Supabase (fallback)
3. Local JSON (last resort, resets on restart)

### On Streamlit Cloud

- ✅ Google Sheets: Works perfectly!
- ❌ Local JSON: Resets on every restart (ephemeral)

That's why Google Sheets is essential for cloud deployment!

---

## 🎯 Quick Start Commands

### For Local Development

Create `.streamlit/secrets.toml`:

```toml
GOOGLE_SHEETS_CREDENTIALS = '''
{paste JSON here}
'''
```

### Test Locally

```bash
cd "/Users/jumbotail/Desktop/Automation Eway Hyd"
.venv/bin/streamlit run src/web/streamlit_app.py
```

Look for:
```
✅ Google Sheets sequence generator initialized successfully
```

---

## 🔒 Security Notes

✅ **Safe:**
- Credentials in Streamlit secrets (encrypted)
- Not in GitHub repository
- Service account has limited scope

✅ **Best Practices:**
- Never commit credentials to Git
- Only share spreadsheet with service account
- Use Editor permission (not Owner)

---

## 📚 Additional Resources

- **Detailed Guide:** `GOOGLE_SHEETS_SETUP.md`
- **Quick Start:** `GOOGLE_SHEETS_QUICK_START.md`
- **System Overview:** `SEQUENCE_SYSTEM_OVERVIEW.md`

---

## ✅ Success Criteria

You'll know it's working when:

1. ✅ Streamlit app loads without errors
2. ✅ Logs show "Google Sheets initialized successfully"
3. ✅ DC numbers are generated with hub codes (AKDCHYDNCH00000001)
4. ✅ Spreadsheet updates in real-time
5. ✅ Sequences persist across app restarts

---

**Ready to deploy! 🚀**

**Next:** Follow the steps above to set up Google Sheets API and deploy to Streamlit Cloud.


