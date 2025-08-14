# sheets_manager.py
# This file handles all Google Sheets operations for the multi-court booking system

import json
import pandas as pd
import pytz
from datetime import datetime
from google.oauth2 import service_account
import gspread
from gspread.exceptions import WorksheetNotFound, APIError

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds in London UK timezone."""
    uk_tz = pytz.timezone('Europe/London')
    london_time = datetime.now(uk_tz)
    return f"[{london_time.strftime('%H:%M:%S.%f')[:-4]}]"

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
    
    def read_configuration_sheet(self):
        """
        Read the Account & Court Configuration sheet.
        
        Returns:
            list: List of dictionaries with account configuration
        """
        try:
            print(f"{get_timestamp()} --- Reading Configuration Sheet ---")
            
            worksheet = self.spreadsheet.worksheet("Account & Court Configuration")
            all_values = worksheet.get_all_values()
            
            if len(all_values) < 2:
                raise ValueError("Configuration sheet must have at least a header row and one data row")
            
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Filter out empty rows
            data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
            
            if not data_rows:
                raise ValueError("No data rows found in configuration sheet")
            
            # Convert to list of dictionaries
            config_data = []
            for row in data_rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                    else:
                        row_dict[header] = ""
                config_data.append(row_dict)
            
            print(f"{get_timestamp()} ✅ Successfully read {len(config_data)} configuration entries")
            return config_data
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Configuration sheet not found")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading configuration sheet: {e}")
            raise
    
    def read_booking_schedule_sheet(self):
        """
        Read the Booking Schedule sheet.
        
        Returns:
            list: List of dictionaries with booking schedule
        """
        try:
            print(f"{get_timestamp()} --- Reading Booking Schedule Sheet ---")
            
            worksheet = self.spreadsheet.worksheet("Booking Schedule")
            all_values = worksheet.get_all_values()
            
            if len(all_values) < 2:
                raise ValueError("Booking schedule sheet must have at least a header row and one data row")
            
            headers = all_values[0]
            data_rows = all_values[1:]
            
            # Filter out empty rows
            data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
            
            if not data_rows:
                raise ValueError("No data rows found in booking schedule sheet")
            
            # Convert to list of dictionaries
            schedule_data = []
            for row in data_rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    if i < len(row):
                        row_dict[header] = row[i]
                    else:
                        row_dict[header] = ""
                schedule_data.append(row_dict)
            
            print(f"{get_timestamp()} ✅ Successfully read {len(schedule_data)} schedule entries")
            return schedule_data
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Booking schedule sheet not found")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading booking schedule sheet: {e}")
            raise
    
    def write_booking_log(self, log_entry):
        """
        Write a new entry to the Booking Log sheet (adds to top).
        
        Args:
            log_entry (dict): Dictionary with log entry data
                Required keys: Timestamp, Email, Court, Date, Time, Status, Error Details
        """
        try:
            print(f"{get_timestamp()} --- Writing to Booking Log ---")
            
            worksheet = self.spreadsheet.worksheet("Booking Log")
            
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
            worksheet.insert_row(row_data, 2)
            
            print(f"{get_timestamp()} ✅ Successfully logged booking entry")
            
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Booking log sheet not found")
            raise
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error writing to booking log: {e}")
            raise
    
    def update_booking_status(self, court, date, time, status, error_details=""):
        """
        Update the status of a specific booking in the schedule sheets.
        
        Args:
            court (str): Court number (e.g., "Court 1")
            date (str): Booking date in DD/MM/YYYY format
            time (str): Booking time in HHMM format
            status (str): New status (e.g., "✅ Success", "❌ Failed")
            error_details (str): Error details if applicable
        """
        try:
            print(f"{get_timestamp()} --- Updating Booking Status ---")
            
            # Determine which schedule sheet to update based on the day
            date_obj = datetime.strptime(date, "%d/%m/%Y")
            day_name = date_obj.strftime('%A')
            
            if day_name in ['Tuesday', 'Thursday']:
                worksheet_name = "Weekday Bookings (Feb-Aug)"
            elif day_name in ['Saturday', 'Sunday']:
                worksheet_name = "Weekend Bookings (All Year)"
            else:
                print(f"{get_timestamp()} ⚠️ No schedule sheet for {day_name}")
                return
            
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            # Find the row to update
            target_row = None
            for i, row in enumerate(all_values):
                if len(row) >= 3:
                    row_day = row[0] if row[0] else ""
                    row_time = row[1] if row[1] else ""
                    
                    # Normalize day and time for comparison
                    from robust_parser import normalize_day_name, normalize_time
                    
                    try:
                        normalized_row_day = normalize_day_name(row_day)
                        normalized_row_time = normalize_time(row_time)
                        normalized_target_day = normalize_day_name(day_name)
                        normalized_target_time = normalize_time(time)
                        
                        if (normalized_row_day == normalized_target_day and 
                            normalized_row_time == normalized_target_time):
                            target_row = i + 1  # Convert to 1-based index
                            break
                    except ValueError:
                        continue
            
            if target_row:
                # Find the court column
                headers = all_values[0]
                court_column = None
                for i, header in enumerate(headers):
                    if court in header:
                        court_column = i + 1  # Convert to 1-based index
                        break
                
                if court_column:
                    # Update the cell
                    cell_address = f"{chr(64 + court_column)}{target_row}"  # Convert to A1 notation
                    worksheet.update(cell_address, status)
                    print(f"{get_timestamp()} ✅ Updated {court} status to {status}")
                else:
                    print(f"{get_timestamp()} ⚠️ Court column not found for {court}")
            else:
                print(f"{get_timestamp()} ⚠️ Schedule row not found for {day_name} {time}")
                
        except WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Schedule sheet not found")
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error updating booking status: {e}")
    
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
        uk_tz = pytz.timezone('Europe/London')
        london_time = datetime.now(uk_tz)
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
