# booking_orchestrator.py
# This file orchestrates the entire multi-court booking process

import asyncio
import os
import pytz
from datetime import datetime, timedelta
from sheets_manager import SheetsManager
from multi_session_manager import MultiSessionManager
from robust_parser import normalize_day_name, normalize_time, get_slots_for_day, parse_booking_schedule
from config import GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON, SHOW_BROWSER

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds in London UK timezone."""
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return f"[{london_time.strftime('%H:%M:%S.%f')[:-4]}]"

class BookingOrchestrator:
    """Orchestrates the entire multi-court booking process."""
    
    def __init__(self):
        """Initialize the booking orchestrator."""
        self.sheets_manager = None
        self.multi_session_manager = None
        self.booking_schedule = []
        self.target_date = None
        self.target_day_name = None
        self.slots_to_book = []
    
    async def initialize(self):
        """Initialize the booking system."""
        try:
            print(f"{get_timestamp()} === Initializing Multi-Court Booking System ===")
            
            # Initialize Google Sheets manager
            if not GSHEET_MAIN_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
                raise ValueError("Google Sheets configuration not set")
            
            self.sheets_manager = SheetsManager(GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
            print(f"{get_timestamp()} ✅ Google Sheets manager initialized")
            
            # Initialize multi-session manager
            self.multi_session_manager = MultiSessionManager(self.sheets_manager)
            
            # Initialize browser sessions
            headless = not SHOW_BROWSER
            if not await self.multi_session_manager.initialize_sessions(headless):
                raise Exception("Failed to initialize browser sessions")
            
            print(f"{get_timestamp()} ✅ Multi-session manager initialized")
            
            # Read booking schedule
            await self.load_booking_schedule()
            
            print(f"{get_timestamp()} ✅ Booking orchestrator initialized successfully")
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Failed to initialize booking orchestrator: {e}")
            return False
    
    async def load_booking_schedule(self):
        """Load and parse the booking schedule from Google Sheets."""
        try:
            print(f"{get_timestamp()} --- Loading booking schedule ---")
            
            # Read raw schedule data
            raw_schedule_data = self.sheets_manager.read_booking_schedule_sheet()
            
            # Parse and normalize schedule
            self.booking_schedule = parse_booking_schedule(raw_schedule_data)
            
            print(f"{get_timestamp()} ✅ Loaded {len(self.booking_schedule)} schedule entries")
            
            # Validate schedule
            from robust_parser import validate_schedule_data
            is_valid, issues = validate_schedule_data(self.booking_schedule)
            
            if not is_valid:
                print(f"{get_timestamp()} ⚠️ Schedule validation issues:")
                for issue in issues:
                    print(f"{get_timestamp()}   - {issue}")
            else:
                print(f"{get_timestamp()} ✅ Schedule validation passed")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error loading booking schedule: {e}")
            raise
    
    def calculate_target_date(self):
        """Calculate the target date (35 days from today)."""
        try:
            # Get current date in UK timezone
            uk_tz = pytz.timezone('Europe/London')
            today = datetime.now(uk_tz).date()
            
            # Calculate target date (35 days from today)
            self.target_date = today + timedelta(days=35)
            self.target_day_name = self.target_date.strftime('%A')
            
            print(f"{get_timestamp()} 📅 Target date: {self.target_date.strftime('%d/%m/%Y')} ({self.target_day_name})")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error calculating target date: {e}")
            raise
    
    def determine_slots_to_book(self):
        """Determine which slots to book based on the target day."""
        try:
            print(f"{get_timestamp()} --- Determining slots to book for {self.target_day_name} ---")
            
            # Get all slots for the target day
            self.slots_to_book = get_slots_for_day(self.booking_schedule, self.target_day_name)
            
            if not self.slots_to_book:
                print(f"{get_timestamp()} ⚠️ No slots configured for {self.target_day_name}")
                return False
            
            print(f"{get_timestamp()} ✅ Found {len(self.slots_to_book)} slots to book:")
            for slot in self.slots_to_book:
                print(f"{get_timestamp()}   - {slot}")
            
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error determining slots to book: {e}")
            return False
    
    async def execute_booking_process(self):
        """Execute the complete booking process."""
        try:
            print(f"{get_timestamp()} === Starting Multi-Court Booking Process ===")
            
            # Step 1: Calculate target date
            self.calculate_target_date()
            
            # Step 2: Determine slots to book
            if not self.determine_slots_to_book():
                print(f"{get_timestamp()} ⚠️ No slots to book for {self.target_day_name}")
                return False
            
            # Step 3: Login to all sessions
            print(f"{get_timestamp()} --- Step 1: Logging in all sessions ---")
            if not await self.multi_session_manager.login_all_sessions():
                print(f"{get_timestamp()} ❌ Failed to login to any sessions")
                return False
            
            # Step 4: Book all courts for the target date
            print(f"{get_timestamp()} --- Step 2: Booking all courts ---")
            target_date_str = self.target_date.strftime('%d/%m/%Y')
            if not await self.multi_session_manager.book_all_courts_for_day(target_date_str, self.slots_to_book):
                print(f"{get_timestamp()} ⚠️ No successful bookings made")
            
            # Step 5: Process checkout for all sessions
            print(f"{get_timestamp()} --- Step 3: Processing checkout ---")
            await self.multi_session_manager.checkout_all_sessions()
            
            # Step 6: Logout and cleanup
            print(f"{get_timestamp()} --- Step 4: Logging out and cleanup ---")
            await self.multi_session_manager.logout_all_sessions()
            await self.multi_session_manager.cleanup_all_sessions()
            
            # Step 7: Generate summary
            await self.generate_booking_summary()
            
            print(f"{get_timestamp()} === Multi-Court Booking Process Completed ===")
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during booking process: {e}")
            
            # Ensure cleanup happens even on error
            try:
                await self.multi_session_manager.logout_all_sessions()
                await self.multi_session_manager.cleanup_all_sessions()
            except:
                pass
            
            return False
    
    async def generate_booking_summary(self):
        """Generate and log a summary of the booking results."""
        try:
            print(f"{get_timestamp()} --- Generating booking summary ---")
            
            summary = self.multi_session_manager.get_booking_summary()
            
            print(f"{get_timestamp()} === BOOKING SUMMARY ===")
            print(f"{get_timestamp()} 📊 Target Date: {self.target_date.strftime('%d/%m/%Y')} ({self.target_day_name})")
            print(f"{get_timestamp()} 🏟️ Courts: {summary['total_sessions']}")
            print(f"{get_timestamp()} ✅ Successful Bookings: {summary['successful_bookings']}")
            print(f"{get_timestamp()} ❌ Failed Bookings: {summary['failed_bookings']}")
            
            if summary['successful_bookings'] > 0:
                print(f"{get_timestamp()} 📋 Successful Details:")
                for booking in summary['successful_details']:
                    court_url, date, time = booking
                    print(f"{get_timestamp()}   - {date} {time}")
            
            if summary['failed_bookings'] > 0:
                print(f"{get_timestamp()} 📋 Failed Details:")
                for booking in summary['failed_bookings']:
                    court_url, date, time = booking
                    print(f"{get_timestamp()}   - {date} {time}")
            
            # Log summary to Google Sheets
            uk_tz = pytz.timezone('Europe/London')
            london_time = datetime.now(uk_tz)
            summary_log_entry = {
                'Timestamp': london_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Email': 'SYSTEM',
                'Court': 'ALL',
                'Date': self.target_date.strftime('%d/%m/%Y'),
                'Time': f"{len(self.slots_to_book)} slots",
                'Status': f"📊 Summary: {summary['successful_bookings']}✅ {summary['failed_bookings']}❌",
                'Error Details': f"Target: {self.target_day_name}, Courts: {summary['total_sessions']}"
            }
            self.sheets_manager.write_booking_log(summary_log_entry)
            
            print(f"{get_timestamp()} ✅ Booking summary generated and logged")
            
            # Send email notification
            await self.send_email_notification(summary)
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error generating booking summary: {e}")
    
    async def send_email_notification(self, summary):
        """Send email notification with booking results."""
        try:
            print(f"{get_timestamp()} --- Sending email notification ---")
            
            from config import SENDER_EMAIL, RECIPIENT_KYLE, RECIPIENT_INFO, GMAIL_APP_PASSWORD
            
            if not all([SENDER_EMAIL, RECIPIENT_KYLE, GMAIL_APP_PASSWORD]):
                print(f"{get_timestamp()} ⚠️ Email configuration incomplete, skipping email notification")
                return
            
            # Create email content
            subject = f"Tennis Court Booking Results - {self.target_date.strftime('%d/%m/%Y')}"
            
            body = f"""
🎾 Tennis Court Booking Results

📅 Date: {self.target_date.strftime('%d/%m/%Y')} ({self.target_day_name})
🏟️ Courts: {summary['total_sessions']}
✅ Successful Bookings: {summary['successful_bookings']}
❌ Failed Bookings: {summary['failed_bookings']}

📋 Summary:
- Target Date: {self.target_date.strftime('%d/%m/%Y')}
- Day of Week: {self.target_day_name}
- Total Courts: {summary['total_sessions']}
- Slots Attempted: {len(self.slots_to_book)}

This is an automated notification from the Tennis Court Booking System.
            """.strip()
            
            # Send email using Gmail SMTP
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECIPIENT_KYLE
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to Gmail SMTP
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            
            # Send email
            text = msg.as_string()
            server.sendmail(SENDER_EMAIL, RECIPIENT_KYLE, text)
            server.quit()
            
            print(f"{get_timestamp()} ✅ Email notification sent successfully")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending email notification: {e}")

async def main():
    """Main function to run the booking orchestrator."""
    try:
        print(f"{get_timestamp()} 🎾 Multi-Court Tennis Booking System")
        print(f"{get_timestamp()} ======================================")
        
        # Create and initialize orchestrator
        orchestrator = BookingOrchestrator()
        
        if not await orchestrator.initialize():
            print(f"{get_timestamp()} ❌ Failed to initialize booking system")
            return False
        
        # Execute booking process
        success = await orchestrator.execute_booking_process()
        
        if success:
            print(f"{get_timestamp()} 🎉 Booking process completed successfully")
        else:
            print(f"{get_timestamp()} ⚠️ Booking process completed with issues")
        
        return success
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Fatal error in main process: {e}")
        return False

if __name__ == "__main__":
    # Run the async main function
    success = asyncio.run(main())
    
    if success:
        print(f"{get_timestamp()} 🎉 Multi-court booking system completed successfully")
        exit(0)
    else:
        print(f"{get_timestamp()} ❌ Multi-court booking system failed")
        exit(1)
