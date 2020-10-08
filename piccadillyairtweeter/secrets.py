import os
import pickle

import tweepy


def capture_secrets():
    consumer_key = input("Twitter Consumer Key: ")
    consumer_secret = input("Twitter Consumer Secret: ")
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    redirect_url = auth.get_authorization_url()
    print(f"Go to {redirect_url}")
    verifier = input("Twitter Verifier: ")
    auth.get_access_token(verifier)
    with open("secrets.pickle", "w") as pickle_file:
        pickle.dumps(
            {
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "access_token": auth.access_token,
                "access_token_secret": auth.access_token_secret,
            },
            pickle_file,
        )


def fetch_secrets():
    if not os.path.exists("secrets.pickle"):
        capture_secrets()
    with open("secrets.pickle") as pickle_file:
        return pickle.load(pickle_file)
