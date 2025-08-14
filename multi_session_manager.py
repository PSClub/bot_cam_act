# multi_session_manager.py
# This file handles concurrent browser sessions for the multi-court booking system

import asyncio
import os
import pytz
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from sheets_manager import SheetsManager
from robust_parser import normalize_day_name, normalize_time, get_slots_for_day
from browser_actions import (
    navigate_to_court,
    find_date_on_calendar,
    book_slot,
    checkout_basket,
    take_screenshot
)

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

class BookingSession:
    """Represents a single booking session for one court/email combination."""
    
    def __init__(self, account_name, email, password, court_number, court_url, sheets_manager):
        """
        Initialize a booking session.
        
        Args:
            account_name (str): Account name (e.g., "Mother", "Father", "Bruce")
            email (str): Email address for this account
            password (str): Password for this account
            court_number (str): Court number (e.g., "Court 1")
            court_url (str): Court booking URL
            sheets_manager (SheetsManager): Google Sheets manager instance
        """
        self.account_name = account_name
        self.email = email
        self.password = password
        self.court_number = court_number
        self.court_url = court_url
        self.sheets_manager = sheets_manager
        
        # Browser session components
        self.browser = None
        self.page = None
        self.playwright = None
        
        # Session state
        self.is_logged_in = False
        self.current_court_url = None
        self.current_date = None
        
        # Booking results
        self.successful_bookings = []
        self.failed_bookings = []
    
    async def initialize_browser(self, headless=True):
        """Initialize the browser session."""
        try:
            print(f"{get_timestamp()} --- Initializing browser for {self.account_name} ({self.court_number}) ---")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.page = await self.browser.new_page()
            
            print(f"{get_timestamp()} ✅ Browser initialized for {self.account_name}")
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Failed to initialize browser for {self.account_name}: {e}")
            return False
    
    async def login(self):
        """Login to the Camden Active website."""
        try:
            print(f"{get_timestamp()} --- Logging in {self.account_name} ({self.email}) ---")
            
            from config import LOGIN_URL
            
            # Navigate to login page
            await self.page.goto(LOGIN_URL)
            
            # Handle privacy banner if present
            try:
                await self.page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            except:
                pass  # Privacy banner might not be present
            
            # Fill login form
            await self.page.get_by_label("Email Address").fill(self.email)
            await self.page.get_by_label("Password").fill(self.password)
            
            # Click login button
            await self.page.locator("a.button-primary:has-text('Log in')").click()
            
            # Wait for successful login
            await self.page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
            
            self.is_logged_in = True
            print(f"{get_timestamp()} ✅ {self.account_name} logged in successfully")
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Login failed for {self.account_name}: {e}")
            await take_screenshot(self.page, f"login_failed_{self.account_name.lower()}")
            return False
    
    async def book_slots_for_day(self, target_date, slots_to_book):
        """
        Book all specified slots for a given day.
        
        Args:
            target_date (str): Target date in DD/MM/YYYY format
            slots_to_book (list): List of time slots to book (in HHMM format)
        """
        try:
            print(f"{get_timestamp()} --- {self.account_name} booking {len(slots_to_book)} slots for {target_date} ---")
            
            # Navigate to court if needed
            if self.current_court_url != self.court_url:
                if not await navigate_to_court(self.page, self.court_url):
                    print(f"{get_timestamp()} ❌ Failed to navigate to {self.court_number}")
                    return False
                self.current_court_url = self.court_url
                self.current_date = None
            
            # Navigate to date if needed
            if self.current_date != target_date:
                if not await find_date_on_calendar(self.page, target_date, (self.court_url, target_date, slots_to_book[0]), False):
                    print(f"{get_timestamp()} ❌ Failed to find date {target_date} for {self.court_number}")
                    return False
                self.current_date = target_date
            
            # Book each slot
            for slot_time in slots_to_book:
                slot_details = (self.court_url, target_date, slot_time)
                
                print(f"{get_timestamp()} --- {self.account_name} booking {slot_time} on {target_date} ---")
                
                if await book_slot(self.page, target_date, slot_time, slot_details):
                    self.successful_bookings.append(slot_details)
                    
                    # Log successful booking
                    log_entry = {
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Email': self.email,
                        'Court': self.court_number,
                        'Date': target_date,
                        'Time': slot_time,
                        'Status': '✅ Success',
                        'Error Details': ''
                    }
                    await self.sheets_manager.write_booking_log(log_entry)
                    
                    print(f"{get_timestamp()} ✅ {self.account_name} successfully booked {slot_time}")
                else:
                    self.failed_bookings.append(slot_details)
                    
                    # Log failed booking
                    log_entry = {
                        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Email': self.email,
                        'Court': self.court_number,
                        'Date': target_date,
                        'Time': slot_time,
                        'Status': '❌ Failed',
                        'Error Details': 'Slot not available or booking failed'
                    }
                    await self.sheets_manager.write_booking_log(log_entry)
                    
                    print(f"{get_timestamp()} ❌ {self.account_name} failed to book {slot_time}")
            
            return True
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error booking slots for {self.account_name}: {e}")
            await take_screenshot(self.page, f"booking_error_{self.account_name.lower()}")
            return False
    
    async def checkout(self):
        """Process checkout for all successful bookings."""
        try:
            if not self.successful_bookings:
                print(f"{get_timestamp()} --- {self.account_name} has no bookings to checkout ---")
                return True
            
            print(f"{get_timestamp()} --- {self.account_name} checking out {len(self.successful_bookings)} bookings ---")
            
            from config import (
                BASKET_URL, LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH, LB_CARD_EXPIRY_YEAR,
                LB_CARD_SECURITY_CODE, LB_CARDHOLDER_NAME, LB_ADDRESS, LB_CITY, LB_POSTCODE
            )
            
            success = await checkout_basket(
                self.page, BASKET_URL, LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH,
                LB_CARD_EXPIRY_YEAR, LB_CARD_SECURITY_CODE, LB_CARDHOLDER_NAME,
                LB_ADDRESS, LB_CITY, LB_POSTCODE, self.email
            )
            
            if success:
                print(f"{get_timestamp()} ✅ {self.account_name} checkout successful")
            else:
                print(f"{get_timestamp()} ❌ {self.account_name} checkout failed")
            
            return success
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during checkout for {self.account_name}: {e}")
            await take_screenshot(self.page, f"checkout_error_{self.account_name.lower()}")
            return False
    
    async def logout(self):
        """Logout from the website."""
        try:
            if self.is_logged_in and self.page:
                print(f"{get_timestamp()} --- Logging out {self.account_name} ---")
                
                try:
                    if await self.page.locator("a:has-text('Logout')").is_visible(timeout=5000):
                        await self.page.locator("a:has-text('Logout')").click()
                        await self.page.wait_for_load_state('domcontentloaded')
                        print(f"{get_timestamp()} ✅ {self.account_name} logged out successfully")
                    else:
                        print(f"{get_timestamp()} ⚠️ {self.account_name} already logged out or session expired")
                except Exception as e:
                    print(f"{get_timestamp()} ⚠️ Could not logout {self.account_name}: {e}")
                
                self.is_logged_in = False
                
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during logout for {self.account_name}: {e}")
    
    async def cleanup(self):
        """Clean up browser resources."""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print(f"{get_timestamp()} ✅ {self.account_name} browser session cleaned up")
        except Exception as e:
            print(f"{get_timestamp()} ⚠️ Error cleaning up {self.account_name} browser: {e}")

class MultiSessionManager:
    """Manages multiple concurrent booking sessions."""
    
    def __init__(self, sheets_manager):
        """
        Initialize the multi-session manager.
        
        Args:
            sheets_manager (SheetsManager): Google Sheets manager instance
        """
        self.sheets_manager = sheets_manager
        self.sessions = []
        self.all_successful_bookings = []
        self.all_failed_bookings = []
    
    async def initialize_sessions(self, headless=True):
        """Initialize all booking sessions."""
        try:
            print(f"{get_timestamp()} === Initializing Multi-Session Booking System ===")
            
            # Read configuration from Google Sheets
            config_data = self.sheets_manager.read_configuration_sheet()
            
            # Create booking sessions for each account
            for config_entry in config_data:
                account_name = config_entry.get('Account', '')
                email = config_entry.get('Email', '')
                court_number = config_entry.get('Court Number', '')
                court_url = config_entry.get('Court URL', '')
                
                # Get password from environment variables
                password_env_var = f"{account_name.upper()}_CAM_PASSWORD"
                password = os.environ.get(password_env_var)
                
                if not all([account_name, email, password, court_number, court_url]):
                    print(f"{get_timestamp()} ⚠️ Skipping incomplete configuration for {account_name}")
                    continue
                
                # Create booking session
                session = BookingSession(
                    account_name=account_name,
                    email=email,
                    password=password,
                    court_number=court_number,
                    court_url=court_url,
                    sheets_manager=self.sheets_manager
                )
                
                # Initialize browser
                if await session.initialize_browser(headless):
                    self.sessions.append(session)
                    print(f"{get_timestamp()} ✅ Session initialized for {account_name}")
                else:
                    print(f"{get_timestamp()} ❌ Failed to initialize session for {account_name}")
            
            print(f"{get_timestamp()} ✅ Initialized {len(self.sessions)} booking sessions")
            return len(self.sessions) > 0
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error initializing sessions: {e}")
            return False
    
    async def login_all_sessions(self):
        """Login to all sessions concurrently."""
        try:
            print(f"{get_timestamp()} === Logging in all sessions ===")
            
            # Login to all sessions concurrently
            login_tasks = [session.login() for session in self.sessions]
            login_results = await asyncio.gather(*login_tasks, return_exceptions=True)
            
            successful_logins = 0
            for i, result in enumerate(login_results):
                if isinstance(result, Exception):
                    print(f"{get_timestamp()} ❌ Login failed for {self.sessions[i].account_name}: {result}")
                elif result:
                    successful_logins += 1
                    print(f"{get_timestamp()} ✅ Login successful for {self.sessions[i].account_name}")
                else:
                    print(f"{get_timestamp()} ❌ Login failed for {self.sessions[i].account_name}")
            
            print(f"{get_timestamp()} ✅ {successful_logins}/{len(self.sessions)} sessions logged in successfully")
            return successful_logins > 0
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during login process: {e}")
            return False
    
    async def book_all_courts_for_day(self, target_date, slots_to_book):
        """
        Book all courts for a given day and time slots.
        
        Args:
            target_date (str): Target date in DD/MM/YYYY format
            slots_to_book (list): List of time slots to book (in HHMM format)
        """
        try:
            print(f"{get_timestamp()} === Booking all courts for {target_date} ===")
            print(f"{get_timestamp()} 📅 Slots to book: {', '.join(slots_to_book)}")
            
            # Book all courts concurrently
            booking_tasks = [
                session.book_slots_for_day(target_date, slots_to_book)
                for session in self.sessions
            ]
            booking_results = await asyncio.gather(*booking_tasks, return_exceptions=True)
            
            # Collect results
            for i, result in enumerate(booking_results):
                session = self.sessions[i]
                if isinstance(result, Exception):
                    print(f"{get_timestamp()} ❌ Booking failed for {session.account_name}: {result}")
                elif result:
                    print(f"{get_timestamp()} ✅ Booking completed for {session.account_name}")
                    self.all_successful_bookings.extend(session.successful_bookings)
                    self.all_failed_bookings.extend(session.failed_bookings)
                else:
                    print(f"{get_timestamp()} ❌ Booking failed for {session.account_name}")
            
            total_successful = len(self.all_successful_bookings)
            total_failed = len(self.all_failed_bookings)
            
            print(f"{get_timestamp()} === Booking Summary ===")
            print(f"{get_timestamp()} ✅ Successful bookings: {total_successful}")
            print(f"{get_timestamp()} ❌ Failed bookings: {total_failed}")
            
            return total_successful > 0
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during booking process: {e}")
            return False
    
    async def checkout_all_sessions(self):
        """Process checkout for all sessions."""
        try:
            print(f"{get_timestamp()} === Processing checkout for all sessions ===")
            
            # Checkout all sessions concurrently
            checkout_tasks = [session.checkout() for session in self.sessions]
            checkout_results = await asyncio.gather(*checkout_tasks, return_exceptions=True)
            
            successful_checkouts = 0
            for i, result in enumerate(checkout_results):
                if isinstance(result, Exception):
                    print(f"{get_timestamp()} ❌ Checkout failed for {self.sessions[i].account_name}: {result}")
                elif result:
                    successful_checkouts += 1
                    print(f"{get_timestamp()} ✅ Checkout successful for {self.sessions[i].account_name}")
                else:
                    print(f"{get_timestamp()} ❌ Checkout failed for {self.sessions[i].account_name}")
            
            print(f"{get_timestamp()} ✅ {successful_checkouts}/{len(self.sessions)} sessions checked out successfully")
            return successful_checkouts > 0
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during checkout process: {e}")
            return False
    
    async def logout_all_sessions(self):
        """Logout from all sessions."""
        try:
            print(f"{get_timestamp()} === Logging out all sessions ===")
            
            # Logout all sessions concurrently
            logout_tasks = [session.logout() for session in self.sessions]
            await asyncio.gather(*logout_tasks, return_exceptions=True)
            
            print(f"{get_timestamp()} ✅ All sessions logged out")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during logout process: {e}")
    
    async def cleanup_all_sessions(self):
        """Clean up all browser sessions."""
        try:
            print(f"{get_timestamp()} === Cleaning up all sessions ===")
            
            # Cleanup all sessions concurrently
            cleanup_tasks = [session.cleanup() for session in self.sessions]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            print(f"{get_timestamp()} ✅ All sessions cleaned up")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error during cleanup process: {e}")
    
    def get_booking_summary(self):
        """Get a summary of all booking results."""
        return {
            'total_sessions': len(self.sessions),
            'successful_bookings': len(self.all_successful_bookings),
            'failed_bookings': len(self.all_failed_bookings),
            'successful_details': self.all_successful_bookings,
            'failed_details': self.all_failed_bookings
        }
