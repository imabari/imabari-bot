import datetime
import os
import pathlib

import pdfbox
import requests
import tweepy


def fetch_file(url, dir="."):

    p = pathlib.Path(dir, pathlib.PurePath(url).name)
    p.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(url)
    r.raise_for_status()

    with p.open(mode="wb") as fw:
        fw.write(r.content)
    return p

url = "https://www.police.pref.ehime.jp/kotsusidou/map/5.pdf"

p = fetch_file(url)

pdfbox.PDFBox().pdf_to_images(p, imageType="png", dpi=200)

JST = datetime.timezone(datetime.timedelta(hours=+9))
dt_now = datetime.datetime.now(JST).replace(tzinfo=None)

twit = f"{dt_now.month + 1}月中の公開交通取締り（今治署） #imabari\n{url}\n"

consumer_key = os.environ["IMABARI_CK"]
consumer_secret = os.environ["IMABARI_CS"]
access_token = os.environ["IMABARI_AT"]
access_token_secret = os.environ["IMABARI_AS"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

client = tweepy.Client(
    consumer_key=consumer_key,
    consumer_secret=consumer_secret,
    access_token=access_token,
    access_token_secret=access_token_secret,
)

media = api.media_upload("51.png").media_id
client.create_tweet(text=twit, media_ids=[media.media_id])
