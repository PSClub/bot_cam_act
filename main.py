# main.py
# This is the main entry point for the booking automation script.

import asyncio
import io
import os
import pytz
import smtplib
import sys
import argparse
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from playwright.async_api import async_playwright

# Import functions and variables from our other files
from config import (
    LOGIN_URL,
    BASKET_URL,
    USERNAME,
    PASSWORD,
    BOOKING_FILE_PATH,
    SENDER_EMAIL,
    RECIPIENT_KYLE,
    RECIPIENT_INFO,
    GMAIL_APP_PASSWORD,
    SHOW_BROWSER,
    KEEP_BROWSER_OPEN,
    LB_CARD_NUMBER,
    LB_CARD_EXPIRY_MONTH,
    LB_CARD_EXPIRY_YEAR,
    LB_CARD_SECURITY_CODE,
    LB_CARDHOLDER_NAME,
    LB_ADDRESS,
    LB_CITY,
    LB_POSTCODE,
    GSHEET_CAM_ID,
    GSHEET_TAB_NAME,
    GOOGLE_SERVICE_ACCOUNT_JSON,
)
from data_processor import process_booking_file
from browser_actions import (
    navigate_to_court,
    find_date_on_calendar,
    book_slot,
    checkout_basket,
    take_screenshot,
)

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

def print_london_time():
    """Prints the current time in the London timezone."""
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    print(f"{get_timestamp()} Current time in London: {now.strftime('%A, %d %B %Y at %I:%M:%S %p %Z')}")


async def send_email_report(log_output, successful_bookings, failed_bookings):
    """Sends an email report with the script's log and any screenshots."""
    print(f"{get_timestamp()} --- Preparing Email Report ---")

    # --- Email Recipients ---
    # Filter out any None or empty email addresses
    recipients = [addr for addr in [RECIPIENT_KYLE, RECIPIENT_INFO] if addr]
    if not recipients:
        print(f"{get_timestamp()} No recipient emails configured. Skipping email report.")
        return

    # --- Email Subject ---
    subject = f"bot_cam_act: Booking Process Report - {datetime.now(pytz.timezone('Europe/London')).strftime('%Y-%m-%d %H:%M')}"

    # --- Email Body ---
    # Start with the summary, then add the log
    body = "<h2>Booking Summary</h2>"
    body += f"<b>Successfully booked: {len(successful_bookings)} slots.</b>"
    if successful_bookings:
        body += "<ul>"
        for slot in successful_bookings:
            body += f"<li>{slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}</li>"
        body += "</ul>"

    body += f"<b>Failed or skipped: {len(failed_bookings)} slots.</b>"
    if failed_bookings:
        body += "<ul>"
        for slot in failed_bookings:
            body += f"<li>{slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}</li>"
        body += "</ul>"
    
    body += "<hr>" # Add a separator
    body += "<h2>Booking Process Log</h2>"
    body += f"<pre>{log_output}</pre>"


    # --- Create the email ---
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(recipients) # Join multiple recipients
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    # Attach screenshots
    screenshot_dir = "screenshots"
    if os.path.exists(screenshot_dir):
        for filename in os.listdir(screenshot_dir):
            if filename.endswith(".png"):
                path = os.path.join(screenshot_dir, filename)
                with open(path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                msg.attach(part)
                print(f"{get_timestamp()} Attaching screenshot: {filename}")

    # --- Send the email ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"{get_timestamp()} ✅ Email report sent successfully to: {', '.join(recipients)}")
    except Exception as e:
        print(f"{get_timestamp()} ❌ Failed to send email report. Error: {e}")


def parse_arguments():
    """Parse command line arguments for browser control."""
    parser = argparse.ArgumentParser(description='Tennis Court Booking Bot')
    parser.add_argument(
        '--headless', 
        action='store_true', 
        default=not SHOW_BROWSER,
        help='Run browser in headless mode (default: based on SHOW_BROWSER env var)'
    )
    parser.add_argument(
        '--show-browser', 
        action='store_true',
        help='Show browser window (overrides --headless)'
    )
    parser.add_argument(
        '--keep-open', 
        action='store_true',
        default=KEEP_BROWSER_OPEN,
        help='Keep browser open after completion for debugging (default: based on KEEP_BROWSER_OPEN env var)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode (shows browser and keeps it open)'
    )
    
    args = parser.parse_args()
    
    # If debug mode is enabled, override other settings
    if args.debug:
        args.headless = False
        args.show_browser = True
        args.keep_open = True
    
    # If show-browser is specified, disable headless
    if args.show_browser:
        args.headless = False
    
    return args


async def main(headless=True, keep_open=False):
    """
    The main asynchronous function that orchestrates the entire booking process.
    
    Args:
        headless (bool): Whether to run browser in headless mode
        keep_open (bool): Whether to keep browser open after completion
    """
    print_london_time()
    print(f"{get_timestamp()} Browser mode: {'Headless' if headless else 'Visible'}")
    print(f"{get_timestamp()} Keep browser open: {'Yes' if keep_open else 'No'}")
    
    # Capture print statements to a string for email reporting (but still show real-time)
    log_capture_string = io.StringIO()
    
    class TeeOutput:
        def __init__(self, *outputs):
            self.outputs = outputs
        def write(self, text):
            for output in self.outputs:
                output.write(text)
                output.flush()
        def flush(self):
            for output in self.outputs:
                output.flush()
    
    # Set up dual output: console + string capture
    old_stdout = sys.stdout
    sys.stdout = TeeOutput(old_stdout, log_capture_string)
    
    slots_to_book = process_booking_file(BOOKING_FILE_PATH, GSHEET_CAM_ID, GSHEET_TAB_NAME, GOOGLE_SERVICE_ACCOUNT_JSON)
    if not slots_to_book:
        print(f"{get_timestamp()} Booking list is empty or could not be processed. Exiting.")
        return

    if not USERNAME or not PASSWORD:
        print(f"{get_timestamp()} Error: BRUCE_CAM_EMAIL_ADDRESS and BRUCE_CAM_PASSWORD secrets are not set. Exiting.")
        return
    
    if not GMAIL_APP_PASSWORD:
        print(f"{get_timestamp()} Error: GMAIL_APP_PASSWORD secret is not set. Email reporting disabled.")
    
    # Check for card details
    if not LB_CARD_NUMBER or not LB_CARD_EXPIRY_MONTH or not LB_CARD_EXPIRY_YEAR or not LB_CARD_SECURITY_CODE:
        print(f"{get_timestamp()} Warning: Card details (LB_CARD_*) not fully configured. Payment processing may fail.")
        print(f"{get_timestamp()} Required: LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH, LB_CARD_EXPIRY_YEAR, LB_CARD_SECURITY_CODE")
    else:
        print(f"{get_timestamp()} ✅ Card details configured for payment processing.")
    
    # Check for cardholder details
    if not LB_CARDHOLDER_NAME or not LB_ADDRESS or not LB_CITY or not LB_POSTCODE:
        print(f"{get_timestamp()} Warning: Cardholder details (LB_CARDHOLDER_*, LB_ADDRESS, LB_CITY, LB_POSTCODE) not fully configured.")
        print(f"{get_timestamp()} Required: LB_CARDHOLDER_NAME, LB_ADDRESS, LB_CITY, LB_POSTCODE")
    else:
        print(f"{get_timestamp()} ✅ Cardholder details configured for payment processing.")


    successful_bookings, failed_bookings = [], []

    # Don't use async context manager - keep Playwright instance alive
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=headless)
    page = await browser.new_page()

    try:
        # --- 1. Login ---
        print(f"{get_timestamp()} --- Starting Login Process ---")
        await page.goto(LOGIN_URL)
        await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
        await page.get_by_label("Email Address").fill(USERNAME)
        await page.get_by_label("Password").fill(PASSWORD)
        await page.locator("a.button-primary:has-text('Log in')").click()
        await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
        print(f"{get_timestamp()} ✅ Login successful.")

        # --- 2. Process Bookings ---
        print(f"{get_timestamp()} --- Starting Booking Process ---")
        
        # Group slots by court and date for optimized booking
        from collections import defaultdict
        slots_by_court_date = defaultdict(list)
        for slot_details in slots_to_book:
            target_court_url, target_date, target_time = slot_details
            court_name = target_court_url.split('/')[-2]
            key = (court_name, target_date, target_court_url)
            slots_by_court_date[key].append(slot_details)
        
        # Check if we should use strategic timing (near midnight)
        import pytz
        london_tz = pytz.timezone("Europe/London")
        now = datetime.now(london_tz)
        use_strategic_timing = (now.hour == 23 and now.minute >= 50) or (now.hour == 0 and now.minute <= 10)
        
        if use_strategic_timing:
            print(f"{get_timestamp()} 🎯 Strategic timing mode activated - optimizing for midnight release!")
        
        current_court_url, current_date_str = None, None
        calendar_positioned = False

        for (court_name, target_date, target_court_url), court_date_slots in slots_by_court_date.items():
            print(f"{get_timestamp()} === Processing {len(court_date_slots)} slot(s) for {court_name} on {target_date} ===")
            
            # Navigate to court if different
            if current_court_url != target_court_url:
                if not await navigate_to_court(page, target_court_url):
                    for slot_details in court_date_slots:
                        failed_bookings.append(slot_details)
                    continue
                current_court_url = target_court_url
                current_date_str = None
                calendar_positioned = False

            # Navigate to date if different
            if current_date_str != target_date:
                if not await find_date_on_calendar(page, target_date, court_date_slots[0], use_strategic_timing):
                    for slot_details in court_date_slots:
                        failed_bookings.append(slot_details)
                    continue
                current_date_str = target_date
                calendar_positioned = True

            # Book all slots for this court/date combination
            first_slot_success = False
            for i, slot_details in enumerate(court_date_slots):
                target_court_url, target_date, target_time = slot_details
                print(f"{get_timestamp()} --- Processing slot {i+1}/{len(court_date_slots)}: {target_time} ---")
                
                if await book_slot(page, target_date, target_time, slot_details):
                    successful_bookings.append(slot_details)
                    first_slot_success = True
                    
                    # If this is not the last slot for this court/date, go back to try next slot
                    if i < len(court_date_slots) - 1:
                        try:
                            print(f"{get_timestamp()} ⬅️ Going back to book additional slot on same date...")
                            await page.go_back()
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            print(f"{get_timestamp()} ✅ Successfully returned to calendar view")
                        except Exception as e:
                            print(f"{get_timestamp()} ⚠️ Could not go back: {e}. Will re-navigate to calendar...")
                            # Re-navigate if back button fails
                            if not await navigate_to_court(page, target_court_url):
                                for remaining_slot in court_date_slots[i+1:]:
                                    failed_bookings.append(remaining_slot)
                                break
                            if not await find_date_on_calendar(page, target_date, court_date_slots[i+1], False):
                                for remaining_slot in court_date_slots[i+1:]:
                                    failed_bookings.append(remaining_slot)
                                break
                else:
                    failed_bookings.append(slot_details)
            
            # Reset navigation state if we successfully booked at least one slot
            if first_slot_success:
                current_court_url, current_date_str = None, None
        
        # --- 3. Checkout ---
        if not successful_bookings:
            print(f"{get_timestamp()} No slots were added to the basket. Terminating process.")
        else:
            await checkout_basket(page, BASKET_URL, LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH, LB_CARD_EXPIRY_YEAR, LB_CARD_SECURITY_CODE, LB_CARDHOLDER_NAME, LB_ADDRESS, LB_CITY, LB_POSTCODE, USERNAME)

        # --- 4. Final Summary ---
        print(f"{get_timestamp()} --- Booking Process Finished ---")
        print(f"{get_timestamp()} Successfully booked: {len(successful_bookings)} slots.")
        if successful_bookings:
            for slot in successful_bookings:
                print(f"{get_timestamp()}   - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")
        print(f"{get_timestamp()} Failed or skipped: {len(failed_bookings)} slots.")
        if failed_bookings:
            for slot in failed_bookings:
                print(f"{get_timestamp()}   - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")

    except Exception as e:
        print(f"{get_timestamp()} ❌ A critical error occurred during the process: {e}")
        await take_screenshot(page, "critical_error")
    finally:
        # --- 5. Finalising Session ---
        print(f"{get_timestamp()} --- Finalising Session ---")
        print_london_time()
        
        # Restore stdout and get log content first
        sys.stdout = old_stdout
        log_content = log_capture_string.getvalue()

        if keep_open:
            print(f"{get_timestamp()} Skipping logout to keep session active for debugging.")
            print(f"{get_timestamp()} Browser session kept open for debugging.")
            print(f"{get_timestamp()} Press Ctrl+C to close the browser when finished.")
            # Send email report before returning
            if GMAIL_APP_PASSWORD:
                await send_email_report(log_content, successful_bookings, failed_bookings)
            return p, browser
        else:
            # Only logout if we're not keeping the browser open
            try:
                if await page.locator("a:has-text('Logout')").is_visible(timeout=5000):
                    print(f"{get_timestamp()} Logging out...")
                    await page.locator("a:has-text('Logout')").click()
                    await page.wait_for_load_state('domcontentloaded')
                    print(f"{get_timestamp()} Logout successful.")
                else:
                    print(f"{get_timestamp()} Already logged out or session expired.")
            except Exception as e:
                print(f"{get_timestamp()} ⚠️ Could not perform logout. Error: {e}")
            
            print(f"{get_timestamp()} Closing browser.")
            await browser.close()
            await p.stop()

            # Send email report
            if GMAIL_APP_PASSWORD:
                await send_email_report(log_content, successful_bookings, failed_bookings)


if __name__ == "__main__":
    args = parse_arguments()
    
    try:
        if args.keep_open:
            print(f"{get_timestamp()} Starting booking bot with browser visible and kept open...")
            print(f"{get_timestamp()} Press Ctrl+C to close the browser when finished debugging.")
            result = asyncio.run(main(headless=args.headless, keep_open=True))
            # Keep the script running to maintain the browser session
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n{get_timestamp()} Received interrupt signal. Closing browser...")
                if result:
                    playwright_instance, browser = result
                    try:
                        # Create a new event loop for cleanup
                        cleanup_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(cleanup_loop)
                        cleanup_loop.run_until_complete(browser.close())
                        cleanup_loop.run_until_complete(playwright_instance.stop())
                        cleanup_loop.close()
                    except Exception:
                        # Suppress cleanup errors - they're expected when interrupting
                        pass
                print(f"{get_timestamp()} Browser closed. Exiting.")
                # Give a moment for processes to clean up
                import time
                time.sleep(0.5)
        else:
            asyncio.run(main(headless=args.headless, keep_open=False))
    except KeyboardInterrupt:
        print(f"\n{get_timestamp()} Script interrupted by user.")
    except Exception as e:
        print(f"{get_timestamp()} An error occurred: {e}")
