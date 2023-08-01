#!/usr/bin/env python
import logging
from os.path import dirname, abspath
import http.client
from confluent_kafka import Producer
from time import gmtime
from flask import Flask, request

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s| %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
formatter.converter = gmtime

if len(logger.handlers) == 0:
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

def _full_path_of(path):
    base_dir = dirname(dirname(dirname(abspath(__file__))))
    return f'{base_dir}{path}'

def delivery_callback(error, msg):
    if error is not None:
        logger.error(f'Failed to deliver message: {error}')
    else:
        logger.info(f'Produced record to topic {msg.topic()} partition [{msg.partition()}] @ offset {msg.offset()}')

def get_weather_data(latitude, longitude):
    conn = http.client.HTTPSConnection("weatherapi-com.p.rapidapi.com")

    headers = {
        'X-RapidAPI-Key': "044502cb26msh017138364e50774p1f4c2fjsna420df4f77d9",
        'X-RapidAPI-Host': "weatherapi-com.p.rapidapi.com"
    }

    query = f"/current.json?q={latitude},{longitude}"
    conn.request("GET", query, headers=headers)

    res = conn.getresponse()
    data = res.read()

    return data.decode("utf-8")

def weather_producer(latitude, longitude):
    topic = 'axual-local-example-weathertopic'

    configuration = {
        'bootstrap.servers': 'platform.local:31757',
        'security.protocol': 'SSL',
        'ssl.endpoint.identification.algorithm': 'none',
        'ssl.certificate.location': _full_path_of('/etc/ssl/private/client.pem'),
        'ssl.key.location': _full_path_of('/etc/ssl/private/clientkey.pem'),
        'ssl.ca.location': _full_path_of('/etc/ssl/private/client.pem'),
        'acks': 'all',
        'logger': logger
    }

    producer = Producer(configuration)

    try:
        logger.info(f'Starting kafka producer to produce to topic: {topic}. ^C to exit.')

        for n in range(10):
            record_key = f'key_{n}'
            record_value = get_weather_data(latitude, longitude)

            producer.poll(0)
            producer.produce(topic, key=record_key, value=record_value, on_delivery=delivery_callback)

        logger.info('Done producing.')
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt, stopping.')
    finally:
        logger.info('Flushing producer.')
        producer.flush()


app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        latitude = request.form["latitude"]
        longitude = request.form["longitude"]
        weather_producer(latitude, longitude)
        return "Weather data produced successfully!"
    return '''
    <form method="POST">
        <label for="latitude">Latitude:</label>
        <input type="text" id="latitude" name="latitude" required><br><br>
        <label for="longitude">Longitude:</label>
        <input type="text" id="longitude" name="longitude" required><br><br>
        <input type="submit" value="Submit">
    </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0")
