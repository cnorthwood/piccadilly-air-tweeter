import csv
from datetime import date, timedelta, datetime
from statistics import mean

import requests
import tweepy

from piccadillyairtweeter.secrets import fetch_secrets

THRESHOLDS = {
    "PM<sub>10</sub> particulate matter (Hourly measured)": 40,
    "Nitrogen dioxide": 40,
    "Ozone": 120,
    "Sulphur dioxide": 125,
    "PM<sub>2.5</sub> particulate matter (Hourly measured)": 25,
}

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


def get_readings(area_code, year):
    return {
        build_datetime(reading["Date"], reading["time"]): {
            label: float(value)
            for label, value in reading.items()
            if label not in {"Date", "time", "status", "unit"} and value
        }
        for reading in download_data(area_code, year)
    }


def get_breaches_yesterday(area_code, thresholds):
    yesterday = date.today() - timedelta(days=1)
    yesterdays_readings = {
        dt: readings
        for dt, readings in get_readings(area_code, yesterday.year).items()
        if dt.date() == yesterday
    }
    return {
        field: {
            "average_breached": mean(
                readings[field] for readings in yesterdays_readings.values() if field in readings
            )
            > threshold,
            "hours_breached": sum(
                1
                for readings in yesterdays_readings.values()
                if field in readings and readings[field] > threshold
            ),
        }
        for field, threshold in thresholds.items()
    }


def get_breach_messages(breaches):
    for field, name in NAMES.items():
        if breaches[field]["average_breached"]:
            yield f"{name} levels breached air quality standards all day."
        elif breaches[field]["hours_breached"] > 0:
            yield f"{name} levels breached air quality standards for {breaches[field]['hours_breached']} hours."


def send_tweets(area_name, parts):
    secrets = fetch_secrets()
    auth = tweepy.OAuthHandler(secrets["consumer_key"], secrets["consumer_secret"])
    auth.set_access_token(secrets["access_token"], secrets["access_token_secret"])
    twitter = tweepy.API(auth)

    this_tweet = ""
    tweets = []
    while parts:
        part = parts.pop(0)
        if len(this_tweet) + len(part) + 1 > 280:
            tweets.append(this_tweet)
            this_tweet = part
        else:
            if this_tweet:
                this_tweet = f"{this_tweet} {part}"
            else:
                this_tweet = f"Yesterday in {area_name}, {part}"
    if this_tweet:
        tweets.append(this_tweet)

    last_tweet_id = None
    for tweet in tweets:
        sent_tweet = twitter.update_status(status=tweet, in_reply_to_status_id=last_tweet_id)
        last_tweet_id = sent_tweet.id


send_tweets("Piccadilly", list(get_breach_messages(get_breaches_yesterday("MAN3", THRESHOLDS))))
