Currency Tracker API
Асинхронный backend-сервис для отслеживания курсов валют с API Центрального банка РФ с поддержкой WebSocket-уведомлений и интеграцией с NATS.
Выполнил: Горьков Владислав Дмитриевич РИ-330931


Быстрый запуск
1. Установка зависимостей
# Создание виртуального окружения
python -m venv venv
# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
2. Запуск NATS сервера
# Запуск NATS через Docker Compose
docker-compose up -d
3. Запуск приложения
# Запуск сервера с autoreload
uvicorn app.main:app --reload
Доступные endpoints
REST API
GET / - Информация о API
GET /health - Проверка состояния сервиса
GET /items/ - Список всех курсов валют
GET /items/{id} - Курс валюты по ID
GET /items/code/{code} - Последний курс по коду (USD, EUR и т.д.)
POST /items/ - Создание новой записи
PATCH /items/{id} - Обновление записи
DELETE /items/{id} - Удаление записи
POST /tasks/run - Ручной запуск обновления курсов

WebSocket
ws://localhost:8000/ws/items - WebSocket для real-time уведомлений

Мониторинг
Документация API: http://localhost:8000/docs
NATS мониторинг: http://localhost:8222

Тестирование WebSocket
Для тестирования WebSocket соединения можно использовать скрипт:
python debug_websocket.py
Или подключиться через WebSocket клиент со следующими командами:
ping - проверка соединения
status - получение статистики системы