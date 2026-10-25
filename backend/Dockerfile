FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng fonts-dejavu-core && rm -r /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
RUN useradd --uid 10001 --create-home app
COPY --chown=app:app backend/ ./
COPY --chown=app:app scripts/backend-entrypoint.sh /app/entrypoint.sh
RUN mkdir -p media staticfiles && chown -R app:app media staticfiles && chmod +x /app/entrypoint.sh
USER app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["serve"]
