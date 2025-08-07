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

# --- Email Settings ---
SENDER_EMAIL = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_KYLE = os.environ.get("KYLE_EMAIL_ADDRESS")
RECIPIENT_INFO = os.environ.get("INFO_EMAIL_ADDRESS")
