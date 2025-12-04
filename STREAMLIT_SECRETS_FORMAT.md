# 🔧 How to Format Google Sheets Credentials for Streamlit Secrets

## ⚠️ Common Error

```
Invalid format: please enter valid TOML.
```

This happens when the JSON isn't properly formatted for TOML.

---

## ✅ Correct Format

### Option 1: Single Line (Recommended)

**Step 1:** Open your JSON file and copy ALL content

**Step 2:** Use this EXACT format in Streamlit secrets:

```toml
GOOGLE_SHEETS_CREDENTIALS = '{"type":"service_account","project_id":"your-project","private_key_id":"abc123","private_key":"-----BEGIN PRIVATE KEY-----\\nYourKeyHere\\n-----END PRIVATE KEY-----\\n","client_email":"service@project.iam.gserviceaccount.com","client_id":"12345","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_x509_cert_url":"https://www.googleapis.com/robot/v1/metadata/x509/service%40project.iam.gserviceaccount.com","universe_domain":"googleapis.com"}'
```

**Key Points:**
- ✅ Use SINGLE quotes `'` (not triple quotes for single line)
- ✅ All on ONE line
- ✅ Replace `\n` in private_key with `\\n` (double backslash)
- ✅ Remove all actual newlines from the JSON

---

### Option 2: Multi-line (Also Works)

```toml
GOOGLE_SHEETS_CREDENTIALS = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYour\\nPrivate\\nKey\\nHere\\n-----END PRIVATE KEY-----\\n",
  "client_email": "your-service-account@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account%40your-project.iam.gserviceaccount.com"
}
"""
```

**Key Points:**
- ✅ Use triple DOUBLE quotes `"""`
- ✅ Keep JSON formatting
- ✅ Replace actual newlines in private_key with `\\n`

---

## 🛠️ Step-by-Step Conversion

### Method 1: Online Converter (Easiest)

1. Go to: https://www.convertsimple.com/convert-json-to-toml/
2. Paste your entire JSON file content
3. Copy the TOML output
4. Add this line at the top:
   ```toml
   GOOGLE_SHEETS_CREDENTIALS = """
   ```
5. Add this at the bottom:
   ```toml
   """
   ```
6. Paste into Streamlit secrets

---

### Method 2: Manual Conversion

**Your JSON file looks like this:**
```json
{
  "type": "service_account",
  "project_id": "dc-sequence-manager-12345",
  "private_key": "-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...
...more lines...
-----END PRIVATE KEY-----
",
  "client_email": "dc-sequence-service@dc-sequence-manager-12345.iam.gserviceaccount.com",
  ...
}
```

**Convert to Streamlit format:**

1. **Find the private_key section** - it has multiple lines
2. **Replace the newlines:**
   ```
   -----BEGIN PRIVATE KEY-----
   MIIEvQIBADANBg...
   ...
   -----END PRIVATE KEY-----
   ```
   
   Becomes:
   ```
   -----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBg...\\n...\\n-----END PRIVATE KEY-----\\n
   ```

3. **Put it all in Streamlit format:**
   ```toml
   GOOGLE_SHEETS_CREDENTIALS = """
   {
     "type": "service_account",
     "project_id": "dc-sequence-manager-12345",
     "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBg...\\n-----END PRIVATE KEY-----\\n",
     "client_email": "dc-sequence-service@dc-sequence-manager-12345.iam.gserviceaccount.com",
     ...rest of JSON...
   }
   """
   ```

---

## 🎯 Quick Fix Template

Copy this and replace the values:

```toml
GOOGLE_SHEETS_CREDENTIALS = """
{
  "type": "service_account",
  "project_id": "YOUR_PROJECT_ID_HERE",
  "private_key_id": "YOUR_PRIVATE_KEY_ID_HERE",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nYOUR_PRIVATE_KEY_CONTENT_HERE_ALL_ON_ONE_LINE_WITH_BACKSLASH_N\\n-----END PRIVATE KEY-----\\n",
  "client_email": "YOUR_SERVICE_ACCOUNT_EMAIL_HERE",
  "client_id": "YOUR_CLIENT_ID_HERE",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "YOUR_CERT_URL_HERE"
}
"""
```

---

## 🔍 Common Mistakes

### ❌ Wrong:
```toml
# Using triple single quotes
GOOGLE_SHEETS_CREDENTIALS = '''
{
  "private_key": "-----BEGIN PRIVATE KEY-----
ACTUAL NEWLINES HERE  # ← This breaks it!
-----END PRIVATE KEY-----"
}
'''
```

### ✅ Correct:
```toml
# Using triple double quotes and escaped newlines
GOOGLE_SHEETS_CREDENTIALS = """
{
  "private_key": "-----BEGIN PRIVATE KEY-----\\nONE_LINE_HERE\\n-----END PRIVATE KEY-----\\n"
}
"""
```

---

## 🧪 Test Your Format

After pasting in Streamlit secrets:

1. Click **"Save"**
2. If you see ✅ - Success!
3. If you see ❌ "Invalid format" - Check:
   - Are you using `"""` (triple double quotes)?
   - Did you escape newlines in private_key with `\\n`?
   - Is the closing `"""` on its own line?

---

## 💡 Pro Tip: Use Python to Convert

If you have the JSON file locally:

```python
import json

# Read your JSON file
with open('path/to/your-credentials.json', 'r') as f:
    creds = json.load(f)

# Convert to single-line string
creds_str = json.dumps(creds)

# Print in TOML format
print('GOOGLE_SHEETS_CREDENTIALS = \'%s\'' % creds_str)
```

Copy the output directly into Streamlit secrets!

---

## 📋 Checklist

Before saving in Streamlit:

- [ ] Started with `GOOGLE_SHEETS_CREDENTIALS = """`
- [ ] JSON is properly formatted
- [ ] All newlines in `private_key` are `\\n`
- [ ] No actual line breaks in `private_key`
- [ ] Ended with `"""` on new line
- [ ] Clicked "Save"
- [ ] No error message

---

## 🎉 Success Looks Like

In Streamlit Cloud → Settings → Secrets:

```toml
GOOGLE_SHEETS_CREDENTIALS = """
{
  "type": "service_account",
  ...
}
"""
```

Click **"Save"** → ✅ **"Secrets updated successfully"**

---

**Need help? Share the error message and I'll help debug!**

