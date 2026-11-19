FROM python:3.12-slim

WORKDIR /app

COPY app.py /app/app.py

ENV PYTHONUNBUFFERED=1 \
    PORT=8096

EXPOSE 8096

CMD ["python", "/app/app.py"]
