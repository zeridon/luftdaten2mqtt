FROM python:3-alpine

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY luftdaten2mqtt.py views ./

EXPOSE 8080

HEALTHCHECK \
	--timeout=2s \
	CMD wget -q -T5 -O- http://localhost:8080/status | grep OK || exit 1

# Use command instead of entrypoint to allow custom commands
CMD [ "python3", "/app/luftdaten2mqtt.py" ]
