'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const app = require('../server');
const { FORMATS, FORMAT_PORT_PREFERENCES, resolveEndpoint } = require('../lib/ports');

// Helper: start server on a random port, make a request, close it
function request(method, path) {
  return new Promise((resolve, reject) => {
    const server = app.listen(0, () => {
      const { port } = server.address();
      const req = http.request(
        { hostname: '127.0.0.1', port, path, method },
        (res) => {
          let body = '';
          res.on('data', (chunk) => (body += chunk));
          res.on('end', () => {
            server.close();
            resolve({ status: res.statusCode, headers: res.headers, body });
          });
        },
      );
      req.on('error', (err) => {
        server.close();
        reject(err);
      });
      req.end();
    });
  });
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('GET /', () => {
  it('returns 200', async () => {
    const res = await request('GET', '/');
    assert.equal(res.status, 200);
  });

  it('contains the form', async () => {
    const res = await request('GET', '/');
    assert.ok(res.body.includes('<form'));
    assert.ok(res.body.includes('id="gen-form"'));
  });

  it('lists all formats', async () => {
    const res = await request('GET', '/');
    assert.ok(res.body.includes('WireGuard'));
    assert.ok(res.body.includes('AmneziaWG'));
    assert.ok(res.body.includes('Clash'));
    assert.ok(res.body.includes('WireSock'));
  });

  it('lists DNS servers', async () => {
    const res = await request('GET', '/');
    assert.ok(res.body.includes('Cloudflare'));
  });

  it('lists relay servers', async () => {
    const res = await request('GET', '/');
    assert.ok(res.body.includes('engage.cloudflareclient.com'));
  });

  it('displays Russian text', async () => {
    const res = await request('GET', '/');
    assert.ok(res.body.includes('Генератор'));
    assert.ok(res.body.includes('Сгенерировать'));
  });

  it('supports lang parameter', async () => {
    const res = await request('GET', '/?lang=en');
    assert.ok(res.body.includes('WARP Generator'));
    assert.ok(res.body.includes('Generate'));
  });
});

describe('GET /health', () => {
  it('returns ok', async () => {
    const res = await request('GET', '/health');
    assert.equal(res.status, 200);
    const data = JSON.parse(res.body);
    assert.deepEqual(data, { status: 'ok' });
  });
});

// ── Port resolution (lib/ports.js) ───────────────────────────────────────────

describe('FORMATS', () => {
  it('contains all four canonical format IDs', () => {
    for (const fmt of ['wireguard', 'amnezia', 'wiresock', 'clash']) {
      assert.ok(FORMATS.has(fmt), `FORMATS is missing "${fmt}"`);
    }
  });

  it('format keys match FORMAT_PORT_PREFERENCES', () => {
    const prefKeys = new Set(Object.keys(FORMAT_PORT_PREFERENCES));
    assert.deepEqual(prefKeys, FORMATS);
  });
});

describe('resolveEndpoint', () => {
  const multiRelay   = { host: 'relay.example.com', ports: [4500, 2408] };
  const single4500   = { host: 'relay.example.com', ports: [4500] };
  const single2408   = { host: 'relay.example.com', ports: [2408] };
  const exoticRelay  = { host: 'relay.example.com', ports: [1701] };

  it('wireguard prefers 2408 when relay supports both', () => {
    assert.equal(resolveEndpoint('wireguard', multiRelay), 'relay.example.com:2408');
  });

  it('amnezia prefers 4500 when relay supports both', () => {
    assert.equal(resolveEndpoint('amnezia', multiRelay), 'relay.example.com:4500');
  });

  it('wiresock prefers 2408 when relay supports both', () => {
    assert.equal(resolveEndpoint('wiresock', multiRelay), 'relay.example.com:2408');
  });

  it('clash prefers 2408 when relay supports both', () => {
    assert.equal(resolveEndpoint('clash', multiRelay), 'relay.example.com:2408');
  });

  it('falls back to next preferred port when first choice unavailable', () => {
    // wireguard prefers 2408, not supported → next is 4500
    assert.equal(resolveEndpoint('wireguard', single4500), 'relay.example.com:4500');
  });

  it('amnezia falls back to 2408 when 4500 unavailable', () => {
    assert.equal(resolveEndpoint('amnezia', single2408), 'relay.example.com:2408');
  });

  it('falls back to relay.ports[0] when no preferred port matches', () => {
    assert.equal(resolveEndpoint('wireguard', exoticRelay), 'relay.example.com:1701');
  });

  it('unknown format falls back gracefully using wireguard preferences', () => {
    const ep = resolveEndpoint('unknown_format', multiRelay);
    assert.match(ep, /^relay\.example\.com:\d+$/);
    const port = parseInt(ep.split(':')[1], 10);
    assert.ok(multiRelay.ports.includes(port));
  });

  it('all known formats produce a port within relay.ports', () => {
    for (const fmt of FORMATS) {
      const ep = resolveEndpoint(fmt, multiRelay);
      const port = parseInt(ep.split(':').pop(), 10);
      assert.ok(multiRelay.ports.includes(port), `${fmt}: port ${port} not in relay.ports`);
    }
  });
});
