'use strict';

const path = require('node:path');
const express = require('express');
const { loadConfigs, loadI18n, availableLanguages } = require('./lib/config');
const { registerWarp } = require('./lib/warp');
const { GENERATORS, FORMAT_LABELS, FORMATS } = require('./lib/generators');
const { resolveEndpoint } = require('./lib/ports');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: false }));
app.use(express.json());

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

  if (!FORMATS.has(fmt)) {
    fmt = 'wireguard';
  }
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
