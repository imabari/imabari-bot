import datetime
import os

import pandas as pd
import plotly.express as px
import requests
import tweepy


def fetch_json(url):
    r = requests.get(url)
    r.raise_for_status()

    return r.json()


def fetch_now():
    url = "https://www.river.go.jp/kawabou/file/system/rwCrntTime.json"

    d = fetch_json(url)
    s = d.get("crntRwTime")

    dt_now = pd.to_datetime(s)

    return dt_now.round(freq="10min")


def fetch_dam(dt_now):
    # 今治市
    url = f"https://www.river.go.jp/kawabou/file/files/tmlist/dam/{dt_now.year:04}{dt_now.month:02}{dt_now.day:02}/{dt_now.hour:02}{dt_now.minute:02}/0972900700006.json"

    # print(url)

    d = fetch_json(url)

    col = {
        "obsTime": "日時",
        "storLvl": "貯水位",
        "storCap": "貯水量",
        "storFcntIrr": "貯水率治水容量",
        "storPcntIrr": "貯水率利水容量",
        "allSink": "全流入量",
        "allDisch": "全放流量",
        "storPcntEff": "貯水率有効容量",
    }

    df = pd.json_normalize(d, record_path="min10Values").rename(columns=col).reindex(columns=col.values())
    df["日時"] = pd.to_datetime(df["日時"])
    df.sort_values("日時", inplace=True)
    df.set_index("日時", inplace=True)

    df.dropna(
        subset=[
            "貯水位",
            "貯水量",
            "貯水率利水容量",
            "全流入量",
            "全放流量",
        ],
        how="all",
        inplace=True,
    )

    # 貯水率
    fig_rate = px.line(df, x=df.index, y="貯水率利水容量", range_y=[40, 105], width=800, height=800)
    fig_rate.add_hline(y=65, line_color="orange", line_dash="dash")
    fig_rate.add_hline(y=50, line_color="red", line_dash="dash")
    fig_rate.update_yaxes(title="貯水率(%)")
    fig_rate.show()

    fig_rate.write_image("rate.png", width=800, height=600)

    # 貯水量
    fig_vol = px.line(df, x=df.index, y="貯水量", range_y=[5000, 7500], width=800, height=800)
    fig_vol.show()

    fig_vol.write_image("volume.png", width=800, height=600)

    # 流入量・放流量
    fig_inout = px.line(df, x=df.index, y=["全流入量", "全放流量"], range_y=[0, 20], width=800, height=800)
    fig_inout.update_yaxes(title=None)
    fig_inout.show()

    fig_inout.write_image("in-out.png", width=800, height=600)

    # 最新
    last_row = df.iloc[-1]

    message = f'貯水率：{last_row["貯水率利水容量"]} %\n貯水量：{last_row["貯水量"]} m3\n\n流入量：{last_row["全流入量"]:.2f} m3/s\n放流量：{last_row["全放流量"]:.2f} m3/s\n\nhttps://www.river.go.jp/kawabou/pcfull/tm?itmkndCd=7&ofcCd=9729&obsCd=6&isCurrent=true&fld=0'

    print(message)

    return message


def fetch_katayama(dt_now):
    # 片山
    url = f"https://www.river.go.jp/kawabou/file/files/tmlist/stg/{dt_now.year:04}{dt_now.month:02}{dt_now.day:02}/{dt_now.hour:02}{dt_now.minute:02}/0972900400025.json"

    d = fetch_json(url)

    col = {
        "obsTime": "日時",
        "stg": "水位",
    }

    df = pd.json_normalize(d, record_path="min10Values").rename(columns=col).reindex(columns=col.values())
    df["日時"] = pd.to_datetime(df["日時"])
    df.sort_values("日時", inplace=True)
    df.set_index("日時", inplace=True)

    df.dropna(subset="水位", inplace=True)

    fig = px.line(df, x=df.index, y="水位", width=800, height=600)

    # 氾濫注意水位
    fig.add_hline(y=2.4, line_color="orange", line_dash="dash")

    # 避難判断水位
    fig.add_hline(y=2.6, line_color="red", line_dash="dash")

    # 氾濫危険水位
    fig.add_hline(y=2.85, line_color="purple", line_dash="dash")
    fig.show()

    fig.write_image("river.png", width=800, height=600)


def fetch_river():
    info = fetch_json("https://www.river.go.jp/kawabou/file/files/obslist/twninfo/obs/stg/3801.json")

    df_info = pd.json_normalize(info["prefTwn"], record_path="stg", meta="twnCd")
    df_info = df_info.loc[df_info["twnCd"] == 3801202, ["obsFcd", "obsNm", "warnStg", "spclWarnStg", "dngStg"]]

    data = fetch_json("https://www.river.go.jp/kawabou/file/files/obslist/twninfo/tm/stg/3801.json")
    df_data = pd.json_normalize(data["prefTwn"], record_path="stg")[["obsFcd", "obsTime", "stg"]]
    df_data["obsTime"] = pd.to_datetime(df_data["obsTime"], errors="coerce")

    df = pd.merge(df_info, df_data, on="obsFcd", how="left")
    df.set_index("obsFcd", inplace=True)

    # alert列の作成
    def set_alert(row):
        if row["stg"] >= row["dngStg"]:
            return "氾濫危険"
        elif row["stg"] >= row["spclWarnStg"]:
            return "避難判断"
        elif row["stg"] >= row["warnStg"]:
            return "氾濫注意"
        else:
            return ""

    df["alert"] = df.apply(set_alert, axis=1)

    def make_message(row):
        result = f'{row["obsNm"]}：{row["stg"]} m {row["alert"]}'
        return result.strip()

    lst = [
        make_message(df.loc[m, ["obsNm", "stg", "alert"]]) for m in ["0972900400021", "0972900400024", "0972900400025"]
    ]

    message = "\n".join(lst)
    print(message)

    return message


dt_now = fetch_now()

dam_message = fetch_dam(dt_now)

river_message = fetch_river()

fetch_katayama(dt_now)

message = (
    f"{dt_now:%Y-%m-%d %H:%M} 現在"
    + "\n\n"
    + "玉川ダム\n"
    + dam_message
    + "\n\n"
    + "蒼社川\n"
    + river_message
    + "\n\n"
    + "https://www.river.go.jp/kawabou/pc/tm?zm=15&clat=34.0488528&clon=132.9878167&fld=0&mapType=0&viewGrpStg=0&viewRd=1&viewRW=1&viewRiver=1&viewPoint=1&ext=1&ofcCd=9729&itmkndCd=4&obsCd=25"
    "\n\n" + "#今治市 #玉川ダム #蒼社川"
)

print(message)

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

# 画像リスト
filenames = ["rate.png", "volume.png", "in-out.png", "river.png"]

# 画像をアップロードしてmedia_idを取得
media_ids = []
for filename in filenames:
    res = api.media_upload(filename)
    media_ids.append(res.media_id)

client.create_tweet(text=message, media_ids=media_ids)
