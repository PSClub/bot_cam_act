#!/usr/bin/env python3
"""
Fetch Current Bookings Script
============================

This script logs into all Camden Active accounts concurrently, navigates to the
My Bookings page, scrapes all booking data (handling multiple pages), and
stores it in a Google Sheet called "Upcoming Camden Bookings".

Features:
- Concurrent login to multiple accounts
- Web scraping of booking table data with pagination support
- Google Sheets integration with automatic sheet creation
- Data sorting by booking date (most recent first)
- Cron job compatible

Usage:
    python fetch_current_bookings.py
"""

import asyncio
import os
import json
from datetime import datetime
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
from typing import List, Dict

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
        """Fetch bookings for a single account, handling pagination."""
        playwright = browser = page = None
        all_pages_bookings = []
        try:
            print(f"{get_timestamp()} --- Fetching bookings for {account['name']} ({account['email']}) ---")
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=os.environ.get('HEADLESS_MODE', 'True').lower() == 'true')
            page = await browser.new_page()

            await page.goto(LOGIN_URL)
            try:
                await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            except: pass
            await page.get_by_label("Email Address").fill(account['email'])
            await page.get_by_label("Password").fill(account['password'])
            await page.locator("a.button-primary:has-text('Log in')").click()
            
            try:
                await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
                print(f"{get_timestamp()} ✅ {account['name']} logged in successfully")
            except PlaywrightTimeoutError:
                print(f"                                   ")
                print(f"{get_timestamp()} ❌ LOGIN FAILED for {account['name']}. Please verify credentials in GitHub.")
                print(f"                                   ")
                await take_screenshot_on_error(page, account['name'], "login_failed")
                return []

            my_bookings_url = "https://camdenactive.camden.gov.uk/dashboards/my-bookings/"
            await page.goto(my_bookings_url)
            print(f"{get_timestamp()} 📋 Navigated to My Bookings page for {account['name']}")

            page_num = 1
            while True:
                print(f"{get_timestamp()}   - Scraping page {page_num} for {account['name']}...")
                current_page_bookings = await self._extract_booking_data(page, account['email'])
                if current_page_bookings:
                    all_pages_bookings.extend(current_page_bookings)
                
                next_button = page.locator('a.button-primary:has-text("Next")')
                if await next_button.is_visible(timeout=3000) and await next_button.is_enabled():
                    print(f"{get_timestamp()}   - Next button found, navigating to page {page_num + 1}...")
                    await next_button.click()
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    page_num += 1
                else:
                    print(f"{get_timestamp()}   - No more pages of bookings found.")
                    break
            
            print(f"{get_timestamp()} ✅ Extracted {len(all_pages_bookings)} bookings across {page_num} page(s) for {account['name']}")
            return all_pages_bookings
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during booking fetch for {account['name']}: {e}")
            if page:
                await take_screenshot_on_error(page, account['name'], "fetch_error")
            return all_pages_bookings
        finally:
            if browser: await browser.close()
            if playwright: await playwright.stop()

    async def _extract_booking_data(self, page: Page, email: str) -> List[Dict[str, str]]:
        """Extract booking data from the current page using the corrected strategy."""
        bookings = []
        try:
            # Wait for the main content area to be stable and visible
            await page.locator("div.content-main").wait_for(state="visible", timeout=20000)

            # Check for the "no bookings" message first
            if await page.locator("text='You are not booked onto any courses or sessions.'").is_visible():
                print(f"{get_timestamp()}   - ℹ️ No upcoming bookings found on this page for {email}")
                return []
            
            # New Strategy: Get all column data points and group them
            all_columns = await page.locator("div.booking-column").all()
            
            # Data appears in triplets: Booking Date, Course/Facility, Date(s)
            if len(all_columns) % 3 != 0:
                print(f"{get_timestamp()} ⚠️ Warning: Unexpected number of data columns ({len(all_columns)}). Scraping may be incomplete.")

            for i in range(0, len(all_columns), 3):
                try:
                    booking_date_raw = await all_columns[i].inner_text()
                    facility_info = await all_columns[i+1].inner_text()
                    date_time_info = await all_columns[i+2].inner_text()

                    facility_name, court_number = self._parse_facility_info(facility_info)
                    booking_date_parsed, booking_time = self._parse_date_time_info(date_time_info)

                    if facility_name and booking_date_parsed:
                        bookings.append({
                            'Email': email, 'Booking Date': booking_date_raw.strip(),
                            'Facility': facility_name, 'Court Number': court_number,
                            'Date': booking_date_parsed, 'Time': booking_time
                        })
                except IndexError:
                    # This can happen if the number of columns is not a multiple of 3
                    print(f"{get_timestamp()}   - Could not process final data columns.")
                    break
                except Exception as row_error:
                    print(f"{get_timestamp()} ⚠️ Error processing a booking group: {row_error}")
            
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
        return (date_match.group(1) if date_match else "", time_match.group(1) if time_match else "")

    async def fetch_all_bookings(self) -> List[Dict[str, str]]:
        """Fetch bookings from all accounts concurrently."""
        print(f"{get_timestamp()} === Starting concurrent booking fetch for {len(self.accounts)} accounts ===")
        tasks = [self.fetch_account_bookings(account) for account in self.accounts]
        results = await asyncio.gather(*tasks)
        all_bookings = [booking for result in results for booking in result]
        self.all_bookings = all_bookings
        print(f"{get_timestamp()} ✅ Total bookings fetched across all accounts: {len(self.all_bookings)}")
        return self.all_bookings

    def _sort_bookings_by_date(self, bookings: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Sort bookings by date (most recent first)."""
        try:
            return sorted(bookings, key=lambda b: datetime.strptime(b.get('Date', '01/01/1970'), '%d/%m/%Y'), reverse=True)
        except:
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
            worksheet.update('A1', [headers])

            if sorted_bookings:
                data_rows = [
                    [
                        booking.get('Email', ''),
                        booking.get('Booking Date', ''),
                        booking.get('Facility', ''),
                        booking.get('Court Number', ''),
                        booking.get('Date', ''),
                        booking.get('Time', '')
                    ] for booking in sorted_bookings
                ]
                worksheet.update('A2', data_rows)

            london_time = get_london_datetime()
            summary_info = [
                [f"Last Updated: {london_time.strftime('%Y-%m-%d %H:%M:%S')}"],
                [f"Total Bookings: {len(bookings)}"],
                [f"Accounts Checked: {len(self.accounts)}"]
            ]
            start_row = len(sorted_bookings) + 3
            worksheet.update(f'A{start_row}', summary_info)
            print(f"{get_timestamp()} ✅ Successfully updated Google Sheet")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error updating Google Sheet: {e}")

async def main():
    """Main function to fetch current bookings."""
    try:
        print(f"{get_timestamp()} 🎾 Starting Camden Active Bookings Fetch")
        print(f"{get_timestamp()} ===============================================")
        fetcher = BookingFetcher()
        if not await fetcher.initialize_sheets(): return False
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
