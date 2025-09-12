#!/usr/bin/env python3
"""
Fetch Current Bookings Script
============================

This script logs into all Camden Active accounts concurrently, navigates to the
My Bookings page, scrapes all booking data, and stores it in a Google Sheet
called "Upcoming Camden Bookings".

Features:
- Concurrent login to multiple accounts
- Web scraping of booking table data
- Google Sheets integration with automatic sheet creation
- Data sorting by booking date (most recent first)
- Cron job compatible

Usage:
    python fetch_current_bookings.py

Environment Variables Required:
    - GSHEET_CAM_ID: Google Sheets ID for the main spreadsheet
    - GOOGLE_SERVICE_ACCOUNT_JSON: Service account credentials
    - MOTHER_CAM_EMAIL_ADDRESS, MOTHER_CAM_PASSWORD
    - FATHER_CAM_EMAIL_ADDRESS, FATHER_CAM_PASSWORD
    - BRUCE_CAM_EMAIL_ADDRESS, BRUCE_CAM_PASSWORD
    - SALLIE_CAM_EMAIL_ADDRESS, SALLIE_CAM_PASSWORD
    - JAN_CAM_EMAIL_ADDRESS, JAN_CAM_PASSWORD
    - JO_CAM_EMAIL_ADDRESS, JO_CAM_PASSWORD
"""

import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page
from typing import List, Dict, Optional

# Import existing modules
from config import (
    LOGIN_URL, GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
    MOTHER_EMAIL, MOTHER_PASSWORD,
    FATHER_EMAIL, FATHER_PASSWORD,
    BRUCE_EMAIL, BRUCE_PASSWORD,
    SALLIE_EMAIL, SALLIE_PASSWORD,
    JAN_EMAIL, JAN_PASSWORD,
    JO_EMAIL, JO_PASSWORD
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
        self.all_bookings = []

        # Set up accounts configuration
        self._setup_accounts()

    def _setup_accounts(self):
        """Set up the accounts configuration from environment variables."""
        account_configs = [
            ("Mother", MOTHER_EMAIL, MOTHER_PASSWORD),
            ("Father", FATHER_EMAIL, FATHER_PASSWORD),
            ("Bruce", BRUCE_EMAIL, BRUCE_PASSWORD),
            ("Sallie", SALLIE_EMAIL, SALLIE_PASSWORD),
            ("Jan", JAN_EMAIL, JAN_PASSWORD),
            ("Jo", JO_EMAIL, JO_PASSWORD)
        ]

        for name, email, password in account_configs:
            if email and password:
                self.accounts.append({'name': name, 'email': email, 'password': password})
                print(f"{get_timestamp()} ✅ Added account: {name} ({email})")
            else:
                print(f"{get_timestamp()} ⚠️ Skipping account {name}: missing credentials")

        print(f"{get_timestamp()} 📋 Configured {len(self.accounts)} accounts for booking fetch")

    async def initialize_sheets(self):
        """Initialize Google Sheets connection."""
        try:
            print(f"{get_timestamp()} === Initializing Google Sheets ===")
            if not GSHEET_MAIN_ID or not GOOGLE_SERVICE_ACCOUNT_JSON:
                raise ValueError("Google Sheets configuration not set")
            self.sheets_manager = SheetsManager(GSHEET_MAIN_ID, GOOGLE_SERVICE_ACCOUNT_JSON)
            print(f"{get_timestamp()} ✅ Google Sheets manager initialized")
            return True
        except Exception as e:
            print(f"{get_timestamp()} ❌ Failed to initialize Google Sheets: {e}")
            return False

    async def fetch_account_bookings(self, account: Dict[str, str]) -> List[Dict[str, str]]:
        """Fetch bookings for a single account."""
        playwright = None
        browser = None
        page = None
        try:
            print(f"{get_timestamp()} --- Fetching bookings for {account['name']} ({account['email']}) ---")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=os.environ.get('HEADLESS_MODE', 'True').lower() == 'true')
            page = await browser.new_page()

            await page.goto(LOGIN_URL)
            try:
                await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            except:
                pass

            await page.get_by_label("Email Address").fill(account['email'])
            await page.get_by_label("Password").fill(account['password'])
            await page.locator("a.button-primary:has-text('Log in')").click()
            await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
            print(f"{get_timestamp()} ✅ {account['name']} logged in successfully")

            my_bookings_url = "https://camdenactive.camden.gov.uk/dashboards/my-bookings/"
            await page.goto(my_bookings_url)
            print(f"{get_timestamp()} 📋 Navigated to My Bookings page for {account['name']}")

            bookings = await self._extract_booking_data(page, account['email'])
            print(f"{get_timestamp()} ✅ Extracted {len(bookings)} bookings for {account['name']}")
            return bookings

        except Exception as e:
            print(f"{get_timestamp()} ❌ Error fetching bookings for {account['name']}: {e}")
            if page:
                await take_screenshot_on_error(page, account['name'], "fetch_error")
            return []
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

    async def _extract_booking_data(self, page: Page, email: str) -> List[Dict[str, str]]:
        """Extract booking data from the My Bookings page."""
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=20000)

            no_bookings_locator = page.locator("text='You are not booked onto any courses or sessions.'")
            bookings_exist_locator = page.locator("div.wrapper.row-group")

            # Wait for either the "no bookings" message OR the booking rows to appear
            await asyncio.wait([
                no_bookings_locator.wait_for(state="visible", timeout=20000),
                bookings_exist_locator.first.wait_for(state="visible", timeout=20000)
            ], return_when=asyncio.FIRST_COMPLETED)

            if await no_bookings_locator.is_visible():
                print(f"{get_timestamp()} ℹ️ No upcoming bookings found for {email}")
                return []

            booking_rows = await bookings_exist_locator.all()
            bookings = []
            for row in booking_rows:
                try:
                    columns = await row.locator("div.booking-column").all()
                    if len(columns) >= 3:
                        booking_date_raw = await columns[0].inner_text()
                        facility_info = await columns[1].inner_text()
                        date_time_info = await columns[2].inner_text()
                        facility_name, court_number = self._parse_facility_info(facility_info)
                        booking_date_parsed, booking_time = self._parse_date_time_info(date_time_info)
                        if facility_name and booking_date_parsed:
                            bookings.append({
                                'Email': email, 'Booking Date': booking_date_raw.strip(),
                                'Facility': facility_name, 'Court Number': court_number,
                                'Date': booking_date_parsed, 'Time': booking_time
                            })
                except Exception as row_error:
                    print(f"{get_timestamp()} ⚠️ Error processing booking row: {row_error}")
            return bookings
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during data extraction for {email}: {e}")
            await take_screenshot_on_error(page, email, "extraction_error")
            return []

    def _parse_facility_info(self, facility_info: str) -> tuple:
        """Parse facility information to extract facility name and court number."""
        facility_name, court_number = facility_info.strip(), ""
        if "court" in facility_info.lower():
            parts = facility_info.split()
            for i, part in enumerate(parts):
                if "court" in part.lower() and i + 1 < len(parts):
                    court_number = f"Court {parts[i + 1]}"
                    break
            facility_name = facility_info.split("Court")[0].strip()
        return facility_name, court_number

    def _parse_date_time_info(self, date_time_info: str) -> tuple:
        """Parse date and time information from the booking data."""
        import re
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_time_info)
        time_match = re.search(r'(\d{1,2}:\d{2})', date_time_info)
        return date_match.group(1) if date_match else "", time_match.group(1) if time_match else ""

    async def fetch_all_bookings(self) -> List[Dict[str, str]]:
        """Fetch bookings from all accounts concurrently."""
        print(f"{get_timestamp()} === Starting concurrent booking fetch for {len(self.accounts)} accounts ===")
        tasks = [self.fetch_account_bookings(account) for account in self.accounts]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        all_bookings = [booking for result in results if result for booking in result]
        self.all_bookings = all_bookings
        print(f"{get_timestamp()} ✅ Total bookings fetched: {len(self.all_bookings)}")
        return self.all_bookings

    def _sort_bookings_by_date(self, bookings: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Sort bookings by date (most recent first)."""
        try:
            return sorted(bookings, key=lambda b: datetime.strptime(b.get('Date', '01/01/1970'), '%d/%m/%Y'), reverse=True)
        except Exception as e:
            print(f"{get_timestamp()} ⚠️ Error sorting bookings: {e}")
            return bookings

    async def update_google_sheet(self, bookings: List[Dict[str, str]]):
        """Update the Google Sheet with booking data."""
        try:
            print(f"{get_timestamp()} === Updating Google Sheet with {len(bookings)} bookings ===")
            sorted_bookings = self._sort_bookings_by_date(bookings)
            worksheet_name = "Upcoming Camden Bookings"
            try:
                worksheet = self.sheets_manager.spreadsheet.worksheet(worksheet_name)
            except:
                worksheet = self.sheets_manager.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            
            worksheet.clear()
            headers = ['Email', 'Booking Date', 'Facility', 'Court Number', 'Date', 'Time']
            worksheet.update(values=[headers], range_name='A1')

            if sorted_bookings:
                data_rows = [[b.get(h.replace(' ', ''), '') for h in headers] for b in sorted_bookings]
                worksheet.update(values=data_rows, range_name='A2')

            london_time = get_london_datetime()
            summary_info = [
                [f"Last Updated: {london_time.strftime('%Y-%m-%d %H:%M:%S')}"],
                [f"Total Bookings: {len(bookings)}"],
                [f"Accounts Checked: {len(self.accounts)}"]
            ]
            start_row = len(sorted_bookings) + 3
            worksheet.update(values=summary_info, range_name=f'A{start_row}')
            print(f"{get_timestamp()} ✅ Successfully updated Google Sheet")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error updating Google Sheet: {e}")

async def main():
    """Main function to fetch current bookings."""
    try:
        print(f"{get_timestamp()} 🎾 Starting Camden Active Bookings Fetch")
        print(f"{get_timestamp()} ===============================================")
        fetcher = BookingFetcher()
        if not await fetcher.initialize_sheets():
            return False
        all_bookings = await fetcher.fetch_all_bookings()
        await fetcher.update_google_sheet(all_bookings)
        print(f"{get_timestamp()} 🎉 Successfully completed bookings fetch!")
        return True
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error in main execution: {e}")
        import traceback
        print(f"{get_timestamp()} 🔍 Full error: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
