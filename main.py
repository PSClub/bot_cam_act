# main.py
# This is the main entry point for the booking automation script.

import asyncio
import io
import os
import pytz
import smtplib
import sys
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
)
from data_processor import process_booking_file
from browser_actions import (
    navigate_to_court,
    find_date_on_calendar,
    book_slot,
    checkout_basket,
    take_screenshot,
)

def print_london_time():
    """Prints the current time in the London timezone."""
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    print(f"Current time in London: {now.strftime('%A, %d %B %Y at %I:%M:%S %p %Z')}")


async def send_email_report(log_output, successful_bookings, failed_bookings):
    """Sends an email report with the script's log and any screenshots."""
    print("\n--- Preparing Email Report ---")

    # --- Email Recipients ---
    # Filter out any None or empty email addresses
    recipients = [addr for addr in [RECIPIENT_KYLE, RECIPIENT_INFO] if addr]
    if not recipients:
        print("No recipient emails configured. Skipping email report.")
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
                print(f"Attaching screenshot: {filename}")

    # --- Send the email ---
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
            print(f"✅ Email report sent successfully to: {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ Failed to send email report. Error: {e}")


async def main():
    """
    The main asynchronous function that orchestrates the entire booking process.
    """
    # Capture print statements to a string
    old_stdout = sys.stdout
    sys.stdout = log_capture_string = io.StringIO()

    print_london_time()
    
    slots_to_book = process_booking_file(BOOKING_FILE_PATH)
    if not slots_to_book:
        print("Booking list is empty or could not be processed. Exiting.")
        return

    if not USERNAME or not PASSWORD:
        print("Error: CAMDEN_USERNAME and CAMDEN_PASSWORD secrets are not set. Exiting.")
        return
    
    if not GMAIL_APP_PASSWORD:
        print("Error: GMAIL_APP_PASSWORD secret is not set. Email reporting disabled.")


    successful_bookings, failed_bookings = [], []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # --- 1. Login ---
            print("\n--- Starting Login Process ---")
            await page.goto(LOGIN_URL)
            await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            await page.get_by_label("Email Address").fill(USERNAME)
            await page.get_by_label("Password").fill(PASSWORD)
            await page.locator("a.button-primary:has-text('Log in')").click()
            await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
            print("✅ Login successful.")

            # --- 2. Process Bookings ---
            print("\n--- Starting Booking Process ---")
            
            current_court_url, current_date_str = None, None

            for slot_details in slots_to_book:
                target_court_url, target_date, target_time = slot_details
                print(f"\n--- Processing: {target_court_url.split('/')[-2]} on {target_date} at {target_time} ---")
                
                if current_court_url != target_court_url:
                    if not await navigate_to_court(page, target_court_url):
                        failed_bookings.append(slot_details)
                        continue
                    current_court_url, current_date_str = target_court_url, None

                if current_date_str != target_date:
                    if not await find_date_on_calendar(page, target_date, slot_details):
                        failed_bookings.append(slot_details)
                        continue
                    current_date_str = target_date

                if await book_slot(page, target_date, target_time, slot_details):
                    successful_bookings.append(slot_details)
                    current_court_url, current_date_str = None, None
                else:
                    failed_bookings.append(slot_details)
            
            # --- 3. Checkout ---
            if not successful_bookings:
                print("\nNo slots were added to the basket. Terminating process.")
            else:
                await checkout_basket(page, BASKET_URL)

            # --- 4. Final Summary ---
            print("\n--- Booking Process Finished ---")
            print(f"Successfully booked: {len(successful_bookings)} slots.")
            if successful_bookings:
                for slot in successful_bookings:
                    print(f"  - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")
            print(f"Failed or skipped: {len(failed_bookings)} slots.")
            if failed_bookings:
                for slot in failed_bookings:
                    print(f"  - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")

        except Exception as e:
            print(f"\n❌ A critical error occurred during the process: {e}")
            await take_screenshot(page, "critical_error")
        finally:
            # --- 5. Logout and Cleanup ---
            print("\n--- Finalising Session ---")
            print_london_time()
            try:
                if await page.locator("a:has-text('Logout')").is_visible(timeout=5000):
                    print("Logging out...")
                    await page.locator("a:has-text('Logout')").click()
                    await page.wait_for_load_state('domcontentloaded')
                    print("Logout successful.")
                else:
                    print("Already logged out or session expired.")
            except Exception as e:
                print(f"⚠️ Could not perform logout. Error: {e}")
            
            print("Closing browser.")
            await browser.close()
            
            # Restore stdout and get log content
            log_content = log_capture_string.getvalue()
            sys.stdout = old_stdout
            print(log_content) # print logs to console as well

            # Send email report
            if GMAIL_APP_PASSWORD:
                await send_email_report(log_content, successful_bookings, failed_bookings)


if __name__ == "__main__":
    asyncio.run(main())
