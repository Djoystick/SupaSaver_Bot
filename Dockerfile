FROM aiogram/telegram-bot-api:latest

# Переключаемся на root для установки пакетов
USER root

# Устанавливаем Python, FFmpeg, bash и curl
RUN apk update && apk add --no-cache python3 py3-pip ffmpeg bash curl

# Создаем виртуальное окружение Python (требование Alpine Linux для pip)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Копируем и устанавливаем зависимости Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код бота и скрипт запуска
COPY . .
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Меняем права на директорию, чтобы API сервер мог туда писать
RUN chmod -R 777 /app
RUN chmod -R 777 /var/lib/telegram-bot-api

# Запускаем через наш скрипт
ENTRYPOINT ["/start.sh"]
