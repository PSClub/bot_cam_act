#!/usr/bin/env python3
"""
Script to create the Google Sheets template for the multi-court booking system.
This script will create a new Google Sheets document with the required structure.
"""

import os
import json
from datetime import datetime
from google.oauth2 import service_account
import gspread
from gspread.exceptions import APIError

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

def create_sheets_template(service_account_json):
    """
    Create a new Google Sheets document with the required structure.
    
    Args:
        service_account_json (str): Service account JSON credentials
        
    Returns:
        str: The ID of the created spreadsheet
    """
    try:
        print(f"{get_timestamp()} === Creating Google Sheets Template ===")
        
        # Parse service account credentials
        credentials_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        
        # Authorize and create new spreadsheet
        gc = gspread.authorize(credentials)
        
        # Create new spreadsheet
        spreadsheet_title = f"Tennis Court Booking System - {datetime.now().strftime('%Y-%m-%d')}"
        spreadsheet = gc.create(spreadsheet_title)
        
        print(f"{get_timestamp()} ✅ Created new spreadsheet: {spreadsheet_title}")
        print(f"{get_timestamp()} 📊 Spreadsheet ID: {spreadsheet.id}")
        print(f"{get_timestamp()} 🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit")
        
        # Delete the default "Sheet1"
        try:
            default_sheet = spreadsheet.worksheet("Sheet1")
            spreadsheet.del_worksheet(default_sheet)
            print(f"{get_timestamp()} ✅ Removed default Sheet1")
        except:
            pass
        
        # Create Sheet 1: Account & Court Configuration
        print(f"{get_timestamp()} --- Creating Account & Court Configuration Sheet ---")
        config_sheet = spreadsheet.add_worksheet(
            title="Account & Court Configuration",
            rows=10,
            cols=5
        )
        
        # Set up configuration headers and data
        config_headers = ["Account", "Email", "Password", "Court Number", "Court URL"]
        config_data = [
            ["Mother", "1140749429@qq.com", "[from secrets]", "Court 1", "https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/"],
            ["Father", "huay43105@gmail.com", "[from secrets]", "Court 2", "https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/"],
            ["Bruce", "brcwood48@gmail.com", "[from secrets]", "Court 3", "https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/"]
        ]
        
        # Insert headers
        config_sheet.insert_row(config_headers, 1)
        
        # Insert data
        for i, row in enumerate(config_data, 2):
            config_sheet.insert_row(row, i)
        
        # Format headers (make them bold)
        config_sheet.format('A1:E1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        print(f"{get_timestamp()} ✅ Account & Court Configuration sheet created")
        
        # Create Sheet 2: Booking Schedule
        print(f"{get_timestamp()} --- Creating Booking Schedule Sheet ---")
        schedule_sheet = spreadsheet.add_worksheet(
            title="Booking Schedule",
            rows=15,
            cols=3
        )
        
        # Set up schedule headers and data
        schedule_headers = ["Day", "Time", "Notes"]
        schedule_data = [
            ["Tuesday", "18:00", "Feb-Aug only"],
            ["Tuesday", "19:00", "Summer only (Jun-Aug)"],
            ["Thursday", "18:00", "Feb-Aug only"],
            ["Thursday", "19:00", "Summer only (Jun-Aug)"],
            ["Saturday", "14:00", "All year"],
            ["Saturday", "15:00", "All year"],
            ["Sunday", "14:00", "All year"],
            ["Sunday", "15:00", "All year"]
        ]
        
        # Insert headers
        schedule_sheet.insert_row(schedule_headers, 1)
        
        # Insert data
        for i, row in enumerate(schedule_data, 2):
            schedule_sheet.insert_row(row, i)
        
        # Format headers
        schedule_sheet.format('A1:C1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        print(f"{get_timestamp()} ✅ Booking Schedule sheet created")
        
        # Create Sheet 3: Booking Log
        print(f"{get_timestamp()} --- Creating Booking Log Sheet ---")
        log_sheet = spreadsheet.add_worksheet(
            title="Booking Log",
            rows=100,
            cols=7
        )
        
        # Set up log headers
        log_headers = ["Timestamp", "Email", "Court", "Date", "Time", "Status", "Error Details"]
        
        # Insert headers
        log_sheet.insert_row(log_headers, 1)
        
        # Format headers
        log_sheet.format('A1:G1', {
            'textFormat': {'bold': True},
            'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
        })
        
        # Add a sample log entry
        sample_log = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "test@example.com",
            "Court 1",
            "01/01/2024",
            "1800",
            "🧪 Test Entry",
            "Template created successfully"
        ]
        log_sheet.insert_row(sample_log, 2)
        
        print(f"{get_timestamp()} ✅ Booking Log sheet created")
        
        # Set up sharing (optional - make it accessible to anyone with the link)
        try:
            spreadsheet.share('', perm_type='anyone', role='reader')
            print(f"{get_timestamp()} ✅ Spreadsheet shared with read access")
        except:
            print(f"{get_timestamp()} ⚠️ Could not set up sharing automatically")
        
        print(f"\n{get_timestamp()} 🎉 Google Sheets template created successfully!")
        print(f"{get_timestamp()} 📋 Next steps:")
        print(f"{get_timestamp()}   1. Copy the Spreadsheet ID: {spreadsheet.id}")
        print(f"{get_timestamp()}   2. Set the GSHEET_CAM_ID environment variable")
        print(f"{get_timestamp()}   3. Update the email addresses in the configuration sheet")
        print(f"{get_timestamp()}   4. Test the connection with test_sheets_setup.py")
        
        return spreadsheet.id
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Failed to create Google Sheets template: {e}")
        raise

def main():
    """Main function to create the Google Sheets template."""
    
    print("Google Sheets Template Creator")
    print("=" * 40)
    print()
    
    # Check for service account JSON
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
        print("Please set this variable with your Google Service Account JSON credentials")
        return
    
    try:
        # Create the template
        spreadsheet_id = create_sheets_template(service_account_json)
        
        print(f"\n✅ Template creation completed!")
        print(f"📊 Spreadsheet ID: {spreadsheet_id}")
        print(f"🔗 URL: https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit")
        
    except Exception as e:
        print(f"❌ Template creation failed: {e}")
        print("Please check your Google Service Account credentials and permissions")

if __name__ == "__main__":
    main()
