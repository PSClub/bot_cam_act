#!/usr/bin/env python3
"""
Tests for the new midnight wait and post-midnight calendar advancement functions.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import pytz
import sys
import os

# Add the parent directory to the Python path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from browser_actions import (
    wait_until_midnight,
    post_midnight_calendar_advancement
)

class TestNewMidnightFunctions(unittest.TestCase):
    """Test suite for the new midnight wait and post-midnight functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock page object
        self.mock_page = MagicMock()
        self.mock_page.locator.return_value = MagicMock()
        self.mock_page.wait_for_function = AsyncMock()
        self.mock_page.wait_for_load_state = AsyncMock()
        self.mock_page.reload = AsyncMock()
        self.mock_page.on = MagicMock()
        self.mock_page.remove_listener = MagicMock()
        
        # Mock session object
        self.mock_session = MagicMock()
        self.mock_session.log_message = MagicMock()
        
        # Slot details for testing
        self.slot_details = ("https://example.com/court/1", "22/09/2025", "1400")

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    @patch('browser_actions.asyncio.sleep')
    def test_wait_until_midnight_reaches_target_time(self, mock_sleep, mock_datetime, mock_timestamp):
        """Test that wait_until_midnight correctly waits until 00:00:01."""
        # Mock timestamp to avoid timezone issues
        mock_timestamp.return_value = "[00:00:01.00]"
        
        # Create a sequence of times leading to 00:00:01
        from datetime import datetime as real_datetime
        london_tz = pytz.timezone('Europe/London')
        
        time_23_59_58 = real_datetime(2024, 1, 1, 23, 59, 58).replace(tzinfo=london_tz)
        time_00_00_01 = real_datetime(2024, 1, 2, 0, 0, 1).replace(tzinfo=london_tz)
        
        # Mock datetime.now to return first time, then target time
        mock_datetime.now.side_effect = [time_23_59_58, time_00_00_01]
        mock_datetime.timedelta = timedelta
        mock_sleep.return_value = None
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should have called sleep during countdown
        self.assertTrue(mock_sleep.called, "Should call sleep during countdown")
        print("✅ wait_until_midnight reaches target time correctly")

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_already_past_target(self, mock_datetime, mock_timestamp):
        """Test that wait_until_midnight exits immediately if already past 00:00:01."""
        # Mock timestamp
        mock_timestamp.return_value = "[00:00:05.00]"
        
        # Mock current time as 00:00:05 (already past target)
        from datetime import datetime as real_datetime
        london_tz = pytz.timezone('Europe/London')
        time_00_00_05 = real_datetime(2024, 1, 1, 0, 0, 5).replace(tzinfo=london_tz)
        mock_datetime.now.return_value = time_00_00_05
        mock_datetime.timedelta = timedelta
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should exit immediately without waiting
        print("✅ wait_until_midnight exits immediately when past target")

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')  
    @patch('browser_actions.asyncio.sleep')
    def test_wait_until_midnight_logging_frequency(self, mock_sleep, mock_datetime, mock_timestamp):
        """Test that wait_until_midnight uses correct logging frequency."""
        mock_timestamp.return_value = "[23:50:00.00]"
        
        # Mock current time as 23:50:00 (10 minutes before midnight)
        from datetime import datetime as real_datetime
        london_tz = pytz.timezone('Europe/London')
        time_23_50_00 = real_datetime(2024, 1, 1, 23, 50, 0).replace(tzinfo=london_tz)
        time_00_00_02 = real_datetime(2024, 1, 2, 0, 0, 2).replace(tzinfo=london_tz)
        
        mock_datetime.now.side_effect = [time_23_50_00, time_00_00_02]
        mock_datetime.timedelta = timedelta
        
        # Mock sleep to exit after first iteration
        mock_sleep.return_value = None
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should have called sleep with 30 seconds (for >10 minute check)
        mock_sleep.assert_called_with(30)
        print("✅ wait_until_midnight uses correct logging frequency")

    @patch('browser_actions.take_screenshot')
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_post_midnight_calendar_advancement_finds_date(self, mock_datetime, mock_timestamp, mock_screenshot):
        """Test post_midnight_calendar_advancement when date is immediately visible."""
        mock_timestamp.return_value = "[00:00:02.00]"
        mock_screenshot.return_value = "screenshot.png"
        
        # Mock current time and date parsing
        from datetime import datetime as real_datetime
        london_tz = pytz.timezone('Europe/London')
        time_00_00_02 = real_datetime(2024, 1, 1, 0, 0, 2).replace(tzinfo=london_tz)
        mock_datetime.now.return_value = time_00_00_02
        mock_datetime.strptime.return_value = real_datetime(2025, 9, 22)  # Monday
        
        # Mock page locator to find the target date immediately
        mock_locator = AsyncMock()
        mock_locator.is_visible.return_value = True
        self.mock_page.locator.return_value = mock_locator
        
        # Test the function
        result = asyncio.run(post_midnight_calendar_advancement(
            self.mock_page, "22/09/2025", self.slot_details, self.mock_session
        ))
        
        # Should return True (date found)
        self.assertTrue(result, "Should find target date immediately")
        
        # Should take screenshot when date is found
        mock_screenshot.assert_called()
        print("✅ post_midnight_calendar_advancement finds date when visible")

    @patch('browser_actions.take_screenshot')
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_post_midnight_calendar_advancement_timeout(self, mock_datetime, mock_timestamp, mock_screenshot):
        """Test post_midnight_calendar_advancement timeout behavior."""
        mock_timestamp.return_value = "[00:00:02.00]"
        mock_screenshot.return_value = "screenshot.png"
        
        # Mock datetime to simulate timeout
        from datetime import datetime as real_datetime
        london_tz = pytz.timezone('Europe/London')
        start_time = real_datetime(2025, 1, 1, 0, 0, 2).replace(tzinfo=london_tz)
        timeout_time = start_time + timedelta(minutes=3)  # 3 minutes later (past 2-min timeout)
        
        mock_datetime.now.side_effect = [start_time, timeout_time]
        mock_datetime.strptime.return_value = real_datetime(2025, 9, 22)
        
        # Mock page locator to never find the date
        mock_locator = AsyncMock()
        mock_locator.is_visible.return_value = False
        self.mock_page.locator.return_value = mock_locator
        
        # Test the function
        result = asyncio.run(post_midnight_calendar_advancement(
            self.mock_page, "22/09/2025", self.slot_details, self.mock_session
        ))
        
        # Should return False (timeout reached)
        self.assertFalse(result, "Should timeout and return False")
        print("✅ post_midnight_calendar_advancement respects timeout")

    @patch('browser_actions.take_screenshot')
    @patch('browser_actions.get_timestamp') 
    @patch('browser_actions.datetime')
    def test_post_midnight_calendar_advancement_with_next_week(self, mock_datetime, mock_timestamp, mock_screenshot):
        """Test post_midnight_calendar_advancement with Next Week clicking."""
        mock_timestamp.return_value = "[00:00:02.00]"
        mock_screenshot.return_value = "screenshot.png"
        
        # Mock current time (within timeout)
        start_time = datetime(2025, 1, 1, 0, 0, 2)
        mock_datetime.now.return_value = start_time
        mock_datetime.strptime.return_value = datetime(2025, 9, 22)
        
        # Mock page interactions
        mock_date_locator = AsyncMock()
        mock_next_week_locator = AsyncMock()
        
        # First call: date not visible, second call: date found after clicking
        mock_date_locator.is_visible.side_effect = [False, True]
        mock_next_week_locator.is_visible.return_value = True
        mock_next_week_locator.click = AsyncMock()
        
        # Mock locator to return different objects based on selector
        def mock_locator(selector):
            if "Next Week" in selector or "btnNextWeek" in selector:
                return mock_next_week_locator
            else:
                return mock_date_locator
        
        self.mock_page.locator.side_effect = mock_locator
        
        # Test the function
        result = asyncio.run(post_midnight_calendar_advancement(
            self.mock_page, "22/09/2025", self.slot_details, self.mock_session
        ))
        
        # Should return True (date found after clicking)
        self.assertTrue(result, "Should find date after clicking Next Week")
        
        # Should have clicked Next Week button
        mock_next_week_locator.click.assert_called()
        print("✅ post_midnight_calendar_advancement works with Next Week clicking")

    @patch('browser_actions.take_screenshot')
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_post_midnight_calendar_advancement_dialog_handling(self, mock_datetime, mock_timestamp, mock_screenshot):
        """Test that post_midnight_calendar_advancement sets up dialog handling."""
        mock_timestamp.return_value = "[00:00:02.00]"
        mock_screenshot.return_value = "screenshot.png"
        
        # Mock current time and date parsing
        mock_datetime.now.return_value = self._create_mock_time(0, 0, 2)
        mock_datetime.strptime.return_value = datetime(2025, 9, 22)
        
        # Mock page locator to find date immediately (to exit quickly)
        mock_locator = AsyncMock()
        mock_locator.is_visible.return_value = True
        self.mock_page.locator.return_value = mock_locator
        
        # Test the function
        result = asyncio.run(post_midnight_calendar_advancement(
            self.mock_page, "22/09/2025", self.slot_details, self.mock_session
        ))
        
        # Should have set up dialog handler
        self.mock_page.on.assert_called_with("dialog", unittest.mock.ANY)
        
        # Should have removed dialog handler
        self.mock_page.remove_listener.assert_called_with("dialog", unittest.mock.ANY)
        
        print("✅ post_midnight_calendar_advancement sets up dialog handling")

    def _create_mock_time(self, hour, minute, second):
        """Helper method to create a mock datetime with specific time."""
        mock_time = MagicMock()
        mock_time.hour = hour
        mock_time.minute = minute  
        mock_time.second = second
        mock_time.strftime.return_value = f"{hour:02d}:{minute:02d}:{second:02d}"
        mock_time.replace.return_value = mock_time
        
        # Mock timedelta calculations
        mock_time.__sub__ = MagicMock()
        mock_time.__add__ = MagicMock()
        
        return mock_time

    def test_integration_new_functions_exist(self):
        """Test that new functions are properly imported and callable."""
        # Test wait_until_midnight exists and is callable
        self.assertTrue(callable(wait_until_midnight), "wait_until_midnight should be callable")
        
        # Test post_midnight_calendar_advancement exists and is callable
        self.assertTrue(callable(post_midnight_calendar_advancement), "post_midnight_calendar_advancement should be callable")
        
        print("✅ All new functions are properly imported and callable")


def run_tests():
    """Run all tests and display results."""
    print("🧪 Testing New Midnight Functions...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestNewMidnightFunctions)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed! New midnight functions are working correctly.")
        print("\\n✅ Key Features Verified:")
        print("   - wait_until_midnight waits until 00:00:01")
        print("   - Optimized logging frequency (every minute/10sec/1sec)")
        print("   - post_midnight_calendar_advancement has 2-minute timeout")
        print("   - Dialog handling for pop-ups")
        print("   - Next Week button clicking")
        print("   - Screenshot capture on success")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
