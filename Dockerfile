
FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
ENV PYTHONPATH=/app
ENV DATA_DIR=/app/data

RUN mkdir -p /app/data

EXPOSE 8080
CMD ["python", "-m", "src.app"]
