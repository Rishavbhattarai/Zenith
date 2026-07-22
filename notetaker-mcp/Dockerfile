# Build from the REPO ROOT so this can also copy the sibling docs/runbooks/
# knowledge base:
#   docker build -f notetaker-mcp/Dockerfile -t zenith-notetaker .
FROM python:3.13-slim
WORKDIR /app

COPY notetaker-mcp/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY notetaker-mcp/notetaker ./notetaker
COPY docs/runbooks /docs/runbooks

ENV PYTHONUNBUFFERED=1
ENV RUNBOOKS_DIR=/docs/runbooks
EXPOSE 8000
CMD ["uvicorn", "notetaker.http_api:app", "--host", "0.0.0.0", "--port", "8000"]
