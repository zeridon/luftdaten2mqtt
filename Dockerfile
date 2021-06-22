FROM python:3-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY luftdaten2mqtt.py views ./

ENTRYPOINT [ "python", "/app/luftdaten2mqtt.py" ]
