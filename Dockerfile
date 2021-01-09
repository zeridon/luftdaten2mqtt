FROM python:3-alpine AS build
RUN pip wheel bottle paho-mqtt

FROM python:3-alpine
COPY --from=build /*.whl /tmp/
RUN pip install  --no-cache-dir /tmp/*.whl
COPY luftdaten2mqtt.py /

ENTRYPOINT [ "python", "/luftdaten2mqtt.py" ]
