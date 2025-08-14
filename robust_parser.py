# robust_parser.py
# This file handles robust parsing of day names and time formats

from datetime import datetime

def normalize_day_name(day_input):
    """
    Convert any day input to standardized format.
    
    Args:
        day_input (str): Day name in any format (e.g., "Tuesday", "Tue", "tues")
        
    Returns:
        str: Standardized day name (e.g., "Tuesday")
        
    Examples:
        "Tuesday" -> "Tuesday"
        "tue" -> "Tuesday"
        "tues" -> "Tuesday"
        "sat" -> "Saturday"
        "sun" -> "Sunday"
    """
    if not day_input:
        raise ValueError("Day input cannot be empty")
    
    day_input = str(day_input).strip().lower()
    
    day_mappings = {
        # Full names
        'monday': 'Monday', 'mon': 'Monday',
        'tuesday': 'Tuesday', 'tue': 'Tuesday', 'tues': 'Tuesday',
        'wednesday': 'Wednesday', 'wed': 'Wednesday',
        'thursday': 'Thursday', 'thu': 'Thursday', 'thurs': 'Thursday',
        'friday': 'Friday', 'fri': 'Friday',
        'saturday': 'Saturday', 'sat': 'Saturday',
        'sunday': 'Sunday', 'sun': 'Sunday'
    }
    
    normalized_day = day_mappings.get(day_input)
    if not normalized_day:
        raise ValueError(f"Could not parse day name: '{day_input}'. Valid options: {', '.join(day_mappings.keys())}")
    
    return normalized_day

def normalize_time(time_input):
    """
    Convert any time input to HHMM format.
    
    Args:
        time_input (str): Time in any format (e.g., "8am", "800", "08:00", "4pm")
        
    Returns:
        str: Time in HHMM format (e.g., "0800", "1600")
        
    Examples:
        "8am" -> "0800"
        "800" -> "0800"
        "08:00" -> "0800"
        "4pm" -> "1600"
        "16:00" -> "1600"
        "12am" -> "0000"
        "12pm" -> "1200"
    """
    if not time_input:
        raise ValueError("Time input cannot be empty")
    
    time_input = str(time_input).strip().lower()
    
    # Handle AM/PM formats first
    is_pm = 'pm' in time_input
    is_am = 'am' in time_input
    
    if is_pm or is_am:
        # Remove am/pm from the time string
        time_input = time_input.replace('am', '').replace('pm', '')
        
        # Parse the time number
        try:
            # Handle minutes if present (e.g., "12:30")
            if ':' in time_input:
                parts = time_input.split(':')
                time_num = int(parts[0])
                minute = int(parts[1])
            else:
                time_num = int(time_input)
                minute = 0
            
            # Handle special cases for 12-hour format
            if is_pm:
                # PM: add 12 unless it's 12pm (noon)
                if time_num == 12:
                    hour = 12
                else:
                    hour = time_num + 12
            else:  # is_am
                # AM: subtract 12 if it's 12am (midnight)
                if time_num == 12:
                    hour = 0
                else:
                    hour = time_num
            
            time_input = f"{hour:02d}{minute:02d}"
            
        except ValueError:
            raise ValueError(f"Invalid time format: '{time_input}'")
    
    else:
        # Handle 24-hour format
        # Remove common separators
        time_input = time_input.replace(':', '').replace('.', '').replace(' ', '')
        
        # Ensure 4-digit format
        if len(time_input) == 3:  # e.g., "800" -> "0800"
            time_input = '0' + time_input
        elif len(time_input) == 2:  # e.g., "8" -> "0800" or "20" -> "2000"
            # Check if it's a valid hour (0-23)
            hour = int(time_input)
            if 0 <= hour <= 23:
                time_input = f"{hour:02d}00"
            else:
                raise ValueError(f"Invalid hour: {hour}")
        elif len(time_input) == 1:  # e.g., "8" -> "0800"
            time_input = '0' + time_input + '00'
        elif len(time_input) != 4:
            raise ValueError(f"Invalid time format: '{time_input}'")
    
    # Validate time format
    try:
        hour = int(time_input[:2])
        minute = int(time_input[2:4])
        
        if not (0 <= hour <= 23):
            raise ValueError(f"Hour must be between 0-23, got: {hour}")
        if not (0 <= minute <= 59):
            raise ValueError(f"Minute must be between 0-59, got: {minute}")
        
        return f"{hour:02d}{minute:02d}"
        
    except ValueError as e:
        raise ValueError(f"Could not parse time '{time_input}': {e}")

def parse_booking_schedule(schedule_data):
    """
    Parse and normalize booking schedule data from Google Sheets.
    
    Args:
        schedule_data (list): List of dictionaries from booking schedule sheet
        
    Returns:
        list: Normalized schedule data with standardized day names and times
        
    Example:
        Input: [{"Day": "tue", "Time": "8am", "Notes": "Feb-Aug only"}]
        Output: [{"Day": "Tuesday", "Time": "0800", "Notes": "Feb-Aug only"}]
    """
    normalized_schedule = []
    
    for row in schedule_data:
        try:
            # Normalize day and time
            normalized_day = normalize_day_name(row.get('Day', ''))
            normalized_time = normalize_time(row.get('Time', ''))
            
            # Create normalized row
            normalized_row = {
                'Day': normalized_day,
                'Time': normalized_time,
                'Notes': row.get('Notes', '')
            }
            
            normalized_schedule.append(normalized_row)
            
        except ValueError as e:
            print(f"Warning: Skipping invalid schedule row: {row} - Error: {e}")
            continue
    
    return normalized_schedule

def get_slots_for_day(schedule_data, target_day):
    """
    Get all time slots for a specific day from the booking schedule.
    
    Args:
        schedule_data (list): Normalized booking schedule data
        target_day (str): Target day name (e.g., "Tuesday")
        
    Returns:
        list: List of time slots (in HHMM format) for the target day
        
    Example:
        schedule_data = [
            {"Day": "Tuesday", "Time": "1800", "Notes": "Feb-Aug only"},
            {"Day": "Tuesday", "Time": "1900", "Notes": "Summer only"},
            {"Day": "Thursday", "Time": "1800", "Notes": "Feb-Aug only"}
        ]
        get_slots_for_day(schedule_data, "Tuesday") -> ["1800", "1900"]
    """
    slots = []
    
    for row in schedule_data:
        if row.get('Day') == target_day:
            slots.append(row.get('Time'))
    
    return sorted(slots)  # Return sorted list of times

def validate_schedule_data(schedule_data):
    """
    Validate booking schedule data for common issues.
    
    Args:
        schedule_data (list): Booking schedule data to validate
        
    Returns:
        tuple: (is_valid, issues_list)
        
    Example:
        is_valid, issues = validate_schedule_data(schedule_data)
        if not is_valid:
            print("Schedule validation issues:", issues)
    """
    issues = []
    
    if not schedule_data:
        issues.append("Schedule data is empty")
        return False, issues
    
    # Check for required columns
    required_columns = ['Day', 'Time']
    for row in schedule_data:
        for column in required_columns:
            if column not in row or not row[column]:
                issues.append(f"Missing required column '{column}' in row: {row}")
    
    # Check for valid day names
    valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for row in schedule_data:
        try:
            day = normalize_day_name(row.get('Day', ''))
            if day not in valid_days:
                issues.append(f"Invalid day name: {row.get('Day')}")
        except ValueError:
            issues.append(f"Could not parse day name: {row.get('Day')}")
    
    # Check for valid time formats
    for row in schedule_data:
        try:
            time = normalize_time(row.get('Time', ''))
            # Additional validation: check if time is reasonable for tennis courts
            hour = int(time[:2])
            if hour < 6 or hour > 22:
                issues.append(f"Unusual time for tennis court: {time} (hour: {hour})")
        except ValueError:
            issues.append(f"Could not parse time: {row.get('Time')}")
    
    # Check for duplicate day/time combinations
    day_time_combinations = []
    for row in schedule_data:
        try:
            day = normalize_day_name(row.get('Day', ''))
            time = normalize_time(row.get('Time', ''))
            combination = f"{day} {time}"
            if combination in day_time_combinations:
                issues.append(f"Duplicate day/time combination: {combination}")
            else:
                day_time_combinations.append(combination)
        except ValueError:
            continue  # Skip invalid entries
    
    return len(issues) == 0, issues

def format_time_for_display(time_hhmm):
    """
    Convert HHMM format to user-friendly display format.
    
    Args:
        time_hhmm (str): Time in HHMM format
        
    Returns:
        str: User-friendly time format
        
    Examples:
        "0800" -> "8:00 AM"
        "1600" -> "4:00 PM"
        "1200" -> "12:00 PM"
        "0000" -> "12:00 AM"
    """
    try:
        hour = int(time_hhmm[:2])
        minute = int(time_hhmm[2:4])
        
        if hour == 0:
            display_hour = 12
            period = "AM"
        elif hour < 12:
            display_hour = hour
            period = "AM"
        elif hour == 12:
            display_hour = 12
            period = "PM"
        else:
            display_hour = hour - 12
            period = "PM"
        
        return f"{display_hour}:{minute:02d} {period}"
        
    except (ValueError, IndexError):
        return time_hhmm  # Return original if parsing fails

def test_robust_parser():
    """
    Test function to verify robust parsing functionality.
    """
    print("=== Testing Robust Parser ===")
    
    # Test day name normalization
    day_tests = [
        ("Tuesday", "Tuesday"),
        ("tue", "Tuesday"),
        ("tues", "Tuesday"),
        ("sat", "Saturday"),
        ("sun", "Sunday"),
        ("THURSDAY", "Thursday"),
        ("fri", "Friday")
    ]
    
    print("Testing day name normalization:")
    for input_day, expected in day_tests:
        try:
            result = normalize_day_name(input_day)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{input_day}' -> '{result}' (expected: '{expected}')")
        except ValueError as e:
            print(f"  ❌ '{input_day}' -> Error: {e}")
    
    # Test time normalization
    time_tests = [
        ("8am", "0800"),
        ("800", "0800"),
        ("08:00", "0800"),
        ("4pm", "1600"),
        ("16:00", "1600"),
        ("12am", "0000"),
        ("12pm", "1200"),
        ("12:30am", "0030"),
        ("12:30pm", "1230"),
        ("8", "0800"),
        ("20", "2000")
    ]
    
    print("\nTesting time normalization:")
    for input_time, expected in time_tests:
        try:
            result = normalize_time(input_time)
            status = "✅" if result == expected else "❌"
            print(f"  {status} '{input_time}' -> '{result}' (expected: '{expected}')")
        except ValueError as e:
            print(f"  ❌ '{input_time}' -> Error: {e}")
    
    # Test schedule parsing
    test_schedule = [
        {"Day": "tue", "Time": "8am", "Notes": "Feb-Aug only"},
        {"Day": "thu", "Time": "6pm", "Notes": "Summer only"},
        {"Day": "sat", "Time": "1400", "Notes": "All year"},
        {"Day": "sun", "Time": "3pm", "Notes": "All year"}
    ]
    
    print("\nTesting schedule parsing:")
    try:
        normalized_schedule = parse_booking_schedule(test_schedule)
        print(f"  ✅ Parsed {len(normalized_schedule)} schedule entries")
        for entry in normalized_schedule:
            print(f"    - {entry['Day']} {entry['Time']}: {entry['Notes']}")
    except Exception as e:
        print(f"  ❌ Schedule parsing error: {e}")
    
    # Test validation
    print("\nTesting schedule validation:")
    is_valid, issues = validate_schedule_data(normalized_schedule)
    if is_valid:
        print("  ✅ Schedule validation passed")
    else:
        print("  ❌ Schedule validation issues:")
        for issue in issues:
            print(f"    - {issue}")
    
    print("\n🎉 Robust parser tests completed!")

if __name__ == "__main__":
    test_robust_parser()
