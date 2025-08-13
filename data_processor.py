# data_processor.py
# This file handles reading, cleaning, and preparing the booking data.

import pandas as pd
import re
import json
import tempfile
import os
from datetime import datetime
from io import StringIO
from google.oauth2 import service_account
from googleapiclient.discovery import build
import gspread

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
        print(f"--- Downloading data from Google Sheets (Sheet ID: {sheet_id}, Tab: {tab_name}) ---")
        
        if not sheet_id or not tab_name or not service_account_json:
            print("❌ Error: Google Sheets ID, tab name, or service account JSON not provided.")
            return None
        
        # Parse the service account JSON
        try:
            credentials_info = json.loads(service_account_json)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid service account JSON format: {e}")
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
            print(f"❌ Error: Worksheet '{tab_name}' not found in the spreadsheet.")
            available_sheets = [ws.title for ws in spreadsheet.worksheets()]
            print(f"Available worksheets: {', '.join(available_sheets)}")
            return None
        
        # Get all values from the worksheet
        all_values = worksheet.get_all_values()
        
        if not all_values:
            print("❌ Error: No data found in the worksheet.")
            return None
        
        # Convert to DataFrame
        # Assume first row contains headers
        if len(all_values) < 2:
            print("❌ Error: Worksheet must have at least a header row and one data row.")
            return None
        
        headers = all_values[0]
        data_rows = all_values[1:]
        
        # Filter out empty rows
        data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
        
        if not data_rows:
            print("❌ Error: No data rows found (all rows are empty).")
            return None
        
        df = pd.DataFrame(data_rows, columns=headers)
        
        print(f"✅ Successfully downloaded {len(df)} rows from Google Sheets")
        print(f"📊 Columns found: {', '.join(df.columns.tolist())}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error downloading from Google Sheets: {e}")
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
    # Try Google Sheets first if configured
    if gsheet_id and gsheet_tab and service_account_json:
        print("--- Attempting to download data from Google Sheets ---")
        df = download_data_from_gsheets(gsheet_id, gsheet_tab, service_account_json)
        if df is not None:
            print("✅ Successfully loaded data from Google Sheets")
        else:
            print("⬇️ Google Sheets download failed, falling back to local file...")
            df = pd.read_csv(file_path, skipinitialspace=True)
    else:
        print(f"--- Processing local booking file: {file_path} ---")
        if not gsheet_id and not gsheet_tab and not service_account_json:
            print("📝 Note: Google Sheets not configured. Set GSHEET_CAM_ID and GOOGLE_SERVICE_ACCOUNT_JSON environment variables to use Google Sheets.")
        elif not gsheet_id:
            print("⚠️ Warning: GSHEET_CAM_ID not set. Using local file.")
        elif not gsheet_tab:
            print("⚠️ Warning: Google Sheets tab name not configured. Using local file.")
        elif not service_account_json:
            print("⚠️ Warning: GOOGLE_SERVICE_ACCOUNT_JSON not set. Using local file.")
        df = pd.read_csv(file_path, skipinitialspace=True)
    
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
            print("No bookings found in the 33-35 day window.")
            return []

        print(f"Found {len(booking_window_df)} bookings in the valid window.")

        # 4. Sort the data
        sorted_df = booking_window_df.sort_values(by=['time', 'parsed_date', 'court_link'])
        
        # 5. Format for output
        sorted_df['booking_date_str'] = sorted_df['parsed_date'].dt.strftime('%d/%m/%Y')
        final_list = sorted_df[['court_link', 'booking_date_str', 'time']].values.tolist()
        
        print("\n--- The following bookings will be attempted in this order: ---")
        for item in final_list:
            print(f"  - Court: {item[0].split('/')[-2]}, Date: {item[1]}, Time: {item[2]}")
        print("------------------------------------------------------------")
        
        return final_list

    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
        return []
    except Exception as e:
        print(f"❌ An error occurred while processing the CSV file: {e}")
        return []
