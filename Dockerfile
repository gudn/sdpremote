FROM snakepacker/python:all as builder

RUN python3.9 -m venv /app

COPY dist/*.whl /mnt/dist/

RUN /app/bin/pip install /mnt/dist/* && /app/bin/pip check

FROM snakepacker/python:3.9

COPY --from=builder /app /app

ENV SDP_REMOTE_STORAGE__region=us-west-1

CMD ["/app/bin/uvicorn", "sdpremote.app:app", "--host", "0.0.0.0"]
