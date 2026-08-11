FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY services ./services
COPY packages ./packages
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["uvicorn", "services.platform_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
