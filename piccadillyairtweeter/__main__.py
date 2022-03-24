from statistics import mean

import tweepy

from piccadillyairtweeter.cleanairgm import get_cleanairgm_readings_yesterday
from piccadillyairtweeter.defra import get_defra_readings_yesterday
from piccadillyairtweeter.secrets import log_in_to_twitter

TWEETS_ENABLED = True

ACCOUNTS = {
    "CleanAirPicc": ("in Piccadilly Gardens", "defra", "MAN3"),
    "CleanAirOxfRoad": ("on Oxford Road", "cleanairgm", "MAN1"),
}

# https://apps.who.int/iris/bitstream/handle/10665/345329/9789240034228-eng.pdf?sequence=1&isAllowed=y
THRESHOLDS = {
    "NO₂": 25,
    "PM2.5": 15,
    "PM10": 45,
    "Ozone": 100,
    "SO₂": 40,
}


def get_average_yesterday(readings):
    return mean(readings) if readings else 0


def get_levels_yesterday(provider, *provider_args):
    if provider == "defra":
        yesterdays_readings = get_defra_readings_yesterday(*provider_args)
    elif provider == "cleanairgm":
        yesterdays_readings = get_cleanairgm_readings_yesterday(*provider_args)
    else:
        raise NotImplementedError(f"unrecognised provider: {provider}")
    return {
        field: get_average_yesterday([readings[field] for readings in yesterdays_readings.values() if field in readings]) / threshold
        for field, threshold in THRESHOLDS.items()
    }


def get_breach_messages(breaches):
    for field, level in breaches.items():
        if level >= 1.0:
            yield f"{field} levels were {round(level, 1)} times the WHO air quality guidelines"


def send_tweets(twitter_auth, area_name, parts):
    twitter = tweepy.API(twitter_auth)
    this_tweet = ""
    tweets = []
    while parts:
        part = parts.pop(0)
        if len(this_tweet) + len(part) + 2 > 280:
            tweets.append(this_tweet)
            this_tweet = f"Yesterday {area_name}, {part}."
        else:
            if this_tweet:
                this_tweet = f"{this_tweet} {part}."
            else:
                this_tweet = f"Yesterday {area_name}, {part}."
    if this_tweet:
        tweets.append(this_tweet)

    if twitter_auth:
        last_tweet_id = None
        for tweet in tweets:
            sent_tweet = twitter.update_status(status=tweet, in_reply_to_status_id=last_tweet_id)
            last_tweet_id = sent_tweet.id
    else:
        for tweet in tweets:
            print(tweet)


for account_name, (area_name, *provider) in ACCOUNTS.items():
    send_tweets(
        log_in_to_twitter(account_name) if TWEETS_ENABLED else None,
        area_name,
        list(get_breach_messages(get_levels_yesterday(*provider))),
    )
