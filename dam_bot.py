# -*- coding: utf-8 -*-

import os

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import tweepy

url = "http://183.176.244.72/kawabou-mng/customizeMyMenuKeika.do?GID=05-5101&userId=U1001&myMenuId=U1001_MMENU003&PG=1&KTM=1"

# 現在
dt_now = pd.Timestamp.now(tz="Asia/Tokyo").tz_localize(None)
dt_now

df = (
    pd.read_html(url, na_values=["-", "閉局", "欠測"])[1]
    .rename(
        columns={
            0: "日時",
            1: "貯水位",
            2: "流入量",
            3: "放流量",
            4: "貯水量",
            5: "貯水率",
        }
    )
    .dropna(how="all", axis=1)
)

# 日時

df_date = df["日時"].str.extract("(\d{2}/\d{2})? *(\d{2}:\d{2})").fillna(method="ffill")

df_date["year"] = dt_now.year

df_date[["month", "day"]] = (
    df_date[0].str.strip().str.split("/", expand=True).astype(int)
)

df_date[["hour", "minute"]] = (
    df_date[1].str.strip().str.split(":", expand=True).astype(int)
)

df_date["datetime"] = pd.to_datetime(
    df_date[["year", "month", "day", "hour", "minute"]]
)

df_date["year"].mask(dt_now < df_date["datetime"], df_date["year"] - 1, inplace=True)

df["日時"] = pd.to_datetime(df_date[["year", "month", "day", "hour", "minute"]])

# 貯水率

fig_wsr = px.line(
    df, x="日時", y="貯水率", range_y=[50, 80], width=800, height=800, title="玉川ダムの貯水率"
)
fig_wsr.add_hline(y=60, line_color="orange", line_dash="dash")
# fig_wsr.add_hline(y=50, line_color="red", line_dash="dash")
# fig_wsr.show()

fig_wsr.write_image("dam.png")

# 流入・放流

fig_wio = px.line(
    df,
    x="日時",
    y=["流入量", "放流量"],
    range_y=[0, 10],
    width=800,
    height=800,
    title="玉川ダムの流入量と放流量",
)
# fig_wio.show()

# 表

fig_wio.write_image("dio.png")

fig_tbl = ff.create_table(df)
# fig_tbl

fig_tbl.write_image("table.png")

# Twitter

# 貯水率が欠損の行を削除
df.dropna(subset=["貯水率"], inplace=True)

df.set_index("日時", inplace=True)

if len(df) > 0:

    se = df.iloc[-1]
    tw = {}
    tw["rate"] = se["貯水率"]
    tw["time"] = se.name.strftime("%H:%M")

    twit = f'ただいまの玉川ダムの貯水率は{tw["rate"]}%です（{tw["time"]}）\n#今治 #玉川ダム #貯水率'

    print(twit)


consumer_key = os.environ["IMABARI_CK"]
consumer_secret = os.environ["IMABARI_CS"]
access_token = os.environ["IMABARI_AT"]
access_token_secret = os.environ["IMABARI_AS"]

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# 複数メディア投稿
filenames = ["table.png", "dam.png", "dio.png"]
media_ids = []
for filename in filenames:
    res = api.media_upload(filename)
    media_ids.append(res.media_id)

# tweet with multiple images
api.update_status(status=twit, media_ids=media_ids)
