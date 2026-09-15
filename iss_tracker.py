"""
ISS Live Position Tracker
Fetches the current ISS position from wheretheiss.at and appends it
as a row to a Google Sheet, which Tableau reads live.
"""
import sys
from datetime import datetime, timezone

import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_NAME = "ISS_Live"
CREDS_FILE = "service_account.json"
API_URL = "https://api.wheretheiss.at/v1/satellites/25544"
MAX_ROWS = 720  # ~24h of history at a 2-min polling interval

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]


def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1


def fetch_iss_position():
    r = requests.get(API_URL, timeout=10)
    r.raise_for_status()
    d = r.json()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "latitude": d["latitude"],
        "longitude": d["longitude"],
        "altitude_km": d["altitude"],
        "velocity_kmh": d["velocity"],
        "visibility": d["visibility"],
    }


def trim_old_rows(sheet, max_rows=MAX_ROWS):
    """Stop the sheet from growing forever."""
    total_rows = len(sheet.get_all_values())
    if total_rows > max_rows + 1:  # +1 accounts for the header row
        excess = total_rows - (max_rows + 1)
        sheet.delete_rows(2, 1 + excess)


def main():
    try:
        sheet = get_sheet()
        pos = fetch_iss_position()
        sheet.append_row([
            pos["timestamp"], pos["latitude"], pos["longitude"],
            pos["altitude_km"], pos["velocity_kmh"], pos["visibility"],
        ])
        trim_old_rows(sheet)
        print(f"OK: {pos['timestamp']} lat={pos['latitude']:.2f} lon={pos['longitude']:.2f}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
