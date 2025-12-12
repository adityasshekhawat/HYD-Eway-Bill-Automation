# Security & Data Protection Guide

## ⚠️ IMPORTANT: Public Repository Data Security

This repository is **PUBLIC** on GitHub, which means anyone can view the code and any committed files. We must protect sensitive business data.

## 🔒 Protected Data Types

The following types of data should **NEVER** be committed to the public repository:
- Company GST numbers (GSTIN)
- Business addresses
- FSSAI numbers
- Customer/supplier names and details
- Tax information
- Financial data
- Any PII (Personally Identifiable Information)

## 📁 Sensitive Files (Already in .gitignore)

These files contain sensitive data and are excluded from git:
- `data/final_address.csv`
- `data/final_address_updated.csv`
- `data/HubAddresses.csv`
- `data/Org_Names.csv`
- `data/TaxMaster*.csv`
- `data/*_consolidated.csv`
- `data/realtime_dc__data*.csv`

## 🚀 Setup for Streamlit Cloud

### Method 1: Using Streamlit Secrets (Recommended)

1. **In Streamlit Cloud Dashboard:**
   - Go to your app settings
   - Navigate to "Secrets" section
   - Add your sensitive data as TOML format

2. **Access secrets in code:**
   ```python
   import streamlit as st
   
   # Access secrets
   gstin_data = st.secrets["gstin_mapping"]
   addresses = st.secrets["hub_addresses"]
   ```

### Method 2: Using External Database/Storage

1. **Options:**
   - Supabase (Free tier available)
   - MongoDB Atlas (Free tier available)
   - AWS S3 with signed URLs
   - Google Cloud Storage

2. **Store connection credentials in Streamlit Secrets**

### Method 3: Encrypted Data Files

1. **Encrypt CSV files before committing**
2. **Store decryption key in Streamlit Secrets**
3. **Decrypt at runtime**

## 🛠️ Implementation Steps

### Step 1: Remove Sensitive Data from Git History

**⚠️ WARNING**: Sensitive data is already in git history! Run these commands:

```bash
# Remove files from git tracking (keeps local files)
git rm --cached data/final_address.csv
git rm --cached data/final_address_updated.csv
git rm --cached data/HubAddresses.csv
git rm --cached data/Org_Names.csv

# Commit the removal
git commit -m "Remove sensitive data files from tracking"

# Push changes
git push origin main
```

**Note**: This doesn't remove from git history. For complete removal, you need to use `git filter-branch` or BFG Repo-Cleaner, but this will rewrite history.

### Step 2: Create Template Files

Create template/sample files with dummy data for structure reference:

```bash
# Example: data/final_address_template.csv
Slno,State,Entity name,GST No,FC Data,FC Name,...
1,Sample State,SAMPLE COMPANY NAME,00XXXXX0000X0XX,...
```

### Step 3: Update Code to Load from Secrets

See `src/core/secure_data_loader.py` (to be created) for implementation.

## 📋 Checklist Before Going Live

- [ ] Sensitive CSV files are in .gitignore
- [ ] Removed sensitive files from git tracking
- [ ] Created template files with dummy data
- [ ] Configured Streamlit Secrets with real data
- [ ] Updated code to load from secrets
- [ ] Tested locally with secrets
- [ ] Deployed and tested on Streamlit Cloud
- [ ] Verified no sensitive data is visible in public repo

## 🆘 If Data is Already Exposed

If sensitive data is already in git history:

1. **Immediate Actions:**
   - Rotate/change all exposed GST numbers (if possible)
   - Notify affected parties
   - Document the exposure

2. **Clean Git History:**
   ```bash
   # Use BFG Repo-Cleaner (recommended)
   # Download from: https://rtyley.github.io/bfg-repo-cleaner/
   
   # Clone a fresh copy
   git clone --mirror git@github.com:username/repo.git
   
   # Remove sensitive files from history
   java -jar bfg.jar --delete-files final_address.csv
   
   # Clean up
   cd repo.git
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # Force push (⚠️ This rewrites history!)
   git push --force
   ```

## 📞 Support

For questions about security setup, contact your tech lead or DevOps team.

## 🔗 Useful Links

- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)
- [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)
- [Git Filter-Branch](https://git-scm.com/docs/git-filter-branch)
