from statistics import mean

import tweepy

from piccadillyairtweeter.defra import get_defra_readings_yesterday
from piccadillyairtweeter.secrets import log_in_to_twitter

TWEETS_ENABLED = False

ACCOUNTS = {
    "CleanAirPicc": ("Piccadilly", "defra", "MAN3"),
}

THRESHOLDS = {
    "NO₂": 40,
    "PM2.5": 25,
    "PM10": 40,
    "Ozone": 120,
    "SO₂": 125,
}


def get_breaches_yesterday(provider, *provider_args):
    if provider == "defra":
        yesterdays_readings = get_defra_readings_yesterday(*provider_args)
    else:
        raise NotImplementedError(f"unrecognised provider: {provider}")
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
        for field, threshold in THRESHOLDS.items()
    }


def get_breach_messages(breaches):
    for field, data in breaches.items():
        if data["average_breached"]:
            yield f"{field} levels breached air quality standards all day."
        elif data["hours_breached"] > 0:
            yield f"{field} levels breached air quality standards for {data['hours_breached']} hour{'s' if data['hours_breached'] != 1 else ''}."


def send_tweets(twitter_auth, area_name, parts):
    twitter = tweepy.API(twitter_auth)
    this_tweet = ""
    tweets = []
    while parts:
        part = parts.pop(0)
        if len(this_tweet) + len(part) + 1 > 280:
            tweets.append(this_tweet)
            this_tweet = f"Yesterday in {area_name}, {part}"
        else:
            if this_tweet:
                this_tweet = f"{this_tweet} {part}"
            else:
                this_tweet = f"Yesterday in {area_name}, {part}"
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
        list(get_breach_messages(get_breaches_yesterday(*provider))),
    )
