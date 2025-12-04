# GitHub Sync Setup Guide

## Overview
This guide explains how to set up automatic GitHub sync for DC sequence state persistence when running on Streamlit Cloud.

## 🎯 What It Does
- **Local Development**: No GitHub sync (sequences stay local)
- **Cloud Deployment**: Automatically commits sequence changes back to GitHub
- **Prevents Sequence Loss**: Ensures sequences persist across cloud deployments

## 📋 Setup Steps

### 1. Create GitHub Personal Access Token
1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
2. Click **"Generate new token (classic)"**
3. **Token settings**:
   - **Name**: `E-Way Bill Sequence Sync`
   - **Expiration**: `No expiration` (recommended for production)
   - **Scopes**: Check **`repo`** (Full control of private repositories)
4. Click **"Generate token"**
5. **⚠️ IMPORTANT**: Copy the token immediately (you won't see it again)

### 2. Configure Streamlit Cloud Environment Variables
1. Go to your **Streamlit Cloud** app settings
2. Navigate to **"Secrets"** or **"Environment Variables"**
3. Add these variables:

```toml
# GitHub Configuration
GITHUB_TOKEN = "ghp_your_token_here"
GITHUB_REPO = "your-username/your-repo-name"
GITHUB_BRANCH = "main"
```

**Example:**
```toml
GITHUB_TOKEN = "ghp_abcd1234567890abcdef"
GITHUB_REPO = "jumbotail/e-way-bill-system"
GITHUB_BRANCH = "main"
```

### 3. Deploy to Streamlit Cloud
Once configured, your app will automatically:
- ✅ Detect it's running in the cloud
- ✅ Sync sequence changes to GitHub
- ✅ Preserve sequences across deployments

## 🔍 Verification

### Expected Behavior
**Local Development:**
```
🏠 Local environment - GitHub sync disabled
```

**Cloud Deployment:**
```
✅ GitHub sync enabled for cloud environment
🌐 Cloud environment - syncing sequence state to GitHub...
✅ Successfully synced sequence state to GitHub
   Commit: Auto-sync: Update DC sequences [AKDCAH:5, BDDCAH:3, SBDCAH:2]
```

### Check GitHub Commits
After generating DCs on Streamlit Cloud, you should see automatic commits like:
```
Auto-sync: Update DC sequences [AKDCAH:5, BDDCAH:3, SBDCAH:2]
```

## 🚨 Security Notes

### Token Security
- **Never commit tokens to your repository**
- **Use environment variables only**
- **Rotate tokens periodically**
- **Limit token scope to specific repositories**

### Repository Access
- The token only needs access to your specific repository
- The sync only updates `dc_sequence_state_v2.json`
- No other files are modified

## 🛠️ Troubleshooting

### Common Issues

**1. "GitHub sync disabled" in cloud**
- Check if `GITHUB_TOKEN` is set in Streamlit Cloud secrets
- Verify the token hasn't expired
- Ensure the token has `repo` scope

**2. "Could not get file SHA" error**
- Verify `GITHUB_REPO` format: `username/repo-name`
- Check if the repository exists and is accessible
- Ensure the token has access to the repository

**3. "Failed to sync to GitHub" error**
- Check if the branch exists (default: `main`)
- Verify the file `dc_sequence_state_v2.json` exists in the repository
- Check token permissions

### Debug Mode
To debug sync issues, check the Streamlit Cloud logs for:
- `✅ GitHub sync enabled for cloud environment`
- `🌐 Cloud environment - syncing sequence state to GitHub...`
- `✅ Successfully synced sequence state to GitHub`

## 🎯 Benefits

### Before GitHub Sync
```
Deploy to cloud → Generate DCs → Sequences lost on restart → Duplicate DCs ❌
```

### After GitHub Sync
```
Deploy to cloud → Generate DCs → Auto-sync to GitHub → Sequences preserved ✅
```

## 📞 Support
If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify environment variables are set correctly
3. Test token permissions on GitHub
4. Ensure the repository and file paths are correct 