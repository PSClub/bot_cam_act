# config.py
# This file holds the configuration for the booking bot.

import os

# --- URLs ---
LOGIN_URL = "https://camdenactive.camden.gov.uk/security/login.aspx"
BASKET_URL = "https://camdenactive.camden.gov.uk/basket/"

# --- Credentials ---
# These will be fetched from GitHub repository secrets when run as an Action.
# The names must match the secret names you create in GitHub.
USERNAME = os.environ.get("CAMDEN_USERNAME")
PASSWORD = os.environ.get("CAMDEN_PASSWORD")

# --- File Path ---
BOOKING_FILE_PATH = 'ca_lif_booking_dates.csv'
