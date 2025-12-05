# Google Drive Quota Issue - Fix Guide

## 🚨 Problem

Your Google Sheets sequences aren't saving because:

```
APIError: [403]: The user's Drive storage quota has been exceeded.
```

**The Google Drive account associated with your service account is FULL!**

---

## ✅ Solution 1: Free Up Drive Space (Recommended)

### Steps:
1. **Login to Google Drive** with the account: `hyd-ewaybill@hyd-eway.iam.gserviceaccount.com`
   - If it's a service account, you may not have direct access
   - Login with the owner account that created the service account

2. **Go to Google Drive**: https://drive.google.com/

3. **Delete unnecessary files**:
   - Sort by size (largest first)
   - Delete old/unused files
   - Check "My Drive" and "Shared with me"

4. **Empty Trash**:
   - Click **Trash** in left sidebar
   - Click **Empty trash** at top
   - This permanently deletes files and frees space

5. **Check storage**:
   - Go to https://drive.google.com/settings/storage
   - Verify you have free space

6. **Restart Streamlit app** - sequences will now save!

---

## ✅ Solution 2: Use Existing Spreadsheet

If you can't free up space, manually create a spreadsheet and point the app to it:

### Steps:

1. **Create a spreadsheet** (in an account with free space):
   - Go to https://sheets.google.com/
   - Create new spreadsheet
   - Name it: **DC_Sequences_Database**
   - Add headers in row 1:
     ```
     A1: Sequence Name
     B1: Current Value
     C1: Last Updated
     D1: Total Increments
     ```

2. **Share with service account**:
   - Click **Share** button
   - Add email: `hyd-ewaybill@hyd-eway.iam.gserviceaccount.com`
   - Give **Editor** permissions
   - Click **Done**

3. **Get spreadsheet ID**:
   - Look at URL: `https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit`
   - Copy the `{SPREADSHEET_ID}` part

4. **Add to Streamlit Cloud Secrets**:
   ```toml
   GOOGLE_SHEETS_SPREADSHEET_ID = "your_spreadsheet_id_here"
   ```

5. **Restart Streamlit app** - it will now use your specified spreadsheet!

---

## 📊 Verify It's Working

After applying either solution, check Streamlit logs for:

```
✅ Using Google Sheets sequence generator
✅ Found existing spreadsheet: DC_Sequences_Database
✅ Google Sheets connection test successful: akdcah_seq = 300
```

When you generate a DC, you should see:
```
🔄 Inserting new row in Google Sheets: A2:D2 = [['akdchydnch_seq', 301, '2025-12-05...', 1]]
✅ Google Sheets insert result: {...}
✅ Incremented akdchydnch_seq: 300 → 301
```

And most importantly - **the sequence will persist in Google Sheets!** 🎉

---

## 🔍 Current Status

Your credentials are configured correctly:
- ✅ JSON parsing works
- ✅ Google API authentication works
- ✅ gspread client authorized
- ❌ Drive storage full (need to fix this)

Once you free up space or use an existing spreadsheet, everything will work!

