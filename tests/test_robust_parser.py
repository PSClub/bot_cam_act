# test_robust_parser.py
# Tests for the robust_parser.py functions

import sys
import os

# Add the parent directory to the path so we can import robust_parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from robust_parser import (
    normalize_day_name, 
    normalize_time, 
    parse_booking_schedule, 
    get_slots_for_day,
    validate_schedule_data,
    format_time_for_display
)
from utils import get_timestamp


class TestRobustParser:
    """Test class for robust parser functions."""
    
    def test_normalize_day_name(self):
        """Test day name normalization."""
        # Test full day names
        assert normalize_day_name("Monday") == "Monday"
        assert normalize_day_name("Tuesday") == "Tuesday"
        assert normalize_day_name("Wednesday") == "Wednesday"
        assert normalize_day_name("Thursday") == "Thursday"
        assert normalize_day_name("Friday") == "Friday"
        assert normalize_day_name("Saturday") == "Saturday"
        assert normalize_day_name("Sunday") == "Sunday"
        
        # Test short day names (from actual implementation)
        assert normalize_day_name("mon") == "Monday"
        assert normalize_day_name("tue") == "Tuesday"
        assert normalize_day_name("wed") == "Wednesday"
        assert normalize_day_name("thu") == "Thursday"
        assert normalize_day_name("fri") == "Friday"
        assert normalize_day_name("sat") == "Saturday"
        assert normalize_day_name("sun") == "Sunday"
        
        # Test additional short formats
        assert normalize_day_name("tues") == "Tuesday"
        assert normalize_day_name("thurs") == "Thursday"
        
        # Test case insensitive
        assert normalize_day_name("monday") == "Monday"
        assert normalize_day_name("TUESDAY") == "Tuesday"
        assert normalize_day_name("SAT") == "Saturday"
        
        # Test with extra spaces
        assert normalize_day_name(" Monday ") == "Monday"
        assert normalize_day_name("  tue  ") == "Tuesday"
        
        # Test invalid input
        try:
            normalize_day_name("Invalid")
            assert False, "Should raise ValueError for invalid day"
        except ValueError:
            pass
    
    def test_normalize_time(self):
        """Test time normalization."""
        # Test 12-hour format with AM/PM
        assert normalize_time("8am") == "0800"
        assert normalize_time("12am") == "0000"
        assert normalize_time("1pm") == "1300"
        assert normalize_time("12pm") == "1200"
        assert normalize_time("11pm") == "2300"
        
        # Test 12-hour format with minutes
        assert normalize_time("8:30am") == "0830"
        assert normalize_time("2:15pm") == "1415"
        assert normalize_time("12:45am") == "0045"
        assert normalize_time("12:30pm") == "1230"
        
        # Test 24-hour format
        assert normalize_time("08:00") == "0800"
        assert normalize_time("13:30") == "1330"
        assert normalize_time("00:00") == "0000"
        assert normalize_time("23:59") == "2359"
        
        # Test 24-hour format without colon
        assert normalize_time("0800") == "0800"
        assert normalize_time("1330") == "1330"
        assert normalize_time("2359") == "2359"
        
        # Test single/double digit hours
        assert normalize_time("8") == "0800"
        assert normalize_time("16") == "1600"
        assert normalize_time("800") == "0800"  # HMM format
        
        # Test case insensitive
        assert normalize_time("8AM") == "0800"
        assert normalize_time("2PM") == "1400"
        
        # Test with spaces 
        assert normalize_time(" 8am ") == "0800"
        
        # Test invalid input
        try:
            normalize_time("25:00")
            assert False, "Should raise ValueError for invalid time"
        except ValueError:
            pass
    
    def test_parse_booking_schedule(self):
        """Test booking schedule parsing."""
        schedule_data = [
            {'Day': 'Tuesday', 'Time': '1800', 'Notes': 'Feb-Aug only'},
            {'Day': 'tue', 'Time': '7pm', 'Notes': 'Summer only'},
            {'Day': 'Saturday', 'Time': '1400', 'Notes': 'All year'},
            {'Day': 'sun', 'Time': '3pm', 'Notes': 'All year'}
        ]
        
        result = parse_booking_schedule(schedule_data)
        
        # Should return a list of normalized dictionaries
        assert len(result) == 4
        
        # Check first entry (already normalized)
        assert result[0]['Day'] == 'Tuesday'
        assert result[0]['Time'] == '1800'
        assert result[0]['Notes'] == 'Feb-Aug only'
        
        # Check second entry (needs normalization)
        assert result[1]['Day'] == 'Tuesday'
        assert result[1]['Time'] == '1900'  # 7pm -> 1900
        assert result[1]['Notes'] == 'Summer only'
        
        # Check third entry 
        assert result[2]['Day'] == 'Saturday'
        assert result[2]['Time'] == '1400'
        assert result[2]['Notes'] == 'All year'
        
        # Check fourth entry (needs normalization)
        assert result[3]['Day'] == 'Sunday'  # sun -> Sunday
        assert result[3]['Time'] == '1500'   # 3pm -> 1500
        assert result[3]['Notes'] == 'All year'
    
    def test_get_slots_for_day(self):
        """Test getting slots for a specific day."""
        schedule_data = [
            {'Day': 'Tuesday', 'Time': '1800', 'Notes': 'Feb-Aug only'},
            {'Day': 'Tuesday', 'Time': '1900', 'Notes': 'Summer only'},
            {'Day': 'Saturday', 'Time': '1400', 'Notes': 'All year'},
            {'Day': 'Saturday', 'Time': '1500', 'Notes': 'All year'}
        ]
        
        # Test exact match
        tuesday_slots = get_slots_for_day(schedule_data, 'Tuesday')
        assert len(tuesday_slots) == 2
        assert '1800' in tuesday_slots
        assert '1900' in tuesday_slots
        
        # Test Saturday slots
        saturday_slots = get_slots_for_day(schedule_data, 'Saturday')
        assert len(saturday_slots) == 2
        assert '1400' in saturday_slots
        assert '1500' in saturday_slots
        
        # Test non-existent day
        monday_slots = get_slots_for_day(schedule_data, 'Monday')
        assert len(monday_slots) == 0
    
    def test_validate_schedule_data(self):
        """Test schedule data validation."""
        # Valid data
        valid_data = [
            {'Day': 'Tuesday', 'Time': '1800', 'Notes': 'Feb-Aug only'},
            {'Day': 'Saturday', 'Time': '1400', 'Notes': 'All year'}
        ]
        is_valid, issues = validate_schedule_data(valid_data)
        assert is_valid == True
        assert len(issues) == 0
        
        # Missing Day field
        invalid_data1 = [
            {'Time': '1800', 'Notes': 'Feb-Aug only'}
        ]
        is_valid, issues = validate_schedule_data(invalid_data1)
        assert is_valid == False
        assert len(issues) > 0
        
        # Invalid time
        invalid_data2 = [
            {'Day': 'Tuesday', 'Time': '25:00', 'Notes': 'Invalid time'}
        ]
        is_valid, issues = validate_schedule_data(invalid_data2)
        assert is_valid == False
        assert len(issues) > 0
        
        # Empty data
        is_valid, issues = validate_schedule_data([])
        assert is_valid == False
        assert len(issues) > 0
        
        is_valid, issues = validate_schedule_data(None)
        assert is_valid == False
        assert len(issues) > 0
    
    def test_format_time_for_display(self):
        """Test time formatting for display."""
        assert format_time_for_display("0800") == "8:00 AM"
        assert format_time_for_display("1330") == "1:30 PM"
        assert format_time_for_display("2359") == "11:59 PM"
        assert format_time_for_display("0000") == "12:00 AM"
        assert format_time_for_display("1200") == "12:00 PM"
        
        # Test invalid input - this function doesn't raise errors, just returns original
        result = format_time_for_display("invalid")
        assert result == "invalid"
        
        # Test edge case - "123" gets parsed as "12:03"
        result = format_time_for_display("123")
        assert result == "12:03 PM"


def run_tests():
    """Run all tests."""
    print(f"{get_timestamp()} 🧪 Running Robust Parser Tests...")
    
    test_class = TestRobustParser()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    passed = 0
    failed = 0
    
    for method_name in test_methods:
        try:
            print(f"{get_timestamp()}   Testing {method_name}...")
            test_method = getattr(test_class, method_name)
            test_method()
            print(f"{get_timestamp()}   ✅ {method_name} passed")
            passed += 1
        except Exception as e:
            print(f"{get_timestamp()}   ❌ {method_name} failed: {e}")
            failed += 1
    
    print(f"{get_timestamp()} 📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print(f"{get_timestamp()} ✅ All robust parser tests passed!")
        return True
    else:
        print(f"{get_timestamp()} ❌ Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
