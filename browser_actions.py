# browser_actions.py
# This file contains all the core browser automation functions.

import os
import pytz
import asyncio
import time
from datetime import datetime
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

# --- Updated Screenshot Helper Function ---
async def take_screenshot(page, reason, slot_details=None):
    """
    Takes a full-page screenshot with a descriptive, timestamped filename
    and saves it to the 'screenshots' directory.
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
        print(f"{get_timestamp()} 📸 Screenshot saved: {filepath}")
    except Exception as e:
        print(f"{get_timestamp()} ❌ Could not save screenshot. Error: {e}")

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


async def navigate_to_court(page, court_url):
    """Navigates the browser to the specified court booking page."""
    try:
        print(f"{get_timestamp()} Navigating to court booking page: {court_url.split('/')[-2]}")
        await page.goto(court_url, wait_until="domcontentloaded", timeout=20000)
        await page.locator("#DateTimeDiv").wait_for(state="visible", timeout=15000)
        print(f"{get_timestamp()} ✅ Successfully loaded page for: {await page.title()}")
        
        # Take screenshot after successful navigation
        await take_screenshot(page, "court_navigation_success")
        return True
    except Exception as e:
        print(f"{get_timestamp()} ❌ An error occurred during navigation: {e}")
        await take_screenshot(page, "navigation_error")
        return False

async def check_london_time_near_midnight():
    """Check if current London time is within 10 minutes of midnight."""
    import pytz
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    
    # Calculate minutes until midnight
    midnight = now.replace(hour=23, minute=50, second=0, microsecond=0)
    minutes_to_ten_before_midnight = (midnight - now).total_seconds() / 60
    
    print(f"{get_timestamp()} Current London time: {now.strftime('%H:%M:%S')}")
    
    # Check if we're within 10 minutes of midnight (23:50 to 00:00)
    if now.hour == 23 and now.minute >= 50:
        return True, now
    elif now.hour == 0 and now.minute == 0:
        return True, now
    else:
        return False, now

async def wait_until_midnight():
    """Wait until exactly 00:00:01 London time."""
    import pytz
    import asyncio
    
    london_tz = pytz.timezone("Europe/London")
    
    while True:
        now = datetime.now(london_tz)
        if now.hour == 0 and now.minute == 0 and now.second >= 1:
            print(f"{get_timestamp()} ✅ Midnight reached! Time: {now.strftime('%H:%M:%S')}")
            break
        elif now.hour == 23 and now.minute == 59:
            seconds_to_wait = 61 - now.second
            print(f"{get_timestamp()} ⏰ Final countdown: {seconds_to_wait} seconds until midnight...")
            await optimized_countdown_logging(seconds_to_wait)
        else:
            await asyncio.sleep(0.1)

async def rapid_advance_to_target_week(page, target_date_str, slot_details):
    """Rapidly click Next Week until we find the target date or reach the end."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    
    print(f"{get_timestamp()} 🚀 Rapidly advancing to find '{formatted_date}'...")
    
    for i in range(20):  # Increased limit for rapid advancement
        # Check if target date is visible
        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=500):
            print(f"{get_timestamp()} ✅ Found target date '{formatted_date}' after rapid advancement!")
            await take_screenshot(page, "rapid_advance_success", slot_details)
            return True
        
        # Try to click Next Week
        try:
            next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
            if await next_week_button.is_visible(timeout=500):
                await next_week_button.click()
                
                # Fast but reliable loading check - wait for DOM content, not all network
                await page.wait_for_load_state('domcontentloaded', timeout=2000)
                
                # Additional check: ensure the calendar dates have actually changed
                # This is faster than networkidle but ensures content loaded
                try:
                    await page.wait_for_function(
                        """
                        () => {
                            const headers = document.querySelectorAll('h4.timetable-title');
                            return headers.length > 0; // Ensure calendar headers exist
                        }
                        """,
                        timeout=1500
                    )
                except:
                    # If timing out, add small delay but keep going
                    await asyncio.sleep(0.2)
            else:
                print(f"{get_timestamp()} ❌ No more weeks available")
                break
        except Exception as e:
            print(f"{get_timestamp()} ❌ Cannot advance further: {e}")
            break
    
    # If not found, try refreshing
    print(f"{get_timestamp()} Target date not found, refreshing page...")
    await page.reload()
    try:
        # Handle potential form resubmission dialog
        page.on("dialog", lambda dialog: dialog.accept())
        await page.wait_for_load_state('networkidle', timeout=10000)
        print(f"{get_timestamp()} ✅ Page refreshed successfully")
    except:
        print(f"{get_timestamp()} ⚠️ Page refresh had issues, continuing...")
    
    # Check again after refresh
    if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=2000):
        print(f"{get_timestamp()} ✅ Found target date '{formatted_date}' after refresh!")
        await take_screenshot(page, "rapid_advance_after_refresh", slot_details)
        return True
    
    return False

async def find_date_on_calendar(page, target_date_str, slot_details, is_strategic_timing=False):
    """Enhanced calendar navigation with midnight release strategy."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    print(f"{get_timestamp()} Searching for week containing '{formatted_date}'...")

    # Strategic timing approach
    if is_strategic_timing:
        print(f"{get_timestamp()} 🎯 Using strategic midnight release approach...")
        
        # Step 1: Click Next Week only 3 times (get to week before target)
        print(f"{get_timestamp()} 📅 Advancing 3 weeks ahead to position before target...")
        for i in range(3):
            try:
                next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
                await next_week_button.wait_for(state="visible", timeout=2000)
                print(f"{get_timestamp()}   - Clicking 'Next Week' ({i+1}/3)...")
                await next_week_button.click()
                await page.wait_for_load_state('networkidle', timeout=5000)
                
                # Take screenshot after each week advancement
                await take_screenshot(page, f"week_advance_{i+1}", slot_details)
            except Exception as e:
                print(f"{get_timestamp()} ⚠️ Issue during strategic advancement: {e}")
                break
        
        # Step 2: Check if we're near midnight
        near_midnight, current_time = await check_london_time_near_midnight()
        
        if near_midnight:
            print(f"{get_timestamp()} ⏰ Within 10 minutes of midnight - entering wait mode...")
            await wait_until_midnight()
            
            # Step 3: Rapid advancement after midnight
            success = await rapid_advance_to_target_week(page, target_date_str, slot_details)
            return success
        else:
            print(f"{get_timestamp()} ✅ Not near midnight, proceeding with normal booking...")
    
    # Normal calendar navigation (original logic)
    for i in range(15):
        date_header_locator = page.locator("h4.timetable-title")
        
        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=1000):
            print(f"{get_timestamp()} ✅ Found date '{formatted_date}' on the calendar.")
            await take_screenshot(page, "date_found_on_calendar", slot_details)
            return True

        visible_dates_before_click = await date_header_locator.all_inner_texts()
        last_date_before_click = visible_dates_before_click[-1] if visible_dates_before_click else None
        print(f"{get_timestamp()}   - Latest date currently visible: {last_date_before_click}")

        try:
            next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
            await next_week_button.wait_for(state="visible", timeout=2000)
            print(f"{get_timestamp()}   - Clicking 'Next Week'...")
            await next_week_button.click()

            await page.wait_for_function(
                f"""
                () => {{
                    const headers = Array.from(document.querySelectorAll('h4.timetable-title'));
                    const lastHeader = headers[headers.length - 1];
                    return lastHeader && lastHeader.innerText !== '{last_date_before_click}';
                }}
                """,
                timeout=15000
            )
            print(f"{get_timestamp()}   - New week has loaded successfully.")
            
            # Take screenshot after each week advancement
            await take_screenshot(page, f"week_advance_{i+1}", slot_details)

        except PlaywrightTimeoutError:
            print(f"{get_timestamp()} ❌ Reached end of calendar, but did not find date {formatted_date}.")
            await take_screenshot(page, "end_of_calendar", slot_details)
            return False
            
    print(f"{get_timestamp()} ❌ Searched 15 weeks but did not find {formatted_date}.")
    await take_screenshot(page, f"date_not_found", slot_details)
    return False

async def book_slot(page, target_date_str, target_time_str, slot_details):
    """Finds a specific date/time slot by its unique href and clicks it."""
    href_time_format = target_time_str[:2]
    slot_locator = page.locator(
        f"a.facility-book[href*='fdDate={target_date_str}'][href*='fdTime={href_time_format}']"
    )
    try:
        await slot_locator.wait_for(state="visible", timeout=3000)
        print(f"{get_timestamp()} ✅ Slot at {target_time_str} is available. Clicking 'Book'...")
        
        # Take screenshot before clicking the slot
        await take_screenshot(page, "slot_before_click", slot_details)
        
        await slot_locator.click()
        await page.wait_for_load_state('networkidle')
        print(f"{get_timestamp()} Slot added to basket.")
        
        # Take screenshot after adding to basket
        await take_screenshot(page, "slot_added_to_basket", slot_details)
        return True
    except PlaywrightTimeoutError:
        print(f"{get_timestamp()} ⚠️ Slot at {target_time_str} is not available or is already booked.")
        await take_screenshot(page, f"slot_unavailable", slot_details)
        return False

async def fill_payment_form(page, card_number, expiry_month, expiry_year, security_code):
    """Fill out the payment form with card details."""
    try:
        print(f"{get_timestamp()} --- Filling Payment Form ---")
        
        # Wait for payment form to load
        await page.wait_for_selector("input[name='cardNumber']", timeout=10000)
        print(f"{get_timestamp()} Payment form detected. Filling card details...")
        
        # Take screenshot of empty payment form
        await take_screenshot(page, "payment_form_empty")
        
        # Fill card number
        print(f"{get_timestamp()} Entering card number...")
        await page.fill("input[name='cardNumber']", card_number)
        
        # Fill expiry month
        print(f"{get_timestamp()} Entering expiry month...")
        await page.fill("input[name='expiryDate']", expiry_month)
        
        # Fill expiry year  
        print(f"{get_timestamp()} Entering expiry year...")
        await page.fill("input[name='expiryDate2']", expiry_year)
        
        # Fill security code
        print(f"{get_timestamp()} Entering security code...")
        await page.fill("input[name='csc']", security_code)
        
        print(f"{get_timestamp()} ✅ Payment details filled successfully.")
        
        # Take screenshot before submitting
        await take_screenshot(page, "payment_form_filled")
        
        # Click Continue button
        print(f"{get_timestamp()} Clicking 'Continue' to submit payment...")
        continue_button = page.locator("input[value='Continue']")
        await continue_button.click()
        
        # Wait for processing
        await page.wait_for_load_state('networkidle')
        print(f"{get_timestamp()} Payment submitted. Waiting for response...")
        
        return True
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error filling payment form: {e}")
        await take_screenshot(page, "payment_form_error")
        return False

async def fill_cardholder_details(page, cardholder_name, address, city, postcode, email):
    """Fill out the cardholder additional information form."""
    try:
        print(f"{get_timestamp()} --- Filling Cardholder Details ---")
        
        # Wait for cardholder form to load
        await page.wait_for_selector("input[name='cardholderName']", timeout=10000)
        print(f"{get_timestamp()} Cardholder details form detected. Filling information...")
        
        # Take screenshot of empty cardholder form
        await take_screenshot(page, "cardholder_form_empty")
        
        # Fill cardholder name
        print(f"{get_timestamp()} Entering cardholder name...")
        await page.fill("input[name='cardholderName']", cardholder_name)
        
        # Fill address
        print(f"{get_timestamp()} Entering address...")
        await page.fill("input[name='address1']", address)
        
        # Fill city
        print(f"{get_timestamp()} Entering city...")
        await page.fill("input[name='city']", city)
        
        # Fill postcode
        print(f"{get_timestamp()} Entering postcode...")
        await page.fill("input[name='postcode']", postcode)
        
        # Fill email
        print(f"{get_timestamp()} Entering email...")
        await page.fill("input[name='emailAddress']", email)
        
        print(f"{get_timestamp()} ✅ Cardholder details filled successfully.")
        
        # Take screenshot before submitting
        await take_screenshot(page, "cardholder_details_filled")
        
        # Click Continue button
        print(f"{get_timestamp()} Clicking 'Continue' to submit cardholder details...")
        continue_button = page.locator("input[value='Continue']")
        await continue_button.click()
        
        # Wait for processing
        await page.wait_for_load_state('networkidle')
        print(f"{get_timestamp()} Cardholder details submitted. Waiting for response...")
        
        return True
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error filling cardholder details: {e}")
        await take_screenshot(page, "cardholder_details_error")
        return False

async def checkout_basket(page, basket_url, card_number=None, expiry_month=None, expiry_year=None, security_code=None, cardholder_name=None, address=None, city=None, postcode=None, email=None):
    """Navigates to the basket, takes screenshots, and finalises the booking."""
    try:
        print(f"{get_timestamp()} --- Navigating to Basket and Checking Out ---")
        await page.goto(basket_url, wait_until="domcontentloaded")
        await take_screenshot(page, "basket_page")
        
        checkout_button = page.locator("#ctl00_PageContent_btnContinue")
        await checkout_button.wait_for(state="visible", timeout=10000)
        
        print(f"{get_timestamp()} Basket page loaded. Clicking 'Make Booking'...")
        await checkout_button.click()
        
        await page.wait_for_load_state('networkidle')
        await take_screenshot(page, "after_make_booking")
        
        # First check if we directly reached the Payment Successful page (sufficient credit route)
        print(f"{get_timestamp()} Checking for immediate Payment Successful page...")
        success_locator = page.locator("h1:has-text('Payment Successful')")
        immediate_success = await success_locator.is_visible(timeout=3000)
        
        if immediate_success:
            print(f"{get_timestamp()} ✅ 'Payment Successful' found immediately - sufficient credit route!")
            await take_screenshot(page, "payment_successful_direct")
            return True
        
        # If not successful yet, check for payment form (insufficient credit route)
        print(f"{get_timestamp()} Payment not immediately successful, checking for payment forms...")
        payment_form_exists = await page.locator("input[name='cardNumber']").is_visible(timeout=5000)
        
        if payment_form_exists and card_number:
            print(f"{get_timestamp()} Payment form detected. Processing card payment flow...")
            payment_success = await fill_payment_form(page, card_number, expiry_month, expiry_year, security_code)
            if not payment_success:
                return False
            
            # Check if we're now on the cardholder details page
            await page.wait_for_load_state('networkidle')
            await take_screenshot(page, "after_payment_form")
            
            cardholder_form_exists = await page.locator("input[name='cardholderName']").is_visible(timeout=5000)
            
            if cardholder_form_exists and cardholder_name:
                print(f"{get_timestamp()} Cardholder details form detected. Processing cardholder information...")
                cardholder_success = await fill_cardholder_details(page, cardholder_name, address, city, postcode, email)
                if not cardholder_success:
                    return False
            elif cardholder_form_exists and not cardholder_name:
                print(f"{get_timestamp()} ❌ Cardholder details form detected but no cardholder details provided.")
                await take_screenshot(page, "cardholder_form_no_details")
                return False
            
            # Check if we're on the payment confirmation page with "Make a payment" button
            await page.wait_for_load_state('networkidle')
            await take_screenshot(page, "after_cardholder_details")
            
            make_payment_button = page.locator("input[value='Make a payment']")
            make_payment_exists = await make_payment_button.is_visible(timeout=5000)
            
            if make_payment_exists:
                print(f"{get_timestamp()} Payment confirmation page detected. Clicking 'Make a payment'...")
                await make_payment_button.click()
                await page.wait_for_load_state('networkidle')
                await take_screenshot(page, "after_make_payment")
                
        elif payment_form_exists and not card_number:
            print(f"{get_timestamp()} ❌ Payment form detected but no card details provided.")
            await take_screenshot(page, "payment_form_no_details")
            return False
        else:
            print(f"{get_timestamp()} No payment form detected, checking for other elements...")
        
        # Final check for Payment Successful (after card payment flow)
        print(f"{get_timestamp()} Performing final check for Payment Successful page...")
        try:
            await success_locator.wait_for(state="visible", timeout=15000)
            print(f"{get_timestamp()} ✅ 'Payment Successful' text found after payment flow. Booking is confirmed!")
            await take_screenshot(page, "payment_successful_after_card_flow")
            return True
        except PlaywrightTimeoutError:
            print(f"{get_timestamp()} ❌ 'Payment Successful' text NOT found. Booking may have failed.")
            await take_screenshot(page, "payment_final_fail")
            return False

    except Exception as e:
        print(f"{get_timestamp()} ❌ An error occurred during checkout: {e}")
        await take_screenshot(page, "checkout_critical_error")
        return False
