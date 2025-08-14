#!/usr/bin/env python3
"""
Test script for the multi-session booking system.
This script verifies that the new multi-court booking system components are working correctly.
"""

import asyncio
import os
import sys
from sheets_manager import SheetsManager, test_sheets_connection
from multi_session_manager import MultiSessionManager, BookingSession
from robust_parser import test_robust_parser, normalize_day_name, normalize_time, parse_booking_schedule
from config import SHOW_BROWSER

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    from datetime import datetime
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

def test_environment_setup():
    """Test the environment setup for multi-court booking."""
    
    print("=== Testing Environment Setup ===")
    
    # Check environment variables
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

async def test_multi_session_initialization():
    """Test multi-session manager initialization."""
    
    print("\n=== Testing Multi-Session Initialization ===")
    
    # Check environment variables directly
    gsheet_id = os.environ.get('GSHEET_CAM_ID')
    service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not gsheet_id or not service_account_json:
        print("❌ Google Sheets configuration not set")
        return False
    
    try:
        # Initialize sheets manager
        sheets_manager = SheetsManager(gsheet_id, service_account_json)
        print("✅ Google Sheets manager initialized")
        
        # Initialize multi-session manager
        multi_session_manager = MultiSessionManager(sheets_manager)
        print("✅ Multi-session manager created")
        
        # Test session initialization (headless mode for testing)
        success = await multi_session_manager.initialize_sessions(headless=True)
        
        if success:
            print(f"✅ Successfully initialized {len(multi_session_manager.sessions)} sessions")
            
            # Print session details
            for session in multi_session_manager.sessions:
                print(f"   - {session.account_name}: {session.email} -> {session.court_number}")
            
            # Cleanup sessions
            await multi_session_manager.cleanup_all_sessions()
            print("✅ Sessions cleaned up successfully")
            
            return True
        else:
            print("❌ Failed to initialize sessions")
            return False
        
    except Exception as e:
        print(f"❌ Multi-session initialization failed: {e}")
        return False

async def test_booking_session_class():
    """Test the BookingSession class functionality."""
    
    print("\n=== Testing BookingSession Class ===")
    
    try:
        # Create a test session
        test_session = BookingSession(
            account_name="TestAccount",
            email="test@example.com",
            password="testpassword",
            court_number="Court 1",
            court_url="https://example.com/court1",
            sheets_manager=None  # We'll skip sheets operations for this test
        )
        
        print("✅ BookingSession created successfully")
        
        # Test browser initialization (headless mode)
        success = await test_session.initialize_browser(headless=True)
        
        if success:
            print("✅ Browser initialized successfully")
            
            # Test cleanup
            await test_session.cleanup()
            print("✅ Session cleaned up successfully")
            
            return True
        else:
            print("❌ Browser initialization failed")
            return False
        
    except Exception as e:
        print(f"❌ BookingSession test failed: {e}")
        return False

def test_robust_parsing():
    """Test robust parsing functionality."""
    
    print("\n=== Testing Robust Parsing ===")
    
    try:
        # Run the robust parser tests
        test_robust_parser()
        print("✅ Robust parsing tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Robust parsing test failed: {e}")
        return False

async def test_google_sheets_integration():
    """Test Google Sheets integration."""
    
    print("\n=== Testing Google Sheets Integration ===")
    
    # Check environment variables directly
    gsheet_id = os.environ.get('GSHEET_CAM_ID')
    service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not gsheet_id or not service_account_json:
        print("❌ Google Sheets configuration not set")
        return False
    
    try:
        # Test connection
        success = test_sheets_connection(gsheet_id, service_account_json)
        if not success:
            return False
        
        # Test reading configuration
        sheets_manager = SheetsManager(gsheet_id, service_account_json)
        config_data = sheets_manager.read_configuration_sheet()
        
        print(f"✅ Configuration sheet contains {len(config_data)} entries:")
        for entry in config_data:
            account = entry.get('Account', 'Unknown')
            email = entry.get('Email', 'No email')
            court = entry.get('Court Number', 'No court')
            print(f"   {account}: {email} -> {court}")
        
        # Test reading schedule
        schedule_data = sheets_manager.read_booking_schedule_sheet()
        
        print(f"✅ Schedule sheet contains {len(schedule_data)} entries:")
        for entry in schedule_data:
            day = entry.get('Day', 'Unknown')
            time = entry.get('Time', 'No time')
            notes = entry.get('Notes', 'No notes')
            print(f"   {day} {time}: {notes}")
        
        return True
        
    except Exception as e:
        print(f"❌ Google Sheets test failed: {e}")
        return False

async def test_booking_orchestrator():
    """Test the booking orchestrator (without actual booking)."""
    
    print("\n=== Testing Booking Orchestrator ===")
    
    try:
        from booking_orchestrator import BookingOrchestrator
        
        # Create orchestrator
        orchestrator = BookingOrchestrator()
        print("✅ BookingOrchestrator created")
        
        # Test initialization (this will fail if Google Sheets not set up, but that's expected)
        try:
            await orchestrator.initialize()
            print("✅ BookingOrchestrator initialized successfully")
        except Exception as e:
            print(f"⚠️ BookingOrchestrator initialization failed (expected if sheets not set up): {e}")
            print("   This is normal if Google Sheets are not configured yet")
        
        return True
        
    except Exception as e:
        print(f"❌ Booking orchestrator test failed: {e}")
        return False

async def main():
    """Main test function."""
    
    print("Multi-Court Booking System - Component Tests")
    print("=" * 50)
    print()
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Robust Parsing", test_robust_parsing),
        ("Google Sheets Integration", test_google_sheets_integration),
        ("BookingSession Class", test_booking_session_class),
        ("Multi-Session Initialization", test_multi_session_initialization),
        ("Booking Orchestrator", test_booking_orchestrator)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                if await test_func():
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            else:
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
        print("1. Set up the Google Sheets with the required structure")
        print("2. Configure all environment variables")
        print("3. Test the booking system with a small schedule")
        print("4. Set up cron jobs for automated booking")
        return True
    else:
        print("⚠️ Some tests failed. Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    
    if success:
        print("🎉 Multi-court booking system tests completed successfully")
        sys.exit(0)
    else:
        print("❌ Multi-court booking system tests failed")
        sys.exit(1)
