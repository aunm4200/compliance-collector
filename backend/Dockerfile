# syntax=docker/dockerfile:1.7

# Build context for this Dockerfile is the REPO ROOT, not backend/.
# docker build -f backend/Dockerfile .
# or: az acr build --file backend/Dockerfile .

FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /build

COPY pyproject.toml /build/pyproject.toml
COPY README.md /build/README.md
COPY src /build/src
COPY backend /build/backend

RUN pip install --upgrade pip wheel && \
    pip install /build && \
    pip install /build/backend

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/uvicorn /usr/local/bin/uvicorn

COPY backend/app /app/app

RUN useradd --system --create-home --uid 10001 appuser && chown -R appuser /app
USER appuser

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/healthz').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
