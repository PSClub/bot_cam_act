# email_manager.py
# Dedicated module for handling all email notifications

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils import get_timestamp, get_current_london_time


class EmailManager:
    """Handles all email notifications for the tennis court booking system."""
    
    def __init__(self, sender_email, app_password):
        """
        Initialize the email manager.
        
        Args:
            sender_email (str): Gmail address to send from
            app_password (str): Gmail app password for authentication
        """
        self.sender_email = sender_email
        self.app_password = app_password
        
        # Validate configuration
        if not self.sender_email:
            raise ValueError("Sender email is required")
        if not self.app_password:
            raise ValueError("Gmail app password is required")
    
    async def send_email(self, recipient, subject, body):
        """
        Send a single email using Gmail SMTP.
        
        Args:
            recipient (str): Email address to send to
            subject (str): Email subject line
            body (str): Email body content
            
        Raises:
            Exception: If email sending fails
        """
        server = None
        try:
            print(f"{get_timestamp()}     📧 SMTP: Preparing email to {recipient}")
            print(f"{get_timestamp()}     📧 Subject: {subject}")
            print(f"{get_timestamp()}     📧 Body length: {len(body)} characters")
            
            # Validate inputs
            if not recipient:
                raise ValueError("Recipient email is required")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            print(f"{get_timestamp()}     📧 SMTP: Connecting to Gmail SMTP server...")
            
            # Connect to Gmail SMTP with timeout
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            
            print(f"{get_timestamp()}     📧 SMTP: Authenticating...")
            server.login(self.sender_email, self.app_password)
            
            print(f"{get_timestamp()}     📧 SMTP: Sending email...")
            
            # Send email
            text = msg.as_string()
            result = server.sendmail(self.sender_email, [recipient], text)
            
            # Check if there were any failed recipients
            if result:
                print(f"{get_timestamp()}     ⚠️ SMTP: Some recipients failed: {result}")
            else:
                print(f"{get_timestamp()}     ✅ SMTP: Email sent successfully to {recipient}")
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"{get_timestamp()} ❌ SMTP Authentication failed for {self.sender_email}: {e}")
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
    
    async def send_individual_session_emails(self, session_details, it_email, target_date, target_day_name, slots_to_book):
        """Send individual emails for each session to IT_EMAIL_ADDRESS only."""
        try:
            print(f"{get_timestamp()} --- Sending individual session emails to IT ---")
            print(f"{get_timestamp()}   Target IT email: {it_email}")
            print(f"{get_timestamp()}   Sessions to email: {len(session_details)}")
            
            for i, session in enumerate(session_details):
                print(f"{get_timestamp()} 📧 Sending email {i+1}/{len(session_details)} for {session['account_name']}")
                await self.send_session_email(session, it_email, target_date, target_day_name, slots_to_book)
                
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending individual session emails: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_session_email(self, session, recipient, target_date, target_day_name, slots_to_book):
        """Send detailed email for a single session."""
        try:
            print(f"{get_timestamp()}   📧 Preparing session email for {session['account_name']}")
            
            subject = f"Tennis Court Booking Session - {session['account_name']} - {target_date.strftime('%d/%m/%Y')}"
            
            # Create detailed body for this session
            body = f"""🎾 Tennis Court Booking Session Report

📅 Date: {target_date.strftime('%d/%m/%Y')} ({target_day_name})
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

⏰ Timestamp: {get_current_london_time()}
🎯 Target Day: {target_day_name}
🏟️ Slots Attempted: {len(slots_to_book)}

This is an automated session report from the Tennis Court Booking System.
Complete terminal logs and screenshot details are included above for debugging.
            """.strip()
            
            print(f"{get_timestamp()}   📧 Sending session email for {session['account_name']} to {recipient}")
            
            # Send email
            await self.send_email(recipient, subject, body)
            print(f"{get_timestamp()} ✅ Session email sent for {session['account_name']}")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending session email for {session['account_name']}: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
    
    async def send_summary_email(self, summary, session_details, booking_log_entries, recipients, target_date, target_day_name):
        """Send comprehensive summary email to INFO_EMAIL_ADDRESS and KYLE_EMAIL_ADDRESS only."""
        try:
            print(f"{get_timestamp()} --- Sending summary email ---")
            print(f"{get_timestamp()}   Recipients: {recipients}")
            print(f"{get_timestamp()}   Summary data: {summary}")
            print(f"{get_timestamp()}   Session details: {len(session_details)} sessions")
            print(f"{get_timestamp()}   Log entries: {len(booking_log_entries)} entries")
            
            subject = f"Tennis Court Booking Summary - {target_date.strftime('%d/%m/%Y')}"
            
            # Create comprehensive summary body
            body = f"""🎾 Tennis Court Booking System - Summary Report

📅 Date: {target_date.strftime('%d/%m/%Y')} ({target_day_name})
🏟️ Total Courts: {summary['total_sessions']}
✅ Successful Bookings: {summary['successful_bookings']}
❌ Failed Bookings: {summary['failed_bookings']}
📝 Total Slots Attempted: {len(session_details) * 2 if session_details else 0}

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
                court_num = session['court_number']
                
                # Add successful bookings
                for booking in session['successful_bookings']:
                    court_url, date, time = booking
                    slot_key = f"{date} {time}"
                    if slot_key not in slot_summary:
                        slot_summary[slot_key] = {}
                    slot_summary[slot_key][court_num] = "✅ SUCCESS"
                
                # Add failed bookings
                for booking in session['failed_bookings']:
                    court_url, date, time = booking
                    slot_key = f"{date} {time}"
                    if slot_key not in slot_summary:
                        slot_summary[slot_key] = {}
                    slot_summary[slot_key][court_num] = "❌ FAILED"
            
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

⏰ Timestamp: {get_current_london_time()}
🎯 Target Day: {target_day_name}
🏟️ Courts: {summary['total_sessions']}

This is an automated summary report from the Tennis Court Booking System.
            """.strip()
            
            print(f"{get_timestamp()}   📧 Summary email body prepared, length: {len(body)} characters")
            
            # Send to all recipients
            for recipient in recipients:
                if recipient:
                    print(f"{get_timestamp()}   📧 Sending summary email to {recipient}")
                    await self.send_email(recipient, subject, body)
                    print(f"{get_timestamp()} ✅ Summary email sent to {recipient}")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending summary email: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
