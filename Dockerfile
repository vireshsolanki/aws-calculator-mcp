# AWS Pricing Calculator API — hosted baking server.
# The Playwright base image already contains Chromium + all OS deps, so end users
# never install a browser; it lives only inside this one container.

FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Install the package with its server extras (fastapi, uvicorn, playwright).
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir ".[server]"

ENV PORT=8080
# Ensure this server bakes locally (never forwards to itself).
ENV AWS_CALC_API_URL=""

EXPOSE 8080

# Healthcheck hits the FastAPI /health endpoint (uses $PORT).
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:%s/health'%os.environ.get('PORT','8080')).status==200 else 1)"

# Shell form so $PORT (injected by Render/Fly/etc.) is honored at runtime.
CMD uvicorn aws_calc_mcp.api_server:app --host 0.0.0.0 --port ${PORT:-8080}
