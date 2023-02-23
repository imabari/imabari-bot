import datetime
import os
import pathlib

import pdfbox
import requests
import tweepy

def get_file(url):

    r = requests.get(url)

    p = pathlib.Path(pathlib.PurePath(url).name)

    with p.open(mode="wb") as fw:
        fw.write(r.content)

    return p

url = "https://www.police.pref.ehime.jp/kotsusidou/map/5.pdf"

pdf_file = get_file(url)

p = pdfbox.PDFBox()

p.pdf_to_images(pdf_file, imageType="png", dpi=200)

consumer_key = os.environ["IMABARI_CK"]
consumer_secret = os.environ["IMABARI_CS"]
access_token = os.environ["IMABARI_AT"]
access_token_secret = os.environ["IMABARI_AS"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)

JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
dt_now = datetime.datetime.now(JST)

twit = f"{dt_now.year}年{dt_now.month}月中の公開交通取締り（今治署） #imabari\n{url}"

media_id = api.media_upload("51.png").media_id
api.update_status(status=twit, media_ids=[media_id])
