import os
import pathlib

import pandas as pd
import pdfbox
import pdfplumber
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

pdf = pdfplumber.open(p)
page = pdf.pages[0]

crop = page.within_bbox((0, 920, page.width, 1220))

table = crop.extract_table()

df0 = pd.DataFrame(table[1:], columns=table[0])

# 列名
df0.columns = df0.columns.str.replace("\s", "", regex=True)

df0.set_index("", inplace=True)

df0

# 現在
dt_now = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None)
dt_now

df0["日"] = df0["日"].str.rstrip("日").astype(int)
df0["曜日"] = df0["曜日"].str.strip().str.normalize("NFKC")
df0["時間"] = df0["時間"].str.strip().str.normalize("NFKC")

df0["date"] = df0["日"].apply(lambda x: dt_now.replace(day=x)).dt.date

df0[["start", "end"]] = df0["時間"].str.split("-", expand=True)

df0["start"] = pd.to_datetime(df0["date"]) + pd.to_timedelta(df0["start"] + ":00")
df0["end"] = pd.to_datetime(df0["date"]) + pd.to_timedelta(df0["end"] + ":00")

df0

df1 = df0[(df0["日"] > dt_now.day) & (df0["日"] < dt_now.day + 6)]

if len(df1) > 0:

    twit = f"{dt_now.month}月中の公開交通取締り（今治署） #imabari\n{url}\n"

    for _, row in df1.iterrows():
        twit += f'\n【{row["種別"]}】\n日付：{row["date"]}（{row["曜日"]}）\n時間：{row["時間"]}\n場所：{row["取締場所"]}（{row["路線名"]}）'

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

    media_id = api.media_upload("51.png").media_id
    api.update_status(status=twit, media_ids=[media_id])
