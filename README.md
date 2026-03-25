# 🚀 WARP Config Generator

[Русский](README.md) | [English](README.en.md)

Генератор конфигов **Cloudflare WARP** VPN через **Telegram-бота**, **веб-интерфейс** или **CLI**.

![Веб-интерфейс](https://github.com/user-attachments/assets/84ae89b2-b679-4f03-9acd-b79cbda99180)

## 🆕 Последние изменения

- Добавлены новые пресеты для **split tunnel**: **Spotify**, **Netflix**, **OpenAI**, **TikTok** и **Steam**.
- Расширены IP-диапазоны для существующих сервисов маршрутизации в `configs/routing_services.json`.
- Параметры **Clash** и **WireSock** приведены в соответствие с актуальными значениями **AmneziaWG** из `configs/warp_params.json`.
- Основная документация теперь ведётся на русском языке, английская версия доступна в [README.en.md](README.en.md).

## Поддерживаемые форматы

| Формат | Описание |
|--------|----------|
| **WireGuard** | Стандартный `.conf` для любого WireGuard-клиента |
| **AmneziaWG** | `.conf` с параметрами обфускации + `vpn://` deeplink для AmneziaVPN |
| **Clash** | YAML-конфиг прокси для Clash / Clash Meta |
| **WireSock** | `.conf` для WireSock на Windows |

## Возможности

- **Выбор DNS-сервера** — Cloudflare, Google, Quad9, AdGuard, OpenDNS и другие.
- **Выбор релея / эндпоинта** — альтернативные Cloudflare edge-эндпоинты.
- **Режимы маршрутизации** — весь трафик (full tunnel) или раздельный туннель (split tunnel) с маршрутами для конкретных сервисов.
- **Готовые пресеты split tunnel** — Google/YouTube, Meta, Twitter/X, Telegram, Discord, Spotify, Netflix, OpenAI, TikTok и Steam.
- **Подтверждение перед генерацией** — просмотр настроек перед созданием конфига.
- **Постоянная клавиатура** — кнопки «Генерация», «Статус WARP», «Помощь» всегда видны.
- **Статус WARP** — ссылка на [@cfwarpstatus](https://t.me/cfwarpstatus) для мониторинга.
- **Локализация** — русский и английский (легко добавить новые языки).
- **Помощь прямо в боте** — инструкции по добавлению DNS, релеев и сервисов.
- **Полная настройка** — все параметры хранятся в JSON-файлах в `configs/`.
- **Веб-интерфейс** — Node.js/Express приложение с поддержкой локализации.
- **CLI-генератор** — быстрый запуск через `python generate.py`.

---

## Быстрый старт

### 1. Создайте бота

Напишите [@BotFather](https://t.me/BotFather) в Telegram и создайте нового бота.
Скопируйте API-токен.

### 2. Клонируйте и установите

```bash
git clone https://github.com/cat658011/bash-warp-generator.git
cd bash-warp-generator
pip install -r requirements.txt
```

### 3. Запустите Telegram-бота

```bash
export BOT_TOKEN="ваш-токен-бота"
export BOT_LANG="ru"
python -m bot
```

Бот начнёт получать обновления. Отправьте `/start` в чате, чтобы начать.

### 4. Запустите веб-интерфейс

**Установка зависимостей:**

```bash
cd web
npm install
```

**Запуск в режиме разработки:**

```bash
node web/server.js
```

Откройте `http://localhost:3000` в браузере.

**Продакшн (с pm2):**

```bash
npm install -g pm2
pm2 start web/server.js --name warp-web
```

**Продакшн с nginx (рекомендуется):**

1. Запустите сервер через pm2 или systemd:

```bash
PORT=3000 node web/server.js
```

2. Настройте nginx как реверс-прокси:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Используйте эндпоинт `/health` для мониторинга:

```bash
curl http://localhost:3000/health
# {"status":"ok"}
```

---

## 📁 Файлы конфигурации

Все настройки хранятся в JSON-файлах в папке `configs/`. Редактируйте их — **никаких изменений в коде не требуется**.

| Файл | Назначение |
|------|-----------|
| `dns_servers.json` | DNS-серверы (имя + адреса) |
| `relay_servers.json` | Альтернативные эндпоинты Cloudflare WARP |
| `routing_services.json` | IP-диапазоны сервисов для раздельного туннеля |
| `warp_params.json` | Параметры AmneziaWG, Clash и WireSock: Jc, Jmin, Jmax, H1–H4, MTU, I1 payloads |
| `i18n/ru.json` | Русская локализация (бот + веб) |
| `i18n/en.json` | Английская локализация (бот + веб) |

### Доступные пресеты маршрутизации

`configs/routing_services.json` уже включает готовые наборы маршрутов:

- `full_tunnel`
- `google_youtube`
- `meta`
- `twitter`
- `telegram`
- `discord`
- `spotify`
- `netflix`
- `openai`
- `tiktok`
- `steam`

---

### 📡 Как добавить свой релей (эндпоинт)

Откройте файл `configs/relay_servers.json` и добавьте новый объект в массив:

```json
[
  {
    "name": "Default (Cloudflare)",
    "endpoint": "162.159.192.1:500"
  },
  {
    "name": "Мой кастомный релей",
    "endpoint": "203.0.113.1:51820"
  }
]
```

**Поля:**

| Поле | Описание | Пример |
|------|----------|--------|
| `name` | Отображаемое имя в боте и на сайте | `"Мой релей (Германия)"` |
| `endpoint` | IP-адрес и порт эндпоинта WARP | `"203.0.113.1:51820"` |

**Где найти альтернативные эндпоинты:**

```bash
# Через DNS
dig +short engage.cloudflareclient.com

# Через утилиту nslookup
nslookup engage.cloudflareclient.com
```

Также можно найти актуальные эндпоинты в сообществах и на форумах.

**Поддерживаемые порты:** `500`, `854`, `859`, `1701`, `2408`, `4500`, `51820`

**Поддержка IPv6:**

```json
{
  "name": "Cloudflare IPv6",
  "endpoint": "[2606:4700:d0::a29f:c001]:500"
}
```

> 💡 После редактирования перезапустите бота и/или веб-сервер.

---

### 🌐 Как добавить DNS-сервер

Откройте файл `configs/dns_servers.json` и добавьте объект:

```json
{
  "name": "Мой DNS",
  "servers": ["10.0.0.1", "10.0.0.2"]
}
```

**Поля:**

| Поле | Описание | Пример |
|------|----------|--------|
| `name` | Отображаемое имя | `"AdGuard Family"` |
| `servers` | Массив IP-адресов DNS-серверов | `["94.140.14.15", "94.140.15.16"]` |

---

### 🔀 Как добавить сервис для раздельного туннеля

Откройте файл `configs/routing_services.json` и добавьте объект:

```json
{
  "name": "Мой Сервис",
  "routes": ["203.0.113.0/24", "198.51.100.0/24"]
}
```

**Поля:**

| Поле | Описание | Пример |
|------|----------|--------|
| `name` | Название сервиса | `"Яндекс"` |
| `routes` | Массив CIDR-подсетей | `["77.88.55.0/24", "5.255.255.0/24"]` |

**Как найти IP-диапазоны сервиса:**

```bash
# Через whois
whois -h whois.radb.net -- '-i origin AS13238' | grep route

# Через BGP
# Используйте bgp.he.net для поиска ASN и их префиксов

# Через DNS
dig +short yandex.ru
```

> ⚠️ Первый элемент массива (`index 0`) — это «Весь трафик» (Full Tunnel) и он не отображается в меню выбора сервисов. Ваши сервисы должны идти после него.

---

### 📦 Как изменить названия протоколов (форматов)

Отредактируйте файл `configs/i18n/ru.json` (или `en.json` для английского):

```json
{
  "fmt_wireguard": "🔐 WireGuard",
  "fmt_amnezia": "🛡️ AmneziaWG",
  "fmt_clash": "⚔️ Clash",
  "fmt_wiresock": "🪟 WireSock",
  "fmt_wireguard_desc": "Стандартный WireGuard конфиг (.conf)",
  "fmt_amnezia_desc": "AmneziaWG с защитой от DPI",
  "fmt_clash_desc": "Конфиг прокси Clash / Clash Meta",
  "fmt_wiresock_desc": "WireSock для Windows"
}
```

Измените значения `fmt_*` и `fmt_*_desc` на нужные. Ключи менять нельзя.
Названия используются **и в боте, и в веб-интерфейсе** — один файл на все фронтенды.

---

## 🌍 Локализация

Все текстовые строки (бот + веб) хранятся в `configs/i18n/`.

| Файл | Язык |
|------|------|
| `configs/i18n/ru.json` | Русский (по умолчанию) |
| `configs/i18n/en.json` | Английский |

Язык бота задаётся через переменную `BOT_LANG`:

```bash
export BOT_LANG="ru"
python -m bot
```

Для веб-интерфейса можно использовать ту же переменную окружения или параметр `lang` в URL:

```text
http://localhost:3000/?lang=en
```

### Как добавить новый язык

1. Скопируйте `configs/i18n/ru.json` в `configs/i18n/<код>.json` (например, `uk.json`)
2. Переведите все значения (ключи менять нельзя)
3. Установите `BOT_LANG=uk` и перезапустите бота

Все строки сообщений, надписи на кнопках, описания форматов и весь UI-текст определены в файле языка. Один файл используется **и ботом, и веб-интерфейсом** — изменений в коде не требуется.

---

## ⚙️ Параметры WARP (AmneziaWG / Clash / WireSock)

Параметры обфускации и payload I1 хранятся в `configs/warp_params.json`:

```json
{
  "amnezia": {
    "Jc": 4,
    "Jmin": 40,
    "Jmax": 70,
    "S1": 0,
    "S2": 0,
    "H1": 1,
    "H2": 2,
    "H3": 3,
    "H4": 4
  },
  "mtu": 1280,
  "i1_payloads": [
    "<b 0xc200...>",
    "<b 0xa100...>",
    "<b 0xd300...>"
  ]
}
```

| Поле | Описание |
|------|----------|
| `amnezia` | Параметры обфускации (Jc, Jmin, Jmax, S1, S2, H1–H4) |
| `mtu` | MTU по умолчанию для всех форматов |
| `i1_payloads` | Массив I1-payload'ов — при каждой генерации выбирается **случайный** |

> 💡 Добавьте свои I1-payload'ы в массив — они будут ротироваться автоматически.

---

## 📂 Структура проекта

```text
├── core/                     # Основная библиотека (без зависимости от Telegram)
│   ├── __init__.py
│   ├── config.py             # Загрузка JSON-конфигов и dataclasses
│   ├── generators.py         # Генераторы WireGuard / AmneziaWG / Clash / WireSock
│   ├── ports.py              # Выбор портов для разных форматов
│   └── warp.py               # Клиент API Cloudflare WARP
├── bot/                      # Telegram-бот
│   ├── __init__.py
│   ├── __main__.py           # Точка входа (python -m bot)
│   ├── handlers.py           # Логика диалога + обработчики меню
│   ├── keyboards.py          # Построение inline- и reply-клавиатур
│   └── i18n.py               # Загрузчик локализации (→ configs/i18n/)
├── web/                      # Веб-интерфейс (Node.js / Express)
│   ├── package.json          # Зависимости Node.js
│   ├── package-lock.json
│   ├── server.js             # Express-приложение
│   ├── lib/
│   │   ├── config.js         # Загрузка JSON-конфигов + i18n + warp_params
│   │   ├── generators.js     # Генераторы конфигов
│   │   ├── ports.js          # Выбор портов для веб-форматов
│   │   └── warp.js           # Клиент API WARP (X25519 + регистрация)
│   ├── views/
│   │   └── index.ejs         # HTML-шаблон (EJS, i18n-строки)
│   └── test/
│       └── server.test.js    # Тесты веб-сервера
├── configs/
│   ├── i18n/                 # Локализация (бот + веб)
│   │   ├── ru.json           # Русский
│   │   └── en.json           # Английский
│   ├── dns_servers.json      # DNS-серверы
│   ├── relay_servers.json    # Эндпоинты Cloudflare WARP
│   ├── routing_services.json # IP-маршруты сервисов
│   └── warp_params.json      # Параметры AmneziaWG + I1 payloads
├── tests/
│   ├── test_config.py        # Тесты конфигурации
│   ├── test_generators.py    # Тесты генераторов
│   ├── test_i18n.py          # Тесты локализации
│   ├── test_ports.py         # Тесты выбора портов
│   ├── test_warp.py          # Тесты API WARP
│   └── test_web.py           # Интеграционные тесты веб-сервера
├── .env.example              # Пример переменных окружения
├── generate.py               # CLI-генератор
├── LICENSE
├── README.en.md              # Английская документация
├── README.md                 # Основная русская документация
└── requirements.txt          # Зависимости Python (бот + core)
```

Пакет `core/` содержит всю логику генерации WARP и **не зависит** от Telegram.
Оба фронтенда (бот и веб) читают параметры из общих конфигов в `configs/`: локализацию из `configs/i18n/`, параметры обфускации из `configs/warp_params.json`, а маршруты split tunnel — из `configs/routing_services.json`.

---

## 🧪 Тестирование

**Python-тесты (бот + core + веб-интеграция):**

```bash
pip install -r requirements.txt pytest
python -m pytest tests/ -v
```

**JavaScript-тесты (веб-интерфейс):**

```bash
cd web
npm install
npm test
```

---

## 🔧 Переменные окружения

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `BOT_TOKEN` | Токен Telegram-бота от @BotFather | — (обязательно) |
| `BOT_LANG` | Язык бота и веб-интерфейса по умолчанию (`ru`, `en`) | `ru` |
| `PORT` | Порт веб-интерфейса | `3000` |

---

## 🖥️ CLI-генератор

Для быстрой генерации конфига через командную строку:

```bash
python generate.py
```

Скрипт зарегистрируется в Cloudflare WARP, сгенерирует AmneziaWG-конфиг и выведет его вместе с deep-link для AmneziaVPN. Конфиг также сохраняется в файл `warp-amnezia.conf`.

---

## 🔄 Legacy Bash-скрипт

Оригинальный bash-скрипт в текущем репозитории отсутствует — актуальная реализация перенесена в Python-ядро, Telegram-бот и веб-интерфейс. Если вам нужен терминальный режим, используйте `python generate.py`.

---

## ❓ Решение проблем

| Проблема | Решение |
|----------|---------|
| Бот не отвечает | Убедитесь, что `BOT_TOKEN` задан правильно |
| Ошибка регистрации WARP | API Cloudflare может быть заблокирован; запустите на VPS |
| Ошибки импорта (Python) | Выполните `pip install -r requirements.txt` |
| Язык не загружается | Проверьте, что `BOT_LANG` соответствует файлу в `configs/i18n/` |
| Веб-сервер не запускается | Выполните `cd web && npm install` |
| Порт занят | Измените порт: `PORT=8080 node web/server.js` |

---

## 📜 Лицензия

MIT
