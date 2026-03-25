'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const app = require('../server');
const { FORMATS, resolveEndpoint } = require('../lib/ports');
const originalWindowMs = process.env.WEB_RATE_LIMIT_WINDOW_MS;
const originalMaxRequests = process.env.WEB_RATE_LIMIT_MAX_REQUESTS;

// Helper: start server on a random port, make a request, close it
function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const server = app.listen(0, () => {
      const { port } = server.address();
      const payload = body ? JSON.stringify(body) : null;
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port,
          path,
          method,
          headers: payload
            ? {
              'Content-Type': 'application/json',
              'Content-Length': Buffer.byteLength(payload),
            }
            : undefined,
        },
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
      if (payload) {
        req.write(payload);
      }
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

describe('POST /generate anti-flood', () => {
  it('returns 429 when request limit is exceeded', async () => {
    process.env.WEB_RATE_LIMIT_WINDOW_MS = '60000';
    process.env.WEB_RATE_LIMIT_MAX_REQUESTS = '0';
    try {
      const res = await request('POST', '/generate', { lang: 'en' });
      assert.equal(res.status, 429);
      const data = JSON.parse(res.body);
      assert.equal(data.error, 'Too many requests. Please try again shortly.');
    } finally {
      if (originalWindowMs === undefined) {
        delete process.env.WEB_RATE_LIMIT_WINDOW_MS;
      } else {
        process.env.WEB_RATE_LIMIT_WINDOW_MS = originalWindowMs;
      }
      if (originalMaxRequests === undefined) {
        delete process.env.WEB_RATE_LIMIT_MAX_REQUESTS;
      } else {
        process.env.WEB_RATE_LIMIT_MAX_REQUESTS = originalMaxRequests;
      }
    }
  });
});

// ── Port resolution (lib/ports.js) ───────────────────────────────────────────

describe('FORMATS', () => {
  it('contains all four canonical format IDs', () => {
    for (const fmt of ['wireguard', 'amnezia', 'wiresock', 'clash']) {
      assert.ok(FORMATS.has(fmt), `FORMATS is missing "${fmt}"`);
    }
  });

  it('wireguard is not an AWG format (uses ports[0])', () => {
    const dualRelay = { host: 'relay.example.com', ports: [2408, 4500] };
    assert.equal(resolveEndpoint('wireguard', dualRelay), 'relay.example.com:2408');
  });
});

describe('resolveEndpoint — index-based', () => {
  // ports are [wireguard_port, amneziawg_port]
  const dualRelay   = { host: 'relay.example.com', ports: [2408, 4500] };
  const singleRelay = { host: 'relay.example.com', ports: [4500] };

  it('wireguard uses ports[0]', () => {
    assert.equal(resolveEndpoint('wireguard', dualRelay), 'relay.example.com:2408');
  });

  it('amnezia uses ports[1]', () => {
    assert.equal(resolveEndpoint('amnezia', dualRelay), 'relay.example.com:4500');
  });

  it('wiresock uses ports[1]', () => {
    assert.equal(resolveEndpoint('wiresock', dualRelay), 'relay.example.com:4500');
  });

  it('clash uses ports[1]', () => {
    assert.equal(resolveEndpoint('clash', dualRelay), 'relay.example.com:4500');
  });

  it('amnezia falls back to ports[0] for single-port relay', () => {
    assert.equal(resolveEndpoint('amnezia', singleRelay), 'relay.example.com:4500');
  });

  it('wiresock falls back to ports[0] for single-port relay', () => {
    assert.equal(resolveEndpoint('wiresock', singleRelay), 'relay.example.com:4500');
  });

  it('unknown format uses ports[0]', () => {
    assert.equal(resolveEndpoint('unknown_format', dualRelay), 'relay.example.com:2408');
  });

  it('all known formats produce a port within relay.ports', () => {
    for (const fmt of FORMATS) {
      const ep = resolveEndpoint(fmt, dualRelay);
      const port = parseInt(ep.split(':').pop(), 10);
      assert.ok(dualRelay.ports.includes(port), `${fmt}: port ${port} not in relay.ports`);
    }
  });
});
