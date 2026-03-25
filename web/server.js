'use strict';

const path = require('node:path');
const express = require('express');
const { loadConfigs, loadI18n, availableLanguages } = require('./lib/config');
const { registerWarp } = require('./lib/warp');
const { GENERATORS, FORMAT_LABELS, FORMATS } = require('./lib/generators');
const { resolveEndpoint } = require('./lib/ports');

function parsePositiveIntEnv(name, defaultValue) {
  const raw = process.env[name];
  if (raw === undefined) {
    return defaultValue;
  }
  const parsed = Number.parseInt(raw, 10);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    console.warn(`Invalid ${name}="${raw}", using default ${defaultValue}`);
    return defaultValue;
  }
  return parsed;
}

const app = express();
const PORT = process.env.PORT || 3000;
const RATE_LIMIT_WINDOW_MS = parsePositiveIntEnv('RATE_LIMIT_WINDOW_MS', 60000);
const RATE_LIMIT_GENERATE_MAX = parsePositiveIntEnv('RATE_LIMIT_GENERATE_MAX', 15);
const TRUST_PROXY = process.env.TRUST_PROXY === '1';
const rateLimitStore = new Map();
let requestsSinceCleanup = 0;
const CLEANUP_EVERY_REQUESTS = 50;

// Middleware
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());
if (TRUST_PROXY) {
  app.set('trust proxy', true);
}

// Load configs once at startup
const configs = loadConfigs();
const languages = availableLanguages();

// Helper: resolve translated name for a config item
function resolveNames(items, prefix, i18n) {
  return items.map((item) => ({
    ...item,
    name: i18n[prefix + item.id] || item.id,
  }));
}

// Helper: resolve format labels with localized descriptions
function resolveFormatLabels(formatLabels, i18n) {
  const resolved = {};
  for (const [key, val] of Object.entries(formatLabels)) {
    resolved[key] = {
      name: val.name,
      desc: i18n[val.descKey] || val.descKey,
    };
  }
  return resolved;
}

function getClientIp(req) {
  if (typeof req.ip === 'string' && req.ip.length > 0) {
    return req.ip;
  }
  return req.socket?.remoteAddress || 'unknown';
}

function isRateLimited(req) {
  const now = Date.now();
  requestsSinceCleanup += 1;
  if (requestsSinceCleanup >= CLEANUP_EVERY_REQUESTS) {
    requestsSinceCleanup = 0;
    for (const [key, value] of rateLimitStore) {
      if (now >= value.resetAt) {
        rateLimitStore.delete(key);
      }
    }
  }

  const ip = getClientIp(req);
  const entry = rateLimitStore.get(ip);

  if (!entry || now >= entry.resetAt) {
    rateLimitStore.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS });
    return false;
  }

  if (entry.count >= RATE_LIMIT_GENERATE_MAX) {
    return true;
  }

  entry.count += 1;
  return false;
}

function parseIndex(rawValue) {
  const parsed = Number.parseInt(rawValue, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    return null;
  }
  return parsed;
}

function resetRateLimitStore() {
  rateLimitStore.clear();
  requestsSinceCleanup = 0;
}

// ── Routes ───────────────────────────────────────────────────────────────────

app.get('/', (req, res) => {
  const lang = req.query.lang || process.env.BOT_LANG || 'ru';
  const i18n = loadI18n(lang);

  res.render('index', {
    formats: Object.keys(GENERATORS),
    formatLabels: resolveFormatLabels(FORMAT_LABELS, i18n),
    dnsServers: resolveNames(configs.dnsServers, 'dns_', i18n),
    relayServers: resolveNames(configs.relayServers, 'relay_', i18n),
    routingServices: resolveNames(configs.routingServices, 'svc_', i18n),
    t: i18n,
    currentLang: lang,
    languages,
  });
});

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.post('/generate', async (req, res) => {
  let fmt = req.body.format || 'wireguard';
  const dnsIdx = parseIndex(req.body.dns || '0');
  const relayIdx = parseIndex(req.body.relay || '0');
  const routing = req.body.routing || 'full';
  const selectedSvcs = Array.isArray(req.body.services)
    ? req.body.services
    : req.body.services
      ? [req.body.services]
      : [];

  const lang = req.body.lang || process.env.BOT_LANG || 'ru';
  const i18n = loadI18n(lang);

  if (isRateLimited(req)) {
    return res.status(429).json({
      error: i18n.web_error_rate_limited || 'Too many requests. Please try again later.',
    });
  }

  if (!FORMATS.has(fmt)) {
    fmt = 'wireguard';
  }

  if (dnsIdx === null || relayIdx === null) {
    return res.status(400).json({
      error: i18n.web_error_invalid_request || 'Invalid request parameters.',
    });
  }

  const dns = configs.dnsServers[dnsIdx];
  const relay = configs.relayServers[relayIdx];
  if (!dns || !relay) {
    return res.status(400).json({
      error: i18n.web_error_invalid_request || 'Invalid request parameters.',
    });
  }

  let allowedIps;
  if (routing === 'split' && selectedSvcs.length > 0) {
    allowedIps = [];
    for (const idxStr of selectedSvcs) {
      const svcIdx = parseIndex(idxStr);
      if (svcIdx === null) {
        continue;
      }
      const svc = configs.routingServices[svcIdx];
      if (svc) allowedIps.push(...svc.routes);
    }
  } else {
    allowedIps = ['0.0.0.0/0', '::/0'];
  }

  let account;
  try {
    account = await registerWarp();
  } catch (err) {
    console.error('WARP registration failed:', err);
    return res.status(502).json({ error: i18n.web_error_warp || 'WARP registration failed' });
  }

  const params = {
    privateKey: account.privateKey,
    publicKey: account.publicKey,
    peerPublicKey: account.peerPublicKey,
    clientIpv4: account.clientIpv4,
    clientIpv6: account.clientIpv6,
    dnsServers: dns.servers,
    endpoint: resolveEndpoint(fmt, relay),
    allowedIps,
    mtu: 1280,
  };

  const { content, filename } = GENERATORS[fmt](params);

  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.send(content);
});

// Only start listening when run directly (not when imported for testing)
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`🚀 WARP Config Generator running: http://localhost:${PORT}`);
  });
}

module.exports = app;
module.exports.__resetRateLimitStore = resetRateLimitStore;
module.exports.__rateLimitMax = RATE_LIMIT_GENERATE_MAX;
