# 🚀 WARP Config Generator

[Русский](README.md) | [English](README.en.md)

A **Cloudflare WARP** VPN config generator available as a **Telegram bot**, **web interface**, or **CLI**.

![Web interface](https://github.com/user-attachments/assets/84ae89b2-b679-4f03-9acd-b79cbda99180)

## 🆕 Latest updates

- Added new **split tunnel** presets: **Spotify**, **Netflix**, **OpenAI**, **TikTok**, and **Steam**.
- Expanded IP ranges for existing routing services in `configs/routing_services.json`.
- Removed obfuscation duplication: **Clash** and **WireSock** now reuse **AmneziaWG** values from `configs/warp_params.json`.
- Added a unified launcher via `python launch.py` (`--web-only` / `--bot-only`).
- Switched web generation to a shared Python generation API (single generation code path).
- The main documentation is now Russian-first; this file is the up-to-date English companion README.

## Supported formats

| Format | Description |
|--------|-------------|
| **WireGuard** | Standard `.conf` for any WireGuard client |
| **AmneziaWG** | `.conf` with obfuscation parameters + `vpn://` deeplink for AmneziaVPN |
| **Clash** | YAML proxy config for Clash / Clash Meta |
| **WireSock** | `.conf` for WireSock on Windows |

## Features

- **DNS selection** — Cloudflare, Google, Quad9, AdGuard, OpenDNS, and more.
- **Relay / endpoint selection** — alternative Cloudflare edge endpoints.
- **Routing modes** — full tunnel or split tunnel with routes for specific services.
- **Built-in split-tunnel presets** — Google/YouTube, Meta, Twitter/X, Telegram, Discord, Spotify, Netflix, OpenAI, TikTok, and Steam.
- **Confirmation before generation** — review settings before creating a config.
- **Persistent keyboard** — “Generate”, “WARP status”, and “Help” buttons stay visible in the bot.
- **WARP status shortcut** — link to [@cfwarpstatus](https://t.me/cfwarpstatus) for monitoring.
- **Localization** — Russian and English out of the box, with easy extension.
- **In-bot help** — instructions for adding DNS servers, relays, and routing services.
- **Config-driven setup** — all runtime parameters are stored in JSON files under `configs/`.
- **Localized web interface** — Node.js/Express UI with shared translations.
- **CLI generator** — quick generation via `python generate.py`.

---

## Quick start

### 1. Create a bot

Open [@BotFather](https://t.me/BotFather) in Telegram and create a new bot.
Copy the API token.

### 2. Clone and install

```bash
git clone https://github.com/cat658011/bash-warp-generator.git
cd bash-warp-generator
pip install -r requirements.txt
```

### 3. Run the Telegram bot

```bash
export BOT_TOKEN="your-bot-token"
export BOT_LANG="en"
python -m bot
```

The bot will start polling. Send `/start` in chat to begin.

### 3.1 Unified launch (bot + web)

```bash
python launch.py
```

Flags:

- `--web-only` — run only the web server
- `--bot-only` — run only the Telegram bot

### 4. Run the web interface

**Install dependencies:**

```bash
cd web
npm install
```

**Start in development mode:**

```bash
node web/server.js
```

Open `http://localhost:3000` in your browser.

**Production (with pm2):**

```bash
npm install -g pm2
pm2 start web/server.js --name warp-web
```

**Production with nginx (recommended):**

1. Start the server with pm2 or systemd:

```bash
PORT=3000 node web/server.js
```

2. Configure nginx as a reverse proxy:

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

3. Use the `/health` endpoint for monitoring:

```bash
curl http://localhost:3000/health
# {"status":"ok"}
```

---

## 📁 Configuration files

All settings are stored in JSON files inside `configs/`. You can customize the project without changing the code.

| File | Purpose |
|------|---------|
| `dns_servers.json` | DNS servers (display name + addresses) |
| `relay_servers.json` | Alternative Cloudflare WARP endpoints |
| `routing_services.json` | Service IP ranges for split tunnel |
| `warp_params.json` | AmneziaWG parameters + shared I1 payloads, MTU, Clash reserved and WireSock masking |
| `i18n/ru.json` | Russian localization for bot + web |
| `i18n/en.json` | English localization for bot + web |

### Available routing presets

`configs/routing_services.json` currently includes these built-in route sets:

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

### 📡 Add a custom relay (endpoint)

Open `configs/relay_servers.json` and add a new object to the array:

```json
[
  {
    "name": "Default (Cloudflare)",
    "endpoint": "162.159.192.1:500"
  },
  {
    "name": "My custom relay",
    "endpoint": "203.0.113.1:51820"
  }
]
```

**Fields:**

| Field | Description | Example |
|------|-------------|---------|
| `name` | Display name shown in the bot and web UI | `"My relay (Germany)"` |
| `endpoint` | WARP endpoint IP and port | `"203.0.113.1:51820"` |

**Where to find alternative endpoints:**

```bash
# Via DNS
dig +short engage.cloudflareclient.com

# Via nslookup
nslookup engage.cloudflareclient.com
```

**Supported ports:** `500`, `854`, `859`, `1701`, `2408`, `4500`, `51820`

**IPv6 example:**

```json
{
  "name": "Cloudflare IPv6",
  "endpoint": "[2606:4700:d0::a29f:c001]:500"
}
```

> 💡 Restart the bot and/or web server after editing the config.

---

### 🌐 Add a DNS server

Open `configs/dns_servers.json` and add an object:

```json
{
  "name": "My DNS",
  "servers": ["10.0.0.1", "10.0.0.2"]
}
```

**Fields:**

| Field | Description | Example |
|------|-------------|---------|
| `name` | Display name | `"AdGuard Family"` |
| `servers` | Array of DNS server IP addresses | `["94.140.14.15", "94.140.15.16"]` |

---

### 🔀 Add a split-tunnel service

Open `configs/routing_services.json` and add an object:

```json
{
  "name": "My Service",
  "routes": ["203.0.113.0/24", "198.51.100.0/24"]
}
```

**Fields:**

| Field | Description | Example |
|------|-------------|---------|
| `name` | Service name | `"Yandex"` |
| `routes` | Array of CIDR subnets | `["77.88.55.0/24", "5.255.255.0/24"]` |

**How to find service IP ranges:**

```bash
# Via whois
whois -h whois.radb.net -- '-i origin AS13238' | grep route

# Via BGP
# Use bgp.he.net to look up ASNs and prefixes

# Via DNS
dig +short yandex.ru
```

> ⚠️ The first array item (`index 0`) is the full-tunnel preset and is not shown in the service picker. Custom services must be added after it.

---

### 📦 Rename protocol labels

Edit `configs/i18n/ru.json` (or `en.json` for English):

```json
{
  "fmt_wireguard": "�� WireGuard",
  "fmt_amnezia": "🛡️ AmneziaWG",
  "fmt_clash": "⚔️ Clash",
  "fmt_wiresock": "🪟 WireSock",
  "fmt_wireguard_desc": "Standard WireGuard config (.conf)",
  "fmt_amnezia_desc": "AmneziaWG with DPI resistance",
  "fmt_clash_desc": "Clash / Clash Meta proxy config",
  "fmt_wiresock_desc": "WireSock for Windows"
}
```

Update the `fmt_*` and `fmt_*_desc` values as needed, but keep the keys unchanged. The same localization files are used by both the bot and the web interface.

---

## 🌍 Localization

All UI strings for the bot and web interface live in `configs/i18n/`.

| File | Language |
|------|----------|
| `configs/i18n/ru.json` | Russian (default) |
| `configs/i18n/en.json` | English |

Set the bot language with `BOT_LANG`:

```bash
export BOT_LANG="en"
python -m bot
```

For the web interface, you can use the same environment variable or the `lang` URL parameter:

```text
http://localhost:3000/?lang=en
```

### Add a new language

1. Copy `configs/i18n/ru.json` to `configs/i18n/<code>.json` (for example `uk.json`)
2. Translate the values without changing the keys
3. Set `BOT_LANG=<code>` and restart the bot

The same file is shared between the bot and the web interface.

---

## ⚙️ WARP parameters (AmneziaWG / Clash / WireSock)

Obfuscation parameters and I1 payloads are stored in `configs/warp_params.json`:

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

| Field | Description |
|------|-------------|
| `amnezia` | Obfuscation parameters (Jc, Jmin, Jmax, S1, S2, H1–H4) |
| `mtu` | Default MTU for generated formats |
| `i1_payloads` | Array of I1 payloads; one is chosen **at random** per generation |

> 💡 Add your own I1 payloads to the array and they will rotate automatically.

---

## 📂 Project structure

```text
├── core/                     # Core library (Telegram-independent)
│   ├── __init__.py
│   ├── config.py             # JSON config loading and dataclasses
│   ├── generators.py         # WireGuard / AmneziaWG / Clash / WireSock generators
│   ├── generation_api.py     # Shared HTTP API for config generation
│   ├── ports.py              # Port selection for different formats
│   └── warp.py               # Cloudflare WARP API client
├── bot/                      # Telegram bot
│   ├── __init__.py
│   ├── __main__.py           # Entry point (python -m bot)
│   ├── handlers.py           # Dialog logic and menu handlers
│   ├── keyboards.py          # Inline and reply keyboard builders
│   └── i18n.py               # Localization loader (→ configs/i18n/)
├── web/                      # Web interface (Node.js / Express)
│   ├── package.json          # Node.js dependencies
│   ├── package-lock.json
│   ├── server.js             # Express application
│   ├── lib/
│   │   ├── config.js         # JSON config + i18n + warp_params loader
│   │   ├── formats.js        # UI format metadata
│   │   ├── ports.js          # Port selection for web formats
│   │   └── python_api.js     # Shared Python generation API client
│   ├── views/
│   │   └── index.ejs         # HTML template with i18n strings
│   └── test/
│       └── server.test.js    # Web server tests
├── configs/
│   ├── i18n/                 # Localization (bot + web)
│   │   ├── ru.json           # Russian
│   │   └── en.json           # English
│   ├── dns_servers.json      # DNS servers
│   ├── relay_servers.json    # Cloudflare WARP endpoints
│   ├── routing_services.json # Service routes for split tunnel
│   └── warp_params.json      # Obfuscation params + I1 payloads
├── tests/
│   ├── test_config.py        # Config tests
│   ├── test_generators.py    # Generator tests
│   ├── test_i18n.py          # Localization tests
│   ├── test_ports.py         # Port selection tests
│   ├── test_warp.py          # WARP API tests
│   └── test_web.py           # Web integration tests
├── .env.example              # Example environment variables
├── generate.py               # CLI generator
├── launch.py                 # Unified bot+web launcher
├── LICENSE
├── README.en.md              # English documentation
├── README.md                 # Main Russian documentation
└── requirements.txt          # Python dependencies (bot + core)
```

`core/` contains the generation logic and does **not depend on Telegram**.  
The web server calls `core/generation_api.py`, so config generation is maintained in one codebase (Python).  
The bot and web frontend both read settings from shared files under `configs/`.

---

## 🧪 Testing

**Python tests (bot + core + web integration):**

```bash
pip install -r requirements.txt pytest
python -m pytest tests/ -v
```

**JavaScript tests (web interface):**

```bash
cd web
npm install
npm test
```

---

## 🔧 Environment variables

| Variable | Description | Default |
|---------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token from @BotFather | — (required) |
| `BOT_LANG` | Default language for the bot and web UI (`ru`, `en`) | `ru` |
| `PORT` | Web interface port | `3000` |
| `GENERATION_API_URL` | Shared Python generation API URL used by web | `http://127.0.0.1:8787` |
| `GENERATION_API_MANAGED` | Auto-start generation API from `web/server.js` (`1`/`0`) | `1` |
| `GENERATION_API_HOST` | Host for managed generation API process | `127.0.0.1` |
| `GENERATION_API_PORT` | Port for managed generation API process | `8787` |

---

## 🖥️ CLI generator

To generate a config from the command line:

```bash
python generate.py
```

The script registers with Cloudflare WARP, generates an AmneziaWG config, prints it together with an AmneziaVPN deep link, and saves the config to `warp-amnezia.conf`.

---

## 🔄 Legacy Bash script

The original bash script is not present in the current repository snapshot. The actively maintained implementation now lives in the Python core, Telegram bot, web UI, and CLI generator. For terminal-based usage, run `python generate.py`.

---

## 💡 Project ideas

- Add OpenAPI schema and auto-generated clients for `core/generation_api.py`.
- Move web rate-limit state to Redis for multi-instance deployment.
- Add a “what’s new” web page sourced from release changelog.
- Add QR export for WireGuard/AmneziaWG in the web UI.
- Add observability: Prometheus metrics, structured logs, and alerts for WARP registration failures.

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot does not respond | Make sure `BOT_TOKEN` is set correctly |
| WARP registration fails | Cloudflare's API may be blocked; try running on a VPS |
| Python import errors | Run `pip install -r requirements.txt` |
| Language does not load | Check that `BOT_LANG` matches a file in `configs/i18n/` |
| Web server does not start | Run `cd web && npm install` |
| Port already in use | Change the port: `PORT=8080 node web/server.js` |

---

## �� License

MIT
