# browser_actions.py
# This file contains all the core browser automation functions.

from datetime import datetime
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

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
        return False

async def find_date_on_calendar(page, target_date_str):
    """Navigates the booking calendar to find the week containing the target date."""
    date_obj = datetime.strptime(target_date_str, "%d/%m/%Y")
    formatted_date = f"{date_obj.strftime('%a').upper()} {date_obj.day}/{date_obj.month}"
    print(f"Searching for week containing '{formatted_date}'...")
    for i in range(15):
        if await page.locator(f"h4.timetable-title:has-text('{formatted_date}')").is_visible(timeout=1000):
            print(f"✅ Found date '{formatted_date}' on the calendar.")
            return True
        try:
            next_week_button = page.locator("#ctl00_PageContent_btnNextWeek")
            await next_week_button.wait_for(state="visible", timeout=1000)
            await next_week_button.click()
            await page.locator("#DateTimeDiv").wait_for(state="visible", timeout=15000)
        except PlaywrightTimeoutError:
            print(f"❌ Reached end of calendar, but did not find date {formatted_date}.")
            return False
    print(f"❌ Searched 15 weeks but did not find {formatted_date}.")
    return False

async def book_slot(page, target_date_str, target_time_str):
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
        return False

async def checkout_basket(page, basket_url):
    """Navigates to the basket and finalises the booking."""
    try:
        print("\n--- Navigating to Basket and Checking Out ---")
        await page.goto(basket_url, wait_until="domcontentloaded")
        checkout_button = page.locator("#ctl00_PageContent_btnContinue")
        await checkout_button.wait_for(state="visible", timeout=10000)
        print("Basket page loaded. Clicking 'Make Booking'...")
        await checkout_button.click()
        await page.wait_for_load_state('networkidle')
        success_locator = page.locator(":text('Payment Successful')")
        try:
            await success_locator.wait_for(state="visible", timeout=15000)
            print("✅ 'Payment Successful' text found. Booking is confirmed!")
            return True
        except PlaywrightTimeoutError:
            print("❌ 'Payment Successful' text NOT found. Booking may have failed.")
            await page.screenshot(path="checkout_fail.png")
            return False
    except Exception as e:
        print(f"❌ An error occurred during checkout: {e}")
        await page.screenshot(path="checkout_error.png")
        return False
