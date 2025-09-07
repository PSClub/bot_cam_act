#!/usr/bin/env python3
"""
Test script for Google Sheets setup and robust parser functionality.
This script verifies that the new multi-court booking system components are working correctly.
"""

import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets_manager import SheetsManager, test_sheets_connection
from robust_parser import test_robust_parser, normalize_day_name, normalize_time, parse_booking_schedule
from config import GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON

def test_multi_court_configuration():
    """Test the multi-court configuration setup."""
    
    print("=== Testing Multi-Court Configuration ===")
    
    # Check environment variables
    required_vars = [
        'GSHEET_CAM_ID',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'MOTHER_CAM_EMAIL_ADDRESS',
        'MOTHER_CAM_PASSWORD',
        'FATHER_CAM_EMAIL_ADDRESS',
        'FATHER_CAM_PASSWORD',
        'BRUCE_CAM_EMAIL_ADDRESS',
        'BRUCE_CAM_PASSWORD',
        'SALLIE_CAM_EMAIL_ADDRESS',
        'SALLIE_CAM_PASSWORD',
        'JAN_CAM_EMAIL_ADDRESS',
        'JAN_CAM_PASSWORD',
        'JO_CAM_EMAIL_ADDRESS',
        'JO_CAM_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
    
    # Test court URLs
    from config import COURT_1_URL, COURT_2_URL, COURT_3_URL
    court_urls = [COURT_1_URL, COURT_2_URL, COURT_3_URL]
    
    print("✅ Court URLs configured:")
    for i, url in enumerate(court_urls, 1):
        print(f"   Court {i}: {url}")
    
    return True

def test_google_sheets_structure():
    """Test Google Sheets connection and structure."""
    
    print("\n=== Testing Google Sheets Structure ===")
    
    if not GSHEET_MAIN_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
        print("❌ Google Sheets configuration not set")
        return False
    
    try:
        # Test connection
        success = test_sheets_connection(GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
        if not success:
            return False
        
        # Test reading booking assignments (new simplified system)
        sheets_manager = SheetsManager(GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
        assignments_data = sheets_manager.read_booking_assignments()
        
        print(f"✅ BookingSchedule sheet contains {len(assignments_data)} assignments:")
        for entry in assignments_data:
            account = entry.get('Account', 'Unknown')
            email = entry.get('Email', 'No email')
            court = entry.get('Court Number', 'No court')
            day = entry.get('Day', 'No day')
            time = entry.get('Time', 'No time')
            print(f"   {account}: {email} -> {court} -> {day} {time}")
        
        # Test filtering by day (example with Saturday)
        saturday_assignments = [a for a in assignments_data if a.get('Day', '').lower() == 'saturday']
        print(f"✅ Saturday assignments: {len(saturday_assignments)}")
        for entry in saturday_assignments:
            account = entry.get('Account', 'Unknown')
            time = entry.get('Time', 'No time')
            court = entry.get('Court Number', 'No court')
            print(f"   {account} -> {court} -> {time}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets test failed: {e}")
        return False

def test_robust_parsing():
    """Test robust parsing functionality."""
    
    print("\n=== Testing Robust Parsing ===")
    
    try:
        # Test day name normalization
        day_tests = [
            ("Tuesday", "Tuesday"),
            ("tue", "Tuesday"),
            ("tues", "Tuesday"),
            ("sat", "Saturday"),
            ("sun", "Sunday")
        ]
        
        for input_day, expected in day_tests:
            result = normalize_day_name(input_day)
            if result != expected:
                print(f"❌ Day normalization failed: '{input_day}' -> '{result}' (expected: '{expected}')")
                return False
        
        print("✅ Day name normalization working correctly")
        
        # Test time normalization
        time_tests = [
            ("8am", "0800"),
            ("800", "0800"),
            ("08:00", "0800"),
            ("4pm", "1600"),
            ("16:00", "1600")
        ]
        
        for input_time, expected in time_tests:
            result = normalize_time(input_time)
            if result != expected:
                print(f"❌ Time normalization failed: '{input_time}' -> '{result}' (expected: '{expected}')")
                return False
        
        print("✅ Time normalization working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Robust parsing test failed: {e}")
        return False

def test_schedule_processing():
    """Test schedule processing functionality."""
    
    print("\n=== Testing Schedule Processing ===")
    
    try:
        # Test schedule parsing
        test_schedule = [
            {"Day": "tue", "Time": "8am", "Notes": "Feb-Aug only"},
            {"Day": "thu", "Time": "6pm", "Notes": "Summer only"},
            {"Day": "sat", "Time": "1400", "Notes": "All year"},
            {"Day": "sun", "Time": "3pm", "Notes": "All year"}
        ]
        
        normalized_schedule = parse_booking_schedule(test_schedule)
        
        expected_schedule = [
            {"Day": "Tuesday", "Time": "0800", "Notes": "Feb-Aug only"},
            {"Day": "Thursday", "Time": "1800", "Notes": "Summer only"},
            {"Day": "Saturday", "Time": "1400", "Notes": "All year"},
            {"Day": "Sunday", "Time": "1500", "Notes": "All year"}
        ]
        
        if len(normalized_schedule) != len(expected_schedule):
            print(f"❌ Schedule parsing failed: got {len(normalized_schedule)} entries, expected {len(expected_schedule)}")
            return False
        
        for i, (actual, expected) in enumerate(zip(normalized_schedule, expected_schedule)):
            if actual != expected:
                print(f"❌ Schedule entry {i} mismatch: got {actual}, expected {expected}")
                return False
        
        print("✅ Schedule processing working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Schedule processing test failed: {e}")
        return False

def main():
    """Main test function."""
    
    print("Multi-Court Booking System - Setup Test")
    print("=" * 50)
    print()
    
    tests = [
        ("Multi-Court Configuration", test_multi_court_configuration),
        ("Google Sheets Structure", test_google_sheets_structure),
        ("Robust Parsing", test_robust_parsing),
        ("Schedule Processing", test_schedule_processing)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The multi-court booking system is ready.")
        print("\nNext steps:")
        print("1. Create the Google Sheets with the required structure")
        print("2. Set up the cron jobs for weekday and weekend bookings")
        print("3. Test the booking system with a small schedule")
        sys.exit(0)
    else:
        print("⚠️ Some tests failed. Please fix the issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
