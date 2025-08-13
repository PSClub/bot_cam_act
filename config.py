# config.py
# This file holds the configuration for the booking bot.

import os

# --- URLs ---
LOGIN_URL = "https://camdenactive.camden.gov.uk/security/login.aspx"
BASKET_URL = "https://camdenactive.camden.gov.uk/basket/"

# --- Credentials ---
# These will be fetched from GitHub repository secrets when run as an Action.
# The names must match the secret names you create in GitHub.
USERNAME = os.environ.get("BRUCE_CAM_EMAIL_ADDRESS")
PASSWORD = os.environ.get("BRUCE_CAM_PASSWORD")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# --- File Path ---
BOOKING_FILE_PATH = 'ca_lif_booking_dates.csv'

# --- Google Sheets Configuration ---
# Google Sheets ID for the booking data
# Get this from the shareable link: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
GSHEET_CAM_ID = os.environ.get("GSHEET_CAM_ID")

# Google Sheets tab/worksheet name containing the booking data
GSHEET_TAB_NAME = "camden_active_booking_dates"

# Google Service Account credentials (JSON content as string)
# Create a service account in Google Cloud Console and download the JSON key
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

# --- Email Settings ---
SENDER_EMAIL = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_KYLE = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_INFO = os.environ.get("INFO_EMAIL_ADDRESS")

# --- Payment Card Details ---
# These will be fetched from GitHub repository secrets for payment processing
LB_CARD_NUMBER = os.environ.get("LB_CARD_NUMBER")
LB_CARD_EXPIRY_MONTH = os.environ.get("LB_CARD_EXPIRY_MONTH")
LB_CARD_EXPIRY_YEAR = os.environ.get("LB_CARD_EXPIRY_YEAR")
LB_CARD_SECURITY_CODE = os.environ.get("LB_CARD_SECURITY_CODE")

# --- Cardholder Details ---
LB_CARDHOLDER_NAME = os.environ.get("LB_CARDHOLDER_NAME")
LB_ADDRESS = os.environ.get("LB_ADDRESS")
LB_CITY = os.environ.get("LB_CITY")
LB_POSTCODE = os.environ.get("LB_POSTCODE")

# --- Browser Configuration ---
# Set these environment variables to control browser behavior
# SHOW_BROWSER=true - Shows browser window (default: false/headless)
# KEEP_BROWSER_OPEN=true - Keeps browser open after completion (default: false)
SHOW_BROWSER = os.environ.get("SHOW_BROWSER", "false").lower() == "true"
KEEP_BROWSER_OPEN = os.environ.get("KEEP_BROWSER_OPEN", "false").lower() == "true"
