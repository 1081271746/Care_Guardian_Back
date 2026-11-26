FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run as an unprivileged user; the app never writes to its own directory.
RUN useradd --create-home --uid 10001 careguardian && chown -R careguardian /app
USER careguardian

EXPOSE 8000
# Railway terminates TLS in its proxy; trust its forwarded headers for scheme/client.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
