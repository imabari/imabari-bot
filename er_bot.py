import os
import tweepy

consumer_key = os.environ["IMABARI_CK"]
consumer_secret = os.environ["IMABARI_CS"]
access_token = os.environ["IMABARI_AT"]
access_token_secret = os.environ["IMABARI_AS"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

for status in api.user_timeline("imabari119_bot", count=3)[::-1]:
    if not status.retweeted:
        api.retweet(status.id)
