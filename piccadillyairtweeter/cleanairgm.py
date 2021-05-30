import csv
from collections import defaultdict
from datetime import datetime, timedelta, date

import requests


NAMES = {
    "PM10": "PM10",
    "NO2": "NO₂",
}


def download_data(station):
    response = requests.get(
        "https://ds9g7q4m5yn94.cloudfront.net/annual.php",
        params={"station": station},
        headers={"user-agent": "piccadillyairtweeter/0.1.0"},
    )
    response.raise_for_status()
    lines = list(csv.reader(response.content.decode("utf-8").splitlines()))
    return lines[1:]


def build_datetime(dt_str):
    if dt_str.isdecimal():
        # looks like an Excel serial number
        return datetime(1899, 12, 30) + timedelta(days=int(dt_str), hours=-1)
    date_str, time_str = dt_str.split(" ")
    year, month, day = date_str.split("-")
    hour, minute, seconds = time_str.split(":")
    return datetime(int(year), int(month), int(day), int(hour) - 1, int(minute))


def build_results_from_download(records):
    all_results = defaultdict(dict)
    for record in records:
        for date, location, reading_type, value, unit in (record[i:i+5] for i in range(0, len(record), 5)):
            if not value:
                continue
            all_results[build_datetime(date)][NAMES[reading_type]] = float(value)
    return all_results


def get_cleanairgm_readings_yesterday(station):
    yesterday = date.today() - timedelta(days=1)
    annual_readings = build_results_from_download(download_data(station))
    return {dt: readings for dt, readings in annual_readings.items() if dt.date() == yesterday}
