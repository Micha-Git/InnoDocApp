FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ .

EXPOSE 8083

CMD ["python3", "app.py"]
