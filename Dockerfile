FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN mkdir -p /app/data

ENV STATE_DIR=/app/data
ENV PYTHONPATH=/app/src

CMD ["python", "-m", "idu_monitor"]
