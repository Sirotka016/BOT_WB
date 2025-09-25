# BOT_WB

Телеграм-бот для взаимодействия с кабинетом Wildberries Seller. Проект очищен и подготовлен к минимальному продакшн-запуску: одно сообщение-якорь, надёжная авторизация через реальное окно WB Seller, единое логирование и набор проверок качества.

## 🚀 Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
cp .env.example .env
# заполните BOT_TOKEN и другие переменные
python -m playwright install chromium
python -m bot_wb
```

> Проект рассчитан на `aiogram` версии `3.7` и выше (до `4.0`).
> Параметры `parse_mode`/`disable_web_page_preview`/`protect_content`
> настраиваются через `DefaultBotProperties` при создании экземпляра `Bot`.

## ▶️ Запуск

Способ A (быстрый):
    python main.py

Способ B (рекомендуемый для разработки):
    pip install -e .
    python -m bot_wb

## 🔒 Single instance

- При запуске бот создаёт файл-блокировку `data/bot_wb.lock`, исключая одновременную работу нескольких процессов.
- Повторный запуск завершится с сообщением `Another BOT_WB instance is already running` и не приведёт к конфликту `getUpdates`.

## ⚙️ Переменные окружения

| Переменная | Значение по умолчанию | Назначение |
|------------|-----------------------|------------|
| `BOT_TOKEN` | — | Токен Telegram-бота. Обязателен. |
| `LOG_LEVEL` | `INFO` | Уровень логирования (`DEBUG`/`INFO`/`WARNING`/`ERROR`). |
| `WB_SELLER_BASE` | `https://seller.wildberries.ru` | Базовый URL кабинета WB Seller. |
| `WB_SELLER_AUTH_URL` | `https://seller-auth.wildberries.ru/…` | URL формы авторизации WB Seller. |
| `DATA_DIR` | `data` | Каталог с базой и сессиями (`data/sessions/<tg_id>/cookies.json`). |

## 🧪 Тесты и проверки качества

```bash
pytest
ruff check src tests
black --check src tests
isort --check-only src tests
mypy src
```

Перед коммитом используйте `pre-commit`:

```bash
pre-commit install
pre-commit run --all-files
```

## 📁 Структура

- `src/bot_wb/main.py` — точка входа бота, настраивает логирование и middlewares.
- `src/bot_wb/logging.py` — конфигурация loguru (цвет в консоли и ротация файлов).
- `src/bot_wb/middlewares/` — лог-контекст и обработка ошибок.
- `src/bot_wb/services/` — авторизация через Playwright и HTTP-клиент WB.
- `src/bot_wb/storage/` — SQLite и файловые хранилища сессий.
- `tests/` — pytest + asyncio/respx/aiogram-tests.

## ❗️ Известные ограничения

- Для headful Playwright необходима графическая подсистема. На сервере используйте `xvfb` или запускайте локально.
- Заглушки WB API (`list_organizations`, `set_active_organization`) ещё не подключены к реальным ручкам — в коде помечено `TODO`.
- Тесты мокаю Playwright и HTTP-запросы: для интеграции с реальными сервисами понадобятся дополнительные e2e-проверки.
- Библиотека `aiogram-tests` пока ориентирована на aiogram v2, поэтому тест с её использованием помечен как `xfail`/skip до появления версии под v3.
