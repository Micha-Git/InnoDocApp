FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install . pytest && mkdir results

COPY src .

# Sleep to allow dependent services to start
CMD ["sh", "-c", "sleep 2 && pytest -rfEp > /app/results/report.txt"]