# browser_actions.py
# This file contains all the core browser automation functions.

import os
import pytz
from datetime import datetime
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

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
        print(f"📸 Screenshot saved: {filepath}")
    except Exception as e:
        print(f"❌ Could not save screenshot. Error: {e}")


async def navigate_to_court(page, court_url):
    """Navigates the browser to the specified court booking page."""
    try:
        print(f"Navigating to court booking page: {court_url.split('/')[-2]}")
        await page.goto(court_url, wait_until="domcontentloaded", timeout=20000)
        await page.locator("#DateTimeDiv").wait_for(state="visible", timeout=15000)
        print(f"✅ Successfully loaded page for: {await page.title()}")
        return True
    except Exception as e:
        print(f"\n❌ An error occurred during navigation: {e}")
        await take_screenshot(page, "navigation_error")
        return False

async def find_date_on_calendar(page, target_date_str, slot_details):
    """Navigates the booking calendar to find the week containing the target date."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    print(f"Searching for week containing '{formatted_date}'...")

    for i in range(15):
        date_header_locator = page.locator("h4.timetable-title")
        
        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=1000):
            print(f"✅ Found date '{formatted_date}' on the calendar.")
            return True

        visible_dates_before_click = await date_header_locator.all_inner_texts()
        last_date_before_click = visible_dates_before_click[-1] if visible_dates_before_click else None
        print(f"  - Latest date currently visible: {last_date_before_click}")

        try:
            next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
            await next_week_button.wait_for(state="visible", timeout=2000)
            print("  - Clicking 'Next Week'...")
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
            print("  - New week has loaded successfully.")

        except PlaywrightTimeoutError:
            print(f"❌ Reached end of calendar, but did not find date {formatted_date}.")
            await take_screenshot(page, "end_of_calendar", slot_details)
            return False
            
    print(f"❌ Searched 15 weeks but did not find {formatted_date}.")
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
        print(f"✅ Slot at {target_time_str} is available. Clicking 'Book'...")
        await slot_locator.click()
        await page.wait_for_load_state('networkidle')
        print("Slot added to basket.")
        return True
    except PlaywrightTimeoutError:
        print(f"⚠️ Slot at {target_time_str} is not available or is already booked.")
        await take_screenshot(page, f"slot_unavailable", slot_details)
        return False

async def checkout_basket(page, basket_url):
    """Navigates to the basket, takes screenshots, and finalises the booking."""
    try:
        print("\n--- Navigating to Basket and Checking Out ---")
        await page.goto(basket_url, wait_until="domcontentloaded")
        await take_screenshot(page, "basket_page")
        
        checkout_button = page.locator("#ctl00_PageContent_btnContinue")
        await checkout_button.wait_for(state="visible", timeout=10000)
        
        print("Basket page loaded. Clicking 'Make Booking'...")
        await checkout_button.click()
        
        await page.wait_for_load_state('networkidle')
        await take_screenshot(page, "payment_page")
        
        # --- CORRECTED LOCATOR ---
        # Target the <h1> heading specifically to resolve the ambiguity.
        success_locator = page.locator("h1:has-text('Payment Successful')")
        try:
            await success_locator.wait_for(state="visible", timeout=15000)
            print("✅ 'Payment Successful' text found. Booking is confirmed!")
            await take_screenshot(page, "payment_successful")
            return True
        except PlaywrightTimeoutError:
            print("❌ 'Payment Successful' text NOT found. Booking may have failed.")
            await take_screenshot(page, "payment_fail")
            return False

    except Exception as e:
        print(f"❌ An error occurred during checkout: {e}")
        await take_screenshot(page, "checkout_critical_error")
        return False
