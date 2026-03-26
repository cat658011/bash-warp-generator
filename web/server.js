'use strict';

const path = require('node:path');
const { spawn } = require('node:child_process');
const express = require('express');
const { loadConfigs, loadI18n, availableLanguages } = require('./lib/config');
const { FORMAT_LABELS, FORMATS } = require('./lib/formats');
const { resolveEndpoint } = require('./lib/ports');
const { generateViaPython } = require('./lib/python_api');

const app = express();
const PORT = process.env.PORT || 3000;
const API_HOST = process.env.GENERATION_API_HOST || '127.0.0.1';
const API_PORT = process.env.GENERATION_API_PORT || '8787';
const API_MANAGED = (process.env.GENERATION_API_MANAGED || '1') !== '0';
const SHUTDOWN_TIMEOUT_MS = 500;
const rateLimitState = new Map();
let lastRateLimitCleanupAt = 0;
let generationApiProcess = null;
const NO_IP_BUCKET = '__unknown_ip__';

// Middleware
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

function getRateLimitConfig() {
  const windowMsRaw = Number(process.env.WEB_RATE_LIMIT_WINDOW_MS || 60_000);
  const maxRequestsRaw = Number(process.env.WEB_RATE_LIMIT_MAX_REQUESTS || 10);
  return {
    windowMs: Number.isFinite(windowMsRaw) && windowMsRaw > 0 ? windowMsRaw : 60_000,
    maxRequests: Number.isFinite(maxRequestsRaw) && maxRequestsRaw >= 0 ? maxRequestsRaw : 10,
  };
}

function cleanupRateLimitState(now, windowMs) {
  for (const [ip, entry] of rateLimitState.entries()) {
    if (now - entry.windowStart >= windowMs) {
      rateLimitState.delete(ip);
    }
  }
}

function antiFlood(req, res, next) {
  const { windowMs, maxRequests } = getRateLimitConfig();
  const now = Date.now();
  if (now - lastRateLimitCleanupAt >= windowMs) {
    cleanupRateLimitState(now, windowMs);
    lastRateLimitCleanupAt = now;
  }
  const ip = req.ip || req.socket?.remoteAddress || NO_IP_BUCKET;
  let entry = rateLimitState.get(ip);
  if (!entry || now - entry.windowStart >= windowMs) {
    entry = { count: 0, windowStart: now };
    rateLimitState.set(ip, entry);
  }

  if (entry.count >= maxRequests) {
    const lang = req.body?.lang || process.env.BOT_LANG || 'ru';
    const i18n = loadI18n(lang);
    return res
      .status(429)
      .json({ error: i18n.web_error_rate_limited || 'Too many requests. Try again later.' });
  }

  entry.count += 1;
  return next();
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

function ensureGenerationApi() {
  if (!API_MANAGED || generationApiProcess) {
    return;
  }
  generationApiProcess = spawn(
    'python',
    ['-m', 'core.generation_api', '--host', API_HOST, '--port', String(API_PORT)],
    {
      cwd: path.resolve(__dirname, '..'),
      stdio: ['ignore', 'ignore', 'pipe'],
    },
  );
  generationApiProcess.stderr.on('data', (chunk) => {
    const message = chunk.toString().trim();
    if (message) {
      console.error('[generation-api]', message);
    }
  });
  generationApiProcess.on('error', (err) => {
    console.error('Failed to start generation API process:', err);
  });
  generationApiProcess.on('exit', () => {
    generationApiProcess = null;
  });
}

function stopGenerationApi() {
  if (generationApiProcess && !generationApiProcess.killed) {
    generationApiProcess.kill('SIGTERM');
  }
}

// ── Routes ───────────────────────────────────────────────────────────────────

app.get('/', (req, res) => {
  const lang = req.query.lang || process.env.BOT_LANG || 'ru';
  const i18n = loadI18n(lang);

  res.render('index', {
    formats: Array.from(FORMATS),
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

app.post('/generate', antiFlood, async (req, res) => {
  let fmt = req.body.format || 'wireguard';
  const dnsIdx = parseInt(req.body.dns || '0', 10);
  const relayIdx = parseInt(req.body.relay || '0', 10);
  const routing = req.body.routing || 'full';
  const selectedSvcs = Array.isArray(req.body.services)
    ? req.body.services
    : req.body.services
      ? [req.body.services]
      : [];

  const lang = req.body.lang || process.env.BOT_LANG || 'ru';
  const i18n = loadI18n(lang);

  const dns = configs.dnsServers[dnsIdx];
  const relay = configs.relayServers[relayIdx];

  let allowedIps;
  if (routing === 'split' && selectedSvcs.length > 0) {
    allowedIps = [];
    for (const idxStr of selectedSvcs) {
      const svc = configs.routingServices[parseInt(idxStr, 10)];
      if (svc) allowedIps.push(...svc.routes);
    }
  } else {
    allowedIps = ['0.0.0.0/0', '::/0'];
  }

  if (!FORMATS.has(fmt)) {
    fmt = 'wireguard';
  }

  let generated;
  try {
    generated = await generateViaPython({
      format: fmt,
      dns_servers: dns.servers,
      endpoint: resolveEndpoint(fmt, relay),
      allowed_ips: allowedIps,
      mtu: 1280,
    });
  } catch (err) {
    console.error('Python generation API failed:', err);
    return res.status(502).json({ error: i18n.web_error_warp || 'WARP registration failed' });
  }

  const { content, filename } = generated;

  res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
  res.setHeader('Content-Type', 'application/octet-stream');
  res.send(content);
});

// Only start listening when run directly (not when imported for testing)
if (require.main === module) {
  ensureGenerationApi();
  const server = app.listen(PORT, () => {
    console.log(`🚀 WARP Config Generator running: http://localhost:${PORT}`);
  });
  const shutdown = () => {
    stopGenerationApi();
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), SHUTDOWN_TIMEOUT_MS).unref();
  };
  process.on('SIGINT', shutdown);
  process.on('SIGTERM', shutdown);
}

module.exports = app;
