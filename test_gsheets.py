#!/usr/bin/env python3
"""
Test script for Google Sheets data download functionality.
This script can be used to verify that the Google Sheets integration is working correctly.
"""

import os
import sys
from data_processor import download_data_from_gsheets, process_booking_file

def test_gsheets_integration():
    """Test the Google Sheets integration with environment variables."""
    
    print("=== Testing Google Sheets Integration ===\n")
    
    # Get environment variables
    sheet_id = os.environ.get("GSHEET_CAM_ID")
    tab_name = "camden_active_booking_dates"  # Fixed tab name
    service_account_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    # Check if environment variables are set
    if not sheet_id:
        print("❌ GSHEET_CAM_ID environment variable not set")
        return False
    
    if not service_account_json:
        print("❌ GOOGLE_SERVICE_ACCOUNT_JSON environment variable not set")
        return False
    
    print(f"✅ GSHEET_CAM_ID: {sheet_id}")
    print(f"✅ Tab Name: {tab_name}")
    print(f"✅ GOOGLE_SERVICE_ACCOUNT_JSON: {'*' * 20}... (hidden for security)")
    print()
    
    # Test direct download
    print("--- Testing direct Google Sheets download ---")
    df = download_data_from_gsheets(sheet_id, tab_name, service_account_json)
    
    if df is not None:
        print("✅ Successfully downloaded Google Sheets data")
        print(f"📊 Data shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"📋 Columns: {', '.join(df.columns.tolist())}")
        print("📋 First 3 rows:")
        print(df.head(3).to_string())
        print()
    else:
        print("❌ Failed to download Google Sheets data")
        return False
    
    # Test full processing pipeline
    print("--- Testing full booking file processing ---")
    local_backup_file = "ca_lif_booking_dates.csv"
    
    try:
        slots = process_booking_file(local_backup_file, sheet_id, tab_name, service_account_json)
        if slots:
            print(f"✅ Successfully processed {len(slots)} booking slots")
            print("📅 Sample bookings:")
            for i, slot in enumerate(slots[:3]):  # Show first 3 slots
                court_name = slot[0].split('/')[-2] if '/' in slot[0] else slot[0]
                print(f"  {i+1}. {court_name} on {slot[1]} at {slot[2]}")
            if len(slots) > 3:
                print(f"  ... and {len(slots) - 3} more")
        else:
            print("⚠️ No booking slots found (this might be normal if no slots are in the 33-35 day window)")
        print()
    except Exception as e:
        print(f"❌ Error processing booking file: {e}")
        return False
    
    print("🎉 Google Sheets integration test completed successfully!")
    return True

def main():
    """Main function to run the test."""
    
    print("Google Sheets Integration Test")
    print("=" * 40)
    print()
    
    if test_gsheets_integration():
        print("\n✅ All tests passed! Google Sheets integration is working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main()
