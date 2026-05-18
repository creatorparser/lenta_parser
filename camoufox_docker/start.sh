#!/bin/bash
rm -f /tmp/.X99-lock

# Создание директории для X-сокетов и установка правильных прав
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Запуск Xvfb
Xvfb :99 -screen 0 1920x1080x24 -nolisten tcp &
export DISPLAY=:99

echo "🚀 Starting Camoufox Service on port 8000..."
exec python -m uvicorn server:app --host 0.0.0.0 --port 8000 --log-level info