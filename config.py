# config.py
# This file holds the configuration for the booking bot.

import os

# =============================================================================
# --- WEBSITE URLs ---
# =============================================================================
LOGIN_URL = "https://camdenactive.camden.gov.uk/security/login.aspx"
BASKET_URL = "https://camdenactive.camden.gov.uk/basket/"

# =============================================================================
# --- LEGACY CREDENTIALS (for backward compatibility) ---
# =============================================================================
# These will be fetched from GitHub repository secrets when run as an Action.
# The names must match the secret names you create in GitHub.
USERNAME = os.environ.get("BRUCE_CAM_EMAIL_ADDRESS")
PASSWORD = os.environ.get("BRUCE_CAM_PASSWORD")

# =============================================================================
# --- GOOGLE SHEETS CONFIGURATION ---
# =============================================================================
# Google Sheets ID for the multi-court booking system
# Get this from the shareable link: https://docs.google.com/spreadsheets/d/SHEET_ID/edit
GSHEET_MAIN_ID = os.environ.get("GSHEET_CAM_ID")

# Google Service Account credentials (JSON content as string)
# Create a service account in Google Cloud Console and download the JSON key
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")

# =============================================================================
# --- MULTI-COURT EMAIL ACCOUNTS ---
# =============================================================================
# These will be fetched from GitHub repository secrets when run as an Action.
# The names must match the secret names you create in GitHub.
MOTHER_EMAIL = os.environ.get("MOTHER_CAM_EMAIL_ADDRESS")
MOTHER_PASSWORD = os.environ.get("MOTHER_CAM_PASSWORD")
FATHER_EMAIL = os.environ.get("FATHER_CAM_EMAIL_ADDRESS")
FATHER_PASSWORD = os.environ.get("FATHER_CAM_PASSWORD")
BRUCE_EMAIL = os.environ.get("BRUCE_CAM_EMAIL_ADDRESS")
BRUCE_PASSWORD = os.environ.get("BRUCE_CAM_PASSWORD")
SALLIE_EMAIL = os.environ.get("SALLIE_CAM_EMAIL_ADDRESS")
SALLIE_PASSWORD = os.environ.get("SALLIE_CAM_PASSWORD")
JAN_EMAIL = os.environ.get("JAN_CAM_EMAIL_ADDRESS")
JAN_PASSWORD = os.environ.get("JAN_CAM_PASSWORD")
JO_EMAIL = os.environ.get("JO_CAM_EMAIL_ADDRESS")
JO_PASSWORD = os.environ.get("JO_CAM_PASSWORD")

# =============================================================================
# --- TENNIS COURT URLs ---
# =============================================================================
COURT_1_URL = "https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/"
COURT_2_URL = "https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/"
COURT_3_URL = "https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/"

# =============================================================================
# --- EMAIL NOTIFICATION SETTINGS ---
# =============================================================================
SENDER_EMAIL = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_KYLE = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_INFO = os.environ.get("INFO_EMAIL_ADDRESS")
IT_EMAIL_ADDRESS = os.environ.get("IT_EMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# =============================================================================
# --- FILE PATHS ---
# =============================================================================
BOOKING_FILE_PATH = 'ca_lif_booking_dates.csv'

# =============================================================================
# --- PAYMENT CARD DETAILS ---
# =============================================================================
# These will be fetched from GitHub repository secrets for payment processing
LB_CARD_NUMBER = os.environ.get("LB_CARD_NUMBER")
LB_CARD_EXPIRY_MONTH = os.environ.get("LB_CARD_EXPIRY_MONTH")
LB_CARD_EXPIRY_YEAR = os.environ.get("LB_CARD_EXPIRY_YEAR")
LB_CARD_SECURITY_CODE = os.environ.get("LB_CARD_SECURITY_CODE")

# =============================================================================
# --- CARDHOLDER DETAILS ---
# =============================================================================
LB_CARDHOLDER_NAME = os.environ.get("LB_CARDHOLDER_NAME")
LB_ADDRESS = os.environ.get("LB_ADDRESS")
LB_CITY = os.environ.get("LB_CITY")
LB_POSTCODE = os.environ.get("LB_POSTCODE")

# =============================================================================
# --- BROWSER CONFIGURATION ---
# =============================================================================
# Set these environment variables to control browser behavior
# SHOW_BROWSER=true - Shows browser window (default: false/headless)
# KEEP_BROWSER_OPEN=true - Keeps browser open after completion (default: false)
SHOW_BROWSER = os.environ.get("SHOW_BROWSER", "false").lower() == "true"
KEEP_BROWSER_OPEN = os.environ.get("KEEP_BROWSER_OPEN", "false").lower() == "true"
