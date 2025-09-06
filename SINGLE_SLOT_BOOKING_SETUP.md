# Single Slot Per Account Booking System Setup

## Overview

The tennis booking system has been modified to ensure **one slot per account** instead of all accounts trying to book all available slots. This change enables fair distribution of tennis court bookings across 6 different accounts.

## Key Changes Made

### 1. **Booking Logic Modification**

#### Before:
- All 6 accounts would attempt to book ALL available slots
- This could result in one account getting multiple slots while others get none
- No fair distribution mechanism

#### After:
- Each account gets assigned exactly ONE slot per booking session
- Slots are distributed in round-robin fashion across accounts
- If there are 6 slots available, each of the 6 accounts gets exactly 1 slot
- If there are fewer slots than accounts, only the first N accounts get slots

### 2. **Code Changes**

#### `booking_orchestrator.py`
- Added `distribute_slots_among_sessions()` method to fairly distribute slots
- Modified `execute_booking_process()` to use slot distribution
- Each session now gets assigned a specific slot instead of all slots

#### `multi_session_manager.py`
- Added `book_distributed_slots()` method to handle individual slot assignments
- Each session now books only their assigned slot
- Maintains concurrent booking across all sessions

#### `config.py`
- Added environment variable configurations for 3 new accounts:
  - `SALLIE_CAM_EMAIL_ADDRESS` / `SALLIE_CAM_PASSWORD`
  - `JAN_CAM_EMAIL_ADDRESS` / `JAN_CAM_PASSWORD`
  - `JO_CAM_EMAIL_ADDRESS` / `JO_CAM_PASSWORD`

### 3. **GitHub Actions Workflow**

Updated existing `.github/workflows/book_ca_lif.yaml` with:
- Added environment variables for 3 new accounts (Sallie, Jan, Jo)
- Maintains existing repository dispatch and manual triggers
- All 6 accounts now configured for the single-slot booking system

## Required GitHub Configuration

You need to configure the following in your GitHub repository:

### **Account Email Addresses (Variables)**

Configure these as **Variables** (not Secrets) in your repository settings:

| Variable Name | Description | Example |
|---------------|-------------|---------|
| `MOTHER_CAM_EMAIL_ADDRESS` | Mother's email | `mother@example.com` |
| `FATHER_CAM_EMAIL_ADDRESS` | Father's email | `father@example.com` |
| `BRUCE_CAM_EMAIL_ADDRESS` | Bruce's email | `bruce@example.com` |
| `SALLIE_CAM_EMAIL_ADDRESS` | Sallie's email | `sallie@example.com` |
| `JAN_CAM_EMAIL_ADDRESS` | Jan's email | `jan@example.com` |
| `JO_CAM_EMAIL_ADDRESS` | Jo's email | `jo@example.com` |

### **Account Passwords (Secrets)**

Configure these as **Secrets** in your repository settings:

| Secret Name | Description |
|-------------|-------------|
| `MOTHER_CAM_PASSWORD` | Mother's password |
| `FATHER_CAM_PASSWORD` | Father's password |
| `BRUCE_CAM_PASSWORD` | Bruce's password |
| `SALLIE_CAM_PASSWORD` | Sallie's password |
| `JAN_CAM_PASSWORD` | Jan's password |
| `JO_CAM_PASSWORD` | Jo's password |

### **Google Sheets Configuration**

| Secret Name | Description |
|-------------|-------------|
| `GSHEET_CAM_ID` | Google Sheets ID from the shareable URL |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON content of Google Service Account key |

### **Payment Information**

| Secret Name | Description |
|-------------|-------------|
| `LB_CARD_NUMBER` | Credit card number |
| `LB_CARD_EXPIRY_MONTH` | Card expiry month (MM) |
| `LB_CARD_EXPIRY_YEAR` | Card expiry year (YYYY) |
| `LB_CARD_SECURITY_CODE` | CVV/Security code |
| `LB_CARDHOLDER_NAME` | Name on the card |
| `LB_ADDRESS` | Billing address |
| `LB_CITY` | Billing city |
| `LB_POSTCODE` | Billing postcode |

### **Email Notifications**

| Secret Name | Description |
|-------------|-------------|
| `KYLE_EMAIL_ADDRESS` | Kyle's email for notifications |
| `INFO_EMAIL_ADDRESS` | Info email for summary notifications |
| `IT_EMAIL_ADDRESS` | IT email for detailed session logs |
| `GMAIL_APP_PASSWORD` | Gmail app password for sending emails |

## Google Sheets Configuration

Ensure your Google Sheets has the "Account & Court Configuration" sheet with the following structure:

| Account | Email | Password | Court Number | Court URL |
|---------|-------|----------|--------------|-----------|
| Mother | `[email from secrets]` | `[from secrets]` | Court 1 | `https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/` |
| Father | `[email from secrets]` | `[from secrets]` | Court 2 | `https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/` |
| Bruce | `[email from secrets]` | `[from secrets]` | Court 3 | `https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/` |
| Sallie | `[email from secrets]` | `[from secrets]` | Court 1 | `https://camdenactive.camden.gov.uk/courses/detail/171/lincoln-s-inn-fields-tennis-court-1/` |
| Jan | `[email from secrets]` | `[from secrets]` | Court 2 | `https://camdenactive.camden.gov.uk/courses/detail/176/lincoln-s-inn-fields-tennis-court-2/` |
| Jo | `[email from secrets]` | `[from secrets]` | Court 3 | `https://camdenactive.camden.gov.uk/courses/detail/177/lincoln-s-inn-fields-tennis-court-3/` |

## How It Works Now

1. **Slot Distribution**: When the system finds available slots (e.g., 6 slots for a particular day), it distributes them evenly:
   - Slot 1 → Mother (Court 1)
   - Slot 2 → Father (Court 2)  
   - Slot 3 → Bruce (Court 3)
   - Slot 4 → Sallie (Court 1)
   - Slot 5 → Jan (Court 2)
   - Slot 6 → Jo (Court 3)

2. **Concurrent Booking**: All 6 accounts book their assigned slots simultaneously

3. **Fair Distribution**: Each account gets exactly one slot per booking session

4. **Court Coverage**: The 6 accounts cover all 3 courts with 2 accounts per court

## Testing the Configuration

To test the new setup:

1. **Local Testing**:
   ```bash
   # Set environment variables locally
   export MOTHER_CAM_EMAIL_ADDRESS="test@example.com"
   export MOTHER_CAM_PASSWORD="testpass"
   # ... (set all other variables)
   
   # Run the booking system
   python main.py --no-headless
   ```

2. **GitHub Actions Testing**:
   - Go to Actions tab in GitHub
   - Click "Tennis Court Booking Bot"
   - Click "Run workflow"
   - Enable "Run in debug mode" for visible browser testing

## Benefits of This Approach

1. **Fair Distribution**: Each account gets exactly one slot
2. **No Conflicts**: No competition between accounts for the same slots  
3. **Maximum Coverage**: 6 accounts can book up to 6 different slots
4. **Scalable**: Easy to add more accounts if needed
5. **Predictable**: Clear assignment of which account books which slot

## Troubleshooting

### Common Issues:

1. **Missing Secrets**: Ensure all GitHub secrets are properly configured
2. **Google Sheets Access**: Verify service account has access to the sheets
3. **Email Configuration**: Check Gmail app password is correct
4. **Account Credentials**: Verify all Camden Active account credentials are valid

### Debugging:

- Use the manual workflow trigger with debug mode enabled
- Check the uploaded artifacts for screenshots and logs
- Review the Google Sheets booking log for detailed results

## Next Steps

1. **Configure GitHub Secrets**: Add all required secrets to your GitHub repository
2. **Update Google Sheets**: Ensure the Account & Court Configuration sheet has all 6 accounts
3. **Test the System**: Run a manual workflow to verify everything works
4. **Monitor Results**: Check email notifications and Google Sheets logs

The system is now ready to provide fair, distributed booking with one slot per account!
