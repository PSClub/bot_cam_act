# test_midnight_function.py
# Tests for the wait_until_midnight function in browser_actions.py

import asyncio
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import browser_actions
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_actions import optimized_countdown_logging
from utils import get_timestamp


class TestMidnightFunction:
    """Test class for midnight-related functions."""
    
    async def test_optimized_countdown_logging_5_seconds(self):
        """Test countdown logging for 5 seconds and verify output messages."""
        with patch('asyncio.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            # Mock the function to return after each sleep call
            call_count = 0
            def mock_sleep_side_effect(seconds):
                nonlocal call_count
                call_count += 1
                if call_count >= 5:  # Stop after 5 calls
                    raise asyncio.CancelledError()
                return None
            
            mock_sleep.side_effect = mock_sleep_side_effect
            
            try:
                await optimized_countdown_logging(5)
            except asyncio.CancelledError:
                pass
            
            # Should sleep 5 times for 1 second each
            assert mock_sleep.call_count == 5
            for call in mock_sleep.call_args_list:
                assert call == ((1,),)
            
            # Verify countdown messages were printed
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            countdown_messages = [msg for msg in print_calls if '⏰' in msg and 'remaining' in msg]
            
            # Should have 5 countdown messages (5, 4, 3, 2, 1 seconds)
            assert len(countdown_messages) == 5
            
            # Verify countdown sequence
            expected_counts = ['5 seconds', '4 seconds', '3 seconds', '2 seconds', '1 second']
            for i, expected in enumerate(expected_counts):
                assert expected in countdown_messages[i]
    
    async def test_optimized_countdown_logging_15_seconds(self):
        """Test countdown logging for 15 seconds and verify message content."""
        with patch('asyncio.sleep') as mock_sleep, \
             patch('builtins.print') as mock_print:
            
            # Mock the function to return after each sleep call  
            call_count = 0
            def mock_sleep_side_effect(seconds):
                nonlocal call_count
                call_count += 1
                if call_count >= 6:  # Stop after 6 calls (1x10s + 5x1s)
                    raise asyncio.CancelledError()
                return None
            
            mock_sleep.side_effect = mock_sleep_side_effect
            
            try:
                await optimized_countdown_logging(15)
            except asyncio.CancelledError:
                pass
            
            # Should have multiple sleep calls - exact count may vary due to timing logic
            assert mock_sleep.call_count >= 5  # At least the final 5 second-by-second calls
            assert mock_sleep.call_count <= 7   # But not more than expected maximum
            
            # Last 5 calls should be 1 second each (final countdown)
            final_calls = mock_sleep.call_args_list[-5:]
            for call in final_calls:
                assert call == ((1,),)
            
            # Verify countdown messages structure
            print_calls = [call.args[0] for call in mock_print.call_args_list]
            countdown_messages = [msg for msg in print_calls if '⏰' in msg and 'remaining' in msg]
            
            # Should have initial 10-second countdown and final 1-second countdowns
            assert len(countdown_messages) >= 5  # At least final 5 countdown messages
            
            # Check that final countdown messages are present
            final_countdown_msgs = [msg for msg in countdown_messages if any(num in msg for num in ['5 seconds', '4 seconds', '3 seconds', '2 seconds', '1 second'])]
            assert len(final_countdown_msgs) >= 5


async def run_tests():
    """Run all tests."""
    print(f"{get_timestamp()} 🧪 Running Midnight Function Tests...")
    
    test_class = TestMidnightFunction()
    
    # Test countdown logging
    print(f"{get_timestamp()}   Testing countdown logging...")
    await test_class.test_optimized_countdown_logging_5_seconds()
    await test_class.test_optimized_countdown_logging_15_seconds()
    
    print(f"{get_timestamp()} ✅ All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(run_tests())
