# GitHub Sequence Storage Setup Guide

## 🎯 **Why GitHub for Sequences?**

GitHub is now the **RECOMMENDED** backend for DC sequence storage because:

- ✅ **FREE** - No quota limits
- ✅ **RELIABLE** - 99.9% uptime
- ✅ **VERSION CONTROLLED** - Full audit trail of every sequence change
- ✅ **WORKS ON STREAMLIT CLOUD** - Perfect for deployment
- ✅ **NO EXTERNAL DEPENDENCIES** - Uses existing GitHub repo
- ✅ **AUTOMATIC BACKUPS** - Git history is the backup

---

## 📋 **Prerequisites**

1. A GitHub account
2. Your GitHub repository (e.g., `adityasshekhawat/HYD-Eway-Bill-Automation`)
3. 5 minutes to complete setup

---

## 🔧 **Setup Steps**

### **Step 1: Create GitHub Personal Access Token**

1. **Go to GitHub Settings**:
   - Visit: https://github.com/settings/tokens
   - Or: Click your profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click **"Generate new token (classic)"**
   - Name: `DC-Sequence-Storage`
   - Expiration: **No expiration** (or 1 year)
   
3. **Select Permissions** (IMPORTANT):
   - ✅ **repo** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   
4. **Generate and Copy**:
   - Click **"Generate token"**
   - ⚠️ **COPY THE TOKEN NOW** - You won't be able to see it again!
   - It looks like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### **Step 2: Add Secrets to Streamlit Cloud**

1. **Go to your Streamlit Cloud app**:
   - Visit: https://share.streamlit.io/
   - Select your app

2. **Open Settings**:
   - Click ⚙️ **Settings** (gear icon)
   - Click **Secrets**

3. **Add GitHub Configuration**:
   
   ```toml
   # GitHub Sequence Storage Configuration
   GITHUB_TOKEN = "ghp_your_token_here"
   GITHUB_REPO = "username/repository-name"
   GITHUB_BRANCH = "main"
   ```
   
   **Replace with your values**:
   - `GITHUB_TOKEN`: Your token from Step 1
   - `GITHUB_REPO`: Format `username/repo-name` (e.g., `adityasshekhawat/HYD-Eway-Bill-Automation`)
   - `GITHUB_BRANCH`: Usually `main` (or `master` for older repos)

4. **Click "Save"**

---

### **Step 3: Restart Streamlit App**

1. After saving secrets, **restart your app**:
   - Click the menu (⋮) → **Reboot app**

2. **Check logs** - you should see:
   ```
   🔄 Attempting to initialize GitHub sequence generator...
   ✅ Using GitHub token from Streamlit secrets
   ✅ Using GitHub repo from Streamlit secrets: username/repo-name
   📝 Creating initial sequence file in GitHub...
   ✅ Sequence file initialized in GitHub
   ✅ GitHub sequence generator initialized successfully
   ✅ GitHub connection test successful: akdcah_seq = 300
   ```

---

## ✅ **Verification**

### **Check 1: Sequence File Created**

Visit your GitHub repository:
```
https://github.com/username/repo-name/blob/main/sequence_data.json
```

You should see a file like:
```json
{
  "sequences": {
    "akdcah_seq": 300,
    "akdcsg_seq": 300,
    "akdchydnch_seq": 300,
    "akdchydbal_seq": 300,
    ...
  },
  "last_updated": "2025-12-05T20:30:00.000000",
  "version": "1.0"
}
```

### **Check 2: Generate a DC**

1. Generate a DC in your Streamlit app
2. Check the logs for:
   ```
   ✅ Incremented akdchydnch_seq: 300 → 301
   ✅ Successfully committed to GitHub: Increment akdchydnch_seq: 300 → 301
   ```

3. **Refresh your GitHub repo** - you'll see a new commit:
   ```
   Increment akdchydnch_seq: 300 → 301
   ```

### **Check 3: Verify Sequence Persists**

1. Generate a DC: Get sequence 301
2. **Restart your Streamlit app**
3. Generate another DC: Get sequence 302 ✅
   - If it was 301 again, sequences aren't persisting (check logs)

---

## 🎨 **Benefits You Get**

### **1. Full Audit Trail**

Every sequence increment is a Git commit! View history:
```
https://github.com/username/repo-name/commits/main/sequence_data.json
```

Example commits:
```
Increment akdchydnch_seq: 300 → 301
Increment akdchydnch_seq: 301 → 302
Increment akdchydbal_seq: 300 → 301
```

### **2. Easy Manual Correction**

Need to fix a sequence? Just edit the file on GitHub:
1. Go to `sequence_data.json`
2. Click ✏️ Edit
3. Change the value
4. Commit

### **3. Rollback Capability**

Made a mistake? Roll back to any previous state:
1. View commit history
2. Find the correct version
3. Copy the old content
4. Create a new commit with correct values

### **4. No Quota Issues**

- GitHub has generous API limits (5000 requests/hour)
- At 1 DC/minute, that's 83 hours of continuous generation
- Way more than you'll ever need!

---

## 🔧 **Local Development Setup** (Optional)

For testing locally, create a `.env` file:

```bash
# .env (DO NOT commit this file!)
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=username/repository-name
GITHUB_BRANCH=main
```

Then load it in Python:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🐛 **Troubleshooting**

### **Error: "GitHub token not found"**

**Fix**: Check Streamlit secrets:
- Verify `GITHUB_TOKEN` is set correctly
- Token should start with `ghp_`
- No extra spaces or quotes

### **Error: "403 Forbidden"**

**Fix**: Check token permissions:
- Token needs **full `repo` access**
- Regenerate token with correct permissions

### **Error: "404 Not Found"**

**Fix**: Check repository name:
- Format must be `username/repo-name`
- Repository must exist
- Token must have access to the repository

### **Sequences not persisting**

**Fix**: Check logs for:
```
✅ Successfully committed to GitHub
```

If you see:
```
❌ Failed to commit to GitHub: 409
```
This is a conflict - the system will auto-retry.

---

## 📊 **How It Works**

```
1. App starts → Initialize GitHubSequenceGenerator
2. Read sequence_data.json from GitHub repo
3. User generates DC → Increment sequence in memory
4. Commit updated file back to GitHub
5. Automatic retry on conflicts (race conditions)
```

**Thread Safety**:
- GitHub API is atomic (no two commits can have same SHA)
- If conflict occurs, system retries with fresh SHA
- Up to 5 retries with exponential backoff

---

## 🎉 **You're Done!**

Your sequences are now stored in GitHub with:
- ✅ Free unlimited storage
- ✅ Full version control
- ✅ Automatic audit trail
- ✅ No quota limits
- ✅ Perfect for Streamlit Cloud

**Generate a DC and watch the magic happen!** 🚀

