'use strict';

const path = require('node:path');
const express = require('express');
const { loadConfigs, loadI18n, availableLanguages } = require('./lib/config');
const { registerWarp } = require('./lib/warp');
const { GENERATORS, FORMAT_LABELS } = require('./lib/generators');
const JSZip = require('jszip');

const app = express();
const PORT = process.env.PORT || 3000;
const MAX_CONFIGS = 5;

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
  const count = Math.min(
    MAX_CONFIGS,
    Math.max(1, parseInt(req.body.count || '1', 10) || 1),
  );
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

  if (!(fmt in GENERATORS)) {
    fmt = 'wireguard';
  }

  async function generateOnce(idx) {
    const account = await registerWarp();
    const params = {
      privateKey: account.privateKey,
      publicKey: account.publicKey,
      peerPublicKey: account.peerPublicKey,
      clientIpv4: account.clientIpv4,
      clientIpv6: account.clientIpv6,
      dnsServers: dns.servers,
      endpoint: relay.endpoint,
      allowedIps,
      mtu: 1280,
    };

    const { content, filename } = GENERATORS[fmt](params);
    if (count === 1) {
      return { content, filename };
    }
    // Append suffix before extension when generating multiple files
    const dot = filename.lastIndexOf('.');
    if (dot === -1) {
      return { content, filename: `${filename}-${idx}` };
    }
    const base = filename.slice(0, dot);
    const ext = filename.slice(dot);
    return { content, filename: `${base}-${idx}${ext}` };
  }

  try {
    if (count === 1) {
      const { content, filename } = await generateOnce(1);
      res.setHeader('Content-Disposition', `attachment; filename="${filename}"`);
      res.setHeader('Content-Type', 'application/octet-stream');
      return res.send(content);
    }

    const zip = new JSZip();
    for (let i = 1; i <= count; i += 1) {
      const { content, filename } = await generateOnce(i);
      zip.file(filename, content);
    }
    const zipBuf = await zip.generateAsync({ type: 'nodebuffer' });
    res.setHeader('Content-Disposition', 'attachment; filename="warp-configs.zip"');
    res.setHeader('Content-Type', 'application/zip');
    return res.send(zipBuf);
  } catch (err) {
    console.error('WARP registration failed:', err);
    return res.status(502).json({ error: i18n.web_error_warp || 'WARP registration failed' });
  }
});

// Only start listening when run directly (not when imported for testing)
if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`🚀 WARP Config Generator running: http://localhost:${PORT}`);
  });
}

module.exports = app;
