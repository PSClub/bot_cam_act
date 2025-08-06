# main.py
# This is the main entry point for the booking automation script.

import asyncio
import pytz
from datetime import datetime
from playwright.async_api import async_playwright

# Import functions and variables from our other files
from config import LOGIN_URL, BASKET_URL, USERNAME, PASSWORD, BOOKING_FILE_PATH
from data_processor import process_booking_file
from browser_actions import (
    navigate_to_court, 
    find_date_on_calendar, 
    book_slot, 
    checkout_basket,
    take_screenshot  # Import the new screenshot function
)

def print_london_time():
    """Prints the current time in the London timezone."""
    london_tz = pytz.timezone("Europe/London")
    now = datetime.now(london_tz)
    print(f"Current time in London: {now.strftime('%A, %d %B %Y at %I:%M:%S %p %Z')}")


async def main():
    """
    The main asynchronous function that orchestrates the entire booking process.
    """
    print_london_time()
    
    slots_to_book = process_booking_file(BOOKING_FILE_PATH)
    if not slots_to_book:
        print("Booking list is empty or could not be processed. Exiting.")
        return

    if not USERNAME or not PASSWORD:
        print("Error: CAMDEN_USERNAME and CAMDEN_PASSWORD secrets are not set. Exiting.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            # --- 1. Login ---
            print("\n--- Starting Login Process ---")
            await page.goto(LOGIN_URL)
            await page.locator("#rtPrivacyBannerAccept").click(timeout=5000)
            await page.get_by_label("Email Address").fill(USERNAME)
            await page.get_by_label("Password").fill(PASSWORD)
            await page.locator("a.button-primary:has-text('Log in')").click()
            await page.locator("a:has-text('Logout')").wait_for(state="visible", timeout=15000)
            print("✅ Login successful.")

            # --- 2. Process Bookings ---
            print("\n--- Starting Booking Process ---")
            successful_bookings, failed_bookings = [], []
            current_court_url, current_date_str = None, None

            for slot_details in slots_to_book:
                target_court_url, target_date, target_time = slot_details
                print(f"\n--- Processing: {target_court_url.split('/')[-2]} on {target_date} at {target_time} ---")
                
                if current_court_url != target_court_url:
                    if not await navigate_to_court(page, target_court_url):
                        failed_bookings.append(slot_details)
                        continue
                    current_court_url, current_date_str = target_court_url, None

                if current_date_str != target_date:
                    # Pass slot_details for screenshot naming on failure
                    if not await find_date_on_calendar(page, target_date, slot_details):
                        failed_bookings.append(slot_details)
                        continue
                    current_date_str = target_date

                # Pass slot_details for screenshot naming on failure
                if await book_slot(page, target_date, target_time, slot_details):
                    successful_bookings.append(slot_details)
                    current_court_url, current_date_str = None, None
                else:
                    failed_bookings.append(slot_details)
            
            # --- 3. Checkout ---
            if not successful_bookings:
                print("\nNo slots were added to the basket. Terminating process.")
            else:
                await checkout_basket(page, BASKET_URL)

            # --- 4. Final Summary ---
            print("\n--- Booking Process Finished ---")
            print(f"Successfully booked: {len(successful_bookings)} slots.")
            if successful_bookings:
                for slot in successful_bookings:
                    print(f"  - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")
            print(f"Failed or skipped: {len(failed_bookings)} slots.")
            if failed_bookings:
                for slot in failed_bookings:
                    print(f"  - {slot[0].split('/')[-2]} on {slot[1]} @ {slot[2]}")

        except Exception as e:
            print(f"\n❌ A critical error occurred during the process: {e}")
            await take_screenshot(page, "critical_error")
        finally:
            # --- 5. Logout and Cleanup ---
            print("\n--- Finalising Session ---")
            print_london_time()
            try:
                if await page.locator("a:has-text('Logout')").is_visible(timeout=5000):
                    print("Logging out...")
                    await page.locator("a:has-text('Logout')").click()
                    await page.wait_for_load_state('domcontentloaded')
                    print("Logout successful.")
                else:
                    print("Already logged out or session expired.")
            except Exception as e:
                print(f"⚠️ Could not perform logout. Error: {e}")
            
            print("Closing browser.")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())