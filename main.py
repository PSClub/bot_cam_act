#!/usr/bin/env python3
"""
Multi-Court Tennis Booking Bot for Camden Active
This script automates the booking of multiple tennis courts at Lincoln's Inn Fields.
"""

import asyncio
import os
import sys
from booking_orchestrator import main as booking_main

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds in London UK timezone."""
    from datetime import datetime
    import pytz
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return f"[{london_time.strftime('%H:%M:%S.%f')[:-4]}]"

async def main():
    """Main function to run the multi-court booking system."""
    try:
        print(f"{get_timestamp()} 🎾 Multi-Court Tennis Booking System")
        print(f"{get_timestamp()} ======================================")
        
        # Run the booking orchestrator
        success = await booking_main()
        
        if success:
            print(f"{get_timestamp()} 🎉 Multi-court booking system completed successfully")
            return True
        else:
            print(f"{get_timestamp()} ⚠️ Multi-court booking system completed with issues")
            return False
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Fatal error in main process: {e}")
        return False

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    
    if success:
        print(f"{get_timestamp()} 🎉 Multi-court booking system completed successfully")
        sys.exit(0)
    else:
        print(f"{get_timestamp()} ❌ Multi-court booking system failed")
        sys.exit(1)
