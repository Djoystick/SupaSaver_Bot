#!/bin/bash

echo "Starting Telegram Bot API Server..."
# Запускаем официальный сервер локально на порту 8081 в фоне
/docker-entrypoint.sh telegram-bot-api --local --api-id="${TELEGRAM_API_ID}" --api-hash="${TELEGRAM_API_HASH}" &

# Даем серверу 3 секунды на инициализацию
sleep 3

echo "Starting Python Bot..."
# Запускаем нашего бота
python main.py
