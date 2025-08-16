#!/usr/bin/env python3
"""
Demo script to show how session logging and screenshot tracking works.
This script simulates a booking session with logs and screenshots.
"""

import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from multi_session_manager import BookingSession
from utils import get_timestamp

def demo_session_logging():
    """Demonstrate session logging and screenshot tracking."""
    
    print(f"{get_timestamp()} === Session Logging Demo ===\n")
    
    # Create a demo session
    session = BookingSession(
        account_name="Demo User",
        email="demo@example.com", 
        password="demo_password",
        court_number="Court 1",
        court_url="https://example.com/court1",
        sheets_manager=None  # Mock for demo
    )
    
    print(f"{get_timestamp()} 🎬 Starting demo session logging...\n")
    
    # Simulate some session activity with logs
    session.log_message(f"{get_timestamp()} --- Demo Session Started ---")
    session.log_message(f"{get_timestamp()} ✅ Browser initialized successfully")
    session.log_message(f"{get_timestamp()} 🔑 Logging in to Demo Account...")
    session.log_message(f"{get_timestamp()} ✅ Login successful for demo@example.com")
    session.log_message(f"{get_timestamp()} 🏟️ Navigating to Court 1...")
    
    # Simulate some screenshots being taken
    session.add_screenshot("screenshots/demo_login.png", "Login page screenshot")
    session.add_screenshot("screenshots/demo_court_page.png", "Court booking page")
    session.add_screenshot("screenshots/demo_basket.png", "Basket confirmation")
    
    session.log_message(f"{get_timestamp()} 📸 Screenshot taken: Login page")
    session.log_message(f"{get_timestamp()} 🎯 Attempting to book slot: 19/02/2024 at 1800")
    session.log_message(f"{get_timestamp()} 📸 Screenshot taken: Court booking page")
    session.log_message(f"{get_timestamp()} ✅ Slot successfully added to basket")
    session.log_message(f"{get_timestamp()} 📸 Screenshot taken: Basket confirmation")
    session.log_message(f"{get_timestamp()} 💳 Processing payment...")
    session.log_message(f"{get_timestamp()} ✅ Payment successful - booking confirmed!")
    session.log_message(f"{get_timestamp()} --- Demo Session Completed ---")
    
    print(f"{get_timestamp()} 📊 Demo Results:")
    print(f"{get_timestamp()}   Session Logs: {len(session.session_logs)} entries")
    print(f"{get_timestamp()}   Screenshots: {len(session.screenshots_taken)} files")
    print()
    
    print(f"{get_timestamp()} 📝 Sample Terminal Logs:")
    print("=" * 60)
    for i, log_entry in enumerate(session.session_logs[:5], 1):  # Show first 5 entries
        print(f"{i}. {log_entry}")
    if len(session.session_logs) > 5:
        print(f"... and {len(session.session_logs) - 5} more log entries")
    print("=" * 60)
    print()
    
    print(f"{get_timestamp()} 📸 Sample Screenshot Details:")
    print("-" * 60)
    for i, screenshot in enumerate(session.screenshots_taken, 1):
        print(f"{i}. {screenshot['timestamp']} - {screenshot['description']}")
        print(f"   File: {screenshot['path']}")
    print("-" * 60)
    print()
    
    # Simulate what would be included in the IT email
    print(f"{get_timestamp()} 📧 Email Content Preview:")
    print("=" * 80)
    print("Subject: Tennis Court Booking Session - Demo User - 15/01/2024")
    print()
    print("🎾 Tennis Court Booking Session Report")
    print()
    print("📅 Date: 15/01/2024 (Monday)")
    print("👤 Account: Demo User")
    print("📧 Email: demo@example.com")
    print("🏟️ Court: Court 1")
    print()
    print(f"📸 Screenshots Taken: {len(session.screenshots_taken)}")
    print("📸 Screenshot Details:")
    for i, screenshot in enumerate(session.screenshots_taken, 1):
        print(f"   {i}. {screenshot['timestamp']} - {screenshot['description']}")
        print(f"      File: {screenshot['path']}")
    print()
    print(f"📝 Complete Terminal Logs: {len(session.session_logs)} entries")
    print("📝 Full Terminal Output:")
    print("=" * 80)
    for log_entry in session.session_logs:
        print(log_entry)
    print("=" * 80)
    print()
    print("This is an automated session report from the Tennis Court Booking System.")
    print("Complete terminal logs and screenshot details are included above for debugging.")
    print("=" * 80)
    
    print(f"\n{get_timestamp()} ✅ Session logging demo completed!")
    print(f"{get_timestamp()} 💡 The IT emails will now contain:")
    print(f"{get_timestamp()}   - Complete terminal output with timestamps")
    print(f"{get_timestamp()}   - All screenshots taken during the booking process")
    print(f"{get_timestamp()}   - File paths for easy access to screenshots")
    print(f"{get_timestamp()}   - Detailed debugging information")

if __name__ == "__main__":
    demo_session_logging()
