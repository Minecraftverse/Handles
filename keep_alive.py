"""
Tiny web server whose only job is to give an external uptime-pinger
(e.g. UptimeRobot) something to hit every few minutes, so free hosts
like Replit don't put the bot to sleep from inactivity.
"""

import os
from flask import Flask
from threading import Thread

app = Flask("")


@app.route("/")
def home():
    return "Handles is online. Diagnostics nominal, Sir."


def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
