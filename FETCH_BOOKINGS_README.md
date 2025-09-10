# 📋 Camden Active Bookings Fetcher

A standalone script that concurrently logs into all Camden Active accounts, fetches current bookings from the "My Bookings" page, and stores the data in a Google Sheet for easy filtering and analysis.

## ✨ Features

- **🔄 Concurrent Login**: Logs into all configured accounts simultaneously for maximum efficiency
- **📊 Data Extraction**: Scrapes booking data from the My Bookings page including:
  - Email address (account identifier)
  - Booking date
  - Facility name
  - Court number
  - Date and time
- **📈 Google Sheets Integration**: Creates and updates "Upcoming Camden Bookings" sheet
- **🔄 Data Refresh**: Clears and repopulates the sheet on each run
- **📅 Smart Sorting**: Sorts bookings by date (most recent first)
- **⏰ Cron Job Ready**: Designed to run automatically via GitHub Actions

## 🚀 Usage

### Manual Execution

```bash
python fetch_current_bookings.py
```

### Automated Execution

The script runs automatically via GitHub Actions daily at 8:00 AM UTC (9:00 AM BST).

You can also trigger it manually:
1. Go to your repository's Actions tab
2. Select "Fetch Current Camden Bookings" workflow
3. Click "Run workflow"

## 📋 Requirements

### Environment Variables

All the same environment variables as the main booking system:

```bash
# Google Sheets Configuration
GSHEET_CAM_ID=your_google_sheets_id
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'

# Account Credentials
MOTHER_CAM_EMAIL_ADDRESS=email@example.com
MOTHER_CAM_PASSWORD=password
FATHER_CAM_EMAIL_ADDRESS=email@example.com
FATHER_CAM_PASSWORD=password
BRUCE_CAM_EMAIL_ADDRESS=email@example.com
BRUCE_CAM_PASSWORD=password
SALLIE_CAM_EMAIL_ADDRESS=email@example.com
SALLIE_CAM_PASSWORD=password
JAN_CAM_EMAIL_ADDRESS=email@example.com
JAN_CAM_PASSWORD=password
JO_CAM_EMAIL_ADDRESS=email@example.com
JO_CAM_PASSWORD=password
```

### Dependencies

The script uses the same dependencies as the main booking system:
- playwright
- gspread
- google-auth
- All existing project dependencies

## 📊 Output Format

The Google Sheet "Upcoming Camden Bookings" contains:

| Column | Description | Example |
|--------|-------------|---------|
| Email | Account email address | mother@example.com |
| Booking Date | Original booking date text | 08/09/2025 00:02 |
| Facility | Facility name | Lincoln's Inn Fields Tennis |
| Court Number | Court identifier | Court 2 |
| Date | Parsed booking date | 27/09/2025 |
| Time | Parsed booking time | 14:00 |

Additional information at the bottom:
- Last Updated timestamp
- Total bookings count
- Number of accounts checked

## 🔧 Configuration

### Workflow Schedule

Edit `.github/workflows/fetch_bookings.yml` to change the schedule:

```yaml
on:
  schedule:
    # Run every day at 8:00 AM UTC
    - cron: '0 8 * * *'
```

### Browser Settings

The script runs in headless mode by default. To show browser windows during development:

```bash
export HEADLESS_MODE=False
python fetch_current_bookings.py
```

## 🧪 Testing

Run the test suite to verify functionality:

```bash
python test_fetch_bookings.py
```

Tests cover:
- Account initialization
- Facility name parsing
- Date/time extraction
- Booking data sorting
- Mock data processing

## 📁 File Structure

```
fetch_current_bookings.py      # Main script
test_fetch_bookings.py         # Test suite
.github/workflows/fetch_bookings.yml  # GitHub Actions workflow
FETCH_BOOKINGS_README.md       # This documentation
```

## 🔍 How It Works

1. **Initialization**: Sets up accounts from environment variables
2. **Google Sheets**: Connects to the main spreadsheet
3. **Concurrent Execution**: Creates browser sessions for each account
4. **Login Process**: Logs into Camden Active for each account
5. **Navigation**: Goes to My Bookings page
6. **Data Extraction**: Scrapes booking table data
7. **Data Processing**: Parses and standardizes the information
8. **Sheet Update**: Clears and repopulates the Google Sheet
9. **Cleanup**: Closes all browser sessions

## 🛠️ Troubleshooting

### Common Issues

**No bookings found**: 
- Check that accounts have valid credentials
- Verify accounts have active bookings
- Check the Camden Active website structure hasn't changed

**Google Sheets errors**:
- Verify `GSHEET_CAM_ID` is correct
- Check service account has edit permissions
- Ensure `GOOGLE_SERVICE_ACCOUNT_JSON` is valid

**Login failures**:
- Verify email/password combinations
- Check if Camden Active login page has changed
- Review browser screenshots in GitHub Actions artifacts

### Debug Mode

To run with visible browser for debugging:

```bash
export HEADLESS_MODE=False
export SHOW_BROWSER=true
python fetch_current_bookings.py
```

### Logs and Screenshots

- All operations are logged with timestamps
- Screenshots are automatically taken on errors
- GitHub Actions stores screenshots as artifacts for 7 days

## 🔄 Integration with Main System

This fetcher is completely independent of the main booking system but uses:
- Same configuration system (`config.py`)
- Same Google Sheets manager (`sheets_manager.py`)
- Same utilities (`utils.py`)
- Same browser automation patterns

The fetched data complements the booking logs by showing what's currently booked across all accounts.

## 📅 Scheduling Recommendations

- **Daily**: 8:00 AM UTC (current setting) - Good for daily overview
- **Twice Daily**: Add 6:00 PM UTC for evening updates
- **Weekly**: Mondays only if less frequent updates are needed

Edit the workflow file to adjust timing based on your needs.
