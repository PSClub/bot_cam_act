# multi_session_manager.py
# This file handles concurrent browser sessions for the multi-court booking system

import asyncio
import os
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
from utils import get_timestamp

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
        self.total_attempts = 0
        
        # Session logging and screenshots
        self.session_logs = []  # Capture all terminal output for this session
        self.screenshots_taken = []  # Track all screenshots taken during this session
        self.log_start_time = None
    
    def log_message(self, message):
        """Capture a log message for this session."""
        from utils import get_london_datetime
        timestamp = get_london_datetime().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Include milliseconds
        log_entry = f"[{timestamp}] {message}"
        self.session_logs.append(log_entry)
        print(message)  # Still print to terminal
    
    def add_screenshot(self, screenshot_path, description=""):
        """Track a screenshot taken during this session."""
        from utils import get_london_datetime
        timestamp = get_london_datetime().strftime('%Y-%m-%d %H:%M:%S')
        screenshot_info = {
            'path': screenshot_path,
            'description': description,
            'timestamp': timestamp
        }
        self.screenshots_taken.append(screenshot_info)
    
    async def initialize_browser(self, headless=os.environ.get('HEADLESS_MODE', 'True').lower() == 'true'):
        """Initialize the browser session with simplified headless parameter logic."""
        try:
            self.log_message(f"{get_timestamp()} --- Initializing browser for {self.account_name} ({self.court_number}) ---")
            
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=headless)
            self.page = await self.browser.new_page()
            
            self.log_message(f"{get_timestamp()} ✅ Browser initialized for {self.account_name} (headless={headless})")
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
            self.log_message(f"{get_timestamp()} ✅ {self.account_name} logged in successfully")
            return True
            
        except Exception as e:
            self.log_message(f"{get_timestamp()} ❌ Login failed for {self.account_name}: {e}")
            await take_screenshot(self.page, f"login_failed_{self.account_name.lower()}", session=self)
            return False
    
    async def book_slots_for_day(self, target_date, slots_to_book):
        """
        Book all specified slots for a given day.
        
        Args:
            target_date (str): Target date in DD/MM/YYYY format
            slots_to_book (list): List of time slots to book (in HHMM format)
        """
        try:
            self.log_message(f"{get_timestamp()} --- {self.account_name} booking {len(slots_to_book)} slots for {target_date} ---")
            
            # Record ALL slot attempts upfront - this ensures they're counted even if booking fails early
            self.total_attempts = len(slots_to_book)
            self.log_message(f"{get_timestamp()} 📋 Recording {self.total_attempts} slot attempts for {self.account_name}")
            
            # Pre-create failed bookings for all slots (will be removed if successful)
            for slot_time in slots_to_book:
                slot_details = (self.court_url, target_date, slot_time)
                self.failed_bookings.append(slot_details)
                
                # Log all attempts to Google Sheets immediately
                log_entry = self.sheets_manager.create_log_entry(
                    email=self.email,
                    court=self.court_number,
                    date=target_date,
                    time=slot_time,
                    status='🔄 Attempting',
                    error_details='Booking process started'
                )
                self.sheets_manager.write_booking_log(log_entry)
            
            # Navigate to court if needed
            if self.current_court_url != self.court_url:
                self.log_message(f"{get_timestamp()} 🏟️ Navigating to {self.court_number}...")
                if not await navigate_to_court(self.page, self.court_url, session=self):
                    self.log_message(f"{get_timestamp()} ❌ Failed to navigate to {self.court_number}")
                    await take_screenshot(self.page, f"navigation_failed_{self.court_number.lower()}", session=self)
                    
                    # Update all pre-recorded attempts as failed due to navigation failure
                    for slot_time in slots_to_book:
                        log_entry = self.sheets_manager.create_log_entry(
                            email=self.email,
                            court=self.court_number,
                            date=target_date,
                            time=slot_time,
                            status='❌ Failed',
                            error_details='Failed to navigate to court page'
                        )
                        self.sheets_manager.write_booking_log(log_entry)
                    
                    return False
                self.log_message(f"{get_timestamp()} ✅ Successfully navigated to {self.court_number}")
                await take_screenshot(self.page, f"court_page_{self.court_number.lower()}", session=self)
                self.current_court_url = self.court_url
                self.current_date = None
            
            # Navigate to date if needed
            if self.current_date != target_date:
                self.log_message(f"{get_timestamp()} 📅 Navigating to date {target_date}...")
                if not await find_date_on_calendar(self.page, target_date, (self.court_url, target_date, slots_to_book[0]), False, session=self):
                    self.log_message(f"{get_timestamp()} ❌ Failed to find date {target_date} for {self.court_number}")
                    await take_screenshot(self.page, f"date_not_found_{target_date.replace('/', '-')}", session=self)
                    
                    # Update all pre-recorded attempts as failed due to date not found
                    for slot_time in slots_to_book:
                        log_entry = self.sheets_manager.create_log_entry(
                            email=self.email,
                            court=self.court_number,
                            date=target_date,
                            time=slot_time,
                            status='❌ Failed',
                            error_details='Target date not found on calendar (too far in advance)'
                        )
                        self.sheets_manager.write_booking_log(log_entry)
                    
                    return False
                self.log_message(f"{get_timestamp()} ✅ Successfully navigated to date {target_date}")
                await take_screenshot(self.page, f"date_found_{target_date.replace('/', '-')}", session=self)
                self.current_date = target_date
            
            # Book each slot
            successful_slots = 0
            for slot_time in slots_to_book:
                slot_details = (self.court_url, target_date, slot_time)
                
                self.log_message(f"{get_timestamp()} 🎯 {self.account_name} attempting to book {slot_time} on {target_date}")
                
                if await book_slot(self.page, target_date, slot_time, slot_details, session=self):
                    # Remove from failed bookings and add to successful
                    if slot_details in self.failed_bookings:
                        self.failed_bookings.remove(slot_details)
                    self.successful_bookings.append(slot_details)
                    
                    # Update log entry for successful booking
                    log_entry = self.sheets_manager.create_log_entry(
                        email=self.email,
                        court=self.court_number,
                        date=target_date,
                        time=slot_time,
                        status='✅ Success',
                        error_details='Booking completed successfully'
                    )
                    self.sheets_manager.write_booking_log(log_entry)
                    
                    self.log_message(f"{get_timestamp()} ✅ {self.account_name} successfully booked {slot_time}")
                    await take_screenshot(self.page, f"booking_success_{slot_time}", session=self)
                    successful_slots += 1
                else:
                    # Update the existing failed booking entry with specific failure reason
                    log_entry = self.sheets_manager.create_log_entry(
                        email=self.email,
                        court=self.court_number,
                        date=target_date,
                        time=slot_time,
                        status='❌ Failed',
                        error_details='Slot not available or booking failed'
                    )
                    self.sheets_manager.write_booking_log(log_entry)
                    
                    self.log_message(f"{get_timestamp()} ❌ {self.account_name} failed to book {slot_time}")
                    await take_screenshot(self.page, f"booking_failed_{slot_time}", session=self)
            
            self.log_message(f"{get_timestamp()} 📊 Booking completed: {successful_slots} successful, {len(slots_to_book) - successful_slots} failed")
            
            # Return True if at least one slot was booked successfully
            return successful_slots > 0
            
        except Exception as e:
            self.log_message(f"{get_timestamp()} ❌ Error booking slots for {self.account_name}: {e}")
            await take_screenshot(self.page, f"booking_error_{self.account_name.lower()}", session=self)
            
            # Update any remaining failed bookings with the exception details
            for slot_time in slots_to_book:
                # Only log if this slot hasn't been processed yet
                slot_details = (self.court_url, target_date, slot_time)
                if slot_details in self.failed_bookings:
                    log_entry = self.sheets_manager.create_log_entry(
                        email=self.email,
                        court=self.court_number,
                        date=target_date,
                        time=slot_time,
                        status='❌ Failed',
                        error_details=f'Booking process error: {str(e)}'
                    )
                    self.sheets_manager.write_booking_log(log_entry)
            
            return False
    
    async def checkout(self):
        """Process checkout for all successful bookings."""
        try:
            if not self.successful_bookings:
                self.log_message(f"{get_timestamp()} --- {self.account_name} has no bookings to checkout ---")
                return True
            
            self.log_message(f"{get_timestamp()} --- {self.account_name} checking out {len(self.successful_bookings)} bookings ---")
            
            from config import (
                BASKET_URL, LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH, LB_CARD_EXPIRY_YEAR,
                LB_CARD_SECURITY_CODE, LB_CARDHOLDER_NAME, LB_ADDRESS, LB_CITY, LB_POSTCODE
            )
            
            success = await checkout_basket(
                self.page, BASKET_URL, LB_CARD_NUMBER, LB_CARD_EXPIRY_MONTH,
                LB_CARD_EXPIRY_YEAR, LB_CARD_SECURITY_CODE, LB_CARDHOLDER_NAME,
                LB_ADDRESS, LB_CITY, LB_POSTCODE, self.email, session=self
            )
            
            if success:
                self.log_message(f"{get_timestamp()} ✅ {self.account_name} checkout successful")
                await take_screenshot(self.page, f"checkout_success_{self.account_name.lower()}", session=self)
            else:
                self.log_message(f"{get_timestamp()} ❌ {self.account_name} checkout failed")
                await take_screenshot(self.page, f"checkout_failed_{self.account_name.lower()}", session=self)
            
            return success
            
        except Exception as e:
            self.log_message(f"{get_timestamp()} ❌ Error during checkout for {self.account_name}: {e}")
            await take_screenshot(self.page, f"checkout_error_{self.account_name.lower()}", session=self)
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
            
            # Collect results with more granular error handling
            for i, result in enumerate(booking_results):
                session = self.sessions[i]
                if isinstance(result, Exception):
                    # Handle specific exception types for better debugging
                    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
                    
                    if isinstance(result, PlaywrightTimeoutError):
                        print(f"{get_timestamp()} ❌ Booking timeout for {session.account_name}: {result}")
                        print(f"{get_timestamp()}   💡 This might be due to slow page loading or network issues")
                    elif isinstance(result, ConnectionError):
                        print(f"{get_timestamp()} ❌ Network connection failed for {session.account_name}: {result}")
                        print(f"{get_timestamp()}   💡 Check internet connection and try again")
                    elif isinstance(result, ValueError):
                        print(f"{get_timestamp()} ❌ Invalid data for {session.account_name}: {result}")
                        print(f"{get_timestamp()}   💡 Check booking date/time format or court configuration")
                    elif isinstance(result, PermissionError):
                        print(f"{get_timestamp()} ❌ Permission denied for {session.account_name}: {result}")
                        print(f"{get_timestamp()}   💡 Check browser permissions or authentication")
                    else:
                        print(f"{get_timestamp()} ❌ Unexpected error for {session.account_name}: {type(result).__name__}: {result}")
                        print(f"{get_timestamp()}   💡 This may require manual investigation")
                    
                    # Even if the session failed, collect any failed bookings that were attempted
                    self.all_failed_bookings.extend(session.failed_bookings)
                elif result:
                    print(f"{get_timestamp()} ✅ Booking completed for {session.account_name}")
                    self.all_successful_bookings.extend(session.successful_bookings)
                    self.all_failed_bookings.extend(session.failed_bookings)
                else:
                    print(f"{get_timestamp()} ❌ Booking failed for {session.account_name}")
                    # Even if the session failed, collect any failed bookings that were attempted
                    self.all_failed_bookings.extend(session.failed_bookings)
            
            total_successful = len(self.all_successful_bookings)
            total_failed = len(self.all_failed_bookings)
            
            print(f"{get_timestamp()} === Booking Summary ===")
            print(f"{get_timestamp()} ✅ Successful bookings: {total_successful}")
            print(f"{get_timestamp()} ❌ Failed bookings: {total_failed}")
            
            # Debug: Print detailed results for each session
            for session in self.sessions:
                print(f"{get_timestamp()} 📊 {session.account_name}: {len(session.successful_bookings)}✅ {len(session.failed_bookings)}❌")
                if session.successful_bookings:
                    print(f"{get_timestamp()}   ✅ Successful: {session.successful_bookings}")
                if session.failed_bookings:
                    print(f"{get_timestamp()}   ❌ Failed: {session.failed_bookings}")
            
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
        # Ensure all bookings are collected from individual sessions
        # This is crucial if all_successful_bookings/all_failed_bookings weren't populated properly
        if not self.all_successful_bookings and not self.all_failed_bookings:
            print(f"{get_timestamp()} ⚠️ Global booking lists empty, collecting from individual sessions...")
            for session in self.sessions:
                self.all_successful_bookings.extend(session.successful_bookings)
                self.all_failed_bookings.extend(session.failed_bookings)
        
        summary = {
            'total_sessions': len(self.sessions),
            'successful_bookings': len(self.all_successful_bookings),
            'failed_bookings': len(self.all_failed_bookings),
            'successful_details': self.all_successful_bookings,
            'failed_details': self.all_failed_bookings
        }
        
        # Debug: Print summary details
        print(f"{get_timestamp()} 🔍 Debug - Summary data:")
        print(f"{get_timestamp()}   Total sessions: {summary['total_sessions']}")
        print(f"{get_timestamp()}   Successful bookings: {summary['successful_bookings']}")
        print(f"{get_timestamp()}   Failed bookings: {summary['failed_bookings']}")
        print(f"{get_timestamp()}   All successful: {self.all_successful_bookings}")
        print(f"{get_timestamp()}   All failed: {self.all_failed_bookings}")
        
        return summary
    
    def get_session_details(self):
        """Get detailed information about each session's booking attempts."""
        session_details = []
        
        for session in self.sessions:
            session_info = {
                'account_name': session.account_name,
                'email': session.email,
                'court_number': session.court_number,
                'court_url': session.court_url,
                'successful_bookings': session.successful_bookings,
                'failed_bookings': session.failed_bookings,
                'total_attempts': session.total_attempts,
                'session_logs': session.session_logs,  # Include all terminal output for this session
                'screenshots_taken': session.screenshots_taken  # Include all screenshots taken
            }
            
            # Debug logging to verify counts
            print(f"{get_timestamp()} 🔍 Session details for {session.account_name}:")
            print(f"{get_timestamp()}   Total attempts: {session.total_attempts}")
            print(f"{get_timestamp()}   Successful bookings: {len(session.successful_bookings)}")
            print(f"{get_timestamp()}   Failed bookings: {len(session.failed_bookings)}")
            print(f"{get_timestamp()}   Session logs count: {len(session.session_logs)}")
            print(f"{get_timestamp()}   Screenshots count: {len(session.screenshots_taken)}")
            
            session_details.append(session_info)
        
        return session_details
