FROM python:3-alpine
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt
COPY luftdaten2mqtt.py /

ENTRYPOINT [ "python", "/luftdaten2mqtt.py" ]
