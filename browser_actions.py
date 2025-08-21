# browser_actions.py
# This file contains all the core browser automation functions.

import os
import pytz
import asyncio
import time
from datetime import datetime, timedelta
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from utils import get_timestamp

# --- Updated Screenshot Helper Function ---
async def take_screenshot(page, reason, slot_details=None, session=None):
    """
    Takes a full-page screenshot with a descriptive, timestamped filename
    and saves it to the 'screenshots' directory.
    
    Args:
        page: Playwright page object
        reason: Description of why screenshot was taken
        slot_details: Optional slot details for filename
        session: Optional BookingSession to track the screenshot
    
    Returns:
        str: Path to the saved screenshot file, or None if failed
    """
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    timestamp = now.strftime("%y.%m.%d_%H-%M-%S")
    
    sanitized_reason = reason.replace(" ", "_").replace(":", "").replace("/", "-")
    
    # Add slot details to the filename if they are provided
    if slot_details:
        court_name = slot_details[0].split('/')[-2]
        date = slot_details[1].replace('/', '-')
        time = slot_details[2]
        filename = f"{timestamp}_{sanitized_reason}_{court_name}_{date}_{time}.png"
    else:
        filename = f"{timestamp}_{sanitized_reason}.png"

    filepath = os.path.join(screenshot_dir, filename)
    
    try:
        await page.screenshot(path=filepath, full_page=True)
        log_msg = f"{get_timestamp()} 📸 Screenshot saved: {filepath}"
        
        if session:
            session.log_message(log_msg)
            session.add_screenshot(filepath, reason)
        else:
            print(log_msg)
        
        return filepath
        
    except Exception as e:
        error_msg = f"{get_timestamp()} ❌ Could not save screenshot. Error: {e}"
        
        if session:
            session.log_message(error_msg)
        else:
            print(error_msg)
        
        return None

async def optimized_countdown_logging(seconds_to_wait):
    """
    Optimized countdown logging: every 10 seconds, then every second for last 5 seconds.
    """
    if seconds_to_wait <= 5:
        # Last 5 seconds: log every second
        for remaining in range(seconds_to_wait, 0, -1):
            print(f"{get_timestamp()} ⏰ {remaining} second{'s' if remaining != 1 else ''} remaining...")
            await asyncio.sleep(1)
    else:
        # More than 5 seconds: log every 10 seconds, then every second for last 5
        initial_countdown = seconds_to_wait - 5
        
        # Log every 10 seconds for the initial countdown
        for remaining in range(initial_countdown, 5, -10):
            if remaining > 0:
                print(f"{get_timestamp()} ⏰ {remaining} seconds remaining...")
                await asyncio.sleep(10)
        
        # Log every second for the last 5 seconds
        for remaining in range(5, 0, -1):
            print(f"{get_timestamp()} ⏰ {remaining} second{'s' if remaining != 1 else ''} remaining...")
            await asyncio.sleep(1)


async def navigate_to_court(page, court_url, session=None):
    """Navigates the browser to the specified court booking page."""
    try:
        log_msg = f"{get_timestamp()} Navigating to court booking page: {court_url.split('/')[-2]}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.goto(court_url, wait_until="domcontentloaded", timeout=20000)
        await page.locator("#DateTimeDiv").wait_for(state="visible", timeout=15000)
        log_msg = f"{get_timestamp()} ✅ Successfully loaded page for: {await page.title()}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Take screenshot after successful navigation
        await take_screenshot(page, "court_navigation_success", session=session)
        return True
    except Exception as e:
        log_msg = f"{get_timestamp()} ❌ An error occurred during navigation: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, "navigation_error", session=session)
        return False

async def check_london_time_near_midnight():
    """Check if current London time is within 10 minutes of midnight."""
    import pytz
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    
    print(f"{get_timestamp()} Current London time: {now.strftime('%H:%M:%S')}")
    
    # Check if we're within 10 minutes of midnight (23:50 to 00:10)
    if now.hour == 23 and now.minute >= 50:
        # Between 23:50 and 23:59 - near midnight
        return True, now
    elif now.hour == 0 and now.minute <= 10:
        # Between 00:00 and 00:10 - just past midnight, still in window
        return True, now
    else:
        return False, now

async def wait_until_midnight():
    """Wait until exactly 00:00:01 London time with optimized logging."""
    import pytz
    import asyncio
    
    try:
        london_tz = pytz.timezone("Europe/London")
        
        while True:
            now = datetime.now(london_tz)
            
            # Check if we've reached or passed the target time (00:00:01)
            if now.hour == 0 and now.minute == 0 and now.second >= 1:
                # We've reached 00:00:01 or later, exit immediately
                print(f"{get_timestamp()} ✅ Target time 00:00:01 reached! Current: {now.strftime('%H:%M:%S')}")
                break
            
            # Calculate target time - if we're before midnight, target is 00:00:01 next day
            # If we're after midnight but before 00:00:01, target is 00:00:01 same day
            if now.hour == 0 and now.minute == 0 and now.second < 1:
                # We're between 00:00:00 and 00:00:01, target is 00:00:01 today
                target_time = now.replace(hour=0, minute=0, second=1, microsecond=0)
            else:
                # We're before midnight, target is 00:00:01 tomorrow
                target_time = now.replace(hour=0, minute=0, second=1, microsecond=0) + timedelta(days=1)
            
            seconds_to_wait = (target_time - now).total_seconds()
            
            # Exit if we're past target (shouldn't happen with logic above, but safety check)
            if seconds_to_wait <= 0:
                print(f"{get_timestamp()} ✅ Target time 00:00:01 reached! Current: {now.strftime('%H:%M:%S')}")
                break
            
            # Optimized logging based on time remaining
            if seconds_to_wait <= 10:
                # Last 10 seconds: log every second
                print(f"{get_timestamp()} ⏰ {int(seconds_to_wait)} second{'s' if int(seconds_to_wait) != 1 else ''} until 00:00:01...")
                await asyncio.sleep(1)
            elif seconds_to_wait <= 60:
                # Last minute: log every 10 seconds
                print(f"{get_timestamp()} ⏰ {int(seconds_to_wait)} seconds until 00:00:01...")
                await asyncio.sleep(10)
            elif seconds_to_wait <= 600:
                # Between 10-1 minutes: log every minute
                minutes = int(seconds_to_wait / 60)
                print(f"{get_timestamp()} ⏰ {minutes} minute{'s' if minutes != 1 else ''} until 00:00:01...")
                await asyncio.sleep(60)
            else:
                # More than 10 minutes: log every minute but sleep for shorter periods
                minutes = int(seconds_to_wait / 60)
                print(f"{get_timestamp()} ⏰ {minutes} minutes until 00:00:01...")
                await asyncio.sleep(30)  # Check more frequently to be responsive
                
        return True  # Successfully reached target time
        
    except Exception as e:
        print(f"{get_timestamp()} ⚠️ Exception in wait_until_midnight: {e}")
        print(f"{get_timestamp()} Continuing execution despite timing error...")
        return False  # Failed to complete midnight wait

async def post_midnight_calendar_advancement(page, target_date_str, slot_details, session=None):
    """
    Advanced post-midnight calendar navigation with timeout protection.
    Attempts to find the target date with refreshes and dialog handling.
    Exits after 2 minutes if date is not found.
    """
    import pytz
    
    london_tz = pytz.timezone("Europe/London")
    start_time = datetime.now(london_tz)
    timeout_minutes = 2
    
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    
    log_msg = f"{get_timestamp()} 🚀 Post-midnight calendar advancement for '{formatted_date}'..."
    if session:
        session.log_message(log_msg)
    else:
        print(log_msg)
    
    # Set up dialog handler for any pop-ups
    async def dialog_handler(dialog):
        log_msg = f"{get_timestamp()} 🔄 Handling dialog: {dialog.message}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await dialog.accept()
    
    page.on("dialog", dialog_handler)
    
    try:
        for attempt in range(5):  # Maximum 5 attempts
            current_time = datetime.now(london_tz)
            elapsed = (current_time - start_time).total_seconds()
            
            # Check timeout (2 minutes = 120 seconds)
            if elapsed > (timeout_minutes * 60):
                log_msg = f"{get_timestamp()} ⏰ Timeout reached ({timeout_minutes} minutes). Exiting post-midnight advancement."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                return False
            
            log_msg = f"{get_timestamp()} 🔄 Attempt {attempt + 1}/5 to find target date..."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            
            # Check if target date is already visible
            try:
                if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=1000):
                    log_msg = f"{get_timestamp()} ✅ Target date '{formatted_date}' found!"
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                    await take_screenshot(page, "post_midnight_date_found", slot_details, session=session)
                    return True
            except:
                pass
            
            # Try to advance the calendar
            try:
                next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
                if await next_week_button.is_visible(timeout=1000):
                    log_msg = f"{get_timestamp()} 📅 Clicking 'Next Week' to advance calendar..."
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                    
                    # Click with timeout and better error handling
                    await next_week_button.click(timeout=10000)
                    
                    # Wait for page to load with longer timeout
                    await page.wait_for_load_state('domcontentloaded', timeout=10000)
                    # Give extra time for JavaScript calendar updates
                    await asyncio.sleep(1)
                    
                    # Check for target date again
                    try:
                        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=1000):
                            log_msg = f"{get_timestamp()} ✅ Target date '{formatted_date}' found after advancement!"
                            if session:
                                session.log_message(log_msg)
                            else:
                                print(log_msg)
                            await take_screenshot(page, "post_midnight_date_found_after_advance", slot_details, session=session)
                            return True
                    except:
                        pass
                else:
                    log_msg = f"{get_timestamp()} ⚠️ Next Week button not visible, refreshing page..."
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                    break  # Exit to refresh
            except Exception as e:
                log_msg = f"{get_timestamp()} ⚠️ Error during calendar advancement: {e}"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                break  # Exit to refresh
        
        # If we get here, try refreshing the page
        log_msg = f"{get_timestamp()} 🔄 Refreshing page to reload calendar..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        await page.reload()
        await page.wait_for_load_state('domcontentloaded', timeout=10000)
        
        # Final check after refresh
        try:
            if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=2000):
                log_msg = f"{get_timestamp()} ✅ Target date '{formatted_date}' found after refresh!"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                await take_screenshot(page, "post_midnight_date_found_after_refresh", slot_details, session=session)
                return True
        except:
            pass
        
        # If still not found, exit
        log_msg = f"{get_timestamp()} ❌ Target date '{formatted_date}' not found after all attempts."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        return False
        
    except Exception as e:
        log_msg = f"{get_timestamp()} ❌ Error in post_midnight_calendar_advancement: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        return False
    finally:
        # Remove dialog handler
        page.remove_listener("dialog", dialog_handler)

async def rapid_advance_to_target_week(page, target_date_str, slot_details, session=None):
    """Rapidly click Next Week until we find the target date or reach the end."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    
    log_msg = f"{get_timestamp()} 🚀 Rapidly advancing to find '{formatted_date}'..."
    if session:
        session.log_message(log_msg)
    else:
        print(log_msg)
    
    for i in range(20):  # Increased limit for rapid advancement
        # Check if target date is visible
        try:
            if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=500):
                log_msg = f"{get_timestamp()} ✅ Found target date '{formatted_date}' after rapid advancement!"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                await take_screenshot(page, "rapid_advance_success", slot_details, session=session)
                return True
        except:
            pass
        
        # Try to click Next Week
        try:
            next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
            if await next_week_button.is_visible(timeout=500):
                await next_week_button.click()
                
                # Wait for calendar content to update using Playwright's built-in waits
                try:
                    # Wait for the calendar to actually change by checking for new content
                    await page.wait_for_function(
                        """
                        () => {
                            const headers = document.querySelectorAll('h4.timetable-title');
                            return headers.length > 0 && headers[0].textContent.trim() !== '';
                        }
                        """,
                        timeout=2000
                    )
                except:
                    # If the function times out, use a more reliable approach
                    await page.wait_for_load_state('domcontentloaded', timeout=3000)
                    
                    # Additional verification that calendar content loaded
                    try:
                        await page.wait_for_selector('h4.timetable-title', timeout=2000)
                    except:
                        log_msg = f"{get_timestamp()} ⚠️ Calendar content not loading properly, continuing..."
                        if session:
                            session.log_message(log_msg)
                        else:
                            print(log_msg)
            else:
                log_msg = f"{get_timestamp()} ❌ No more weeks available"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                break
        except Exception as e:
            log_msg = f"{get_timestamp()} ❌ Cannot advance further: {e}"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            break
    
    # If not found, try refreshing
    log_msg = f"{get_timestamp()} Target date not found, refreshing page..."
    if session:
        session.log_message(log_msg)
    else:
        print(log_msg)
    await page.reload()
    try:
        # Handle potential form resubmission dialog
        page.on("dialog", lambda dialog: dialog.accept())
        await page.wait_for_load_state('domcontentloaded', timeout=10000)
        log_msg = f"{get_timestamp()} ✅ Page refreshed successfully"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
    except:
        log_msg = f"{get_timestamp()} ⚠️ Page refresh had issues, continuing..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
    
    # Check again after refresh
    try:
        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=2000):
            log_msg = f"{get_timestamp()} ✅ Found target date '{formatted_date}' after refresh!"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            await take_screenshot(page, "rapid_advance_after_refresh", slot_details, session=session)
            return True
    except:
        pass
    
    return False

async def find_date_on_calendar(page, target_date_str, slot_details, is_strategic_timing=False, session=None):
    """Enhanced calendar navigation with midnight release strategy."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    log_msg = f"{get_timestamp()} Searching for week containing '{formatted_date}'..."
    if session:
        session.log_message(log_msg)
    else:
        print(log_msg)

    # Strategic timing approach
    if is_strategic_timing:
        log_msg = f"{get_timestamp()} 🎯 Using strategic midnight release approach..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Step 1: Click Next Week only 3 times (get to week before target)
        log_msg = f"{get_timestamp()} 📅 Advancing 3 weeks ahead to position before target..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
            
        for i in range(3):
            try:
                next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
                # Increase timeout and use more robust waiting
                await next_week_button.wait_for(state="visible", timeout=10000)
                log_msg = f"{get_timestamp()}   - Clicking 'Next Week' ({i+1}/3)..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                
                # Click and wait for navigation with longer timeout
                await next_week_button.click()
                await page.wait_for_load_state('domcontentloaded', timeout=15000)
                # Give extra time for any JavaScript to update the calendar
                await asyncio.sleep(1)
                
                # Take screenshot after each week advancement
                await take_screenshot(page, f"week_advance_{i+1}", slot_details, session=session)
            except Exception as e:
                log_msg = f"{get_timestamp()} ⚠️ Issue during strategic advancement: {e}"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                # Continue with other attempts instead of breaking completely
                continue
        
        # Initialize success flag
        success = False
        
        try:
            # Step 2: Check if we're near midnight
            near_midnight, current_time = await check_london_time_near_midnight()
            
            if near_midnight:
                log_msg = f"{get_timestamp()} ⏰ Within 10 minutes of midnight - entering wait mode..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                
                # Wait until midnight with error handling
                midnight_success = await wait_until_midnight()
                if midnight_success:
                    log_msg = f"{get_timestamp()} ✅ Midnight wait completed successfully"
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                else:
                    log_msg = f"{get_timestamp()} ⚠️ Midnight wait failed or timed out"
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                    # Still proceed with post-midnight logic as a fallback
            else:
                log_msg = f"{get_timestamp()} ✅ Not near midnight, proceeding immediately with rapid advancement..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
            
            # Step 3: Post-midnight advancement (after midnight or immediately if not near midnight)
            if near_midnight:
                # We waited until midnight, now use the advanced post-midnight function
                log_msg = f"{get_timestamp()} 🚀 Starting post-midnight calendar advancement..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                success = await post_midnight_calendar_advancement(page, target_date_str, slot_details, session=session)
            else:
                # Not near midnight, use rapid advancement
                log_msg = f"{get_timestamp()} 🚀 Starting rapid advancement to find target date..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                success = await rapid_advance_to_target_week(page, target_date_str, slot_details, session=session)
        
        except Exception as e:
            log_msg = f"{get_timestamp()} ❌ Error in strategic timing logic: {e}"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            success = False
        
        return success


async def book_slot(page, target_date_str, target_time_str, slot_details, session=None):
    """Finds a specific date/time slot by its unique href and clicks it."""
    href_time_format = target_time_str[:2]
    slot_locator = page.locator(
        f"a.facility-book[href*='fdDate={target_date_str}'][href*='fdTime={href_time_format}']"
    )
    try:
        await slot_locator.wait_for(state="visible", timeout=3000)
        log_msg = f"{get_timestamp()} ✅ Slot at {target_time_str} is available. Clicking 'Book'..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Take screenshot before clicking the slot
        await take_screenshot(page, "slot_before_click", slot_details, session=session)
        
        await slot_locator.click()
        await page.wait_for_load_state('networkidle')
        log_msg = f"{get_timestamp()} Slot added to basket."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Take screenshot after adding to basket
        await take_screenshot(page, "slot_added_to_basket", slot_details, session=session)
        
        # Navigate back to calendar for next slot booking
        try:
            log_msg = f"{get_timestamp()} 🔙 Navigating back to calendar using browser back navigation..."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            
            # Use browser back navigation directly (no back button on page)
            await page.go_back()
            await page.wait_for_load_state('domcontentloaded', timeout=10000)
            
            # Give extra time for calendar to reload
            await asyncio.sleep(2)
            
            # Take screenshot after returning to calendar
            await take_screenshot(page, "returned_to_calendar", slot_details, session=session)
            
            # Verify we're back on the calendar page
            try:
                # Check for calendar elements to confirm we're on the right page
                calendar_present = await page.locator("#DateTimeDiv, .timetable-title, #ctl00_PageContent_btnNextWeek").first.is_visible(timeout=3000)
                if calendar_present:
                    log_msg = f"{get_timestamp()} ✅ Successfully returned to calendar page"
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
                else:
                    log_msg = f"{get_timestamp()} ⚠️ May not be on calendar page, calendar elements not visible"
                    if session:
                        session.log_message(log_msg)
                    else:
                        print(log_msg)
            except:
                log_msg = f"{get_timestamp()} ⚠️ Could not verify calendar page presence"
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                
        except Exception as e:
            log_msg = f"{get_timestamp()} ⚠️ Error navigating back to calendar: {e}"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
        
        return True
    except PlaywrightTimeoutError:
        log_msg = f"{get_timestamp()} ⚠️ Slot at {target_time_str} is not available or is already booked."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, f"slot_unavailable", slot_details, session=session)
        return False

async def fill_payment_form(page, card_number, expiry_month, expiry_year, security_code, session=None):
    """Fill out the payment form with card details."""
    try:
        log_msg = f"{get_timestamp()} --- Filling Payment Form ---"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Wait for payment form to load
        await page.wait_for_selector("input[name='cardNumber']", timeout=10000)
        log_msg = f"{get_timestamp()} Payment form detected. Filling card details..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Take screenshot of empty payment form
        await take_screenshot(page, "payment_form_empty", session=session)
        
        # Fill card number
        log_msg = f"{get_timestamp()} Entering card number..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='cardNumber']", card_number)
        
        # Fill expiry month
        log_msg = f"{get_timestamp()} Entering expiry month..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='expiryDate']", expiry_month)
        
        # Fill expiry year  
        log_msg = f"{get_timestamp()} Entering expiry year..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='expiryDate2']", expiry_year)
        
        # Fill security code
        log_msg = f"{get_timestamp()} Entering security code..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='csc']", security_code)
        
        log_msg = f"{get_timestamp()} ✅ Payment details filled successfully."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Click Continue button
        log_msg = f"{get_timestamp()} Clicking 'Continue' to submit payment..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        continue_button = page.locator("input[value='Continue']")
        await continue_button.click()
        
        # Wait for processing
        await page.wait_for_load_state('networkidle')
        log_msg = f"{get_timestamp()} Payment submitted. Waiting for response..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        return True
        
    except Exception as e:
        log_msg = f"{get_timestamp()} ❌ Error filling payment form: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, "payment_form_error", session=session)
        return False

async def fill_cardholder_details(page, cardholder_name, address, city, postcode, email, session=None):
    """Fill out the cardholder additional information form."""
    try:
        log_msg = f"{get_timestamp()} --- Filling Cardholder Details ---"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Wait for cardholder form to load
        await page.wait_for_selector("input[name='cardholderName']", timeout=10000)
        log_msg = f"{get_timestamp()} Cardholder details form detected. Filling information..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Take screenshot of empty cardholder form
        await take_screenshot(page, "cardholder_form_empty", session=session)
        
        # Fill cardholder name
        log_msg = f"{get_timestamp()} Entering cardholder name..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='cardholderName']", cardholder_name)
        
        # Fill address
        log_msg = f"{get_timestamp()} Entering address..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='address1']", address)
        
        # Fill city
        log_msg = f"{get_timestamp()} Entering city..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='city']", city)
        
        # Fill postcode
        log_msg = f"{get_timestamp()} Entering postcode..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='postcode']", postcode)
        
        # Fill email
        log_msg = f"{get_timestamp()} Entering email..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.fill("input[name='emailAddress']", email)
        
        log_msg = f"{get_timestamp()} ✅ Cardholder details filled successfully."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        # Click Continue button
        log_msg = f"{get_timestamp()} Clicking 'Continue' to submit cardholder details..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        continue_button = page.locator("input[value='Continue']")
        await continue_button.click()
        
        # Wait for processing
        await page.wait_for_load_state('networkidle')
        log_msg = f"{get_timestamp()} Cardholder details submitted. Waiting for response..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        
        return True
        
    except Exception as e:
        log_msg = f"{get_timestamp()} ❌ Error filling cardholder details: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, "cardholder_details_error", session=session)
        return False

async def checkout_basket(page, basket_url, card_number=None, expiry_month=None, expiry_year=None, security_code=None, cardholder_name=None, address=None, city=None, postcode=None, email=None, session=None):
    """Navigates to the basket, takes screenshots, and finalises the booking."""
    try:
        log_msg = f"{get_timestamp()} --- Navigating to Basket and Checking Out ---"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await page.goto(basket_url, wait_until="domcontentloaded")
        await take_screenshot(page, "basket_page", session=session)
        
        checkout_button = page.locator("#ctl00_PageContent_btnContinue")
        await checkout_button.wait_for(state="visible", timeout=10000)
        
        log_msg = f"{get_timestamp()} Basket page loaded. Clicking 'Make Booking'..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await checkout_button.click()
        
        await page.wait_for_load_state('networkidle')
        await take_screenshot(page, "after_make_booking", session=session)
        
        # First check if we directly reached the Payment Successful page (sufficient credit route)
        log_msg = f"{get_timestamp()} Checking for immediate Payment Successful page..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        success_locator = page.locator("h1:has-text('Payment Successful')")
        immediate_success = await success_locator.is_visible(timeout=3000)
        
        if immediate_success:
            log_msg = f"{get_timestamp()} ✅ 'Payment Successful' found immediately - sufficient credit route!"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            await take_screenshot(page, "payment_successful_direct", session=session)
            return True
        
        # If not successful yet, check for payment form (insufficient credit route)
        log_msg = f"{get_timestamp()} Payment not immediately successful, checking for payment forms..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        payment_form_exists = await page.locator("input[name='cardNumber']").is_visible(timeout=5000)
        
        if payment_form_exists and card_number:
            log_msg = f"{get_timestamp()} Payment form detected. Processing card payment flow..."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            payment_success = await fill_payment_form(page, card_number, expiry_month, expiry_year, security_code, session=session)
            if not payment_success:
                return False
            
            # Check if we're now on the cardholder details page
            await page.wait_for_load_state('networkidle')
            await take_screenshot(page, "after_payment_form", session=session)
            
            cardholder_form_exists = await page.locator("input[name='cardholderName']").is_visible(timeout=5000)
            
            if cardholder_form_exists and cardholder_name:
                log_msg = f"{get_timestamp()} Cardholder details form detected. Processing cardholder information..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                cardholder_success = await fill_cardholder_details(page, cardholder_name, address, city, postcode, email, session=session)
                if not cardholder_success:
                    return False
            elif cardholder_form_exists and not cardholder_name:
                log_msg = f"{get_timestamp()} ❌ Cardholder details form detected but no cardholder details provided."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                await take_screenshot(page, "cardholder_form_no_details", session=session)
                return False
            
            # Check if we're on the payment confirmation page with "Make a payment" button
            await page.wait_for_load_state('networkidle')
            await take_screenshot(page, "after_cardholder_details", session=session)
            
            make_payment_button = page.locator("input[value='Make a payment']")
            make_payment_exists = await make_payment_button.is_visible(timeout=5000)
            
            if make_payment_exists:
                log_msg = f"{get_timestamp()} Payment confirmation page detected. Clicking 'Make a payment'..."
                if session:
                    session.log_message(log_msg)
                else:
                    print(log_msg)
                await make_payment_button.click()
                await page.wait_for_load_state('networkidle')
                await take_screenshot(page, "after_make_payment", session=session)
                
        elif payment_form_exists and not card_number:
            log_msg = f"{get_timestamp()} ❌ Payment form detected but no card details provided."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            await take_screenshot(page, "payment_form_no_details", session=session)
            return False
        else:
            log_msg = f"{get_timestamp()} No payment form detected, checking for other elements..."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
        
        # Final check for Payment Successful (after card payment flow)
        log_msg = f"{get_timestamp()} Performing final check for Payment Successful page..."
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        try:
            await success_locator.wait_for(state="visible", timeout=15000)
            log_msg = f"{get_timestamp()} ✅ 'Payment Successful' text found after payment flow. Booking is confirmed!"
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            await take_screenshot(page, "payment_successful_after_card_flow", session=session)
            return True
        except PlaywrightTimeoutError:
            log_msg = f"{get_timestamp()} ❌ 'Payment Successful' text NOT found. Booking may have failed."
            if session:
                session.log_message(log_msg)
            else:
                print(log_msg)
            await take_screenshot(page, "payment_final_fail", session=session)
            return False

    except PlaywrightTimeoutError as e:
        log_msg = f"{get_timestamp()} ❌ Timeout during checkout process: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, "checkout_timeout_error", session=session)
        return False
    except Exception as e:
        log_msg = f"{get_timestamp()} ❌ Unexpected error during checkout: {e}"
        if session:
            session.log_message(log_msg)
        else:
            print(log_msg)
        await take_screenshot(page, "checkout_critical_error", session=session)
        return False
