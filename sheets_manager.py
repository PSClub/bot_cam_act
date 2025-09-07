# sheets_manager.py
# This file handles all Google Sheets operations for the multi-court booking system

import json
import pandas as pd
import time
from datetime import datetime
from google.oauth2 import service_account
import gspread
from gspread.exceptions import WorksheetNotFound, APIError, SpreadsheetNotFound
import requests
from utils import get_timestamp, get_london_datetime

class SheetsManager:
    """Manages all Google Sheets operations for the booking system."""
    
    def __init__(self, sheet_id, service_account_json):
        """
        Initialize the sheets manager.
        
        Args:
            sheet_id (str): Google Sheets ID
            service_account_json (str): Service account JSON credentials
        """
        self.sheet_id = sheet_id
        self.service_account_json = service_account_json
        self.gc = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Google Sheets."""
        try:
            print(f"{get_timestamp()} --- Connecting to Google Sheets ---")
            
            if not self.sheet_id or not self.service_account_json:
                raise ValueError("Sheet ID and service account JSON are required")
            
            # Parse service account credentials
            credentials_info = json.loads(self.service_account_json)
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            
            # Authorize and open spreadsheet
            self.gc = gspread.authorize(credentials)
            self.spreadsheet = self.gc.open_by_key(self.sheet_id)
            
            print(f"{get_timestamp()} ✅ Successfully connected to Google Sheets")
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Failed to connect to Google Sheets: {e}")
            raise
    
    def _retry_api_call(self, func, *args, max_retries=3, delay=1, **kwargs):
        """
        Retry wrapper for Google Sheets API calls with exponential backoff.
        Handles network issues, rate limiting, and temporary API errors.
        
        Args:
            func: Function to call
            *args: Function arguments
            max_retries (int): Maximum number of retry attempts
            delay (float): Initial delay between retries in seconds
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
                
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    print(f"{get_timestamp()} 🔄 Network error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    print(f"{get_timestamp()}   Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"{get_timestamp()} ❌ All network retry attempts failed")
                    
            except APIError as e:
                last_exception = e
                # Handle specific Google Sheets API errors
                if "RATE_LIMIT_EXCEEDED" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt) + 5  # Extra delay for rate limits
                        print(f"{get_timestamp()} 🔄 Rate limit exceeded (attempt {attempt + 1}/{max_retries + 1})")
                        print(f"{get_timestamp()}   Waiting {wait_time:.1f} seconds before retry...")
                        time.sleep(wait_time)
                    else:
                        print(f"{get_timestamp()} ❌ Rate limit retry attempts exhausted")
                elif "INTERNAL_ERROR" in str(e) or "backend" in str(e).lower():
                    if attempt < max_retries:
                        wait_time = delay * (2 ** attempt)
                        print(f"{get_timestamp()} 🔄 Google Sheets internal error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                        print(f"{get_timestamp()}   Retrying in {wait_time:.1f} seconds...")
                        time.sleep(wait_time)
                    else:
                        print(f"{get_timestamp()} ❌ All API retry attempts failed")
                else:
                    # Don't retry for other API errors (e.g., permission denied, not found)
                    print(f"{get_timestamp()} ❌ Non-retryable API error: {e}")
                    raise
                    
            except (SpreadsheetNotFound, WorksheetNotFound) as e:
                # Don't retry for not found errors
                print(f"{get_timestamp()} ❌ Resource not found: {e}")
                raise
                
            except Exception as e:
                # Don't retry for unexpected errors
                print(f"{get_timestamp()} ❌ Unexpected error in API call: {e}")
                raise
        
        # If we get here, all retries were exhausted
        print(f"{get_timestamp()} ❌ Failed after {max_retries + 1} attempts. Last error: {last_exception}")
        raise last_exception
    
    def _read_worksheet_to_dicts(self, worksheet_name, description=""):
        """
        Private helper method to read a worksheet and convert to list of dictionaries.
        Implements DRY principle for shared worksheet reading logic.
        
        Args:
            worksheet_name (str): Name of the worksheet to read
            description (str): Optional description for logging
            
        Returns:
            list: List of dictionaries with worksheet data
            
        Raises:
            WorksheetNotFound: If worksheet doesn't exist
            ValueError: If worksheet structure is invalid
        """
        try:
            print(f"{get_timestamp()} --- Reading {worksheet_name} Sheet{' (' + description + ')' if description else ''} ---")
            
            worksheet = self._retry_api_call(self.spreadsheet.worksheet, worksheet_name)
            all_values = self._retry_api_call(worksheet.get_all_values)
            
            if len(all_values) < 2:
                raise ValueError(f"{worksheet_name} sheet must have at least a header row and one data row")
            
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Filter out empty rows
            data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
            
            if not data_rows:
                raise ValueError(f"No data rows found in {worksheet_name} sheet")
            
            # Convert to list of dictionaries
            sheet_data = []
            for row in data_rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                    else:
                        row_dict[header] = ""
                sheet_data.append(row_dict)
            
            print(f"{get_timestamp()} ✅ Successfully read {len(sheet_data)} entries from {worksheet_name}")
            return sheet_data
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ {worksheet_name} sheet not found")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading {worksheet_name} sheet: {e}")
            raise
    
    def create_log_entry(self, email, court, date, time, status, error_details=""):
        """
        Helper function to create a standardized log entry dictionary.
        Reduces code duplication when creating log entries throughout the application.
        
        Args:
            email (str): Email address of the account
            court (str): Court identifier (e.g., "Court 1", "Court 2")
            date (str): Booking date in DD/MM/YYYY format
            time (str): Booking time in HHMM format
            status (str): Status of the booking attempt
            error_details (str): Optional error details for failed bookings
            
        Returns:
            dict: Standardized log entry dictionary ready for writing to Google Sheets
        """
        from utils import get_london_datetime
        
        log_entry = {
            'Timestamp': get_london_datetime().strftime('%Y-%m-%d %H:%M:%S'),
            'Email': str(email),
            'Court': str(court),
            'Date': str(date),
            'Time': str(time),
            'Status': str(status),
            'Error Details': str(error_details)
        }
        
        return log_entry
    
    def read_booking_assignments(self):
        """
        Read the BookingSchedule sheet which now contains both account config and booking assignments.
        
        Returns:
            list: List of dictionaries with account and booking assignment data
        """
        return self._read_worksheet_to_dicts("BookingSchedule", "account and booking assignments")
    
    def read_booking_schedule_sheet(self):
        """
        Read the Booking Schedule sheet.
        
        Returns:
            list: List of dictionaries with booking schedule
        """
        return self._read_worksheet_to_dicts("Booking Schedule")
    
    def write_booking_log(self, log_entry):
        """
        Write a new entry to the Booking Log sheet (adds to top).
        
        Args:
            log_entry (dict): Dictionary with log entry data
                Required keys: Timestamp, Email, Court, Date, Time, Status, Error Details
        """
        try:
            print(f"{get_timestamp()} --- Writing to Booking Log ---")
            
            worksheet = self._retry_api_call(self.spreadsheet.worksheet, "Booking Log")
            
            # Prepare the row data
            row_data = [
                log_entry.get('Timestamp', ''),
                log_entry.get('Email', ''),
                log_entry.get('Court', ''),
                log_entry.get('Date', ''),
                log_entry.get('Time', ''),
                log_entry.get('Status', ''),
                log_entry.get('Error Details', '')
            ]
            
            # Insert at row 2 (after header)
            self._retry_api_call(worksheet.insert_row, row_data, 2)
            
            print(f"{get_timestamp()} ✅ Successfully logged booking entry")
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Booking log sheet not found")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error writing to booking log: {e}")
            raise
    
    def read_booking_log(self, limit=50, offset=0, get_all=False):
        """
        Read entries from the Booking Log sheet with pagination support.
        
        Args:
            limit (int): Maximum number of entries to retrieve per page
            offset (int): Number of entries to skip from the beginning (after header)
            get_all (bool): If True, retrieve all entries ignoring limit and offset
            
        Returns:
            dict: Contains 'entries' (list), 'total_count', 'has_more', 'next_offset'
        """
        try:
            print(f"{get_timestamp()} --- Reading Booking Log (limit={limit}, offset={offset}, get_all={get_all}) ---")
            
            worksheet = self._retry_api_call(self.spreadsheet.worksheet, "Booking Log")
            all_values = self._retry_api_call(worksheet.get_all_values)
            
            if len(all_values) <= 1:  # Only header or empty
                return {
                    'entries': [],
                    'total_count': 0,
                    'has_more': False,
                    'next_offset': 0
                }
            
            # Get headers and total data rows
            headers = all_values[0]
            all_data_rows = all_values[1:]  # Exclude header
            total_count = len(all_data_rows)
            
            # Apply pagination if not getting all
            if get_all:
                data_rows = all_data_rows
                has_more = False
                next_offset = 0
            else:
                # Apply offset and limit
                start_idx = offset
                end_idx = offset + limit
                data_rows = all_data_rows[start_idx:end_idx]
                has_more = end_idx < total_count
                next_offset = end_idx if has_more else 0
            
            # Convert to list of dictionaries
            log_entries = []
            for row in data_rows:
                if len(row) >= len(headers):
                    entry = {}
                    for i, header in enumerate(headers):
                        entry[header] = row[i] if i < len(row) else ''
                    log_entries.append(entry)
            
            result = {
                'entries': log_entries,
                'total_count': total_count,
                'has_more': has_more,
                'next_offset': next_offset
            }
            
            print(f"{get_timestamp()} ✅ Retrieved {len(log_entries)} log entries (total: {total_count})")
            return result
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Booking log sheet not found")
            return {
                'entries': [],
                'total_count': 0,
                'has_more': False,
                'next_offset': 0
            }
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading booking log: {e}")
            return {
                'entries': [],
                'total_count': 0,
                'has_more': False,
                'next_offset': 0
            }
    

    
    def get_sheet_info(self):
        """
        Get information about all worksheets in the spreadsheet.
        
        Returns:
            dict: Information about the spreadsheet and its worksheets
        """
        try:
            worksheets = self.spreadsheet.worksheets()
            sheet_info = {
                'spreadsheet_id': self.sheet_id,
                'spreadsheet_title': self.spreadsheet.title,
                'worksheets': []
            }
            
            for ws in worksheets:
                sheet_info['worksheets'].append({
                    'title': ws.title,
                    'row_count': ws.row_count,
                    'col_count': ws.col_count
                })
            
            return sheet_info
            
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error getting sheet info: {e}")
            raise

def test_sheets_connection(sheet_id, service_account_json):
    """
    Test function to verify Google Sheets connection and structure.
    
    Args:
        sheet_id (str): Google Sheets ID
        service_account_json (str): Service account JSON credentials
        
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        print(f"{get_timestamp()} === Testing Google Sheets Connection ===")
        
        # Create sheets manager
        sheets_manager = SheetsManager(sheet_id, service_account_json)
        
        # Get sheet information
        sheet_info = sheets_manager.get_sheet_info()
        print(f"{get_timestamp()} 📊 Spreadsheet: {sheet_info['spreadsheet_title']}")
        print(f"{get_timestamp()} 📋 Worksheets found:")
        for ws in sheet_info['worksheets']:
            print(f"{get_timestamp()}   - {ws['title']} ({ws['row_count']} rows, {ws['col_count']} cols)")
        
        # Test reading configuration
        config_data = sheets_manager.read_configuration_sheet()
        print(f"{get_timestamp()} ✅ Configuration sheet read successfully")
        print(f"{get_timestamp()} 📋 Configuration entries: {len(config_data)}")
        
        # Test reading schedule
        schedule_data = sheets_manager.read_booking_schedule_sheet()
        print(f"{get_timestamp()} ✅ Schedule sheet read successfully")
        print(f"{get_timestamp()} 📅 Schedule entries: {len(schedule_data)}")
        
        # Test writing to log
        from utils import get_london_datetime
        london_time = get_london_datetime()
        test_log_entry = {
            'Timestamp': london_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Email': 'test@example.com',
            'Court': 'Court 1',
            'Date': '01/01/2024',
            'Time': '1800',
            'Status': '🧪 Test Entry',
            'Error Details': 'Test log entry'
        }
        sheets_manager.write_booking_log(test_log_entry)
        print(f"{get_timestamp()} ✅ Log sheet write test successful")
        
        print(f"{get_timestamp()} 🎉 All Google Sheets tests passed!")
        return True
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Google Sheets test failed: {e}")
        return False
