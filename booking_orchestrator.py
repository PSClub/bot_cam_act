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
            self.sheets_manager.write_booking_log(summary_log_entry)
            
            print(f"{get_timestamp()} ✅ Booking summary generated and logged")
            
            # Send email notification
            await self.send_email_notification(summary)
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error generating booking summary: {e}")
    
    async def send_email_notification(self, summary):
        """Send email notification with booking results."""
        try:
            print(f"{get_timestamp()} --- Sending email notifications ---")
            
            from config import SENDER_EMAIL, RECIPIENT_KYLE, RECIPIENT_INFO, IT_EMAIL_ADDRESS, GMAIL_APP_PASSWORD
            
            # Check email configuration
            print(f"{get_timestamp()} 🔍 Email configuration check:")
            print(f"{get_timestamp()}   SENDER_EMAIL: {'✅ Set' if SENDER_EMAIL else '❌ Missing'}")
            print(f"{get_timestamp()}   GMAIL_APP_PASSWORD: {'✅ Set' if GMAIL_APP_PASSWORD else '❌ Missing'}")
            print(f"{get_timestamp()}   IT_EMAIL_ADDRESS: {'✅ Set' if IT_EMAIL_ADDRESS else '❌ Missing'}")
            print(f"{get_timestamp()}   RECIPIENT_INFO: {'✅ Set' if RECIPIENT_INFO else '❌ Missing'}")
            print(f"{get_timestamp()}   RECIPIENT_KYLE: {'✅ Set' if RECIPIENT_KYLE else '❌ Missing'}")
            
            if not all([SENDER_EMAIL, GMAIL_APP_PASSWORD]):
                print(f"{get_timestamp()} ⚠️ Email configuration incomplete, skipping email notifications")
                return
            
            # Get session details and booking log
            print(f"{get_timestamp()} 📊 Collecting session details and booking log...")
            session_details = self.multi_session_manager.get_session_details()
            print(f"{get_timestamp()}   Session details collected: {len(session_details)} sessions")
            
            booking_log_result = self.sheets_manager.read_booking_log(limit=100)
            booking_log_entries = booking_log_result['entries']
            print(f"{get_timestamp()}   Booking log entries collected: {len(booking_log_entries)} entries")
            
            # Validate email configuration
            from config import SENDER_EMAIL, GMAIL_APP_PASSWORD
            
            if not SENDER_EMAIL:
                print(f"{get_timestamp()} ❌ SENDER_EMAIL (KYLE_EMAIL_ADDRESS) not configured, cannot send emails")
                return
            
            if not GMAIL_APP_PASSWORD:
                print(f"{get_timestamp()} ❌ GMAIL_APP_PASSWORD not configured, cannot send emails")
                return
            
            print(f"{get_timestamp()} ✅ Email configuration validated - Sender: {SENDER_EMAIL}")
            
            # Send individual session emails to IT_EMAIL_ADDRESS only (one email per court)
            if IT_EMAIL_ADDRESS:
                print(f"{get_timestamp()} 📧 Sending individual session emails to IT ({IT_EMAIL_ADDRESS})...")
                print(f"{get_timestamp()}   Will send {len(session_details)} separate emails (one per court)")
                await self.send_individual_session_emails(session_details, IT_EMAIL_ADDRESS)
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
                await self.send_summary_email(summary, session_details, booking_log_entries, summary_recipients)
            else:
                print(f"{get_timestamp()} ⚠️ No summary email recipients configured (INFO_EMAIL_ADDRESS and/or KYLE_EMAIL_ADDRESS), skipping summary email")
            
            print(f"{get_timestamp()} ✅ All email notifications sent successfully")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending email notifications: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_individual_session_emails(self, session_details, it_email):
        """Send individual emails for each session to IT_EMAIL_ADDRESS only."""
        try:
            print(f"{get_timestamp()} --- Sending individual session emails to IT ---")
            print(f"{get_timestamp()}   Target IT email: {it_email}")
            print(f"{get_timestamp()}   Sessions to email: {len(session_details)}")
            
            from config import SENDER_EMAIL, GMAIL_APP_PASSWORD
            
            for i, session in enumerate(session_details):
                print(f"{get_timestamp()} 📧 Sending email {i+1}/{len(session_details)} for {session['account_name']}")
                await self.send_session_email(session, it_email, SENDER_EMAIL, GMAIL_APP_PASSWORD)
                
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending individual session emails: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_session_email(self, session, recipient, sender_email, app_password):
        """Send detailed email for a single session."""
        try:
            print(f"{get_timestamp()}   📧 Preparing session email for {session['account_name']}")
            
            subject = f"Tennis Court Booking Session - {session['account_name']} - {self.target_date.strftime('%d/%m/%Y')}"
            
            # Create detailed body for this session
            body = f"""
🎾 Tennis Court Booking Session Report

📅 Date: {self.target_date.strftime('%d/%m/%Y')} ({self.target_day_name})
👤 Account: {session['account_name']}
📧 Email: {session['email']}
🏟️ Court: {session['court_number']}
🔗 Court URL: {session['court_url']}

📊 Booking Results:
✅ Successful Bookings: {len(session['successful_bookings'])}
❌ Failed Bookings: {len(session['failed_bookings'])}
📝 Total Attempts: {session['total_attempts']}

📋 Successful Bookings:
"""
            
            if session['successful_bookings']:
                for booking in session['successful_bookings']:
                    court_url, date, time = booking
                    body += f"   ✅ {date} at {time}\n"
            else:
                body += "   None\n"
            
            body += "\n📋 Failed Bookings:\n"
            
            if session['failed_bookings']:
                for booking in session['failed_bookings']:
                    court_url, date, time = booking
                    body += f"   ❌ {date} at {time}\n"
            else:
                body += "   None\n"
            
            # Add screenshot information
            body += f"""

📸 Screenshots Taken: {len(session.get('screenshots_taken', []))}
"""
            
            if session.get('screenshots_taken'):
                body += "📸 Screenshot Details:\n"
                for i, screenshot in enumerate(session['screenshots_taken'], 1):
                    body += f"   {i}. {screenshot['timestamp']} - {screenshot['description']}\n"
                    body += f"      File: {screenshot['path']}\n"
            else:
                body += "📸 No screenshots were taken during this session.\n"
            
            # Add full terminal logs
            body += f"""

📝 Complete Terminal Logs: {len(session.get('session_logs', []))} entries
"""
            
            if session.get('session_logs'):
                body += "📝 Full Terminal Output:\n"
                body += "=" * 80 + "\n"
                for log_entry in session['session_logs']:
                    body += f"{log_entry}\n"
                body += "=" * 80 + "\n"
            else:
                body += "📝 No session logs were captured.\n"
            
            body += f"""

⏰ Timestamp: {self.get_current_london_time()}
🎯 Target Day: {self.target_day_name}
🏟️ Slots Attempted: {len(self.slots_to_book)}

This is an automated session report from the Tennis Court Booking System.
Complete terminal logs and screenshot details are included above for debugging.
            """.strip()
            
            print(f"{get_timestamp()}   📧 Sending session email for {session['account_name']} to {recipient}")
            
            # Send email
            await self.send_email(sender_email, recipient, subject, body, app_password)
            print(f"{get_timestamp()} ✅ Session email sent for {session['account_name']}")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending session email for {session['account_name']}: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_summary_email(self, summary, session_details, booking_log_entries, recipients):
        """Send comprehensive summary email to INFO_EMAIL_ADDRESS and KYLE_EMAIL_ADDRESS only."""
        try:
            print(f"{get_timestamp()} --- Sending summary email ---")
            print(f"{get_timestamp()}   Recipients: {recipients}")
            print(f"{get_timestamp()}   Summary data: {summary}")
            print(f"{get_timestamp()}   Session details: {len(session_details)} sessions")
            print(f"{get_timestamp()}   Log entries: {len(booking_log_entries)} entries")
            
            from config import SENDER_EMAIL, GMAIL_APP_PASSWORD
            
            subject = f"Tennis Court Booking Summary - {self.target_date.strftime('%d/%m/%Y')}"
            
            # Create comprehensive summary body
            body = f"""
🎾 Tennis Court Booking System - Summary Report

📅 Date: {self.target_date.strftime('%d/%m/%Y')} ({self.target_day_name})
🏟️ Total Courts: {summary['total_sessions']}
✅ Successful Bookings: {summary['successful_bookings']}
❌ Failed Bookings: {summary['failed_bookings']}
📝 Total Slots Attempted: {len(self.slots_to_book)}

📊 Session Summary:
"""
            
            for session in session_details:
                body += f"""
👤 {session['account_name']} ({session['court_number']}):
   📧 {session['email']}
   ✅ Successful: {len(session['successful_bookings'])}
   ❌ Failed: {len(session['failed_bookings'])}
   📝 Total: {session['total_attempts']}
"""
            
            body += f"""

📋 Slot-by-Slot Booking Summary:
"""
            
            # Create a detailed table showing every slot attempted across all courts
            slot_summary = {}
            for session in session_details:
                account_name = session['account_name']
                court_num = session['court_number']
                
                # Track attempted slots
                attempted_slots = set()
                
                # Add successful bookings
                for booking in session['successful_bookings']:
                    court_url, date, time = booking
                    slot_key = f"{date} {time}"
                    if slot_key not in slot_summary:
                        slot_summary[slot_key] = {}
                    slot_summary[slot_key][court_num] = "✅ SUCCESS"
                    attempted_slots.add(slot_key)
                
                # Add failed bookings
                for booking in session['failed_bookings']:
                    court_url, date, time = booking
                    slot_key = f"{date} {time}"
                    if slot_key not in slot_summary:
                        slot_summary[slot_key] = {}
                    slot_summary[slot_key][court_num] = "❌ FAILED"
                    attempted_slots.add(slot_key)
            
            # Format the slot summary table
            if slot_summary:
                body += "   Date & Time       | Court 1 (Mother) | Court 2 (Father) | Court 3 (Bruce)\n"
                body += "   " + "-" * 75 + "\n"
                
                for slot_key in sorted(slot_summary.keys()):
                    court1_status = slot_summary[slot_key].get("Court 1", "-")
                    court2_status = slot_summary[slot_key].get("Court 2", "-")
                    court3_status = slot_summary[slot_key].get("Court 3", "-")
                    
                    body += f"   {slot_key:<17} | {court1_status:<16} | {court2_status:<16} | {court3_status:<15}\n"
            else:
                body += "   No slots attempted\n"
            
            body += f"""

📋 Recent Booking Log Entries (Last 10):
"""
            
            if booking_log_entries:
                # Create a more readable log table
                body += "   Timestamp           | Email                | Court   | Date       | Time | Status\n"
                body += "   " + "-" * 80 + "\n"
                
                # Add log entries (limit to most recent 10 for email readability)
                for entry in booking_log_entries[:10]:
                    timestamp = str(entry.get('Timestamp', ''))[:19]  # Truncate timestamp
                    email = str(entry.get('Email', ''))[:20]  # Truncate email
                    court = str(entry.get('Court', ''))[:7]  # Truncate court
                    date = str(entry.get('Date', ''))[:10]
                    time = str(entry.get('Time', ''))[:4]
                    status = str(entry.get('Status', ''))[:20]
                    
                    body += f"   {timestamp:<19} | {email:<20} | {court:<7} | {date:<10} | {time:<4} | {status}\n"
            else:
                body += "   No log entries available\n"
            
            body += f"""

⏰ Timestamp: {self.get_current_london_time()}
🎯 Target Day: {self.target_day_name}
🏟️ Courts: {summary['total_sessions']}

This is an automated summary report from the Tennis Court Booking System.
            """.strip()
            
            print(f"{get_timestamp()}   📧 Summary email body prepared, length: {len(body)} characters")
            
            # Send to all recipients
            for recipient in recipients:
                if recipient:
                    print(f"{get_timestamp()}   📧 Sending summary email to {recipient}")
                    await self.send_email(sender_email, recipient, subject, body, app_password)
                    print(f"{get_timestamp()} ✅ Summary email sent to {recipient}")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending summary email: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_email(self, sender_email, recipient, subject, body, app_password):
        """Send a single email using Gmail SMTP."""
        server = None
        try:
            print(f"{get_timestamp()}     📧 SMTP: Preparing email to {recipient}")
            print(f"{get_timestamp()}     📧 Subject: {subject}")
            print(f"{get_timestamp()}     📧 Body length: {len(body)} characters")
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Validate inputs
            if not sender_email or not recipient or not app_password:
                raise ValueError(f"Missing email configuration: sender={bool(sender_email)}, recipient={bool(recipient)}, password={bool(app_password)}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            print(f"{get_timestamp()}     📧 SMTP: Connecting to Gmail SMTP server...")
            
            # Connect to Gmail SMTP with timeout
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            
            print(f"{get_timestamp()}     📧 SMTP: Authenticating...")
            server.login(sender_email, app_password)
            
            print(f"{get_timestamp()}     📧 SMTP: Sending email...")
            
            # Send email
            text = msg.as_string()
            result = server.sendmail(sender_email, [recipient], text)
            
            # Check if there were any failed recipients
            if result:
                print(f"{get_timestamp()}     ⚠️ SMTP: Some recipients failed: {result}")
            else:
                print(f"{get_timestamp()}     ✅ SMTP: Email sent successfully to {recipient}")
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"{get_timestamp()} ❌ SMTP Authentication failed for {sender_email}: {e}")
            print(f"{get_timestamp()} 💡 Check your Gmail App Password is correct and enabled")
            raise
        except smtplib.SMTPRecipientsRefused as e:
            print(f"{get_timestamp()} ❌ SMTP Recipient {recipient} refused: {e}")
            raise
        except smtplib.SMTPServerDisconnected as e:
            print(f"{get_timestamp()} ❌ SMTP Server disconnected: {e}")
            raise
        except smtplib.SMTPException as e:
            print(f"{get_timestamp()} ❌ SMTP Error sending email to {recipient}: {e}")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Unexpected error sending email to {recipient}: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
            raise
        finally:
            # Always close the server connection
            if server:
                try:
                    server.quit()
                    print(f"{get_timestamp()}     📧 SMTP: Connection closed")
                except:
                    pass  # Ignore errors when closing
    
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
