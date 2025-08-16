#!/usr/bin/env python3
"""
Multi-Court Tennis Booking Bot for Camden Active
This script automates the booking of multiple tennis courts at Lincoln's Inn Fields.
"""

import argparse
import asyncio
import os
import sys
from booking_orchestrator import main as booking_main
from utils import get_timestamp

async def main(headless=True):
    """Main function to run the multi-court booking system."""
    try:
        print(f"{get_timestamp()} 🎾 Multi-Court Tennis Booking System")
        print(f"{get_timestamp()} ======================================")
        print(f"{get_timestamp()} Browser mode: {'Headless' if headless else 'Visible'}")
        
        # Set environment variable for headless mode
        os.environ['HEADLESS_MODE'] = str(headless)
        
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Multi-Court Tennis Booking Bot for Camden Active')
    parser.add_argument('--headless', action='store_true', default=True,
                       help='Run browser in headless mode (default: True)')
    parser.add_argument('--no-headless', dest='headless', action='store_false',
                       help='Run browser in visible mode')
    
    args = parser.parse_args()
    
    # Run the async main function
    success = asyncio.run(main(headless=args.headless))
    
    if success:
        print(f"{get_timestamp()} 🎉 Multi-court booking system completed successfully")
        sys.exit(0)
    else:
        print(f"{get_timestamp()} ❌ Multi-court booking system failed")
        sys.exit(1)
