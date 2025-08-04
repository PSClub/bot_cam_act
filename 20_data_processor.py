# 20_data_processor.py
# This file handles reading, cleaning, and preparing the booking data.

import pandas as pd
import re
from datetime import datetime

def process_booking_file(file_path):
    """
    Reads, cleans, filters, and sorts booking data from a CSV file.
    """
    print(f"--- Processing booking file: {file_path} ---")
    try:
        df = pd.read_csv(file_path, skipinitialspace=True)
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
