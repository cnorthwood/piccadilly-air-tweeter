import csv
from datetime import datetime, timedelta, date

import requests

NAMES = {
    "PM<sub>10</sub> particulate matter (Hourly measured)": "PM10",
    "Nitrogen dioxide": "NO₂",
    "Ozone": "Ozone",
    "Sulphur dioxide": "SO₂",
    "PM<sub>2.5</sub> particulate matter (Hourly measured)": "PM2.5",
}


def download_data(area_code, year):
    response = requests.get(
        f"https://uk-air.defra.gov.uk/datastore/data_files/site_data/{area_code}_{year}.csv",
        headers={"user-agent": "piccadillyairtweeter/0.1.0"},
    )
    response.raise_for_status()
    lines = list(csv.reader(response.content.decode("utf-8").splitlines()))
    header = lines[4]
    for line in lines[6:]:
        yield dict(zip(header, line))


def build_datetime(date, time):
    day, month, year = date.split("-")
    hour, minute = time.split(":")
    return datetime(int(year), int(month), int(day), int(hour) - 1, int(minute))


def get_defra_readings_yesterday(area_code):
    yesterday = date.today() - timedelta(days=1)
    annual_readings = {
        build_datetime(reading["Date"], reading["time"]): {
            NAMES[label]: float(value)
            for label, value in reading.items()
            if label in NAMES and value
        }
        for reading in download_data(area_code, yesterday.year)
    }
    return {dt: readings for dt, readings in annual_readings.items() if dt.date() == yesterday}
