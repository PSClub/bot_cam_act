# bot_cam_act

An automated tennis court booking bot for Camden Active that can read booking data from Google Drive.

## Features

- **Automated Court Booking**: Books tennis court slots automatically
- **Google Sheets Integration**: Reads booking data directly from Google Sheets in real-time
- **Fallback Support**: Falls back to local CSV files if Google Sheets is unavailable
- **Email Reporting**: Sends detailed reports with booking results
- **Strategic Timing**: Optimized for midnight slot releases

## Setup

### Prerequisites

1. Python 3.7 or higher
2. Google Cloud Project with Drive API enabled
3. Service Account with Google Drive access

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bot_cam_act
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

### Google Sheets Setup

#### Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs:
   - Navigate to "APIs & Services" > "Library"
   - Search for and enable "Google Sheets API"
   - Search for and enable "Google Drive API" (needed for file access)

#### Step 2: Create a Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details
4. After creation, click on the service account
5. Go to the "Keys" tab
6. Click "Add Key" > "Create New Key"
7. Choose "JSON" format and download the key file

#### Step 3: Create and Share Your Google Sheets

1. Create a new Google Sheets document or use an existing one
2. Create a worksheet/tab named exactly: `camden_active_booking_dates`
3. Set up your data with these column headers in row 1:
   - Column A: `court_link`
   - Column B: `booking_date` 
   - Column C: `time`
4. Share the Google Sheets with the service account:
   - Click "Share" button in Google Sheets
   - Add the service account email (found in the JSON key file) with "Viewer" permissions
5. Copy the Sheets ID from the URL: `https://docs.google.com/spreadsheets/d/{SHEETS_ID}/edit`
### Environment Variables

Set these environment variables (or GitHub secrets for Actions):

#### Required for Basic Functionality
```bash
BRUCE_CAM_EMAIL_ADDRESS=your_email@example.com
BRUCE_CAM_PASSWORD=your_password
```

#### Required for Google Sheets Integration
```bash
GSHEET_CAM_ID=your_google_sheets_id
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"...","private_key_id":"...","private_key":"...","client_email":"...","client_id":"...","auth_uri":"...","token_uri":"...","auth_provider_x509_cert_url":"...","client_x509_cert_url":"..."}'
```

#### Optional for Email Reports
```bash
GMAIL_APP_PASSWORD=your_gmail_app_password
KYLE_EMAIL_ADDRESS=recipient@example.com
INFO_EMAIL_ADDRESS=info@example.com
```

#### Optional for Payment Processing
```bash
LB_CARD_NUMBER=1234567890123456
LB_CARD_EXPIRY_MONTH=12
LB_CARD_EXPIRY_YEAR=25
LB_CARD_SECURITY_CODE=123
LB_CARDHOLDER_NAME="John Doe"
LB_ADDRESS="123 Main St"
LB_CITY="London"
LB_POSTCODE="SW1A 1AA"
```

## Data Format

Your Google Sheets tab "camden_active_booking_dates" (or local CSV file) should have the following format:

```csv
court_link,booking_date,time
https://camdenactive.camden.gov.uk/booking/court1,25/12/2024,1400
https://camdenactive.camden.gov.uk/booking/court2,26/12/2024,1500
```

- **court_link**: Full URL to the court booking page
- **booking_date**: Date in DD/MM/YYYY format
- **time**: Time in 24-hour format (HHMM)

## Usage

### Command Line Options

```bash
# Run with default settings
python main.py

# Show browser window
python main.py --show-browser

# Keep browser open for debugging
python main.py --keep-open

# Enable full debug mode
python main.py --debug

# Run in headless mode
python main.py --headless
```

### Booking Window

The bot automatically filters bookings to only attempt slots that are 33-35 days in the future, as this is typically when new slots become available.

## How It Works

1. **Data Source**: The bot first attempts to read data from the Google Sheets tab "camden_active_booking_dates"
2. **Fallback**: If Google Sheets is not configured or fails, it falls back to the local CSV file
3. **Processing**: The data is cleaned, filtered, and sorted
4. **Automation**: The bot uses Playwright to navigate the booking website and make reservations
5. **Reporting**: Results are logged and optionally emailed with screenshots

## Google Sheets Integration Benefits

- **Real-time Updates**: Modify booking data directly in Google Sheets without redeploying
- **Team Collaboration**: Multiple people can update the booking list simultaneously
- **No Manual Uploads**: No need to manually update files in the repository
- **Version Control**: Google Sheets maintains edit history
- **Accessibility**: Edit from anywhere with a web browser
- **Live Data**: Changes are immediately available to the bot on next run

## Troubleshooting

### Google Sheets Issues

- **"Worksheet not found"**: Ensure the tab is named exactly "camden_active_booking_dates"
- **"File not found"**: Ensure the service account has been granted access to the Google Sheets
- **"Authentication failed"**: Verify the service account JSON is valid and properly formatted
- **"API not enabled"**: Enable both Google Sheets API and Google Drive API in your Google Cloud project

### Environment Variables

- Use single quotes around the `GOOGLE_SERVICE_ACCOUNT_JSON` value to preserve the JSON format
- For GitHub Actions, paste the entire JSON content as a secret (GitHub handles escaping)

### Local Testing

You can test the Google Sheets integration locally by setting the environment variables and running:

```bash
python test_gsheets.py
```

Or test the integration directly:

```bash
python -c "from data_processor import download_data_from_gsheets; import os; print(download_data_from_gsheets(os.environ['GSHEET_CAM_ID'], 'camden_active_booking_dates', os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']))"
```

## License

[Add your license information here]