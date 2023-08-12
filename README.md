# Сборка
```
git clone https://github.com/zxcvve/gitlab-telegram-notifier.git
cd gitlab-telegram-notifier
docker build -t gitlab-notifier .
```

# Запуск
```
docker run -p 8000:8000 --env TELEGRAM_API_TOKEN=<YOUR API TOKEN> --env TELEGRAM_CHAT_ID=<YOUR CHAT ID> -d gitlab-notifier
```