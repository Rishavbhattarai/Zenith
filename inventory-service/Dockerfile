FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY inventory ./inventory
COPY db ./db

ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["uvicorn", "inventory.main:app", "--host", "0.0.0.0", "--port", "8001"]
