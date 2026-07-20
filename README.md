# Perpetum

Минимальный аналог Perplexity на FastAPI: запрос ищется через **Yandex Search API v2**, затем LLM составляет ответ исключительно по найденным фрагментам и расставляет ссылки `[1]`, `[2]`.

## Запуск

1. Создайте сервисный аккаунт Yandex Cloud, выдайте ему роль `search-api.webSearch.user`, создайте API-ключ с областью `yc.search-api.execute` и узнайте ID каталога.
2. Скопируйте `.env.example` в `.env` и заполните `YANDEX_SEARCH_API_KEY` и `YANDEX_FOLDER_ID`. Для генерации можно задать отдельный `YANDEX_AI_API_KEY`; если он пуст, используется поисковый ключ.
3. Установите зависимости и запустите приложение:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Откройте http://127.0.0.1:8000. Документация API доступна по адресу http://127.0.0.1:8000/docs.

## Запуск в Docker

Заполните `.env`, затем соберите и запустите сервис:

```bash
docker compose up --build -d
```

Если порт `8000` занят локальным Uvicorn, остановите его или выберите другой порт:

```bash
HOST_PORT=8001 docker compose up --build -d
```

Тогда интерфейс будет доступен по адресу http://127.0.0.1:8001.

Проверка состояния и просмотр логов:

```bash
docker compose ps
docker compose logs -f perpetum
curl http://127.0.0.1:8000/api/health
```

Остановка:

```bash
docker compose down
```

Для запуска без Compose:

```bash
docker build -t perpetum .
docker run --rm -p 8000:8000 --env-file .env perpetum
```

Файл `.env` исключён из Docker-образа. `data/ofrs_merge.xlsx` копируется внутрь образа при сборке, поэтому после обновления таблицы образ необходимо пересобрать.

## Авторизация

Главная страница и `/api/ask` защищены подписанной сессией в `HttpOnly` cookie. Перед запуском задайте в `.env`:

```dotenv
AUTH_USERNAME=admin
AUTH_PASSWORD=сложный-пароль
AUTH_SECRET=случайная-строка-длиной-не-менее-32-символов
AUTH_SESSION_HOURS=24
AUTH_COOKIE_SECURE=true
```

Секрет можно сгенерировать командой:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Локально по HTTP оставьте `AUTH_COOKIE_SECURE=false`. На сервере используйте HTTPS и установите `true`.

## Yandex AI Studio

Ответ генерирует Alice AI LLM Flash через OpenAI-совместимый Chat Completions API Yandex AI Studio. Используются endpoint `https://ai.api.cloud.yandex.net/v1` и URI модели `gpt://<folder_id>/aliceai-llm-flash`. Сервисному аккаунту нужна роль `ai.languageModels.user`; API-ключ передаётся со схемой `Api-Key`.

Поиск всегда выполняется отдельно через Yandex Search API v2. Чтобы использовать один ключ для обоих сервисов, создайте его с областями `yc.search-api.execute` и `yc.ai.foundationModels.execute`, а сервисному аккаунту назначьте обе необходимые роли.

## API

`POST /api/ask`

```json
{"query": "Что нового в FastAPI?"}
```

`GET /api/health` показывает, заданы ли необходимые ключи, не раскрывая их значения.
