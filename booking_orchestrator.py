# booking_orchestrator.py
# This file orchestrates the entire multi-court booking process

import asyncio
import os
from datetime import datetime, timedelta
from sheets_manager import SheetsManager
from multi_session_manager import MultiSessionManager
from robust_parser import normalize_day_name, normalize_time, get_slots_for_day, parse_booking_schedule
from config import GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON, SHOW_BROWSER
from utils import get_timestamp
from email_manager import EmailManager

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
            from utils import get_london_datetime
            today = get_london_datetime().date()
            
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
    
    def distribute_slots_among_sessions(self):
        """
        Distribute available slots among active sessions (one slot per account).
        
        Returns:
            dict: Dictionary mapping session index to slot time
        """
        try:
            print(f"{get_timestamp()} --- Distributing {len(self.slots_to_book)} slots among {len(self.multi_session_manager.sessions)} accounts ---")
            
            slot_distribution = {}
            active_sessions = self.multi_session_manager.sessions
            
            # Distribute slots in round-robin fashion
            for i, slot_time in enumerate(self.slots_to_book):
                if i < len(active_sessions):
                    session_index = i
                    account_name = active_sessions[session_index].account_name
                    slot_distribution[session_index] = slot_time
                    print(f"{get_timestamp()} 🎯 {account_name} assigned slot: {slot_time}")
                else:
                    print(f"{get_timestamp()} ⚠️ More slots ({len(self.slots_to_book)}) than accounts ({len(active_sessions)}) - slot {slot_time} will not be booked")
            
            print(f"{get_timestamp()} ✅ Slot distribution complete: {len(slot_distribution)} assignments made")
            return slot_distribution
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error distributing slots: {e}")
            return {}
    
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
            
            # Step 4: Distribute slots among sessions (one slot per account)
            print(f"{get_timestamp()} --- Step 2: Distributing slots among accounts ---")
            slot_distribution = self.distribute_slots_among_sessions()
            
            # Step 5: Book distributed slots for each session
            print(f"{get_timestamp()} --- Step 3: Booking distributed slots ---")
            target_date_str = self.target_date.strftime('%d/%m/%Y')
            if not await self.multi_session_manager.book_distributed_slots(target_date_str, slot_distribution):
                print(f"{get_timestamp()} ⚠️ No successful bookings made")
            
            # Step 6: Process checkout for all sessions
            print(f"{get_timestamp()} --- Step 4: Processing checkout ---")
            await self.multi_session_manager.checkout_all_sessions()
            
            # Step 7: Logout and cleanup
            print(f"{get_timestamp()} --- Step 5: Logging out and cleanup ---")
            await self.multi_session_manager.logout_all_sessions()
            await self.multi_session_manager.cleanup_all_sessions()
            
            # Step 8: Generate summary
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
                for booking in summary['failed_details']:
                    try:
                        court_url, date, time = booking
                        print(f"{get_timestamp()}   - {date} {time}")
                    except Exception as unpack_error:
                        print(f"{get_timestamp()} ❌ Error unpacking booking: {booking}, error: {unpack_error}")
                        print(f"{get_timestamp()}   - Failed booking (raw): {booking}")
            
            # Log summary to Google Sheets
            from utils import get_london_datetime
            london_time = get_london_datetime()
            summary_log_entry = {
                'Timestamp': london_time.strftime('%Y-%m-%d %H:%M:%S'),
                'Email': 'SYSTEM',
                'Court': 'ALL',
                'Date': self.target_date.strftime('%d/%m/%Y'),
                'Time': f"{len(self.slots_to_book)} slots",
                'Status': f"📊 Summary: {summary['successful_bookings']}✅ {summary['failed_bookings']}❌",
                'Error Details': f"Target: {self.target_day_name}, Courts: {summary['total_sessions']}"
            }
            # self.sheets_manager.write_booking_log(summary_log_entry)
            
            print(f"{get_timestamp()} ✅ Booking summary generated and logged")
            
            # Send email notification
            await self.send_email_notification(summary)
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error generating booking summary: {e}")
    
    async def send_email_notification(self, summary):
        """Send email notifications with booking results using EmailManager."""
        try:
            print(f"{get_timestamp()} === Sending Email Notifications ===")
            
            if not summary:
                print(f"{get_timestamp()} ⚠️ No summary data provided, skipping email notifications")
                return
            
            # Get session details and booking log
            print(f"{get_timestamp()} 📊 Collecting session details and booking log...")
            session_details = self.multi_session_manager.get_session_details()
            print(f"{get_timestamp()}   Session details collected: {len(session_details)} sessions")
            
            booking_log_result = self.sheets_manager.read_booking_log(limit=100)
            booking_log_entries = booking_log_result['entries']
            print(f"{get_timestamp()}   Booking log entries collected: {len(booking_log_entries)} entries")
            
            # Validate email configuration and create EmailManager
            from config import SENDER_EMAIL, GMAIL_APP_PASSWORD, RECIPIENT_KYLE, RECIPIENT_INFO, IT_EMAIL_ADDRESS
            
            if not SENDER_EMAIL:
                print(f"{get_timestamp()} ❌ SENDER_EMAIL (KYLE_EMAIL_ADDRESS) not configured, cannot send emails")
                return
            
            if not GMAIL_APP_PASSWORD:
                print(f"{get_timestamp()} ❌ GMAIL_APP_PASSWORD not configured, cannot send emails")
                return
            
            print(f"{get_timestamp()} ✅ Email configuration validated - Sender: {SENDER_EMAIL}")
            
            # Create EmailManager instance
            email_manager = EmailManager(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            
            # Send individual session emails to IT_EMAIL_ADDRESS only (one email per court)
            if IT_EMAIL_ADDRESS:
                print(f"{get_timestamp()} 📧 Sending individual session emails to IT ({IT_EMAIL_ADDRESS})...")
                print(f"{get_timestamp()}   Will send {len(session_details)} separate emails (one per court)")
                await email_manager.send_individual_session_emails(
                    session_details, IT_EMAIL_ADDRESS, self.target_date, self.target_day_name, self.slots_to_book
                )
            else:
                print(f"{get_timestamp()} ⚠️ IT_EMAIL_ADDRESS not configured, skipping individual session emails")
            
            # Send summary email to INFO_EMAIL_ADDRESS and KYLE_EMAIL_ADDRESS
            summary_recipients = []
            if RECIPIENT_INFO:
                summary_recipients.append(RECIPIENT_INFO)
            if RECIPIENT_KYLE:
                summary_recipients.append(RECIPIENT_KYLE)
            
            if summary_recipients:
                print(f"{get_timestamp()} 📧 Sending summary email to {len(summary_recipients)} recipients...")
                print(f"{get_timestamp()}   Recipients: {summary_recipients}")
                await email_manager.send_summary_email(
                    summary, session_details, booking_log_entries, summary_recipients, 
                    self.target_date, self.target_day_name
                )
            else:
                print(f"{get_timestamp()} ⚠️ No summary email recipients configured (INFO_EMAIL_ADDRESS and/or KYLE_EMAIL_ADDRESS), skipping summary email")
            
            print(f"{get_timestamp()} ✅ All email notifications sent successfully")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending email notifications: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    

    
    def get_current_london_time(self):
        """Get current time in London timezone as formatted string."""
        from utils import get_current_london_time
        return get_current_london_time()

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
