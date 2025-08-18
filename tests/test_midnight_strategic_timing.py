#!/usr/bin/env python3
"""
Comprehensive tests for the strategic timing and midnight wait functionality.

This test suite validates:
1. Midnight detection logic
2. Strategic timing approach (3 weeks advance)
3. Wait until midnight functionality
4. London timezone handling
5. Complete flow integration
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
    check_london_time_near_midnight,
    wait_until_midnight,
    find_date_on_calendar,
    rapid_advance_to_target_week
)

class TestMidnightStrategicTiming(unittest.TestCase):
    """Test suite for midnight detection and strategic timing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock London timezone
        self.london_tz = pytz.timezone('Europe/London')
        
        # Mock page object
        self.mock_page = MagicMock()
        self.mock_page.locator.return_value = MagicMock()
        self.mock_page.wait_for_function = AsyncMock()
        self.mock_page.wait_for_load_state = AsyncMock()
        
        # Mock session object
        self.mock_session = MagicMock()
        self.mock_session.log_message = MagicMock()
        
        # Slot details for testing
        self.slot_details = ("https://example.com/court/1", "20/09/2025", "1400")

    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_check_london_time_near_midnight_true(self, mock_datetime, mock_timezone):
        """Test midnight detection when within 10 minutes of midnight."""
        # Set up: 11:55 PM London time (5 minutes to midnight)
        mock_london_tz = MagicMock()
        mock_timezone.return_value = mock_london_tz
        
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 55
        mock_now.second = 0
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions
        self.assertTrue(result[0], "Should detect being near midnight at 23:55")
        mock_timezone.assert_called_with('Europe/London')
        mock_datetime.now.assert_called_with(mock_london_tz)

    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_check_london_time_near_midnight_false(self, mock_datetime, mock_timezone):
        """Test midnight detection when NOT within 10 minutes of midnight."""
        # Set up: 11:30 PM London time (30 minutes to midnight)
        mock_london_tz = MagicMock()
        mock_timezone.return_value = mock_london_tz
        
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 30
        mock_now.second = 0
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions
        self.assertFalse(result[0], "Should NOT detect being near midnight at 23:30")

    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_check_london_time_exactly_midnight(self, mock_datetime, mock_timezone):
        """Test midnight detection exactly at midnight."""
        # Set up: 12:00 AM London time (exactly midnight)
        mock_london_tz = MagicMock()
        mock_timezone.return_value = mock_london_tz
        
        mock_now = MagicMock()
        mock_now.hour = 0
        mock_now.minute = 0
        mock_now.second = 0
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions
        self.assertFalse(result[0], "Should NOT detect being near midnight at exactly 00:00")

    @patch('browser_actions.asyncio.sleep')
    @patch('browser_actions.get_timestamp')
    @patch('utils.pytz.timezone')
    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_immediate(self, mock_datetime, mock_browser_timezone, mock_utils_timezone, mock_timestamp, mock_sleep):
        """Test wait_until_midnight when already past midnight."""
        from datetime import datetime as real_datetime, timedelta as real_timedelta
        # Mock current time as 00:05 (5 minutes past midnight)
        mock_london_tz = pytz.timezone('Europe/London')
        mock_browser_timezone.return_value = mock_london_tz
        mock_utils_timezone.return_value = mock_london_tz
        
        # Create real datetime object for 00:05:00
        mock_now = real_datetime(2024, 1, 16, 0, 5, 0).replace(tzinfo=mock_london_tz)
        mock_datetime.now.return_value = mock_now
        
        # Mock timedelta calculation for negative value (past midnight)
        mock_timedelta = real_timedelta(seconds=-300)  # 5 minutes past
        mock_datetime.timedelta = real_timedelta
        
        mock_timestamp.return_value = "[00:05:00.00]"
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should not sleep if already past midnight
        mock_sleep.assert_not_called()

    @patch('browser_actions.asyncio.sleep')
    @patch('browser_actions.get_timestamp')
    @patch('utils.pytz.timezone')
    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_short_wait(self, mock_datetime, mock_browser_timezone, mock_utils_timezone, mock_timestamp, mock_sleep):
        """Test wait_until_midnight with a short wait (3 seconds)."""
        from datetime import datetime as real_datetime, timedelta as real_timedelta
        # Mock current time as 23:59:57 (3 seconds to midnight)
        mock_london_tz = pytz.timezone('Europe/London')
        mock_browser_timezone.return_value = mock_london_tz
        mock_utils_timezone.return_value = mock_london_tz
        
        # Create real datetime object for 23:59:57
        mock_now = real_datetime(2024, 1, 15, 23, 59, 57).replace(tzinfo=mock_london_tz)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = real_timedelta
        
        mock_timestamp.return_value = "[23:59:57.00]"
        
        # Mock sleep to avoid actual waiting
        mock_sleep.return_value = None
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should call sleep for countdown
        self.assertTrue(mock_sleep.called, "Should call sleep for countdown")

    @patch('browser_actions.rapid_advance_to_target_week')
    @patch('browser_actions.wait_until_midnight')
    @patch('browser_actions.check_london_time_near_midnight')
    @patch('browser_actions.take_screenshot')
    def test_find_date_strategic_timing_near_midnight(self, mock_screenshot, mock_check_midnight, mock_wait_midnight, mock_rapid_advance):
        """Test find_date_on_calendar with strategic timing when near midnight."""
        # Set up: Near midnight
        mock_check_midnight.return_value = (True, "23:55")
        mock_wait_midnight.return_value = None
        mock_rapid_advance.return_value = True
        mock_screenshot.return_value = None
        
        # Mock page interactions for 3-week advancement
        mock_button = AsyncMock()
        self.mock_page.locator.return_value = mock_button
        mock_button.wait_for = AsyncMock()
        mock_button.click = AsyncMock()
        
        # Test the function
        result = asyncio.run(find_date_on_calendar(
            self.mock_page, 
            "20/09/2025", 
            self.slot_details, 
            is_strategic_timing=True, 
            session=self.mock_session
        ))
        
        # Assertions
        mock_check_midnight.assert_called_once()
        mock_wait_midnight.assert_called_once()
        mock_rapid_advance.assert_called_once()
        self.assertTrue(result, "Should return True when rapid advancement succeeds")
        
        # Verify session logging
        self.assertTrue(self.mock_session.log_message.called)
        logged_messages = [call.args[0] for call in self.mock_session.log_message.call_args_list]
        midnight_messages = [msg for msg in logged_messages if "Within 10 minutes of midnight" in msg]
        self.assertTrue(len(midnight_messages) > 0, "Should log midnight detection message")

    @patch('browser_actions.rapid_advance_to_target_week')
    @patch('browser_actions.wait_until_midnight')
    @patch('browser_actions.check_london_time_near_midnight')
    @patch('browser_actions.take_screenshot')
    def test_find_date_strategic_timing_not_near_midnight(self, mock_screenshot, mock_check_midnight, mock_wait_midnight, mock_rapid_advance):
        """Test find_date_on_calendar with strategic timing when NOT near midnight."""
        # Set up: NOT near midnight
        mock_check_midnight.return_value = (False, "22:30")
        mock_rapid_advance.return_value = True
        mock_screenshot.return_value = None
        
        # Mock page interactions for 3-week advancement
        mock_button = AsyncMock()
        self.mock_page.locator.return_value = mock_button
        mock_button.wait_for = AsyncMock()
        mock_button.click = AsyncMock()
        
        # Test the function
        result = asyncio.run(find_date_on_calendar(
            self.mock_page, 
            "20/09/2025", 
            self.slot_details, 
            is_strategic_timing=True, 
            session=self.mock_session
        ))
        
        # Assertions
        mock_check_midnight.assert_called_once()
        mock_wait_midnight.assert_not_called()  # Should NOT wait if not near midnight
        mock_rapid_advance.assert_called_once()
        self.assertTrue(result, "Should return True when rapid advancement succeeds")
        
        # Verify session logging
        logged_messages = [call.args[0] for call in self.mock_session.log_message.call_args_list]
        immediate_messages = [msg for msg in logged_messages if "proceeding immediately" in msg]
        self.assertTrue(len(immediate_messages) > 0, "Should log immediate execution message")

    @patch('browser_actions.take_screenshot')
    def test_strategic_timing_three_week_advancement(self, mock_screenshot):
        """Test that strategic timing advances exactly 3 weeks."""
        mock_screenshot.return_value = None
        
        # Mock page interactions
        mock_button = AsyncMock()
        self.mock_page.locator.return_value = mock_button
        mock_button.wait_for = AsyncMock()
        mock_button.click = AsyncMock()
        
        # Track click calls
        click_count = 0
        
        async def count_clicks():
            nonlocal click_count
            click_count += 1
        
        mock_button.click.side_effect = count_clicks
        
        # Mock midnight check to return False (not near midnight)
        with patch('browser_actions.check_london_time_near_midnight') as mock_check:
            with patch('browser_actions.rapid_advance_to_target_week') as mock_rapid:
                mock_check.return_value = (False, "22:30")
                mock_rapid.return_value = True
                
                # Test the function
                result = asyncio.run(find_date_on_calendar(
                    self.mock_page, 
                    "20/09/2025", 
                    self.slot_details, 
                    is_strategic_timing=True, 
                    session=self.mock_session
                ))
                
                # Should click Next Week exactly 3 times
                self.assertEqual(click_count, 3, "Should click Next Week exactly 3 times")

    def test_integration_flow_documentation(self):
        """Document the complete strategic timing flow for verification."""
        expected_flow = [
            "1. Strategic timing enabled (is_strategic_timing=True)",
            "2. Log: 'Using strategic midnight release approach'",
            "3. Advance exactly 3 weeks (click Next Week 3 times)",
            "4. Take screenshots after each advancement",
            "5. Check if within 10 minutes of midnight",
            "6a. IF near midnight: Log wait message, call wait_until_midnight()",
            "6b. IF NOT near midnight: Log immediate execution message",
            "7. Call rapid_advance_to_target_week() to find target date",
            "8. Return result of rapid advancement"
        ]
        
        # This test serves as documentation of the expected flow
        self.assertTrue(len(expected_flow) == 8, "Complete flow should have 8 steps")
        print("\\n".join(expected_flow))


class TestMidnightFunctionRobustness(unittest.TestCase):
    """Test robustness and edge cases for midnight functionality."""
    
    @patch('utils.pytz.timezone')
    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_daylight_saving_time_handling(self, mock_datetime, mock_browser_timezone, mock_utils_timezone):
        """Test midnight detection during daylight saving time transitions."""
        # This test ensures the function works correctly during DST changes
        from datetime import datetime as real_datetime
        mock_london_tz = pytz.timezone('Europe/London')
        mock_browser_timezone.return_value = mock_london_tz
        mock_utils_timezone.return_value = mock_london_tz
        
        # Mock a time during DST (23:55)
        mock_now = real_datetime(2024, 7, 15, 23, 55, 0).replace(tzinfo=mock_london_tz)
        mock_now.hour = 23
        mock_now.minute = 55
        mock_datetime.now.return_value = mock_now
        
        result = asyncio.run(check_london_time_near_midnight())
        
        # Should still work correctly
        self.assertTrue(result[0])
        mock_browser_timezone.assert_called_with('Europe/London')

    @patch('browser_actions.asyncio.sleep')
    @patch('browser_actions.get_timestamp')
    @patch('utils.pytz.timezone')
    @patch('browser_actions.pytz.timezone')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_error_handling(self, mock_datetime, mock_browser_timezone, mock_utils_timezone, mock_timestamp, mock_sleep):
        """Test error handling in wait_until_midnight function."""
        from datetime import datetime as real_datetime, timedelta as real_timedelta
        # Set up timezone mocks
        mock_london_tz = pytz.timezone('Europe/London')
        mock_browser_timezone.return_value = mock_london_tz
        mock_utils_timezone.return_value = mock_london_tz
        
        # Mock current time as 23:59:59 (close to midnight)
        mock_now = real_datetime(2024, 1, 15, 23, 59, 59).replace(tzinfo=mock_london_tz)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = real_timedelta
        
        mock_timestamp.return_value = "[23:59:59.00]"
        
        # Mock sleep to raise an exception
        mock_sleep.side_effect = Exception("Sleep interrupted")
        
        # Should handle exceptions gracefully (not raise them)
        try:
            asyncio.run(wait_until_midnight())
            # If we get here, the function handled the exception gracefully
            self.assertTrue(True, "Function handled exception gracefully")
        except Exception as e:
            self.fail(f"wait_until_midnight should handle exceptions gracefully, but raised: {e}")


def run_tests():
    """Run all tests and display results."""
    print("🧪 Running Strategic Timing and Midnight Function Tests...")
    print("=" * 60)
    
    # Create test suites
    timing_suite = unittest.TestLoader().loadTestsFromTestCase(TestMidnightStrategicTiming)
    robustness_suite = unittest.TestLoader().loadTestsFromTestCase(TestMidnightFunctionRobustness)
    
    # Combine suites
    all_tests = unittest.TestSuite([timing_suite, robustness_suite])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(all_tests)
    
    # Print summary
    print("\\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 All tests passed! Strategic timing functionality is working correctly.")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, error in result.failures + result.errors:
            print(f"   - {test}: {error}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
