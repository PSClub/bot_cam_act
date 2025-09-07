#!/usr/bin/env python3
"""
Test script for Google Sheets integration with the new multi-court booking system.
This script verifies that the Google Sheets integration is working correctly.
"""

import os
import sys
import json

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets_manager import SheetsManager
from utils import get_timestamp

def test_gsheets_integration():
    """Test the Google Sheets integration with environment variables."""
    
    print(f"{get_timestamp()} === Testing Google Sheets Integration ===\n")
    
    # Get environment variables
    sheet_id = os.environ.get("GSHEET_CAM_ID")
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    # Check if environment variables are set
    if not sheet_id:
        print(f"{get_timestamp()} ❌ GSHEET_CAM_ID environment variable not set")
        return False
    
    if not service_account_json:
        print(f"{get_timestamp()} ❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
        return False
    
    print(f"{get_timestamp()} ✅ GSHEET_CAM_ID: {sheet_id}")
    print(f"{get_timestamp()} ✅ GOOGLE_SERVICE_ACCOUNT_JSON: {'*' * 20}... (hidden for security)")
    print()
    
    try:
        # Initialize the SheetsManager
        print(f"{get_timestamp()} --- Initializing SheetsManager ---")
        sheets_manager = SheetsManager(sheet_id, service_account_json)
        print(f"{get_timestamp()} ✅ SheetsManager initialized successfully")
        print()
        
        # Test sheet info
        print(f"{get_timestamp()} --- Testing sheet information ---")
        sheet_info = sheets_manager.get_sheet_info()
        if sheet_info:
            print(f"{get_timestamp()} ✅ Sheet info retrieved:")
            print(f"{get_timestamp()} 📋 Title: {sheet_info.get('title', 'N/A')}")
            print(f"{get_timestamp()} 📋 Worksheets: {len(sheet_info.get('worksheets', []))}")
            for ws in sheet_info.get('worksheets', []):
                print(f"{get_timestamp()}   - {ws}")
        else:
            print(f"{get_timestamp()} ❌ Failed to get sheet information")
            return False
        print()
        
        # Test reading booking assignments (new simplified system)
        print(f"{get_timestamp()} --- Testing BookingSchedule sheet (simplified system) ---")
        try:
            assignments_data = sheets_manager.read_booking_assignments()
            if assignments_data:
                print(f"{get_timestamp()} ✅ Successfully read {len(assignments_data)} booking assignments")
                print(f"{get_timestamp()} 📋 Sample assignments:")
                for i, entry in enumerate(assignments_data[:5]):  # Show first 5 entries
                    account = entry.get('Account', 'N/A')
                    day = entry.get('Day', 'N/A')
                    time = entry.get('Time', 'N/A')
                    court = entry.get('Court Number', 'N/A')
                    print(f"{get_timestamp()}   {i+1}. {account} -> {court} -> {day} {time}")
                if len(assignments_data) > 5:
                    print(f"{get_timestamp()}   ... and {len(assignments_data) - 5} more")
                
                # Test filtering by day
                saturday_assignments = [a for a in assignments_data if a.get('Day', '').lower() == 'saturday']
                print(f"{get_timestamp()} 📋 Saturday assignments: {len(saturday_assignments)}")
                for entry in saturday_assignments[:3]:
                    account = entry.get('Account', 'N/A')
                    time = entry.get('Time', 'N/A')
                    court = entry.get('Court Number', 'N/A')
                    print(f"{get_timestamp()}     {account} -> {court} -> {time}")
            else:
                print(f"{get_timestamp()} ⚠️ No booking assignments found")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading booking assignments: {e}")
            return False
        print()
        
        # Test writing to booking log
        print(f"{get_timestamp()} --- Testing Booking Log write ---")
        try:
            test_log_entry = {
                'Timestamp': '2024-01-01 12:00:00',
                'Email': 'test@example.com',
                'Court': 'Test Court',
                'Date': '2024-02-01',
                'Time': '1800',
                'Status': 'Test Entry',
                'Error Details': 'This is a test entry from automated tests'
            }
            sheets_manager.write_booking_log(test_log_entry)
            print(f"{get_timestamp()} ✅ Successfully wrote test entry to booking log")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error writing to booking log: {e}")
            return False
        print()
        
        # Test reading from booking log (with pagination)
        print(f"{get_timestamp()} --- Testing Booking Log read with pagination ---")
        try:
            log_result = sheets_manager.read_booking_log(limit=5, offset=0)
            if log_result['entries']:
                print(f"{get_timestamp()} ✅ Successfully read booking log")
                print(f"{get_timestamp()} 📊 Total entries: {log_result['total_count']}")
                print(f"{get_timestamp()} 📊 Retrieved: {len(log_result['entries'])}")
                print(f"{get_timestamp()} 📊 Has more: {log_result['has_more']}")
                print(f"{get_timestamp()} 📋 Recent entries:")
                for i, entry in enumerate(log_result['entries'][:3]):
                    status = entry.get('Status', 'N/A')
                    timestamp = entry.get('Timestamp', 'N/A')
                    print(f"{get_timestamp()}   {i+1}. {timestamp} - {status}")
            else:
                print(f"{get_timestamp()} ⚠️ No log entries found (this might be normal for a new sheet)")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading booking log: {e}")
            return False
        print()
        
        # Test connection verification using the standalone function
        print(f"{get_timestamp()} --- Testing connection verification ---")
        from sheets_manager import test_sheets_connection
        connection_test = test_sheets_connection(sheet_id, service_account_json)
        if connection_test:
            print(f"{get_timestamp()} ✅ Connection test passed")
        else:
            print(f"{get_timestamp()} ❌ Connection test failed")
            return False
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"{get_timestamp()} 🎉 Google Sheets integration test completed successfully!")
    return True

def main():
    """Main function to run the test."""
    
    print(f"{get_timestamp()} Google Sheets Integration Test")
    print(f"{get_timestamp()}" + "=" * 40)
    print()
    
    if test_gsheets_integration():
        print(f"\n{get_timestamp()} ✅ All tests passed! Google Sheets integration is working correctly.")
        sys.exit(0)
    else:
        print(f"\n{get_timestamp()} ❌ Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
