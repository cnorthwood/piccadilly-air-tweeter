import os
import pickle

import tweepy


def get_twitter_oauth_handler():
    if not os.path.exists("secrets.pickle"):
        api_key = input("Twitter API Key: ")
        secret_key = input("Twitter API Key Secret: ")
        with open("secrets.pickle", "wb") as pickle_file:
            pickle.dump(
                {"api_key": api_key, "api_key_secret": secret_key, "accounts": {}},
                pickle_file,
            )
    with open("secrets.pickle", "rb") as pickle_file:
        secrets = pickle.load(pickle_file)
        return (
            tweepy.OAuth1UserHandler(secrets["api_key"], secrets["api_key_secret"], callback="oob"),
            secrets["accounts"],
        )


def log_in_to_twitter(account_name):
    auth, account_secrets = get_twitter_oauth_handler()
    if account_name not in account_secrets:
        redirect_url = auth.get_authorization_url()
        print(f"Go to {redirect_url} as {account_name}")
        verifier = input("Twitter Verifier PIN: ")
        access_token, access_token_secret = auth.get_access_token(verifier)
        account_secrets[account_name] = {
            "access_token": access_token,
            "access_token_secret": access_token_secret,
        }
        with open("secrets.pickle", "wb") as pickle_file:
            pickle.dump(
                {
                    "consumer_key": auth.consumer_key,
                    "consumer_secret": auth.consumer_secret,
                    "accounts": account_secrets,
                },
                pickle_file,
            )
    auth.set_access_token(
        account_secrets[account_name]["access_token"],
        account_secrets[account_name]["access_token_secret"],
    )
    return auth
