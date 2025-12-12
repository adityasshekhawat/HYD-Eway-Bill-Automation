# 🚨 URGENT: Security Setup Guide

## Current Situation
Your repository is **PUBLIC** and contains **SENSITIVE DATA** that is visible to everyone on the internet:
- ✅ Company GST numbers
- ✅ Business addresses  
- ✅ FSSAI numbers
- ✅ Customer/supplier information

## 🔥 Immediate Actions Required

### Step 1: Stop Tracking Sensitive Files (5 minutes)

```bash
cd "/Users/jumbotail/Desktop/Automation Eway Hyd"

# Remove sensitive files from git tracking
git rm --cached data/final_address.csv
git rm --cached data/final_address_updated.csv
git rm --cached data/HubAddresses.csv
git rm --cached data/Org_Names.csv
git rm --cached data/TaxMaster*.csv

# Commit the removal
git commit -m "Security: Remove sensitive data files from git tracking"

# Push changes
git push origin main
```

**Note**: This removes files from future commits but they're still in git history.

### Step 2: Configure Streamlit Secrets (10 minutes)

1. **Go to Streamlit Cloud**:
   - Visit: https://share.streamlit.io/
   - Open your app dashboard
   - Click on "⚙️ Settings" → "Secrets"

2. **Copy your CSV content**:
   ```bash
   # Read your current file
   cat data/final_address_updated.csv
   ```

3. **Paste in Streamlit Secrets** in this format:
   ```toml
   [secrets]
   final_address_csv = """
   Slno,State,Entity name,GST No,FC Data,FC Name,...
   1,Telangana,AMOLAKCHAND...
   2,Telangana,BODEGA...
   ...paste all your rows...
   """
   ```

4. **Click "Save"**

### Step 3: Update Code to Use Secrets (15 minutes)

Update these files to use the secure data loader:

**In `src/core/hub_metadata_service.py`**:
```python
# Add at the top
from src.core.secure_data_loader import get_secure_data_loader

# In _load_hub_data method, replace:
# hub_df = pd.read_csv('data/final_address_updated.csv')

# With:
loader = get_secure_data_loader()
hub_df = loader.load_final_address_csv()
```

**In `src/core/config_loader.py`**:
```python
# Same changes
from src.core.secure_data_loader import get_secure_data_loader

# In _load_final_address method:
loader = get_secure_data_loader()
self.final_address = loader.load_final_address_csv()
```

### Step 4: Test Locally (5 minutes)

```bash
# Create .streamlit/secrets.toml locally (for testing)
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit secrets.toml and add your data
nano .streamlit/secrets.toml

# Test your app
streamlit run src/web/streamlit_app.py
```

### Step 5: Deploy and Verify (5 minutes)

1. Commit your code changes
2. Push to GitHub
3. Streamlit Cloud will auto-deploy
4. **Verify**: Check that data loads correctly in production
5. **Verify**: Check GitHub - sensitive files should NOT be visible

## 🔒 Alternative: Quick Encryption Solution

If Streamlit Secrets is too complex, here's a faster encryption approach:

### Encrypt Your Files

```python
# Create encrypt_data.py
from cryptography.fernet import Fernet
import sys

# Generate key (save this in Streamlit Secrets!)
key = Fernet.generate_key()
print(f"ENCRYPTION_KEY={key.decode()}")

# Encrypt file
cipher = Fernet(key)
with open('data/final_address_updated.csv', 'rb') as f:
    encrypted = cipher.encrypt(f.read())
    
with open('data/final_address_updated.csv.encrypted', 'wb') as f:
    f.write(encrypted)

print("✅ File encrypted!")
```

### Decrypt at Runtime

```python
# In your code
from cryptography.fernet import Fernet
import streamlit as st

key = st.secrets["ENCRYPTION_KEY"]
cipher = Fernet(key.encode())

with open('data/final_address_updated.csv.encrypted', 'rb') as f:
    decrypted = cipher.decrypt(f.read())
    
df = pd.read_csv(StringIO(decrypted.decode()))
```

Then:
1. Commit only `.encrypted` files
2. Store encryption key in Streamlit Secrets
3. Decrypt at runtime

## ⚠️ Clean Git History (Advanced)

**WARNING**: This rewrites git history and requires all users to re-clone!

```bash
# Install BFG Repo-Cleaner
# Mac: brew install bfg
# Or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Clone a mirror
git clone --mirror https://github.com/adityasshekhawat/HYD-Eway-Bill-Automation.git

# Remove sensitive files from ALL commits
bfg --delete-files final_address.csv HYD-Eway-Bill-Automation.git
bfg --delete-files final_address_updated.csv HYD-Eway-Bill-Automation.git

# Clean up
cd HYD-Eway-Bill-Automation.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (⚠️ DESTRUCTIVE!)
git push --force
```

## 📋 Priority Actions

- [ ] **HIGH**: Stop tracking sensitive files (Step 1)
- [ ] **HIGH**: Configure Streamlit Secrets (Step 2)
- [ ] **MEDIUM**: Update code to use secure loader (Step 3)
- [ ] **MEDIUM**: Test locally (Step 4)
- [ ] **MEDIUM**: Deploy and verify (Step 5)
- [ ] **LOW**: Clean git history (only if highly sensitive)

## 🆘 Need Help?

Check `SECURITY_README.md` for detailed explanations.

## ⏱️ Time Required

- **Quick Fix** (Steps 1-2): ~15 minutes
- **Complete Fix** (Steps 1-5): ~40 minutes
- **With Git History Cleanup**: ~1 hour

## 📞 Questions?

Open an issue or contact your tech lead immediately if you need help securing this data.
