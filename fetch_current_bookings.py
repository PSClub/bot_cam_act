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
from playwright.async_api import async_playwright
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
            if email and password:  # Only add accounts with valid credentials
                self.accounts.append({
                    'name': name,
                    'email': email,
                    'password': password
                })
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
        """
        Fetch bookings for a single account.

        Args:
            account: Dictionary with account details (name, email, password)

        Returns:
            List of booking dictionaries
        """
        bookings = []
        playwright = None
        browser = None

        try:
            print(f"{get_timestamp()} --- Fetching bookings for {account['name']} ({account['email']}) ---")

            # Initialize browser
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=os.environ.get('HEADLESS_MODE', 'True').lower() == 'true'
            )
            page = await browser.new_page()

            # Login to Camden Active
            await page.goto(LOGIN_URL)

            # Handle privacy banner if present
            try:
                await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            except:
                pass

            # Fill login form
            await page.get_by_label("Email Address").fill(account['email'])
            await page.get_by_label("Password").fill(account['password'])

            # Click login button
            await page.locator("a.button-primary:has-text('Log in')").click()

            # Wait for successful login
            await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
            print(f"{get_timestamp()} ✅ {account['name']} logged in successfully")

            # Navigate to My Bookings page
            my_bookings_url = "https://camdenactive.camden.gov.uk/dashboards/my-bookings/"
            await page.goto(my_bookings_url)
            print(f"{get_timestamp()} 📋 Navigated to My Bookings page for {account['name']}")

            # Wait for the booking table to load
            await page.wait_for_selector("table, .booking-table, .booking-row", timeout=10000)

            # Extract booking data from the table
            bookings = await self._extract_booking_data(page, account['email'])

            print(f"{get_timestamp()} ✅ Extracted {len(bookings)} bookings for {account['name']}")

        except Exception as e:
            print(f"{get_timestamp()} ❌ Error fetching bookings for {account['name']}: {e}")

        finally:
            # Clean up browser resources
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()

        return bookings

    async def _extract_booking_data(self, page, email: str) -> List[Dict[str, str]]:
        """
        Extract booking data from the My Bookings page.

        Args:
            page: Playwright page object
            email: Account email address

        Returns:
            List of booking dictionaries with standardized format
        """
        bookings = []

        try:
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle", timeout=10000)

            # Look for booking table rows - trying multiple selectors based on Camden Active structure
            booking_rows = await page.locator("tr:has(td)").all()

            if not booking_rows:
                print(f"{get_timestamp()} ⚠️ No booking rows found for {email}")
                return bookings

            for row in booking_rows:
                try:
                    # Extract text content from all cells in the row
                    cells = await row.locator("td").all()

                    if len(cells) >= 4:  # Minimum expected columns
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip())

                        # Parse booking data based on expected structure
                        # Expected columns: Booking Date, Course/Facility, Date(s), Details button, etc.
                        if len(cell_texts) >= 3:
                            booking_date = cell_texts[0] if cell_texts[0] else ""
                            facility_info = cell_texts[1] if cell_texts[1] else ""
                            date_time_info = cell_texts[2] if cell_texts[2] else ""

                            # Parse facility and court information
                            facility_name, court_number = self._parse_facility_info(facility_info)

                            # Parse date and time information
                            booking_date_parsed, booking_time = self._parse_date_time_info(date_time_info)

                            # Only add if we have meaningful data
                            if facility_name and booking_date_parsed:
                                booking = {
                                    'Email': email,
                                    'Booking Date': booking_date,
                                    'Facility': facility_name,
                                    'Court Number': court_number,
                                    'Date': booking_date_parsed,
                                    'Time': booking_time
                                }
                                bookings.append(booking)

                except Exception as row_error:
                    print(f"{get_timestamp()} ⚠️ Error processing booking row: {row_error}")
                    continue

        except Exception as e:
            print(f"{get_timestamp()} ❌ Error extracting booking data: {e}")

        return bookings

    def _parse_facility_info(self, facility_info: str) -> tuple:
        """Parse facility information to extract facility name and court number."""
        facility_name = facility_info
        court_number = ""

        # Look for court number patterns
        if "court" in facility_info.lower():
            parts = facility_info.split()
            for i, part in enumerate(parts):
                if "court" in part.lower() and i + 1 < len(parts):
                    court_number = f"Court {parts[i + 1]}"
                    break

            # Extract facility name (everything before court info)
            if "court" in facility_info.lower():
                facility_name = facility_info.split("Court")[0].strip()

        return facility_name, court_number

    def _parse_date_time_info(self, date_time_info: str) -> tuple:
        """Parse date and time information from the booking data."""
        booking_date = ""
        booking_time = ""

        try:
            # Look for date patterns (DD/MM/YYYY)
            import re
            date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
            date_match = re.search(date_pattern, date_time_info)
            if date_match:
                booking_date = date_match.group(1)

            # Look for time patterns (HH:MM)
            time_pattern = r'(\d{1,2}:\d{2})'
            time_match = re.search(time_pattern, date_time_info)
            if time_match:
                booking_time = time_match.group(1)

        except Exception as e:
            print(f"{get_timestamp()} ⚠️ Error parsing date/time: {e}")

        return booking_date, booking_time

    async def fetch_all_bookings(self) -> List[Dict[str, str]]:
        """
        Fetch bookings from all accounts concurrently.

        Returns:
            List of all bookings from all accounts
        """
        print(f"{get_timestamp()} === Starting concurrent booking fetch for {len(self.accounts)} accounts ===")

        # Create tasks for concurrent execution
        tasks = [self.fetch_account_bookings(account) for account in self.accounts]

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Combine all bookings
        all_bookings = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"{get_timestamp()} ❌ Error fetching bookings for {self.accounts[i]['name']}: {result}")
            else:
                all_bookings.extend(result)

        print(f"{get_timestamp()} ✅ Total bookings fetched: {len(all_bookings)}")
        self.all_bookings = all_bookings
        return all_bookings

    def _sort_bookings_by_date(self, bookings: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Sort bookings by date (most recent first).

        Args:
            bookings: List of booking dictionaries

        Returns:
            Sorted list of bookings
        """
        try:
            def parse_date(booking):
                date_str = booking.get('Date', '')
                if date_str:
                    try:
                        # Parse DD/MM/YYYY format
                        return datetime.strptime(date_str, '%d/%m/%Y')
                    except ValueError:
                        try:
                            # Try alternative formats if needed
                            return datetime.strptime(date_str, '%Y-%m-%d')
                        except ValueError:
                            pass
                return datetime.min  # Put unparseable dates at the end

            sorted_bookings = sorted(bookings, key=parse_date, reverse=True)
            print(f"{get_timestamp()} ✅ Sorted {len(sorted_bookings)} bookings by date")
            return sorted_bookings

        except Exception as e:
            print(f"{get_timestamp()} ⚠️ Error sorting bookings: {e}")
            return bookings  # Return unsorted if sorting fails

    async def update_google_sheet(self, bookings: List[Dict[str, str]]):
        """
        Update the Google Sheet with booking data.

        Args:
            bookings: List of booking dictionaries
        """
        try:
            print(f"{get_timestamp()} === Updating Google Sheet with {len(bookings)} bookings ===")

            # Sort bookings by date
            sorted_bookings = self._sort_bookings_by_date(bookings)

            # Create or get the worksheet
            worksheet_name = "Upcoming Camden Bookings"

            try:
                worksheet = self.sheets_manager.spreadsheet.worksheet(worksheet_name)
                print(f"{get_timestamp()} ✅ Found existing worksheet: {worksheet_name}")
            except:
                # Create new worksheet if it doesn't exist
                worksheet = self.sheets_manager.spreadsheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=10
                )
                print(f"{get_timestamp()} ✅ Created new worksheet: {worksheet_name}")

            # Clear existing data
            worksheet.clear()

            # Set up headers
            headers = ['Email', 'Booking Date', 'Facility', 'Court Number', 'Date', 'Time']
            worksheet.update(range_name='A1', values=[headers])

            # Prepare data rows
            data_rows = []
            for booking in sorted_bookings:
                row = [
                    booking.get('Email', ''),
                    booking.get('Booking Date', ''),
                    booking.get('Facility', ''),
                    booking.get('Court Number', ''),
                    booking.get('Date', ''),
                    booking.get('Time', '')
                ]
                data_rows.append(row)

            # Update the sheet with all data at once
            if data_rows:
                worksheet.update(range_name='A2', values=data_rows)

            # Add timestamp and summary
            london_time = get_london_datetime()
            summary_info = [
                [f"Last Updated: {london_time.strftime('%Y-%m-%d %H:%M:%S')}"],
                [f"Total Bookings: {len(bookings)}"],
                [f"Accounts Checked: {len(self.accounts)}"]
            ]

            start_row = len(data_rows) + 3
            worksheet.update(range_name=f'A{start_row}', values=summary_info)

            print(f"{get_timestamp()} ✅ Successfully updated Google Sheet with {len(bookings)} bookings")

        except Exception as e:
            print(f"{get_timestamp()} ❌ Error updating Google Sheet: {e}")
            raise


async def main():
    """Main function to fetch current bookings."""
    try:
        print(f"{get_timestamp()} 🎾 Starting Camden Active Bookings Fetch")
        print(f"{get_timestamp()} ===============================================")

        # Initialize booking fetcher
        fetcher = BookingFetcher()

        # Initialize Google Sheets
        if not await fetcher.initialize_sheets():
            print(f"{get_timestamp()} ❌ Failed to initialize Google Sheets")
            return False

        # Fetch all bookings concurrently
        all_bookings = await fetcher.fetch_all_bookings()

        if not all_bookings:
            print(f"{get_timestamp()} ⚠️ No bookings found across all accounts")
            # Still update the sheet to show it was checked
            await fetcher.update_google_sheet([])
            return True

        # Update Google Sheet
        await fetcher.update_google_sheet(all_bookings)

        print(f"{get_timestamp()} 🎉 Successfully completed bookings fetch!")
        print(f"{get_timestamp()} 📊 Total bookings found: {len(all_bookings)}")

        return True

    except Exception as e:
        print(f"{get_timestamp()} ❌ Error in main execution: {e}")
        import traceback
        print(f"{get_timestamp()} 🔍 Full error: {traceback.format_exc()}")
        return False


if __name__ == "__main__":
    import sys

    # Run the async main function
    success = asyncio.run(main())

    # Exit with appropriate code
    sys.exit(0 if success else 1)
