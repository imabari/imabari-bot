import os
import datetime

import requests
import tweepy

CK = os.environ["CONSUMER_KEY"]
CS = os.environ["CONSUMER_SECRET"]
AT = os.environ["ACCESS_TOKEN"]
AS = os.environ["ACCESS_TOKEN_SECRET"]

r = requests.get("https://raw.githubusercontent.com/stop-covid19-hyogo/covid19-scraping/gh-pages/main_summary.json")
data = r.json()

# 入院者数
inpatient = data["children"][0]["children"][0]["value"]
# 更新日時
last_update = datetime.datetime.fromisoformat(data["last_update"]).strftime("%Y-%m-%d")

auth = tweepy.OAuthHandler(CK, CS)
auth.set_access_token(AT, AS)

twit = f"【データ更新】兵庫県が{last_update}に公表した、最新感染動向データを、兵庫県 新型コロナウイルスまとめサイトに反映しました。\n\n現在の入院者数は{inpatient}人です。\n\nhttps://stop-covid19-hyogo.org\n#StopCovid19Hyogo #StopCovid19JP #兵庫コロナ情報"

api.update_status(twit)
