import datetime
import re
import time
import os

import pandas as pd
import requests
import tweepy

import matplotlib.pyplot as plt

consumer_key = os.environ["CONSUMER_KEY"]
consumer_secret = os.environ["CONSUMER_SECRET"]
access_token = os.environ["ACCESS_TOKEN"]
access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

# 現在の時刻から-8分し、10分単位に調整
JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")

dt_now = datetime.datetime.now(JST) - datetime.timedelta(minutes=8)
dt_now -= datetime.timedelta(minutes=(dt_now.minute % 10))

dt_str = dt_now.strftime("%Y%m%d%H%M")


def my_parser(x):

    year = dt_now.year
    month, day = map(int, re.findall("[0-9]{1,2}", x["日付"]))
    h, m = map(int, re.findall("[0-9]{1,2}", x["時間"]))

    return pd.Timestamp(year, month, day) + pd.Timedelta(hours=h, minutes=m)


def get_river():

    url = f"http://183.176.244.72/cgi/050_HQ_030_01.cgi?GID=050_HQ_030&UI=U777&SI=00000&LO=88&SRO=1&KKB=101100&DSP=11110&SKZ=111&NDT=1&MNU=1&BTY=IE6X&SSC=0&RBC=100&DT={dt_str}&GRP=USR020&TPG=1&PG=1&KTM=3"

    # print(url)

    dfs = pd.read_html(url, na_values=["欠測", "−", "閉局"])

    # 観測所名
    name = dfs[0].iloc[0, :].dropna().tolist()

    dfs[3].columns = dfs[0].iloc[0]
    df_lv = dfs[3].reindex(columns=name).set_index("観測所名")

    df_lv.loc["通常"] = 0
    df_lv.loc["危険"] = 999

    katayama_lv = df_lv["片山"].dropna().sort_values()
    kouya_lv = df_lv["高野"].dropna().sort_values()

    # データ個数
    n = len(name)

    # データを結合
    df = pd.concat([pd.concat(i, axis=1) for i in zip(*[iter(dfs[5:])] * n)])

    # 列名を登録
    df.columns = ["日付", "時間"] + name[1:]

    # 日付を補完
    # df["日付"].fillna(method="ffill", inplace=True)

    # 欠損値を補完
    df.fillna(method="ffill", inplace=True)

    # 日時をindexにセット
    df.index = df.apply(my_parser, axis=1)

    df.drop(["日付", "時間"], axis=1, inplace=True)

    df.to_csv("souja.csv")

    df_souja = df.loc[:, ["中通", "高野", "片山"]].sort_index().copy()

    df_diff = df_souja.diff().fillna(0)
    df_diff.to_csv("souja_diff.csv")

    kouya_alert = pd.cut(
        df_souja["高野"], kouya_lv.values.tolist(), labels=kouya_lv.index.tolist()[:-1]
    )

    katayama_alert = pd.cut(
        df_souja["片山"],
        katayama_lv.values.tolist(),
        labels=katayama_lv.index.tolist()[:-1],
    )

    df_sign = df_diff.applymap(lambda x: "↗" if x > 0 else "↘" if x < 0 else "")
    # df_sign.to_csv("souja_sign.csv")

    # 片山
    katayama_str = f'片山：{df_souja.iloc[-1]["片山"]:.2f}m'

    if df_sign.iloc[-1]["片山"] != "":
        katayama_str += f' {df_sign.iloc[-1]["片山"]}'

    if katayama_alert.iloc[-1] != "通常":
        katayama_str += f" {katayama_alert.iloc[-1]}"

    ax1 = df_souja["片山"].plot(title="Katayama", grid=True)
    ax1.axhline(y=2.85, linestyle="--", color="r", linewidth=1, label="")
    ax1.axhline(y=2.6, linestyle="--", color="orange", linewidth=1, label="")
    ax1.axhline(y=2.4, linestyle="--", color="y", linewidth=1, label="")
    ax1.axhline(y=2.1, linestyle="--", color="b", linewidth=1, label="")
    plt.savefig("katayama.png", dpi=200)

    plt.show()
    plt.close()

    # 高野
    kouya_str = f'高野：{df_souja.iloc[-1]["高野"]:.2f}m'

    if df_sign.iloc[-1]["高野"] != "":
        kouya_str += f' {df_sign.iloc[-1]["片山"]}'

    if kouya_alert.iloc[-1] != "通常":
        kouya_str += f" {kouya_alert.iloc[-1]}"

    ax2 = df_souja["高野"].plot(title="Kouya", grid=True)
    ax2.axhline(y=4, linestyle="--", color="y", linewidth=1, label="")
    ax2.axhline(y=3.5, linestyle="--", color="b", linewidth=1, label="")
    plt.savefig("kouya.png", dpi=200)

    plt.show()
    plt.close()

    # 中通
    nakadori_str = f'中通：{df_souja.iloc[-1]["中通"]:.2f}m'

    if df_sign.iloc[-1]["中通"] != "":
        nakadori_str += f' {df_sign.iloc[-1]["片山"]}'

    result = "\n".join(["【蒼社川】", nakadori_str, kouya_str, katayama_str])

    flg = False

    if (kouya_alert.iloc[-1] != "通常") or (katayama_alert.iloc[-1] != "通常"):

        flg = True

    return result, flg


def get_dam():

    url = f"http://183.176.244.72/cgi/170_USER_010_01.cgi?GID=170_USER_010&UI=U777&SI=00000&MNU=1&LO=88&BTY=IE6X&NDT=1&SK=0000000&DT={dt_str}&GRP=USR004&TPG=1&PG=1&KTM=3"

    # print(url)

    dfs = pd.read_html(url, na_values=["欠測", "−", "閉局"])

    name = dfs[2].iloc[1, :].dropna().tolist()

    # データ個数
    n = len(name)

    df = pd.concat([pd.concat(i, axis=1) for i in zip(*[iter(dfs[4:])] * n)])

    # 列名を登録
    df.columns = ["日付", "時間"] + name[1:]

    # 日付を補完
    # df["日付"].fillna(method="ffill", inplace=True)

    # 欠損値を補完
    df.fillna(method="ffill", inplace=True)

    # 日時をindexにセット
    df.index = df.apply(my_parser, axis=1)

    # df.rename(columns={"貯水率(利水容量)": "貯水率"}, inplace=True)

    df.drop(["日付", "時間"], axis=1, inplace=True)

    df.to_csv("tamagawa.csv")

    ax = df["貯水位"].plot(title="Tamagawa", grid=True)
    ax.axhline(y=158, linestyle="--", color="red", linewidth=1, label="")
    ax.axhline(y=155.8, linestyle="--", color="blue", linewidth=1, label="")
    plt.savefig("tamagawa.png", dpi=200)
    plt.show()
    plt.close()

    df_diff = df.diff().fillna(0)

    df_sign = df_diff.applymap(lambda x: "↗" if x > 0 else "↘" if x < 0 else "")

    # 貯水位
    level_str = f'貯水位：{df.iloc[-1]["貯水位"]:.2f}'

    if df_sign.iloc[-1]["貯水位"] != "":
        level_str += f' {df_sign.iloc[-1]["貯水位"]}'

    if df.iloc[-1]["貯水位"] >= 158:
        level_str += " 防災操作開始水位"

    # 全流入量
    in_str = f'全流入量：{df.iloc[-1]["全流入量"]:.2f}'

    if df_sign.iloc[-1]["全流入量"] != "":
        in_str += f' {df_sign.iloc[-1]["全流入量"]}'

    # 全放流量
    out_str = f'全放流量：{df.iloc[-1]["全放流量"]:.2f}'

    if df_sign.iloc[-1]["全放流量"] != "":
        out_str += f' {df_sign.iloc[-1]["全放流量"]}'

    # 貯水量
    storage_str = f'貯水量：{df.iloc[-1]["貯水量"]:.1f}'

    if df_sign.iloc[-1]["貯水量"] != "":
        storage_str += f' {df_sign.iloc[-1]["貯水量"]}'

    result = "\n".join(["【玉川ダム】", level_str, in_str, out_str, storage_str])

    flg = False

    if df.iloc[-1]["全放流量"] > 20:

        flg = True

    return result, flg


if __name__ == "__main__":

    river_str, river_flg = get_river()

    time.sleep(3)

    dam_str, dam_flg = get_dam()

    twit = "\n\n".join(
        [
            river_str,
            dam_str,
            "http://i.river.go.jp/_-p01-_/p/xmn0501010/?mtm=10&swd=&prf=3801&twn=3801202",
        ]
    )

    print(twit)

    if river_flg or dam_flg:

        # 画像
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        url_image = "http://www.pref.ehime.jp/kasen/Jpeg/Cam006/00_big.jpg"
        r = requests.get(url_image, headers=headers)

        with open("souja.jpg", "wb") as fw:
            fw.write(r.content)

        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)

        # 複数メディア投稿
        filenames = ["souja.jpg", "katayama.png", "kouya.png", "tamagawa.png"]
        media_ids = []

        for filename in filenames:
            res = api.media_upload(filename)
            media_ids.append(res.media_id)

        # tweet with multiple images
        api.update_status(status=twit, media_ids=media_ids)
