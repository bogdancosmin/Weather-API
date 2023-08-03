FROM       python:3

ENV        REDIS_URL="redis://localhost:6379"

WORKDIR    /app
COPY       requirements.txt /app/
RUN        pip install -r requirements.txt

COPY       *.py /app/
RUN        chmod a+x *.py

CMD        ["./kafka-flask.py", "./kafka-consumer.py"]



