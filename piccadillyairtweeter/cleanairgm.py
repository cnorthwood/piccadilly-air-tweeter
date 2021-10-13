import csv
from collections import defaultdict
from datetime import datetime, timedelta, date
from itertools import chain

import requests


NAMES = {
    "PM10": "PM10",
    "NO2": "NO₂",
}


def download_data(station, date):
    response = requests.get(
        "https://cleanairgm.com/.netlify/functions/getSiteDetail",
        params={"code": station, "yesterday": date.isoformat(), "today": (date + timedelta(days=1)).isoformat() },
        headers={"user-agent": "piccadillyairtweeter/0.1.0"},
    )
    response.raise_for_status()
    return chain(*response.json())


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
        if not record["Value"]:
            continue
        all_results[build_datetime(record["MeasurementDate"])][NAMES[record["Species"]]] = float(record["Value"])
    return all_results


def get_cleanairgm_readings_yesterday(station):
    yesterday = date.today() - timedelta(days=1)
    readings = build_results_from_download(download_data(station, yesterday))
    return {dt: readings for dt, readings in readings.items() if dt.date() == yesterday}
