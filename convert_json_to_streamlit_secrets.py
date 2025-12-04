#!/usr/bin/env python3
"""
Convert Google Sheets JSON credentials to Streamlit secrets format
Usage: python convert_json_to_streamlit_secrets.py path/to/credentials.json
"""

import json
import sys

def convert_json_to_streamlit_secrets(json_file_path):
    """Convert JSON credentials to Streamlit secrets TOML format"""
    
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            creds = json.load(f)
        
        # Convert to single-line JSON string
        creds_str = json.dumps(creds)
        
        # Create the TOML format
        toml_output = f'GOOGLE_SHEETS_CREDENTIALS = \'{creds_str}\''
        
        print("=" * 80)
        print("✅ CONVERSION SUCCESSFUL!")
        print("=" * 80)
        print("\n📋 Copy everything below this line and paste into Streamlit secrets:\n")
        print("-" * 80)
        print(toml_output)
        print("-" * 80)
        print("\n✅ Instructions:")
        print("1. Copy the line above (starting with GOOGLE_SHEETS_CREDENTIALS)")
        print("2. Go to Streamlit Cloud → Your App → Settings → Secrets")
        print("3. Paste it there")
        print("4. Click 'Save'")
        print("\n🎉 Done! Your credentials will work perfectly!")
        
        # Also save to a file
        output_file = 'streamlit_secrets_output.txt'
        with open(output_file, 'w') as f:
            f.write(toml_output)
        
        print(f"\n💾 Also saved to: {output_file}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File not found: {json_file_path}")
        print("\n💡 Usage: python convert_json_to_streamlit_secrets.py path/to/credentials.json")
        return False
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON format in {json_file_path}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Please provide the path to your JSON credentials file")
        print("\n💡 Usage:")
        print("  python convert_json_to_streamlit_secrets.py credentials.json")
        print("\nOr if your file is in a different location:")
        print("  python convert_json_to_streamlit_secrets.py /path/to/your/credentials.json")
        sys.exit(1)
    
    json_file = sys.argv[1]
    convert_json_to_streamlit_secrets(json_file)

