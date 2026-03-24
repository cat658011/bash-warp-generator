'use strict';

const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const app = require('../server');

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
