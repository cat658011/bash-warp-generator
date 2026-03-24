'use strict';

const crypto = require('node:crypto');

const API_BASE = 'https://api.cloudflareclient.com/v0i1909051800';
const TIMEOUT_MS = 30000;

function generateKeys() {
  const { publicKey, privateKey } = crypto.generateKeyPairSync('x25519');
  const privDer = privateKey.export({ type: 'pkcs8', format: 'der' });
  const pubDer = publicKey.export({ type: 'spki', format: 'der' });

  // Raw 32-byte X25519 keys are at the end of the DER encoding
  const privRaw = privDer.subarray(privDer.length - 32);
  const pubRaw = pubDer.subarray(pubDer.length - 32);

  return {
    privateKey: privRaw.toString('base64'),
    publicKey: pubRaw.toString('base64'),
  };
}

async function registerWarp() {
  const keys = generateKeys();
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');

  // 1. Register a new device
  const regResp = await fetch(`${API_BASE}/reg`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'okhttp/3.12.1',
    },
    body: JSON.stringify({
      install_id: '',
      tos: now,
      key: keys.publicKey,
      fcm_token: '',
      type: 'ios',
      locale: 'en_US',
    }),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });

  if (!regResp.ok) {
    throw new Error(`WARP registration failed: ${regResp.status}`);
  }

  const regData = await regResp.json();
  const accountId = regData.result.id;
  const token = regData.result.token;

  // 2. Enable WARP on the account
  const cfgResp = await fetch(`${API_BASE}/reg/${accountId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'User-Agent': 'okhttp/3.12.1',
    },
    body: JSON.stringify({ warp_enabled: true }),
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });

  if (!cfgResp.ok) {
    throw new Error(`WARP activation failed: ${cfgResp.status}`);
  }

  const cfgData = await cfgResp.json();
  const peer = cfgData.result.config.peers[0];
  const addresses = cfgData.result.config.interface.addresses;

  return {
    privateKey: keys.privateKey,
    publicKey: keys.publicKey,
    peerPublicKey: peer.public_key,
    clientIpv4: addresses.v4,
    clientIpv6: addresses.v6,
  };
}

module.exports = { generateKeys, registerWarp };
