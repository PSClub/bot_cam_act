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
        """Test countdown logging for 5 seconds."""
        with patch('asyncio.sleep') as mock_sleep:
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
    
    async def test_optimized_countdown_logging_15_seconds(self):
        """Test countdown logging for 15 seconds."""
        with patch('asyncio.sleep') as mock_sleep:
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
