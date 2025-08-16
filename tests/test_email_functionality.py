#!/usr/bin/env python3
"""
Test script for email functionality.
This script helps verify that the email system is working correctly.
"""

import os
import sys
import asyncio

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import get_timestamp

async def test_email_configuration():
    """Test email configuration and functionality."""
    
    print(f"{get_timestamp()} === Testing Email Configuration ===\n")
    
    # Check email environment variables
    from config import (
        SENDER_EMAIL, GMAIL_APP_PASSWORD, 
        RECIPIENT_KYLE, RECIPIENT_INFO, IT_EMAIL_ADDRESS
    )
    
    print(f"{get_timestamp()} 📧 Email Configuration Check:")
    print(f"{get_timestamp()}   SENDER_EMAIL (KYLE_EMAIL_ADDRESS): {'✅ Set' if SENDER_EMAIL else '❌ Not Set'}")
    print(f"{get_timestamp()}   GMAIL_APP_PASSWORD: {'✅ Set' if GMAIL_APP_PASSWORD else '❌ Not Set'}")
    print(f"{get_timestamp()}   RECIPIENT_KYLE: {'✅ Set' if RECIPIENT_KYLE else '❌ Not Set'}")
    print(f"{get_timestamp()}   RECIPIENT_INFO: {'✅ Set' if RECIPIENT_INFO else '❌ Not Set'}")
    print(f"{get_timestamp()}   IT_EMAIL_ADDRESS: {'✅ Set' if IT_EMAIL_ADDRESS else '❌ Not Set'}")
    print()
    
    if not SENDER_EMAIL:
        print(f"{get_timestamp()} ❌ SENDER_EMAIL not configured. Set KYLE_EMAIL_ADDRESS environment variable.")
        return False
    
    if not GMAIL_APP_PASSWORD:
        print(f"{get_timestamp()} ❌ GMAIL_APP_PASSWORD not configured.")
        print(f"{get_timestamp()} 💡 To fix:")
        print(f"{get_timestamp()}   1. Go to Gmail settings")
        print(f"{get_timestamp()}   2. Enable 2-factor authentication")
        print(f"{get_timestamp()}   3. Generate an App Password")
        print(f"{get_timestamp()}   4. Set GMAIL_APP_PASSWORD environment variable")
        return False
    
    # Test basic email sending
    print(f"{get_timestamp()} 🧪 Testing email sending functionality...")
    
    try:
        from booking_orchestrator import BookingOrchestrator
        
        # Create a minimal orchestrator for testing
        orchestrator = BookingOrchestrator()
        
        # Test email content
        test_subject = "Tennis Booking System - Email Test"
        test_body = f"""
🎾 Tennis Court Booking System - Email Test

📅 Date: Test Date
⏰ Time: {orchestrator.get_current_london_time()}

This is a test email to verify the email system is working correctly.

📧 Email Configuration:
✅ Sender: {SENDER_EMAIL}
✅ SMTP: Gmail (smtp.gmail.com:587)
✅ Authentication: App Password

If you receive this email, the system is configured correctly!

🎯 Expected Email Flow:
1. Individual Session Emails → IT_EMAIL_ADDRESS ({IT_EMAIL_ADDRESS or 'Not Set'})
   - One email per court (3 total)
   - Detailed logs for each session
   
2. Summary Email → INFO_EMAIL_ADDRESS + KYLE_EMAIL_ADDRESS
   - One combined email
   - Slot-by-slot table
   - Recent log entries

This is an automated test from the Tennis Court Booking System.
        """.strip()
        
        # Send test email to the sender (self-test)
        test_recipient = SENDER_EMAIL
        print(f"{get_timestamp()}   📧 Sending test email to {test_recipient}...")
        
        await orchestrator.send_email(
            SENDER_EMAIL, 
            test_recipient, 
            test_subject, 
            test_body, 
            GMAIL_APP_PASSWORD
        )
        
        print(f"{get_timestamp()} ✅ Test email sent successfully!")
        print(f"{get_timestamp()} 📨 Check your email at {test_recipient}")
        
        return True
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error sending test email: {e}")
        import traceback
        print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
        return False

async def main():
    """Main function to run the email test."""
    
    print(f"{get_timestamp()} Tennis Court Booking - Email Test")
    print(f"{get_timestamp()}" + "=" * 50)
    print()
    
    success = await test_email_configuration()
    
    if success:
        print(f"\n{get_timestamp()} ✅ Email test completed successfully!")
        print(f"{get_timestamp()} 💡 The system should now be able to send booking emails correctly.")
        
        print(f"\n{get_timestamp()} 📋 Expected Email Behavior:")
        print(f"{get_timestamp()}   1. Individual Session Emails (3 emails):")
        print(f"{get_timestamp()}      → To: IT_EMAIL_ADDRESS")
        print(f"{get_timestamp()}      → Content: Detailed session info per court")
        print(f"{get_timestamp()}      → One email each for Mother, Father, Bruce")
        
        print(f"{get_timestamp()}   2. Summary Email (1 email):")
        print(f"{get_timestamp()}      → To: INFO_EMAIL_ADDRESS + KYLE_EMAIL_ADDRESS")
        print(f"{get_timestamp()}      → Content: Slot-by-slot table + recent logs")
        print(f"{get_timestamp()}      → Combined summary for all courts")
        
        print(f"\n{get_timestamp()} 📋 NEW: Enhanced IT Email Content:")
        print(f"{get_timestamp()}   ✅ Complete terminal logs with timestamps")
        print(f"{get_timestamp()}   ✅ All screenshots taken during booking process")
        print(f"{get_timestamp()}   ✅ Screenshot file paths and descriptions")
        print(f"{get_timestamp()}   ✅ Detailed session information for debugging")
        
    else:
        print(f"\n{get_timestamp()} ❌ Email test failed!")
        print(f"{get_timestamp()} 🔧 Please fix the configuration issues above.")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
