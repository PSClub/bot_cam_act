#!/usr/bin/env python3
"""
Fetch Current Bookings Script
============================

This script logs into all Camden Active accounts concurrently, navigates to the
My Bookings page, scrapes all booking data (handling multiple pages), filters
for upcoming bookings, sorts them, and stores them in a Google Sheet. It also
sends an email summary.
"""

import asyncio
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict, Tuple

# Import existing modules
from config import (
    LOGIN_URL, GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
    MOTHER_EMAIL, MOTHER_PASSWORD, FATHER_EMAIL, FATHER_PASSWORD,
    BRUCE_EMAIL, BRUCE_PASSWORD, SALLIE_EMAIL, SALLIE_PASSWORD,
    JAN_EMAIL, JAN_PASSWORD, JO_EMAIL, JO_PASSWORD,
    SENDER_EMAIL, GMAIL_APP_PASSWORD, IT_EMAIL_ADDRESS, KYLE_EMAIL_ADDRESS, RECIPIENT_INFO
)
from sheets_manager import SheetsManager
from utils import get_timestamp, get_london_datetime


async def take_screenshot_on_error(page: Page, account_name: str, reason: str):
    """Takes a screenshot on error for debugging."""
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = get_london_datetime().strftime("%y%m%d_%H%M%S")
    filename = f"{timestamp}_{account_name}_{reason}.png"
    filepath = os.path.join(screenshot_dir, filename)
    try:
        await page.screenshot(path=filepath, full_page=True)
        print(f"{get_timestamp()} 📸 Screenshot saved for {account_name}: {filepath}")
    except Exception as e:
        print(f"{get_timestamp()} ❌ Could not save screenshot for {account_name}. Error: {e}")


class BookingFetcher:
    """Handles fetching current bookings from Camden Active accounts."""

    def __init__(self):
        """Initialize the booking fetcher."""
        self.sheets_manager = None
        self.accounts = []
        self.upcoming_bookings = []
        self.past_bookings = []
        self.fetch_summary = {}
        self._setup_accounts()

    def _setup_accounts(self):
        """Set up the accounts configuration from environment variables."""
        account_configs = [
            ("Mother", MOTHER_EMAIL, MOTHER_PASSWORD), ("Father", FATHER_EMAIL, FATHER_PASSWORD),
            ("Bruce", BRUCE_EMAIL, BRUCE_PASSWORD), ("Sallie", SALLIE_EMAIL, SALLIE_PASSWORD),
            ("Jan", JAN_EMAIL, JAN_PASSWORD), ("Jo", JO_EMAIL, JO_PASSWORD)
        ]
        for name, email, password in account_configs:
            if email and password:
                self.accounts.append({'name': name, 'email': email, 'password': password})
        print(f"{get_timestamp()} 📋 Configured {len(self.accounts)} accounts for booking fetch")

    async def initialize_systems(self):
        """Initialize Google Sheets and Email manager."""
        try:
            print(f"{get_timestamp()} === Initializing External Systems ===")
            if not GSHEET_MAIN_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
                raise ValueError("Google Sheets configuration not set")
            self.sheets_manager = SheetsManager(GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
            print(f"{get_timestamp()} ✅ Google Sheets manager initialized")
            return True
        except Exception as e:
            print(f"{get_timestamp()} ❌ Failed to initialize external systems: {e}")
            return False

    async def fetch_account_bookings(self, account: Dict[str, str]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Fetch bookings for a single account, handling pagination."""
        playwright = browser = page = None
        all_pages_bookings = []
        try:
            print(f"{get_timestamp()} --- Fetching bookings for {account['name']} ---")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=os.environ.get('HEADLESS_MODE', 'True').lower() == 'true')
            page = await browser.new_page()

            await page.goto(LOGIN_URL)
            await page.get_by_label("Email Address").fill(account['email'])
            await page.get_by_label("Password").fill(account['password'])
            await page.locator("a.button-primary:has-text('Log in')").click()
            
            try:
                await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
                print(f"{get_timestamp()} ✅ {account['name']} logged in successfully")
            except PlaywrightTimeoutError:
                print(f"\n{get_timestamp()} ❌ LOGIN FAILED for {account['name']}.\n")
                await take_screenshot_on_error(page, account['name'], "login_failed")
                self.fetch_summary[account['email']] = "Login Failed" # Use email for summary key
                return [], []

            await page.goto("https://camdenactive.camden.gov.uk/dashboards/my-bookings/")
            page_num = 1
            while True:
                print(f"{get_timestamp()}   - Scraping page {page_num} for {account['name']}...")
                all_pages_bookings.extend(await self._extract_booking_data(page, account['email']))
                next_button = page.locator('a.button-primary:has-text("Next")')
                if await next_button.is_visible(timeout=2000) and await next_button.is_enabled():
                    await next_button.click()
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    page_num += 1
                else:
                    break
            
            upcoming, past = self._filter_and_separate_bookings(all_pages_bookings)
            self.fetch_summary[account['email']] = f"{len(upcoming)} upcoming bookings found"
            return upcoming, past
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error fetching for {account['name']}: {e}")
            self.fetch_summary[account['email']] = "Error" # Use email for summary key
            if page: await take_screenshot_on_error(page, account['name'], "fetch_error")
            return [], []
        finally:
            if browser: await browser.close()
            if playwright: await playwright.stop()

    def _filter_and_separate_bookings(self, bookings: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """Filters bookings into upcoming and past/invalid lists."""
        today = get_london_datetime().date()
        upcoming, past_or_invalid = [], []
        for booking in bookings:
            try:
                if not booking.get('Date'):
                    booking['ReasonFiltered'] = 'Missing Date'
                    past_or_invalid.append(booking)
                    continue
                booking_date = datetime.strptime(booking['Date'], '%d/%m/%Y').date()
                if booking_date >= today:
                    # Add Day of the week
                    booking['Day'] = booking_date.strftime('%a')
                    upcoming.append(booking)
                else:
                    booking['ReasonFiltered'] = 'Date in the Past'
                    past_or_invalid.append(booking)
            except (ValueError, KeyError):
                booking['ReasonFiltered'] = 'Invalid Date Format'
                past_or_invalid.append(booking)
        return upcoming, past_or_invalid

    async def _extract_booking_data(self, page: Page, email: str) -> List[Dict[str, str]]:
        """Extract booking data from the current page."""
        bookings = []
        try:
            if await page.locator("text='You are not booked onto any courses or sessions.'").is_visible(timeout=5000):
                return []
            all_columns = await page.locator("div.booking-column").all_inner_texts()
            for i in range(0, len(all_columns), 3):
                date_booking_made_raw, facility_info, date_time_info = all_columns[i:i+3]
                facility_name, court_number = self._parse_facility_info(facility_info)
                booking_date_parsed, booking_time = self._parse_date_time_info(date_time_info)
                bookings.append({
                    'Email': email, 'Facility': facility_name, 'Court Number': court_number,
                    'Date': booking_date_parsed, 'Time': booking_time or "Multiple Slots",
                    'Date Booking Made': date_booking_made_raw.strip()
                })
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during data extraction for {email}: {e}")
        return bookings

    def _parse_facility_info(self, facility_info: str) -> tuple:
        """Parse facility information to extract facility name and court number."""
        facility_name, court_number = facility_info.strip(), ""
        parts = facility_info.split()
        for i, part in enumerate(parts):
            if "court" in part.lower() and i + 1 < len(parts) and parts[i+1].isdigit():
                court_number = f"Court {parts[i + 1]}"
                break
        facility_name = facility_info.split("Court")[0].strip()
        return facility_name, court_number

    def _parse_date_time_info(self, date_time_info: str) -> tuple:
        """Parse date and time information from the booking data."""
        import re
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_time_info)
        time_match = re.search(r'(\d{1,2}:\d{2})', date_time_info)
        return (date_match.group(1) if date_match else "", time_match.group(1) if time_match else "")

    async def fetch_all_bookings(self):
        """Fetch bookings from all accounts concurrently."""
        print(f"{get_timestamp()} === Starting concurrent booking fetch ===")
        tasks = [self.fetch_account_bookings(account) for account in self.accounts]
        results = await asyncio.gather(*tasks)
        for upcoming_list, past_list in results:
            self.upcoming_bookings.extend(upcoming_list)
            self.past_bookings.extend(past_list)
        print(f"\n{get_timestamp()} === Overall Fetch Summary ===")
        for account in self.accounts:
            print(f"{get_timestamp()}   - {account['name']}: {self.fetch_summary.get(account['email'], 'Not Processed')}")
        print(f"{get_timestamp()} ✅ Total upcoming bookings: {len(self.upcoming_bookings)}")
        print(f"{get_timestamp()} - Total past/invalid filtered: {len(self.past_bookings)}")

    def _sort_bookings(self, bookings: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Sort bookings primarily by date (ascending, closest first)."""
        def sort_key(b):
            try:
                date_obj = datetime.strptime(b.get('Date', '31/12/9999'), '%d/%m/%Y')
            except ValueError:
                date_obj = datetime.strptime('31/12/9999', '%d/%m/%Y')
            return (date_obj, b.get('Time', ''), b.get('Facility', ''), b.get('Court Number', ''))
        return sorted(bookings, key=sort_key)

    async def update_google_sheet(self, bookings: List[Dict[str, str]], sheet_name: str, headers: List[str]):
        """Update a Google Sheet with booking data and format the date column."""
        if not self.sheets_manager: return
        try:
            print(f"\n{get_timestamp()} === Updating '{sheet_name}' Sheet... ===")
            sorted_bookings = self._sort_bookings(bookings)
            
            try:
                worksheet = self.sheets_manager.spreadsheet.worksheet(sheet_name)
            except:
                worksheet = self.sheets_manager.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)

            worksheet.clear()
            worksheet.update('A1', [headers])

            if sorted_bookings:
                data_rows = [[booking.get(key, '') for key in headers] for booking in sorted_bookings]
                worksheet.update('A2', data_rows)
                
                try:
                    date_col_letter = chr(ord('A') + headers.index('Date'))
                    worksheet.format(
                        f"{date_col_letter}2:{date_col_letter}",
                        {"numberFormat": {"type": "DATE", "pattern": "dd/mm/yyyy"}}
                    )
                except ValueError:
                    print(f"{get_timestamp()} ⚠️ 'Date' column not in headers; skipping date formatting.")

            if sheet_name == "Upcoming Camden Bookings":
                summary_info = [
                    [f"Last Updated: {get_london_datetime().strftime('%Y-%m-%d %H:%M:%S')}"],
                    [f"Total Upcoming Bookings: {len(bookings)}"]
                ]
                worksheet.update(f'A{len(sorted_bookings) + 3}', summary_info)
            print(f"{get_timestamp()} ✅ Successfully updated '{sheet_name}' Sheet")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error updating '{sheet_name}' Sheet: {e}")

    async def send_summary_email(self):
        """Sends an email with the summary of bookings."""
        if not all([SENDER_EMAIL, GMAIL_APP_PASSWORD, any([IT_EMAIL_ADDRESS, KYLE_EMAIL_ADDRESS, RECIPIENT_INFO])]):
            print(f"{get_timestamp()} 📧 Email configuration missing (sender, password, or recipient), skipping email.")
            return

        print(f"\n{get_timestamp()} === Preparing and Sending Summary Email ===")
        subject = f"Upcoming Camden Tennis Bookings Summary - {get_london_datetime().strftime('%d-%m-%Y')}"
        
        # Build the summary list using emails
        summary_list_html = ""
        for account in self.accounts:
            email = account['email']
            result = self.fetch_summary.get(email, "Not Processed")
            # Highlight failures explicitly
            if "Failed" in result or "Error" in result:
                summary_list_html += f"<li><b>{email}: <span style='color:red;'>{result}</span></b></li>"
            else:
                summary_list_html += f"<li><b>{email}:</b> {result}</li>"

        # Sort bookings for the email body
        sorted_for_email = self._sort_bookings(self.upcoming_bookings)

        # Generate HTML table rows with the new 'Day' column
        table_rows = ""
        if not sorted_for_email:
            table_rows = '<tr><td colspan="7" style="text-align:center;">No upcoming bookings found.</td></tr>'
        else:
            for b in sorted_for_email:
                table_rows += (f"<tr><td>{b.get('Facility','')}</td><td>{b.get('Court Number','')}</td>"
                               f"<td>{b.get('Date','')}</td><td>{b.get('Day','')}</td>"
                               f"<td>{b.get('Time','')}</td><td>{b.get('Email','')}</td>"
                               f"<td>{b.get('Date Booking Made','')}</td></tr>")

        body = f"""
        <html><body>
        <p>This e-mail summarises all future Camden Active bookings for the accounts listed below.</p>
        <h2>Upcoming Bookings ({len(self.upcoming_bookings)})</h2>
        <p>Generated: {get_london_datetime().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <h3>Fetch Summary</h3>
        <ul>{summary_list_html}</ul>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse:collapse;width:100%;font-family:sans-serif;">
        <tr style="background-color:#f2f2f2;"><th>Facility</th><th>Court Number</th><th>Date</th><th>Day</th><th>Time</th><th>Email</th><th>Date Booking Made</th></tr>
        {table_rows}
        </table>
        <p style="margin-top:15px;font-size:small;">
        <i><b>{len(self.past_bookings)}</b> past or invalid bookings were filtered. The full list, including the "Camden Active Booking Dates", can be found on the club's Google Drive.</i>
        </p>
        </body></html>"""
        
        recipients = [rcpt for rcpt in [IT_EMAIL_ADDRESS, KYLE_EMAIL_ADDRESS, RECIPIENT_INFO] if rcpt]
        for recipient in recipients:
            try:
                await self._send_html_email(recipient, subject, body)
            except Exception as e:
                print(f"{get_timestamp()} ❌ Email sending failed for recipient {recipient}: {e}")

    async def _send_html_email(self, recipient, subject, html_body):
        """A self-contained function to send HTML emails."""
        server = None
        try:
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            print(f"{get_timestamp()}     📧 SMTP: Connecting and sending to {recipient}...")
            server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
            server.starttls()
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, [recipient], msg.as_string())
            print(f"{get_timestamp()}     ✅ SMTP: Email sent successfully to {recipient}")
        finally:
            if server:
                server.quit()

async def main():
    """Main function to fetch current bookings."""
    fetcher = BookingFetcher()
    if not await fetcher.initialize_systems(): return
    await fetcher.fetch_all_bookings()

    # Add 'Day' to headers for the upcoming bookings sheet
    upcoming_headers = ['Email', 'Facility', 'Court Number', 'Date', 'Day', 'Time', 'Date Booking Made']
    await fetcher.update_google_sheet(fetcher.upcoming_bookings, "Upcoming Camden Bookings", upcoming_headers)

    past_headers = ['Email', 'Facility', 'Court Number', 'Date', 'Time', 'ReasonFiltered', 'Date Booking Made']
    await fetcher.update_google_sheet(fetcher.past_bookings, "Filtered Out Bookings", past_headers)
    
    await fetcher.send_summary_email()
    print(f"\n{get_timestamp()} 🎉 Successfully completed bookings fetch!")

if __name__ == "__main__":
    asyncio.run(main())
