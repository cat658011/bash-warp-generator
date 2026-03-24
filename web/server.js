'use strict';

const path = require('node:path');
const express = require('express');
const { loadConfigs, loadI18n } = require('./lib/config');
const { registerWarp } = require('./lib/warp');
const { GENERATORS, FORMAT_LABELS } = require('./lib/generators');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(express.urlencoded({ extended: false }));

// Load configs once at startup
const configs = loadConfigs();
const i18n = loadI18n();

// ── Routes ───────────────────────────────────────────────────────────────────

app.get('/', (_req, res) => {
  res.render('index', {
    formats: Object.keys(GENERATORS),
    formatLabels: FORMAT_LABELS,
    dnsServers: configs.dnsServers,
    relayServers: configs.relayServers,
    routingServices: configs.routingServices,
    t: i18n,
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
    return res.status(502).send(i18n.web_error_warp);
  }

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

  if (!(fmt in GENERATORS)) {
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
    console.log(`🚀 WARP Config Generator запущен: http://localhost:${PORT}`);
  });
}

module.exports = app;
