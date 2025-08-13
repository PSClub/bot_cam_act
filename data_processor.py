# data_processor.py
# This file handles reading, cleaning, and preparing the booking data.

import pandas as pd
import re
import json
import tempfile
import os
import time
from datetime import datetime
from io import StringIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread

def get_timestamp():
    """Returns a timestamp string with 100ths of seconds."""
    return f"[{datetime.now().strftime('%H:%M:%S.%f')[:-4]}]"

def download_data_from_gsheets(sheet_id, tab_name, service_account_json):
    """
    Downloads data from Google Sheets using service account authentication.
    
    Args:
        sheet_id (str): The Google Sheets ID
        tab_name (str): The name of the worksheet/tab to read from
        service_account_json (str): JSON string containing service account credentials
        
    Returns:
        pandas.DataFrame: DataFrame with the sheet data, or None if failed
    """
    try:
        print(f"{get_timestamp()} --- Downloading data from Google Sheets (Sheet ID: {sheet_id}, Tab: {tab_name}) ---")
        
        if not sheet_id or not tab_name or not service_account_json:
            print(f"{get_timestamp()} ❌ Error: Google Sheets ID, tab name, or service account JSON not provided.")
            return None
        
        # Parse the service account JSON
        try:
            credentials_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            print(f"{get_timestamp()} ❌ Error: Invalid service account JSON format: {e}")
            return None
        
        # Create credentials from service account info
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/drive.readonly'
            ]
        )
        
        # Authorize and open the spreadsheet
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Get the specific worksheet
        try:
            worksheet = spreadsheet.worksheet(tab_name)
        except gspread.WorksheetNotFound:
            print(f"{get_timestamp()} ❌ Error: Worksheet '{tab_name}' not found in the spreadsheet.")
            available_sheets = [ws.title for ws in spreadsheet.worksheets()]
            print(f"{get_timestamp()} Available worksheets: {', '.join(available_sheets)}")
            return None
        
        # Get all values from the worksheet
        all_values = worksheet.get_all_values()
        
        if not all_values:
            print(f"{get_timestamp()} ❌ Error: No data found in the worksheet.")
            return None
        
        # Convert to DataFrame
        # Assume first row contains headers
        if len(all_values) < 2:
            print(f"{get_timestamp()} ❌ Error: Worksheet must have at least a header row and one data row.")
            return None
        
        headers = all_values[0]
        data_rows = all_values[1:]
        
        # Filter out empty rows
        data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
        
        if not data_rows:
            print(f"{get_timestamp()} ❌ Error: No data rows found (all rows are empty).")
            return None
        
        df = pd.DataFrame(data_rows, columns=headers)
        
        print(f"{get_timestamp()} ✅ Successfully downloaded {len(df)} rows from Google Sheets")
        print(f"{get_timestamp()} 📊 Columns found: {', '.join(df.columns.tolist())}")
        
        return df
        
    except Exception as e:
        print(f"{get_timestamp()} ❌ Error downloading from Google Sheets: {e}")
        return None

def process_booking_file(file_path, gsheet_id=None, gsheet_tab=None, service_account_json=None):
    """
    Reads, cleans, filters, and sorts booking data from a CSV file or Google Sheets.
    Can read from local file or Google Sheets.
    
    Args:
        file_path (str): Local file path (used as fallback or when Google Sheets not configured)
        gsheet_id (str): Google Sheets ID (optional)
        gsheet_tab (str): Google Sheets tab/worksheet name (optional)
        service_account_json (str): Service account JSON for Google Sheets authentication (optional)
    """
    # Debug logging to see what we're receiving
    print(f"{get_timestamp()} 🔍 Debug: gsheet_id = '{gsheet_id}'")
    print(f"{get_timestamp()} 🔍 Debug: gsheet_tab = '{gsheet_tab}'")
    print(f"{get_timestamp()} 🔍 Debug: service_account_json = {'Set' if service_account_json else 'Not set'}")
    
    # Try Google Sheets first if configured
    if gsheet_id and gsheet_tab and service_account_json:
        print(f"{get_timestamp()} --- Attempting to download data from Google Sheets ---")
        df = download_data_from_gsheets(gsheet_id, gsheet_tab, service_account_json)
        if df is not None:
            print(f"{get_timestamp()} ✅ Successfully loaded data from Google Sheets")
        else:
            print(f"{get_timestamp()} ⬇️ Google Sheets download failed, attempting local file fallback...")
            try:
                df = pd.read_csv(file_path, skipinitialspace=True)
                print(f"{get_timestamp()} ✅ Successfully loaded data from local CSV file")
            except FileNotFoundError:
                print(f"{get_timestamp()} ❌ Error: Neither Google Sheets nor local file '{file_path}' could be loaded.")
                print(f"{get_timestamp()} 🔍 Please check:")
                print(f"{get_timestamp()}    1. Google Sheets API is enabled")
                print(f"{get_timestamp()}    2. Service account has access to the spreadsheet")
                print(f"{get_timestamp()}    3. Local CSV file exists (if using fallback)")
                return []
            except Exception as e:
                print(f"{get_timestamp()} ❌ Error reading local CSV file: {e}")
                return []
    else:
        print(f"{get_timestamp()} --- Processing local booking file: {file_path} ---")
        if not gsheet_id and not gsheet_tab and not service_account_json:
            print(f"{get_timestamp()} 📝 Note: Google Sheets not configured. Set GSHEET_CAM_ID and GOOGLE_SERVICE_ACCOUNT_JSON environment variables to use Google Sheets.")
        elif not gsheet_id:
            print(f"{get_timestamp()} ⚠️ Warning: GSHEET_CAM_ID not set. Using local file.")
        elif not gsheet_tab:
            print(f"{get_timestamp()} ⚠️ Warning: Google Sheets tab name not configured. Using local file.")
        elif not service_account_json:
            print(f"{get_timestamp()} ⚠️ Warning: GOOGLE_SERVICE_ACCOUNT_JSON not set. Using local file.")
        
        try:
            df = pd.read_csv(file_path, skipinitialspace=True)
            print(f"{get_timestamp()} ✅ Successfully loaded data from local CSV file")
        except FileNotFoundError:
            print(f"{get_timestamp()} ❌ Error: Local file '{file_path}' not found.")
            print(f"{get_timestamp()} 🔍 Please check:")
            print(f"{get_timestamp()}    1. Local CSV file exists and is accessible")
            print(f"{get_timestamp()}    2. Or configure Google Sheets integration")
            return []
        except Exception as e:
            print(f"{get_timestamp()} ❌ Error reading local CSV file: {e}")
            return []
    
    try:
        df.columns = ['court_link', 'booking_date', 'time']

        # 1. Clean the time column
        df['time'] = df['time'].astype(str).apply(lambda x: ''.join(re.findall(r'\d+', x))).str.zfill(4)

        # 2. Clean and parse the date column
        df['parsed_date'] = pd.to_datetime(df['booking_date'], dayfirst=True, errors='coerce')
        df.dropna(subset=['parsed_date'], inplace=True)

        # 3. Filter by date window (33-35 days from today)
        today = pd.Timestamp.now().normalize()
        df['days_ahead'] = (df['parsed_date'] - today).dt.days
        booking_window_df = df[df['days_ahead'].isin([33, 34, 35])].copy()
        
        if booking_window_df.empty:
            print(f"{get_timestamp()} No bookings found in the 33-35 day window.")
            return []

        print(f"{get_timestamp()} Found {len(booking_window_df)} bookings in the valid window.")

        # 4. Sort the data
        sorted_df = booking_window_df.sort_values(by=['time', 'parsed_date', 'court_link'])
        
        # 5. Format for output
        sorted_df['booking_date_str'] = sorted_df['parsed_date'].dt.strftime('%d/%m/%Y')
        final_list = sorted_df[['court_link', 'booking_date_str', 'time']].values.tolist()
        
        print(f"{get_timestamp()} --- The following bookings will be attempted in this order: ---")
        for item in final_list:
            print(f"{get_timestamp()}   - Court: {item[0].split('/')[-2]}, Date: {item[1]}, Time: {item[2]}")
        print(f"{get_timestamp()} ------------------------------------------------------------")
        
        return final_list

    except FileNotFoundError:
        print(f"{get_timestamp()} ❌ Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"{get_timestamp()} ❌ An error occurred while processing the CSV file: {e}")
        return []
