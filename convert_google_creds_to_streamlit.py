#!/usr/bin/env python3
"""
Convert Google Sheets credentials.json to Streamlit secrets format
"""

import json
import sys

def convert_to_streamlit_secrets(json_file_path):
    """Convert credentials.json to Streamlit secrets.toml format"""
    
    try:
        with open(json_file_path, 'r') as f:
            creds = json.load(f)
        
        print("=" * 70)
        print("STREAMLIT SECRETS FORMAT (Copy this to Streamlit Cloud Secrets)")
        print("=" * 70)
        print()
        print("[gcp_service_account]")
        
        # Handle each field
        for key, value in creds.items():
            if isinstance(value, str):
                # Escape quotes and handle multiline strings (like private_key)
                if '\n' in value:
                    # For multiline strings, use triple quotes
                    escaped_value = value.replace('\\n', '\\n')  # Keep as literal \n
                    print(f'{key} = """{escaped_value}"""')
                else:
                    escaped_value = value.replace('"', '\\"')
                    print(f'{key} = "{escaped_value}"')
            else:
                print(f'{key} = "{value}"')
        
        print()
        print("=" * 70)
        print("INSTRUCTIONS:")
        print("1. Go to Streamlit Cloud → Your App → Settings → Secrets")
        print("2. Copy the [gcp_service_account] section above")
        print("3. Paste it into the Secrets text box")
        print("4. Click 'Save'")
        print("5. Restart your Streamlit app")
        print("=" * 70)
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_file_path}")
        print("\nPlease provide the path to your credentials.json file")
        print("Usage: python convert_google_creds_to_streamlit.py <path_to_credentials.json>")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {json_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python convert_google_creds_to_streamlit.py <path_to_credentials.json>")
        print("\nExample:")
        print("  python convert_google_creds_to_streamlit.py credentials.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    convert_to_streamlit_secrets(json_file)

