#!/usr/bin/env python
import os
import json
import redis
from flask import Flask, request
from weather import get_weather_data

app = Flask(__name__)
redis_conn = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

@app.route("/")
def index():
    return "Usage: http://<hostname>[:<prt>]/api/<url>"

@app.route("/api/")
def api():
    latitude = request.args.get("latitude")
    longitude = request.args.get("longitude")

    weather_data = get_weather_data(latitude, longitude)
    
    jsonlinks = redis_conn.get(latitude + "," + longitude)

    if jsonlinks is None:
        jsonlinks = json.dumps(weather_data)
        redis_conn.set(latitude + "," + longitude, jsonlinks)

    response = app.response_class(
        status=200,
        mimetype="application/json",
        response=jsonlinks
    )

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0")