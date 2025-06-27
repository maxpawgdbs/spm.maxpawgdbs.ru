import flask
import os
import sqlite3
import dotenv
import base64
import requests
import hashlib
import hmac
import datetime

app = flask.Flask(__name__, template_folder=os.getcwd() + "/templates", static_folder=os.getcwd() + "/static")

dotenv.load_dotenv(".env")

TOKEN = os.getenv("TOKEN", None)
ID = os.getenv("ID", None)
if TOKEN is None or ID is None:
    print("нет данных получателя")
    exit(0)

URL = os.getenv("URL", None)
PORT = os.getenv("PORT", None)
if URL is None or PORT is None:
    print("нет адреса")
    exit(0)

AuthToken = base64.b64encode(f"{ID}:{TOKEN}".encode()).decode()
AuthHeader = "Bearer " + AuthToken

conn = sqlite3.connect('payments.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        date TEXT NOT NULL
    )
''')
cursor.close()


req = requests.post("https://spworlds.ru/api/public/payments",
                        json={"items": [{"name": "skam", "count": 1, "price": 1}],
                              "redirectUrl": f"{URL}:{PORT}/get",
                              "webhookUrl": "https://webhook.site/3a57aba7-5087-4f0b-96b5-daaca1843476",
                              # f"{URL}:{PORT}/stats",
                              "data": "Artyom privet"},
                        headers={"Authorization": AuthHeader})
print(req.json())
PAY_URL = req.json()["url"]
print(PAY_URL)

@app.get("/")
def main_page():
    return flask.render_template("main.html", pay_url=PAY_URL)


# @app.get("/pay")
# def skam():
#     req = requests.post("https://spworlds.ru/api/public/payments",
#                         json={"items": [{"name": "skam", "count": 1, "price": 1}],
#                               "redirectUrl": f"{URL}:{PORT}/get",
#                               "webhookUrl": "https://webhook.site/3a57aba7-5087-4f0b-96b5-daaca1843476",
#                               # f"{URL}:{PORT}/stats",
#                               "data": "Artyom privet"},
#                         headers={"Authorization": AuthHeader})
#     print(req.json())
#     return flask.redirect(req.json()["url"])


@app.post("/stats")
def stats():
    auth = flask.request.headers.get("X-Body-Hash", None)
    if auth is None:
        return flask.abort(403)

    mac = hmac.new(TOKEN.encode(), flask.request.data, hashlib.sha256)
    calculated_hash = base64.b64encode(mac.digest()).decode()
    if calculated_hash != auth:
        return flask.abort(403)

    con = sqlite3.connect("payments.db")
    cur = con.cursor()
    cur.execute("INSERT INTO payments(nickname, date) VALUES ?, ?", (flask.request.json(),
                                                                     datetime.datetime.now().strftime(
                                                                         "%Y-%m-%d %H:%M:%S")))
    cur.close()
    return "OK", 200


@app.get("/get")
def get():
    return "hello world all ok"
    # ref = flask.request.headers.get('Referer')
    # if not ref.startswith("https://spworlds.ru/spm/pay"):
    #     return flask.abort(403)
    # con = sqlite3.connect("payments.db")
    # cur = con.cursor()
    # query = cur.execute("SELECT * FROM PAYMENTS ORDER BY date")
    # #дописать

if __name__ == "__main__":
    app.run("0.0.0.0", 80)
