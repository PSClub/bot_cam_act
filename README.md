# 🎾 Multi-Court Tennis Booking Bot for CA

An advanced automated tennis court booking system that manages multiple courts simultaneously with comprehensive Google Sheets integration, robust email notifications, and intelligent scheduling.

## ✨ Features

- **🏟️ Multi-Court Booking**: Books three tennis courts concurrently with different email accounts
- **📊 Google Sheets Integration**: Dynamic configuration and comprehensive logging via Google Sheets
- **📧 Smart Email System**: Detailed session reports to IT and summary emails to management
- **⏰ Strategic Timing**: Optimized for midnight slot releases (35 days in advance)
- **🔄 Robust Error Handling**: Network resilience with retry logic and specific exception handling
- **📸 Screenshot Capture**: Automatic screenshots for debugging and verification
- **🌍 Timezone Aware**: All operations in London UK timezone
- **🧪 Comprehensive Testing**: Full test suite with edge case coverage

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

## 🏗️ System Architecture

### Core Components

```
📊 Google Sheets ←→ 📋 SheetsManager ←→ 🎯 BookingOrchestrator
                                              ↓
                    📧 EmailManager ←←←←← 🎭 MultiSessionManager
                                              ↓
                                      🎮 BookingSession (×3)
                                              ↓
                                      🌐 Browser Actions (Playwright)
```

### How It Works

1. **📋 Configuration Loading**
   - Reads court and account configuration from "Account & Court Configuration" sheet
   - Loads booking schedule from "Booking Schedule" sheet
   - Validates all required environment variables

2. **📅 Dynamic Scheduling**
   - Calculates target date (today + 35 days)
   - Determines which slots to book based on target day of week
   - Matches target day against schedule table entries

3. **🎭 Concurrent Session Management**
   - Initializes three browser sessions simultaneously:
     - Mother → Court 1 (171)
     - Father → Court 2 (176) 
     - Bruce → Court 3 (177)
   - Each session runs independently with its own browser instance

4. **🎮 Booking Process (Per Session)**
   - Navigate to court booking page
   - Login with account credentials
   - Navigate to target date (35 days ahead)
   - Attempt to book all available slots for that day
   - Capture screenshots at each step
   - Log all terminal output with timestamps

5. **📊 Comprehensive Logging**
   - Each slot attempt logged to Google Sheets individually
   - Success/failure status with error details
   - Real-time updates during booking process

6. **📧 Multi-Tier Email Notifications**
   - **IT Emails**: One detailed email per court session to `IT_EMAIL_ADDRESS`
     - Complete terminal logs with timestamps
     - All screenshots taken during process
     - Detailed session information
   - **Summary Email**: Combined overview to `INFO_EMAIL_ADDRESS` + `KYLE_EMAIL_ADDRESS`
     - Slot-by-slot booking table
     - Recent Google Sheets log entries
     - High-level statistics

### 🎯 Smart Features

- **⏰ Midnight Detection**: Automatically waits until 00:00:00 London time if within 10 minutes
- **🔄 Network Resilience**: Exponential backoff retry for Google Sheets API calls
- **📸 Auto-Screenshots**: Captures evidence at key booking steps
- **🌍 Timezone Consistency**: All timestamps in London UK timezone
- **🎨 Flexible Input**: Robust parsing of day names ("sat" → "Saturday") and times ("8pm" → "2000")

## Google Sheets Integration Benefits

- **Real-time Updates**: Modify booking data directly in Google Sheets without redeploying
- **Team Collaboration**: Multiple people can update the booking list simultaneously
- **No Manual Uploads**: No need to manually update files in the repository
- **Version Control**: Google Sheets maintains edit history
- **Accessibility**: Edit from anywhere with a web browser
- **Live Data**: Changes are immediately available to the bot on next run

## 🧪 Testing

### Running the Test Suite

The system includes comprehensive tests for all major components:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test files
python tests/test_robust_parser.py
python tests/test_midnight_function.py
python tests/test_gsheets.py

# Run email functionality test
python tests/test_email_functionality.py
```

### Test Coverage

#### 🔤 Parser Tests (`tests/test_robust_parser.py`)
Tests robust input parsing for user-friendly data entry:

```bash
# Example test cases:
# Day names: "sat" → "Saturday", "tue" → "Tuesday"
# Times: "8am" → "0800", "4pm" → "1600", "18:00" → "1800"
# Edge cases: Invalid inputs, format variations
python tests/test_robust_parser.py
```

#### ⏰ Midnight Function Tests (`tests/test_midnight_function.py`)
Tests the critical midnight waiting functionality:

```bash
# Tests countdown timing accuracy
# Tests midnight detection logic
# Tests timezone handling
python tests/test_midnight_function.py
```

#### 📊 Google Sheets Tests (`tests/test_gsheets.py`)
Tests complete Google Sheets integration:

```bash
# Tests connection and authentication
# Tests reading configuration and schedule sheets
# Tests writing to booking log with pagination
# Tests error handling for missing sheets
python tests/test_gsheets.py
```

#### 📧 Email Tests (`tests/test_email_functionality.py`)
Tests email system configuration and sending:

```bash
# Tests SMTP configuration
# Tests email formatting and content
# Sends actual test email to verify setup
python tests/test_email_functionality.py
```

#### 🎭 Session Logging Demo (`tests/demo_session_logging.py`)
Demonstrates the new session logging and screenshot tracking:

```bash
# Shows how terminal logs are captured
# Shows how screenshots are tracked
# Previews IT email content format
python tests/demo_session_logging.py
```

### 🚀 Integration Testing

Test the complete booking flow in stages:

#### 1. **Environment Setup Test**
```bash
# Test all environment variables are set correctly
python -c "import config; print('✅ Config loaded successfully')"
```

#### 2. **Google Sheets Connection Test**
```bash
# Test Google Sheets API connection and permissions
python tests/test_gsheets.py
```

#### 3. **Email System Test**
```bash
# Test email configuration and send test email
python tests/test_email_functionality.py
```

#### 4. **Parser Validation Test**
```bash
# Test all input parsing edge cases
python tests/test_robust_parser.py
```

#### 5. **Browser Initialization Test**
```bash
# Test browser can launch and navigate (headless mode)
python main.py --headless --dry-run
```

#### 6. **Full System Test (Dry Run)**
```bash
# Run complete system without actual booking attempts
python main.py --dry-run --verbose
```

### 🔧 Debugging Tests

#### Enable Verbose Logging
```bash
# See detailed test output
python tests/test_gsheets.py --verbose
```

#### Test Individual Components
```bash
# Test just the EmailManager
python -c "from email_manager import EmailManager; print('✅ EmailManager imports successfully')"

# Test just the SheetsManager
python -c "from sheets_manager import SheetsManager; print('✅ SheetsManager imports successfully')"

# Test just the MultiSessionManager
python -c "from multi_session_manager import MultiSessionManager; print('✅ MultiSessionManager imports successfully')"
```

#### Browser Tests
```bash
# Test browser with visible window (debugging)
python main.py --no-headless --test-mode

# Test browser in headless mode
python main.py --headless --test-mode
```

### 📋 Test Checklist

Before deploying to production, ensure all tests pass:

- [ ] ✅ `test_robust_parser.py` - All parser functions handle edge cases
- [ ] ✅ `test_midnight_function.py` - Countdown timing works correctly  
- [ ] ✅ `test_gsheets.py` - Google Sheets integration works
- [ ] ✅ `test_email_functionality.py` - Email system configured and working
- [ ] ✅ Environment variables all set correctly
- [ ] ✅ Browser can launch in both headless and visible modes
- [ ] ✅ Google Sheets permissions granted to service account
- [ ] ✅ Email test successfully received
- [ ] ✅ All import statements work without errors

### 🐛 Common Test Issues

#### Import Errors
```bash
# If you get ModuleNotFoundError, ensure you're in the project root:
cd /path/to/bot_cam_act
python tests/test_robust_parser.py
```

#### Environment Variable Issues
```bash
# Check environment variables are set:
python -c "import os; print([k for k in os.environ.keys() if 'CAM' in k or 'GSHEET' in k])"
```

#### Google Sheets Permission Issues
```bash
# Test sheets access specifically:
python -c "from sheets_manager import SheetsManager; import os; sm = SheetsManager(os.environ['GSHEET_CAM_ID'], os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']); print('✅ Sheets accessible')"
```

## 🔧 Troubleshooting

### Google Sheets Issues

- **"Worksheet not found"**: Ensure sheets are named exactly "Account & Court Configuration", "Booking Schedule", and "Booking Log"
- **"File not found"**: Ensure the service account has been granted access to the Google Sheets
- **"Authentication failed"**: Verify the service account JSON is valid and properly formatted
- **"API not enabled"**: Enable both Google Sheets API and Google Drive API in your Google Cloud project
- **"Rate limit exceeded"**: The system includes automatic retry logic with exponential backoff

### Email Issues

- **"SMTP Authentication failed"**: Verify Gmail App Password is correct and 2FA is enabled
- **"No emails received"**: Check spam folder and verify recipient email addresses
- **"Email content missing"**: Ensure all email environment variables are set (`IT_EMAIL_ADDRESS`, `INFO_EMAIL_ADDRESS`, `KYLE_EMAIL_ADDRESS`)

### Browser Issues

- **"Browser won't launch"**: Run `playwright install` to ensure browsers are installed
- **"Timeouts during booking"**: Check internet connection and consider increasing timeout values
- **"Login failures"**: Verify account credentials are correct and accounts aren't locked

### Environment Variables

- Use single quotes around the `GOOGLE_SERVICE_ACCOUNT_JSON` value to preserve the JSON format
- For GitHub Actions, paste the entire JSON content as a secret (GitHub handles escaping)
- Ensure all required variables are set before running tests

## License

[Add your license information here]