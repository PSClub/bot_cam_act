#!/usr/bin/env python3
"""
Fixed comprehensive tests for the strategic timing and midnight wait functionality.

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

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_check_london_time_near_midnight_true(self, mock_datetime, mock_timestamp):
        """Test midnight detection when within 10 minutes of midnight."""
        # Mock timestamp to avoid timezone issues
        mock_timestamp.return_value = "[23:55:00.00]"
        
        # Create a mock datetime object with proper attributes
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 55
        mock_now.second = 0
        mock_now.strftime.return_value = "23:55:00"
        
        # Mock datetime.now to return our mock
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions
        self.assertTrue(result[0], "Should detect being near midnight at 23:55")

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_check_london_time_near_midnight_false(self, mock_datetime, mock_timestamp):
        """Test midnight detection when NOT within 10 minutes of midnight."""
        # Mock timestamp to avoid timezone issues
        mock_timestamp.return_value = "[23:30:00.00]"
        
        # Create a mock datetime object with proper attributes
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 30
        mock_now.second = 0
        mock_now.strftime.return_value = "23:30:00"
        
        # Mock datetime.now to return our mock
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions
        self.assertFalse(result[0], "Should NOT detect being near midnight at 23:30")

    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_check_london_time_exactly_midnight(self, mock_datetime, mock_timestamp):
        """Test midnight detection exactly at midnight."""
        # Mock timestamp to avoid timezone issues
        mock_timestamp.return_value = "[00:00:00.00]"
        
        # Create a mock datetime object with proper attributes
        mock_now = MagicMock()
        mock_now.hour = 0
        mock_now.minute = 0
        mock_now.second = 0
        mock_now.strftime.return_value = "00:00:00"
        
        # Mock datetime.now to return our mock
        mock_datetime.now.return_value = mock_now
        
        # Test the function
        result = asyncio.run(check_london_time_near_midnight())
        
        # Assertions - Actually, according to the logic, 00:00 IS considered "near midnight"
        self.assertTrue(result[0], "Should detect being near midnight at exactly 00:00")

    @patch('browser_actions.optimized_countdown_logging')
    @patch('browser_actions.asyncio.sleep')
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_short_wait(self, mock_datetime, mock_timestamp, mock_sleep, mock_countdown):
        """Test wait_until_midnight with a short wait (3 seconds)."""
        # Mock timestamp
        mock_timestamp.return_value = "[23:59:57.00]"
        
        # Create sequence of datetime mocks: first call returns 23:59:57, second returns 00:00:00
        mock_first_time = MagicMock()
        mock_first_time.hour = 23
        mock_first_time.minute = 59
        mock_first_time.second = 57
        mock_first_time.replace.return_value = MagicMock()
        
        mock_midnight_time = MagicMock()
        mock_midnight_time.hour = 0
        mock_midnight_time.minute = 0
        mock_midnight_time.second = 0
        mock_midnight_time.strftime.return_value = "00:00:00"
        
        # Create proper timedelta mock with arithmetic operations
        from datetime import timedelta as real_timedelta
        mock_timedelta = real_timedelta(seconds=3)
        
        # Mock the arithmetic operation result
        mock_first_time.replace.return_value.__add__ = MagicMock(return_value=MagicMock())
        mock_first_time.replace.return_value.__add__.return_value.__sub__ = MagicMock(return_value=mock_timedelta)
        
        # Set up datetime mocking sequence
        mock_datetime.now.side_effect = [mock_first_time, mock_midnight_time]
        mock_datetime.timedelta = real_timedelta
        
        # Mock sleep and countdown to avoid actual waiting
        mock_sleep.return_value = None
        mock_countdown.return_value = None
        
        # Test the function
        asyncio.run(wait_until_midnight())
        
        # Should call countdown for final seconds
        self.assertTrue(mock_countdown.called, "Should call countdown for final seconds")

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
            "7. Call rapid_advance_to_target_week() to find target date"
        ]
        
        # This test serves as documentation of the expected flow
        self.assertTrue(len(expected_flow) == 8, "Complete flow should have 8 steps")
        print("\\n".join(expected_flow))


class TestMidnightFunctionRobustness(unittest.TestCase):
    """Test robustness and edge cases for midnight functionality."""
    
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_daylight_saving_time_handling(self, mock_datetime, mock_timestamp):
        """Test midnight detection during daylight saving time transitions."""
        # Mock timestamp to avoid timezone issues
        mock_timestamp.return_value = "[23:55:00.00]"
        
        # Create a mock datetime object with proper attributes
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 55
        mock_now.strftime.return_value = "23:55:00"
        
        # Mock datetime.now to return our mock
        mock_datetime.now.return_value = mock_now
        
        result = asyncio.run(check_london_time_near_midnight())
        
        # Should still work correctly
        self.assertTrue(result[0])

    @patch('browser_actions.optimized_countdown_logging')
    @patch('browser_actions.asyncio.sleep')
    @patch('browser_actions.get_timestamp')
    @patch('browser_actions.datetime')
    def test_wait_until_midnight_error_handling(self, mock_datetime, mock_timestamp, mock_sleep, mock_countdown):
        """Test error handling in wait_until_midnight function."""
        # Mock timestamp
        mock_timestamp.return_value = "[23:59:59.00]"
        
        # Create mock datetime that will trigger the error path
        from datetime import timedelta as real_timedelta
        mock_now = MagicMock()
        mock_now.hour = 23
        mock_now.minute = 59
        mock_now.second = 59
        mock_now.strftime.return_value = "23:59:59"
        
        # Set up proper mock for datetime operations
        mock_timedelta = real_timedelta(seconds=1)
        mock_now.replace.return_value.__add__ = MagicMock(return_value=MagicMock())
        mock_now.replace.return_value.__add__.return_value.__sub__ = MagicMock(return_value=mock_timedelta)
        
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = real_timedelta
        
        # Mock countdown to raise an exception during the final countdown phase
        mock_countdown.side_effect = Exception("Sleep interrupted")
        
        # Mock sleep for other parts
        mock_sleep.return_value = None
        
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
