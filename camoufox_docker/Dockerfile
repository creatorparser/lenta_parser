FROM python:3.11-slim

# Устанавливаем Firefox
RUN apt-get update && apt-get install -y \
    firefox-esr \
    xvfb \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходники
COPY server.py .
COPY start.sh .
RUN chmod +x start.sh

RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

# Порт сервера
EXPOSE 8000

CMD ["./start.sh"]