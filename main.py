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

# CERTS = os.getenv("CERTS", None)
# if CERTS is None:
#     print("нет сертов")
#     exit(0)

AuthToken = base64.b64encode(f"{ID}:{TOKEN}".encode()).decode()
AuthHeader = "Bearer " + AuthToken

con = sqlite3.connect('payments.db')
cur = con.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nickname TEXT NOT NULL,
        date TEXT NOT NULL
    )
''')
con.commit()
cur.close()
con.close()

@app.get("/")
def main_page():
    req = requests.post("https://spworlds.ru/api/public/payments",
                        json={"items": [{"name": "donut", "count": 1, "price": 10}],
                              "redirectUrl": f"https://{URL}/get",
                              "webhookUrl": f"https://{URL}/stats",
                              "data": "kto zaplatil do tebya?))"},
                        headers={"Authorization": AuthHeader})
    PAY_URL = req.json()["url"]
    return flask.render_template("main.html", pay_url=PAY_URL)


@app.post("/stats")
def stats():
    auth = flask.request.headers.get("X-Body-Hash", None)
    if auth is None:
        return flask.abort(403)

    mac = hmac.new(TOKEN.encode(), flask.request.data, hashlib.sha256)
    calculated_hash = base64.b64encode(mac.digest()).decode()
    if calculated_hash != auth:
        return flask.abort(403)
    payer = flask.request.json.get("payer", None)
    if payer is None:
        return "error", 400
    con = sqlite3.connect("payments.db")
    cur = con.cursor()
    cur.execute("INSERT INTO payments(nickname, date) VALUES (?, ?)", (payer,
                                                                       datetime.datetime.now().strftime(
                                                                           "%Y-%m-%d %H:%M:%S")))
    con.commit()
    cur.close()
    con.close()
    return "OK", 200


@app.get("/get")
def get():
    ref = flask.request.headers.get('Referer', None)
    if ref is None or not ref == "https://spworlds.ru/":
        return flask.abort(403)
    con = sqlite3.connect("payments.db")
    cur = con.cursor()
    query = cur.execute("SELECT nickname, date FROM PAYMENTS ORDER BY date ASC").fetchall()
    cur.close()
    con.close()
    return flask.render_template("gois.html", pays=query)


if __name__ == "__main__":
    app.run("0.0.0.0", PORT)
