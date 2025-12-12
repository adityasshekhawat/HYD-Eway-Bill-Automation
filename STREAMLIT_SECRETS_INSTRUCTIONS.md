# 🔒 Streamlit Secrets Setup Instructions

## Step-by-Step Guide to Configure Secrets

### Step 1: Open Streamlit Cloud Dashboard

1. Go to: **https://share.streamlit.io/**
2. Log in with your GitHub account
3. Find your app: **HYD-Eway-Bill-Automation**
4. Click on the app name
5. Click **⚙️ (Settings icon)** in the top right
6. Click **"Secrets"** in the left sidebar

### Step 2: Copy Your Secrets Configuration

Open the file `streamlit_secrets_data.txt` in this folder and copy its contents.

### Step 3: Create the Secrets TOML

In the Streamlit Secrets editor, paste this format:

```toml
[secrets]
final_address_csv = """
[PASTE THE ENTIRE CONTENTS OF streamlit_secrets_data.txt HERE]
"""

# Optional: Add environment flag
[environment]
IS_STREAMLIT_CLOUD = "true"
```

**Important**: 
- Keep the `"""` triple quotes at the start and end
- Paste the ENTIRE CSV including the header row
- Don't modify any commas or quotes in the CSV data

### Step 4: Save and Deploy

1. Click **"Save"** button at the bottom
2. Streamlit will automatically restart your app
3. The app will now load data from Secrets in production
4. Local development will continue using local CSV files

### Step 5: Verify

After the app restarts:
1. Open your app URL
2. Test that hub addresses load correctly
3. Check that HYD_ATP shows the Jumbotail address

---

## Alternative: Manual Format

If you prefer to format it yourself, use this structure:

```toml
[secrets]
final_address_csv = """
Slno,State,Entity name,GST No,FC Data,FC Name,FC Seller Address 1,FC Seller Address 1.1,Seller Pin code,Location Status,HUB/FC,Hub Name,Name,Fssai,Address,HUB Buyers Address 1,HUB Buyers Address 1.1,HUB Buyers Pin code
1,Bihar,AMOLAKCHAND ANKUR KOTHARI ENTERPRISES PRIVATE LIMITED,10AAPCA1708D1ZB,FC,FC-Patna,"Tauzi No. - 5225/14851, Survey No -1, Plot No. 32/1690, C/o Shree Shankar Swawlambi Cold Storage","96/1691, 95/1692, Mauza Lakhani Bigha, Pargana, Phulwari, Thana Danapur, PO Khagaul, Patna, Patna, Bihar",801105,Active,HUB,BH_PTN_DDJ, Didarganj,1.04E+13,"Khata no.157 & 227 (part) and Khasra noc.Parts of 517 & 600, at Adbul Rehman Pur Katra Bazar Next to Dina Iron Factory Thana Mal Salami Police Station Didarganj, Patna, Patna,Bihar, 800008",Khata no.157 & 227 (part) and Khasra noc.Parts of 517 & 600,"at Adbul Rehman Pur Katra Bazar Next to Dina Iron Factory Thana Mal Salami Police Station Didarganj, Patna, Patna,Bihar",800008
... [continue with all your rows] ...
"""
```

---

## Troubleshooting

### Error: "Invalid TOML"
- Check that you have triple quotes: `"""`
- Make sure there are no unescaped quotes in your data
- Verify the closing `"""` is on its own line

### Error: "Secrets not loading"
- Verify the key is exactly: `final_address_csv` (under `[secrets]`)
- Check there are no typos
- Restart the app from Streamlit Cloud dashboard

### Data not appearing in app
- Check the app logs in Streamlit Cloud
- Look for debug messages about "Loading from secrets"
- Verify your code is using `secure_data_loader.py`

---

## Need Help?

If you encounter issues:
1. Check the Streamlit Cloud logs
2. Verify the CSV format in secrets matches the original file
3. Test locally first with `.streamlit/secrets.toml`

---

## Security Notes

✅ **What's Secure Now:**
- CSV data is in Streamlit Secrets (encrypted at rest)
- Not visible in public GitHub repository
- Only accessible to your Streamlit app

⚠️ **Still in Git History:**
- Old commits still contain the data
- To completely remove, see `SECURITY_README.md` for BFG Repo-Cleaner

🔒 **Best Practice:**
- Never commit secrets.toml to git (already in .gitignore)
- Rotate sensitive credentials if they were exposed
- Use different credentials for dev vs production
