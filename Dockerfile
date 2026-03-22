FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH=/usr/lib/playwright

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

# Ensure the /tmp/results path is writable for the Flask app
RUN mkdir -p /tmp/results && chmod -R 777 /tmp/results

EXPOSE 5000

# Use gunicorn to handle multiple requests and prevent timeouts
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]