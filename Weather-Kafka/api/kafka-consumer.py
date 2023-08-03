#!/usr/bin/env python
import logging
from os.path import dirname, abspath
from time import gmtime

from confluent_kafka import Consumer, KafkaError
import redis

logger = logging.getLogger('')  # Root logger, to catch all submodule logs
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s.%(msecs)03d|%(levelname)s|%(filename)s| %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
formatter.converter = gmtime  # Log UTC time

if len(logger.handlers) == 0:
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)


def _full_path_of(path):
    base_dir = dirname(dirname(dirname(abspath(__file__))))
    return f'{base_dir}{path}'


def on_assign(consumer_obj, partitions):
    logger.info(f'Consumer assignment: {len(partitions)} partitions:')
    for p in partitions:
        logger.info(f'{p.topic} [{p.partition}] @ {p.offset}')
    consumer_obj.assign(partitions)


if __name__ == '__main__':
    # Resolved topic name
    topic = 'axual-local-example-weathertopic'

    # Kafka consumer configuration
    configuration = {
        'bootstrap.servers': 'platform.local:31757',
        'security.protocol': 'SSL',
        'ssl.endpoint.identification.algorithm': 'none',
        'ssl.ca.location': _full_path_of('/etc/secret-volume/client.pem'),
        'ssl.certificate.location': _full_path_of('/etc/secret-volume/client.pem'),
        'ssl.key.location': _full_path_of('/etc/secret-volume/clientkey.pem'),
        'group.id': 'axual-local-example-weatherconsumer',
        'auto.offset.reset': 'earliest',
        'logger': logger
    }

    consumer = Consumer(configuration)

    # Redis configuration
    redis_host = 'redis'
    redis_port = 6379
    redis_db = 0

    redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db)

    logger.info(f'Starting Kafka consumer for topic: {topic}. ^C to exit.')
    try:
        consumer.subscribe([topic])
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.warning(f'End of partition reached: {msg.topic()} [{msg.partition()}]')
                else:
                    logger.error(f'Error occurred: {msg.error().str()}')
                continue

            logger.info(f'Received message: {msg.value().decode("utf-8")}')
            
            # Store the message in Redis
            redis_client.rpush('messages', msg.value().decode("utf-8"))
            
            # Commit the message offset
            consumer.commit(asynchronous=False)
    except KeyboardInterrupt:
        logger.info('Caught KeyboardInterrupt, stopping.')
    finally:
        logger.info('Committing final offsets and closing consumer.')
        consumer.commit(asynchronous=False)
        consumer.close()
