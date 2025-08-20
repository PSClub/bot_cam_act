# email_manager.py
# Dedicated module for handling all email notifications

import smtplib
import os
import base64
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
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
    
    def _attach_screenshots(self, msg, screenshot_paths):
        """
        Attach screenshot files to the email message.
        
        Args:
            msg (MIMEMultipart): Email message object
            screenshot_paths (list): List of screenshot file paths to attach
            
        Returns:
            int: Number of screenshots successfully attached
        """
        attached_count = 0
        
        for screenshot_path in screenshot_paths:
            try:
                # Check if file exists and is readable
                if not os.path.exists(screenshot_path):
                    print(f"{get_timestamp()}     📸 Screenshot not found: {screenshot_path}")
                    continue
                
                if not os.path.isfile(screenshot_path):
                    print(f"{get_timestamp()}     📸 Path is not a file: {screenshot_path}")
                    continue
                
                # Get file size (Gmail has 25MB attachment limit)
                file_size = os.path.getsize(screenshot_path)
                if file_size > 20 * 1024 * 1024:  # 20MB safety limit
                    print(f"{get_timestamp()}     📸 Screenshot too large ({file_size} bytes): {screenshot_path}")
                    continue
                
                # Read and attach the file
                with open(screenshot_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                # Encode file in ASCII characters to send by email
                encoders.encode_base64(part)
                
                # Add header as key/value pair to attachment part
                filename = os.path.basename(screenshot_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}',
                )
                
                # Attach the part to message
                msg.attach(part)
                attached_count += 1
                print(f"{get_timestamp()}     📸 Attached screenshot: {filename} ({file_size} bytes)")
                
            except Exception as e:
                print(f"{get_timestamp()}     ❌ Failed to attach screenshot {screenshot_path}: {e}")
                continue
        
        return attached_count

    def _embed_screenshots_inline(self, body, screenshot_paths):
        """
        Embed screenshots inline in the email body using base64 encoding.
        
        Args:
            body (str): Original email body text
            screenshot_paths (list): List of screenshot file paths to embed
            
        Returns:
            tuple: (html_body, embedded_count)
        """
        if not screenshot_paths:
            return body, 0
            
        embedded_count = 0
        
        # Sort screenshots by filename in ascending order
        sorted_screenshots = sorted(screenshot_paths, key=lambda path: os.path.basename(path))
        
        # Convert text body to HTML
        html_body = body.replace('\n', '<br>\n')
        
        # Add screenshots section at the end
        html_body += '<br><br><hr><h3>📸 Screenshots (sorted by name):</h3><br>\n'
        
        for screenshot_path in sorted_screenshots:
            try:
                # Check if file exists and is readable
                if not os.path.exists(screenshot_path):
                    print(f"{get_timestamp()}     📸 Screenshot not found: {screenshot_path}")
                    continue
                    
                if not os.path.isfile(screenshot_path):
                    print(f"{get_timestamp()}     📸 Path is not a file: {screenshot_path}")
                    continue
                
                # Get file size (limit to prevent email issues)
                file_size = os.path.getsize(screenshot_path)
                if file_size > 5 * 1024 * 1024:  # 5MB limit per image
                    print(f"{get_timestamp()}     📸 Screenshot too large ({file_size} bytes): {screenshot_path}")
                    continue
                
                # Read and encode the image file
                with open(screenshot_path, 'rb') as image_file:
                    image_data = image_file.read()
                    base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Determine MIME type
                mime_type, _ = mimetypes.guess_type(screenshot_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/png'  # Default to PNG
                
                # Get filename for display
                filename = os.path.basename(screenshot_path)
                
                # Add the inline image to HTML body (displayed at 50% scale to save visual space)
                html_body += f'''
<div style="margin: 15px 0; border: 1px solid #ddd; padding: 8px;">
    <h4 style="margin: 0 0 8px 0; font-size: 14px;">{filename}</h4>
    <img src="data:{mime_type};base64,{base64_image}" 
         alt="{filename}" 
         style="max-width: 50%; height: auto; border: 1px solid #ccc; display: block;">
    <p style="font-size: 11px; color: #666; margin: 5px 0 0 0;">File size: {file_size:,} bytes (displayed at 50% scale for visual space)</p>
</div>
'''
                
                embedded_count += 1
                print(f"{get_timestamp()}     📸 Embedded screenshot: {filename} ({file_size} bytes)")
                
            except Exception as e:
                print(f"{get_timestamp()}     ❌ Failed to embed screenshot {screenshot_path}: {e}")
                continue
        
        return html_body, embedded_count

    async def send_email(self, recipient, subject, body, screenshot_paths=None):
        """
        Send a single email using Gmail SMTP with optional screenshot attachments.
        
        Args:
            recipient (str): Email address to send to
            subject (str): Email subject line
            body (str): Email body content
            screenshot_paths (list, optional): List of screenshot file paths to attach
            
        Raises:
            Exception: If email sending fails
        """
        server = None
        try:
            print(f"{get_timestamp()}     📧 SMTP: Preparing email to {recipient}")
            print(f"{get_timestamp()}     📧 Subject: {subject}")
            print(f"{get_timestamp()}     📧 Body length: {len(body)} characters")
            
            # Handle screenshots
            if screenshot_paths:
                print(f"{get_timestamp()}     📸 Screenshots to attach: {len(screenshot_paths)}")
            
            # Validate inputs
            if not recipient:
                raise ValueError("Recipient email is required")
            
            # Embed screenshots inline if provided
            embedded_count = 0
            if screenshot_paths:
                html_body, embedded_count = self._embed_screenshots_inline(body, screenshot_paths)
                
                # Create multipart message for HTML email with fallback
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                
                # Add plain text version as fallback
                text_part = MIMEText(body, 'plain', 'utf-8')
                html_part = MIMEText(html_body, 'html', 'utf-8')
                
                msg.attach(text_part)
                msg.attach(html_part)
                
                print(f"{get_timestamp()}     📸 Successfully embedded {embedded_count}/{len(screenshot_paths)} screenshots inline")
            else:
                # No screenshots, send as simple plain text
                msg = MIMEText(body, 'plain', 'utf-8')
                msg['From'] = self.sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
            
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
                body += "\n📸 Note: All screenshots are embedded below in the email for easy viewing.\n"
            else:
                body += "📸 No screenshots were taken during this session.\n"
            
            # Add full terminal logs
            session_logs = session.get('session_logs', [])
            body += f"""

📝 Complete Terminal Logs: {len(session_logs)} entries
"""
            
            if session_logs:
                body += "📝 Full Terminal Output:\n"
                body += "=" * 80 + "\n"
                
                # Check if logs are too long for email (Gmail has ~25MB limit, most clients handle ~2MB text well)
                logs_text = "\n".join(session_logs)
                if len(logs_text) > 1500000:  # 1.5MB limit to ensure delivery across all email clients
                    # Include first 500KB and last 500KB with a note about truncation
                    first_part = logs_text[:500000]
                    last_part = logs_text[-500000:]
                    truncation_note = f"\n\n[--- TRUNCATED: {len(logs_text) - 1000000} characters hidden for email delivery ---]\n\n"
                    
                    body += first_part + truncation_note + last_part + "\n"
                    body += f"\n💡 FULL LOGS: Complete logs available in GitHub Actions output\n"
                else:
                    # Include all logs if under size limit
                    body += logs_text + "\n"
                
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
            
            # Collect screenshot paths for this session
            screenshot_paths = []
            if session.get('screenshots_taken'):
                for screenshot in session['screenshots_taken']:
                    screenshot_path = screenshot.get('path')
                    if screenshot_path:
                        screenshot_paths.append(screenshot_path)
            
            print(f"{get_timestamp()}   📸 Including {len(screenshot_paths)} screenshots as attachments")
            
            # Send email with screenshot attachments
            await self.send_email(recipient, subject, body, screenshot_paths)
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
            
            # Calculate actual total slots attempted from session details
            total_slots_attempted = sum(session.get('total_attempts', 0) for session in session_details)
            
            # Create comprehensive summary body
            body = f"""🎾 Tennis Court Booking System - Summary Report

📅 Date: {target_date.strftime('%d/%m/%Y')} ({target_day_name})
🏟️ Total Courts: {summary['total_sessions']}
✅ Successful Bookings: {summary['successful_bookings']}
❌ Failed Bookings: {summary['failed_bookings']}
📝 Total Slots Attempted: {total_slots_attempted}

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
            
            # Add detailed individual slot status table
            body += f"""

📋 Individual Slot Status (Complete List):
"""
            
            if session_details:
                body += "   Court | Account | Date | Time | Status\n"
                body += "   " + "-" * 50 + "\n"
                
                for session in session_details:
                    court_short = session['court_number']
                    account_short = session['account_name'][:8]  # Truncate for table formatting
                    
                    # Add successful bookings
                    for booking in session['successful_bookings']:
                        court_url, date, time = booking
                        body += f"   {court_short:<6} | {account_short:<8} | {date} | {time} | ✅ SUCCESS\n"
                    
                    # Add failed bookings
                    for booking in session['failed_bookings']:
                        court_url, date, time = booking
                        body += f"   {court_short:<6} | {account_short:<8} | {date} | {time} | ❌ FAILED\n"
            else:
                body += "   No slot attempts recorded\n"
            
            body += f"""

⏰ Timestamp: {get_current_london_time()}
🎯 Target Day: {target_day_name}
🏟️ Courts: {summary['total_sessions']}

📸 Note: All screenshots from all court booking sessions are embedded below in the email (sorted by name).

This is an automated summary report from the Tennis Court Booking System.
            """.strip()
            
            print(f"{get_timestamp()}   📧 Summary email body prepared, length: {len(body)} characters")
            
            # Collect all screenshot paths from all sessions for summary email
            all_screenshot_paths = []
            for session in session_details:
                if session.get('screenshots_taken'):
                    for screenshot in session['screenshots_taken']:
                        screenshot_path = screenshot.get('path')
                        if screenshot_path:
                            all_screenshot_paths.append(screenshot_path)
            
            print(f"{get_timestamp()}   📸 Including {len(all_screenshot_paths)} screenshots from all sessions as attachments")
            
            # Send to all recipients
            for recipient in recipients:
                if recipient:
                    print(f"{get_timestamp()}   📧 Sending summary email to {recipient}")
                    await self.send_email(recipient, subject, body, all_screenshot_paths)
                    print(f"{get_timestamp()} ✅ Summary email sent to {recipient}")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error sending summary email: {e}")
            import traceback
            print(f"{get_timestamp()} 🔍 Error details: {traceback.format_exc()}")
