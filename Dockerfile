# ─────────────────────────────────────────────
# Locadora Retrô — Dockerfile para Cloud Run
# ─────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Dependências em camada separada para aproveitar cache do Cloud Build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY . .

EXPOSE 8080

# Gunicorn — 1 worker + 8 threads:
#   • 1 worker: pool de falas (in-memory) e sessões Flask são por-processo.
#     Múltiplos workers causariam estado desincronizado entre eles.
#   • 8 threads: suporta requests simultâneos sem bloquear o SSE de geração.
#   • --timeout 0: desativa timeout do worker (SSE de streaming não pode ser
#     interrompido pelo gunicorn). O Cloud Run gerencia o timeout do request.
CMD exec gunicorn \
        --bind "0.0.0.0:$PORT" \
        --workers 1 \
        --threads 8 \
        --timeout 0 \
        --log-level info \
        app:app
