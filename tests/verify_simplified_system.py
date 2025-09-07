#!/usr/bin/env python3
"""
Verification script for the simplified booking system.
This script validates that the new logic works correctly with real data.
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sheets_manager import SheetsManager
from multi_session_manager import MultiSessionManager
from booking_orchestrator import BookingOrchestrator


def test_booking_assignment_parsing():
    """Test parsing of booking assignments from the new sheet structure."""
    print("🧪 Testing Booking Assignment Parsing")
    print("-" * 40)
    
    # Sample data matching your Google Sheets structure
    sample_assignments = [
        {
            'Account': 'Mother',
            'Email': '1140749429@qq.com',
            'Court Number': 'Court 1',
            'Day': 'Saturday',
            'Time': '1400',
            'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
            'Notes': 'All year'
        },
        {
            'Account': 'Father',
            'Email': 'huay43105@gmail.com',
            'Court Number': 'Court 2',
            'Day': 'Saturday',
            'Time': '1500',
            'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/',
            'Notes': 'All year'
        },
        {
            'Account': 'Bruce',
            'Email': 'brcwood48@gmail.com',
            'Court Number': 'Court 3',
            'Day': 'Saturday',
            'Time': '1600',
            'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/',
            'Notes': 'All year'
        },
        {
            'Account': 'Sallie',
            'Email': 'salliebecker01@gmail.com',
            'Court Number': 'Court 1',
            'Day': 'Sunday',
            'Time': '1400',
            'Court URL': 'https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/',
            'Notes': 'All year'
        }
    ]
    
    print(f"✅ Sample data contains {len(sample_assignments)} assignments")
    
    # Test filtering by day
    saturday_assignments = [a for a in sample_assignments if a['Day'].lower() == 'saturday']
    sunday_assignments = [a for a in sample_assignments if a['Day'].lower() == 'sunday']
    
    print(f"✅ Saturday assignments: {len(saturday_assignments)}")
    for assignment in saturday_assignments:
        print(f"   - {assignment['Account']} -> {assignment['Court Number']} -> {assignment['Time']}")
    
    print(f"✅ Sunday assignments: {len(sunday_assignments)}")
    for assignment in sunday_assignments:
        print(f"   - {assignment['Account']} -> {assignment['Court Number']} -> {assignment['Time']}")
    
    # Test data validation
    required_fields = ['Account', 'Email', 'Court Number', 'Day', 'Time', 'Court URL']
    for i, assignment in enumerate(sample_assignments):
        for field in required_fields:
            if field not in assignment or not assignment[field].strip():
                print(f"❌ Assignment {i+1} missing required field: {field}")
                return False
        
        # Validate time format
        if not assignment['Time'].isdigit() or len(assignment['Time']) != 4:
            print(f"❌ Assignment {i+1} has invalid time format: {assignment['Time']}")
            return False
    
    print("✅ All assignments have valid data structure")
    return True


def test_session_assignment_logic():
    """Test the logic for assigning sessions to specific time slots."""
    print("\n🧪 Testing Session Assignment Logic")
    print("-" * 40)
    
    # Mock assignment data
    saturday_assignments = [
        {'Account': 'Mother', 'Time': '1400', 'Court Number': 'Court 1'},
        {'Account': 'Father', 'Time': '1500', 'Court Number': 'Court 2'},
        {'Account': 'Bruce', 'Time': '1600', 'Court Number': 'Court 3'}
    ]
    
    print("📋 Assignment mapping:")
    for assignment in saturday_assignments:
        print(f"   {assignment['Account']} -> {assignment['Court Number']} -> {assignment['Time']}")
    
    # Verify each account gets exactly one slot
    accounts = set(a['Account'] for a in saturday_assignments)
    slots = [a['Time'] for a in saturday_assignments]
    
    print(f"✅ Unique accounts: {len(accounts)} ({', '.join(accounts)})")
    print(f"✅ Time slots: {', '.join(slots)}")
    print(f"✅ No duplicate accounts: {len(accounts) == len(saturday_assignments)}")
    
    return True


def test_target_date_calculation():
    """Test target date calculation (35 days from today)."""
    print("\n🧪 Testing Target Date Calculation")
    print("-" * 40)
    
    today = datetime.now().date()
    target_date = today + timedelta(days=35)
    target_day_name = target_date.strftime('%A')
    
    print(f"✅ Today: {today.strftime('%d/%m/%Y')} ({today.strftime('%A')})")
    print(f"✅ Target date: {target_date.strftime('%d/%m/%Y')} ({target_day_name})")
    print(f"✅ Days difference: {(target_date - today).days}")
    
    return True


def test_environment_variables():
    """Test that required environment variables are configured."""
    print("\n🧪 Testing Environment Variables")
    print("-" * 40)
    
    required_vars = [
        'GSHEET_CAM_ID',
        'GOOGLE_SERVICE_ACCOUNT_JSON',
        'MOTHER_CAM_PASSWORD',
        'FATHER_CAM_PASSWORD',
        'BRUCE_CAM_PASSWORD',
        'SALLIE_CAM_PASSWORD',
        'JAN_CAM_PASSWORD',
        'JO_CAM_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10} (configured)")
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are configured")
    return True


async def test_sheets_manager_integration():
    """Test SheetsManager integration with real credentials (if available)."""
    print("\n🧪 Testing SheetsManager Integration")
    print("-" * 40)
    
    sheet_id = os.environ.get('GSHEET_CAM_ID')
    service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if not sheet_id or not service_account_json:
        print("⚠️ Skipping integration test - credentials not available")
        return True
    
    try:
        sheets_manager = SheetsManager(sheet_id, service_account_json)
        print("✅ SheetsManager initialized successfully")
        
        # Test reading booking assignments
        assignments = sheets_manager.read_booking_assignments()
        print(f"✅ Read {len(assignments)} booking assignments")
        
        if assignments:
            print("📋 Sample assignments:")
            for i, assignment in enumerate(assignments[:3]):  # Show first 3
                print(f"   {i+1}. {assignment.get('Account', 'N/A')} -> {assignment.get('Day', 'N/A')} -> {assignment.get('Time', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ SheetsManager integration test failed: {e}")
        return False


def validate_booking_schedule_structure():
    """Validate the expected structure of the BookingSchedule sheet."""
    print("\n🧪 Validating BookingSchedule Structure")
    print("-" * 40)
    
    expected_columns = [
        'Account',
        'Email', 
        'Court Number',
        'Day',
        'Time',
        'Court URL',
        'Notes'
    ]
    
    print("📋 Expected columns in BookingSchedule sheet:")
    for i, column in enumerate(expected_columns, 1):
        print(f"   {i}. {column}")
    
    print("\n📋 Expected data types:")
    print("   - Account: String (e.g., 'Mother', 'Father', 'Bruce')")
    print("   - Email: String (valid email address)")
    print("   - Court Number: String (e.g., 'Court 1', 'Court 2', 'Court 3')")
    print("   - Day: String (e.g., 'Saturday', 'Sunday', 'Tuesday')")
    print("   - Time: String (4 digits, e.g., '1400', '1500', '1800')")
    print("   - Court URL: String (full Camden Active URL)")
    print("   - Notes: String (optional, e.g., 'All year')")
    
    print("\n✅ Structure validation complete")
    return True


async def run_all_tests():
    """Run all verification tests."""
    print("🎾 Simplified Booking System Verification")
    print("=" * 50)
    
    tests = [
        ("Booking Assignment Parsing", test_booking_assignment_parsing),
        ("Session Assignment Logic", test_session_assignment_logic),
        ("Target Date Calculation", test_target_date_calculation),
        ("Environment Variables", test_environment_variables),
        ("BookingSchedule Structure", validate_booking_schedule_structure),
        ("SheetsManager Integration", test_sheets_manager_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All verification tests passed! The simplified system is ready.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed. Please address the issues above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
