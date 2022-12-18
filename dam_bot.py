import datetime
import os
import re

import pandas as pd
import requests
import tweepy

dam = {
    "name": "玉川ダム",
    "twt_id": "BotTamagawaDam",
    "dam_id": "U1001_MMENU003",
    "CK": os.environ["IMABARI_CK"],
    "CS": os.environ["IMABARI_CS"],
    "AT": os.environ["IMABARI_AT"],
    "AS": os.environ["IMABARI_AS"],
}

def date_parse(se, year):

    df = se.str.extract("(\d{2}/\d{2})? *(\d{2}:\d{2})").fillna(method="ffill")

    df_date = (
        df[0]
        .str.split("/", expand=True)
        .rename(columns={0: "month", 1: "day"})
        .astype(int)
    )

    df_date["year"] = year

    df_time = (
        df[1]
        .str.split(":", expand=True)
        .rename(columns={0: "hour", 1: "minute"})
        .astype(int)
    )

    return pd.to_datetime(df_date.join(df_time))


def fetch_dam(dam, dt_now):

    # Twitterオブジェクトの生成
    auth = tweepy.OAuthHandler(dam["CK"], dam["CS"])
    auth.set_access_token(dam["AT"], dam["AS"])

    api = tweepy.API(auth)

    url = f'http://183.176.244.72/kawabou-mng/customizeMyMenuKeika.do?GID=05-5101&userId=U1001&myMenuId={dam["dam_id"]}&PG=1&KTM=3'

    df = (
        pd.read_html(url, na_values=["-", "閉局"])[1]
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

    df["日時"] = date_parse(df["日時"], dt_now.year)

    # 貯水率が欠損の行を削除
    df.dropna(subset=["貯水率"], inplace=True)
    
    df.set_index("日時", inplace=True)

    if len(df) > 0:

        if dt_now in df.index:
            se = df.loc[dt_now]
        else:
            se = df.iloc[-1]
            
        tw = {}
        tw["rate"] = se["貯水率"]
        tw["time"] = se.name.strftime("%H:%M")

        twit = f'ただいまの{dam["name"]}の貯水率は{tw["rate"]}%です（{tw["time"]}）\n#今治 #{dam["name"]} #貯水率\n\nhttps://www.city.imabari.ehime.jp/suidou/suigen/dam.html'

        print(twit)
        api.update_status(twit)


if __name__ == "__main__":

    JST = datetime.timezone(datetime.timedelta(hours=+9))
    dt_now = (datetime.datetime.now(JST) - datetime.timedelta(minutes=8)).replace(
        minute=0, second=0, microsecond=0, tzinfo=None
    )

    fetch_dam(dam, dt_now)
