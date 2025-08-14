#!/usr/bin/env python3
"""
Setup script for the multi-court booking system.
This script helps configure environment variables and test Google Sheets access.
"""

import os
import json
import pytz
from datetime import datetime

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds in London UK timezone."""
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return f"[{london_time.strftime('%H:%M:%S.%f')[:-4]}]"

def setup_environment():
    """Interactive setup for environment variables."""
    
    print(f"{get_timestamp()} 🎾 Multi-Court Booking System Setup")
    print(f"{get_timestamp()} ======================================")
    print()
    
    # Check if we're in a GitHub Actions environment
    if os.environ.get('GITHUB_ACTIONS'):
        print(f"{get_timestamp()} ✅ Running in GitHub Actions environment")
        print(f"{get_timestamp()} Environment variables should be set via GitHub Secrets")
        return
    
    print(f"{get_timestamp()} 📋 Environment Setup Guide")
    print(f"{get_timestamp()} ----------------------------")
    print()
    
    # Google Sheets Configuration
    print(f"{get_timestamp()} 🔧 STEP 1: Google Sheets Configuration")
    print(f"{get_timestamp()} You need to set these environment variables:")
    print()
    print(f"{get_timestamp()} GSHEET_CAM_ID")
    print(f"{get_timestamp()}   - This is your Google Sheets file ID")
    print(f"{get_timestamp()}   - Get it from the URL: https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")
    print(f"{get_timestamp()}   - Example: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms")
    print()
    
    print(f"{get_timestamp()} GOOGLE_SERVICE_ACCOUNT_JSON")
    print(f"{get_timestamp()}   - This is your service account JSON credentials")
    print(f"{get_timestamp()}   - Copy the entire JSON content from your service account key file")
    print(f"{get_timestamp()}   - Make sure the service account has Editor access to your Google Sheets")
    print()
    
    # Email Account Configuration
    print(f"{get_timestamp()} 🔧 STEP 2: Email Account Configuration")
    print(f"{get_timestamp()} Set these environment variables for each account:")
    print()
    print(f"{get_timestamp()} MOTHER_CAM_EMAIL_ADDRESS=1140749429@qq.com")
    print(f"{get_timestamp()} MOTHER_CAM_PASSWORD=mother_password")
    print(f"{get_timestamp()} FATHER_CAM_EMAIL_ADDRESS=huay43105@gmail.com")
    print(f"{get_timestamp()} FATHER_CAM_PASSWORD=father_password")
    print(f"{get_timestamp()} BRUCE_CAM_EMAIL_ADDRESS=brcwood48@gmail.com")
    print(f"{get_timestamp()} BRUCE_CAM_PASSWORD=bruce_password")
    print()
    
    # Google Sheets Structure
    print(f"{get_timestamp()} 🔧 STEP 3: Google Sheets Structure")
    print(f"{get_timestamp()} Your Google Sheets file needs 3 sheets with these names:")
    print()
    print(f"{get_timestamp()} Sheet 1: 'Account & Court Configuration'")
    print(f"{get_timestamp()} Headers: Account | Email | Password | Court Number | Court URL")
    print(f"{get_timestamp()} Data:")
    print(f"{get_timestamp()}   Mother | 1140749429@qq.com | [from secrets] | Court 1 | https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/")
    print(f"{get_timestamp()}   Father | huay43105@gmail.com | [from secrets] | Court 2 | https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/")
    print(f"{get_timestamp()}   Bruce | brcwood48@gmail.com | [from secrets] | Court 3 | https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/")
    print()
    
    print(f"{get_timestamp()} Sheet 2: 'Booking Schedule'")
    print(f"{get_timestamp()} Headers: Day | Time | Notes")
    print(f"{get_timestamp()} Data:")
    print(f"{get_timestamp()}   Tuesday | 1800 | Feb-Aug only")
    print(f"{get_timestamp()}   Tuesday | 1900 | Summer only (Jun-Aug)")
    print(f"{get_timestamp()}   Thursday | 1800 | Feb-Aug only")
    print(f"{get_timestamp()}   Thursday | 1900 | Summer only (Jun-Aug)")
    print(f"{get_timestamp()}   Saturday | 1400 | All year")
    print(f"{get_timestamp()}   Saturday | 1500 | All year")
    print(f"{get_timestamp()}   Sunday | 1400 | All year")
    print(f"{get_timestamp()}   Sunday | 1500 | All year")
    print()
    
    print(f"{get_timestamp()} Sheet 3: 'Booking Log'")
    print(f"{get_timestamp()} Headers: Timestamp | Email | Court | Date | Time | Status | Error Details")
    print(f"{get_timestamp()} (This sheet will be populated automatically by the system)")
    print()
    
    # Service Account Access
    print(f"{get_timestamp()} 🔧 STEP 4: Service Account Access")
    print(f"{get_timestamp()} To give your service account write access:")
    print()
    print(f"{get_timestamp()} 1. Open your Google Sheets file")
    print(f"{get_timestamp()} 2. Click 'Share' (top right)")
    print(f"{get_timestamp()} 3. Add your service account email (from the JSON file)")
    print(f"{get_timestamp()} 4. Give it 'Editor' permissions")
    print(f"{get_timestamp()} 5. Click 'Send'")
    print()
    
    # Test current environment
    print(f"{get_timestamp()} 🔧 STEP 5: Test Current Environment")
    print(f"{get_timestamp()} Current environment variables:")
    print()
    
    required_vars = [
        'GSHEET_CAM_ID',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'MOTHER_CAM_EMAIL_ADDRESS',
        'MOTHER_CAM_PASSWORD',
        'FATHER_CAM_EMAIL_ADDRESS',
        'FATHER_CAM_PASSWORD',
        'BRUCE_CAM_EMAIL_ADDRESS',
        'BRUCE_CAM_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'JSON' in var:
                masked_value = value[:10] + "..." if len(value) > 10 else "***"
                print(f"{get_timestamp()} ✅ {var}: {masked_value}")
            else:
                print(f"{get_timestamp()} ✅ {var}: {value}")
        else:
            print(f"{get_timestamp()} ❌ {var}: NOT SET")
            missing_vars.append(var)
    
    print()
    
    if missing_vars:
        print(f"{get_timestamp()} ⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print(f"{get_timestamp()} Please set these variables before running the booking system")
    else:
        print(f"{get_timestamp()} ✅ All required environment variables are set!")
        print(f"{get_timestamp()} You can now test the system with: python test_sheets_setup.py")
    
    print()
    print(f"{get_timestamp()} 📋 Next Steps:")
    print(f"{get_timestamp()} 1. Set the missing environment variables")
    print(f"{get_timestamp()} 2. Ensure your Google Sheets has the correct structure")
    print(f"{get_timestamp()} 3. Give your service account Editor access to the sheet")
    print(f"{get_timestamp()} 4. Run: python test_sheets_setup.py")
    print(f"{get_timestamp()} 5. If all tests pass, you're ready to use the booking system!")

def test_service_account_access():
    """Test if the service account can access Google Sheets."""
    
    print(f"{get_timestamp()} 🔧 Testing Service Account Access")
    print(f"{get_timestamp()} --------------------------------")
    
    # Check if we have the required variables
    sheet_id = os.environ.get('GSHEET_CAM_ID')
    service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not sheet_id or not service_account_json:
        print(f"{get_timestamp()} ❌ Missing GSHEET_CAM_ID or GOOGLE_SERVICE_ACCOUNT_JSON")
        print(f"{get_timestamp()} Please set these environment variables first")
        return False
    
    try:
        # Parse the service account JSON to get the email
        credentials_info = json.loads(service_account_json)
        service_account_email = credentials_info.get('client_email')
        
        if service_account_email:
            print(f"{get_timestamp()} ✅ Service account email: {service_account_email}")
            print(f"{get_timestamp()} 📋 Make sure this email has Editor access to your Google Sheets")
        else:
            print(f"{get_timestamp()} ❌ Could not find client_email in service account JSON")
            return False
        
        # Try to connect to Google Sheets
        from sheets_manager import test_sheets_connection
        success = test_sheets_connection(sheet_id, service_account_json)
        
        if success:
            print(f"{get_timestamp()} ✅ Service account can access Google Sheets successfully!")
            return True
        else:
            print(f"{get_timestamp()} ❌ Service account cannot access Google Sheets")
            print(f"{get_timestamp()} Please check:")
            print(f"{get_timestamp()} 1. The sheet ID is correct")
            print(f"{get_timestamp()} 2. The service account has Editor access")
            print(f"{get_timestamp()} 3. The service account JSON is valid")
            return False
            
    except json.JSONDecodeError:
        print(f"{get_timestamp()} ❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_JSON")
        return False
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error testing service account access: {e}")
        return False

def main():
    """Main setup function."""
    
    print(f"{get_timestamp()} 🎾 Multi-Court Booking System Setup")
    print(f"{get_timestamp()} ======================================")
    print()
    
    # Show setup guide
    setup_environment()
    print()
    
    # Test service account access if variables are set
    if os.environ.get('GSHEET_CAM_ID') and os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
        print(f"{get_timestamp()} 🔧 Testing Service Account Access...")
        test_service_account_access()
    else:
        print(f"{get_timestamp()} ⚠️ Skipping service account test - variables not set")
    
    print()
    print(f"{get_timestamp()} 🎉 Setup guide completed!")
    print(f"{get_timestamp()} Follow the steps above to configure your system.")

if __name__ == "__main__":
    main()
