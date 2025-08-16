# run_tests.py
# Simple test runner for the midnight function tests

import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_midnight_function import run_tests
from utils import get_timestamp

async def main():
    """Main test runner."""
    try:
        print(f"{get_timestamp()} 🚀 Starting Test Suite...")
        await run_tests()
        print(f"{get_timestamp()} 🎉 All tests passed!")
        return 0
    except Exception as e:
        print(f"{get_timestamp()} ❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
