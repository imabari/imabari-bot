import os

import pandas as pd
import requests
import tweepy
from bs4 import BeautifulSoup

# スクレイピング

url = "https://www.bs.jrc.or.jp/csk/ehime/place/m1_03_index.html?selectarea=%E4%BB%8A%E6%B2%BB%E5%B8%82&selectday=-"

r = requests.get(url)
r.raise_for_status()

soup = BeautifulSoup(r.content, "html.parser")

dfs = []

for i in soup.select("div.mod-table-scrollWrap"):

    df_tmp = pd.read_html(i.find("table").prettify())[0]
    df_tmp["日付"] = i.find_previous_sibling("p").get_text(strip=True)

    dfs.append(df_tmp)

df0 = pd.concat(dfs).reset_index(drop=True)

df0["記念品"] = df0["献血会場"].str.contains("※ご協力団体様から記念品進呈いたします")

# 不要文字削除
df0["献血会場"] = (
    df0["献血会場"]
    .str.replace("(\[MAP\]|⌚Web予約可|（前日17時まで）|※ご協力団体様から記念品進呈いたします)", "", regex=True)
    .str.split()
)

df0["住所"] = df0["献血会場"].str[-1]
df0["献血会場"] = df0["献血会場"].str[:-1].str.join(" ")

df0[["場所", "受付"]] = df0["献血会場"].str.split("受付場所：", expand=True)

df0["場所"] = df0["場所"].str.strip()
df0["受付"] = df0["受付"].str.strip()

df0["受付時間"] = df0["受付時間"].str.replace("（昼中断なし）", "").str.normalize("NFKC").str.split()
df0["時間"] = df0["受付時間"].str.join("/")

# 日付
dt_now = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None).date()

nextweek = dt_now + pd.Timedelta(days=7)
week_num = nextweek.isocalendar()[1]

df0["year"] = dt_now.year
df0[["month", "day"]] = df0["日付"].str.extract("(\d{1,2})月 ?(\d{1,2})日").astype(int)

df0["date"] = pd.to_datetime(df0[["year", "month", "day"]])
df0["week"] = df0["date"].dt.isocalendar().week

df1 = df0[df0["week"] == week_num].copy()

bearer_token = os.environ["IMABARI_BT"]
consumer_key = os.environ["IMABARI_CK"]
consumer_secret = os.environ["IMABARI_CS"]
access_token = os.environ["IMABARI_AT"]
access_token_secret = os.environ["IMABARI_AS"]

client = tweepy.Client(bearer_token, consumer_key, consumer_secret, access_token, access_token_secret)

for _, row in df1.iterrows():

    twit = f'献血バスの運行予定（今治市）\n\n【日時】\n{row["日付"]} {row["時間"]}\n\n【献血会場】\n{row["場所"]}（{row["住所"]}）'

    if row["受付"]:
        twit += f'\n\n【受付場所】\n{row["受付"]}'

    if row["記念品"]:
        twit += f"\n\n※ご協力団体様から記念品進呈"

    twit += f'\n\n{url}\n\n#献血 #愛媛県 #{row["市区町村"]} '

    client.create_tweet(text=twit)
