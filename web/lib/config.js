'use strict';

const fs = require('node:fs');
const path = require('node:path');

const CONFIGS_DIR = path.resolve(__dirname, '..', '..', 'configs');

function loadJson(filename) {
  const filePath = path.join(CONFIGS_DIR, filename);
  return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
}

function loadConfigs() {
  return {
    dnsServers: loadJson('dns_servers.json'),
    relayServers: loadJson('relay_servers.json'),
    routingServices: loadJson('routing_services.json'),
  };
}

function loadWarpParams() {
  return loadJson('warp_params.json');
}

function loadI18n(lang) {
  const code = lang || process.env.BOT_LANG || 'ru';
  const filePath = path.join(CONFIGS_DIR, 'i18n', `${code}.json`);
  if (fs.existsSync(filePath)) {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  }
  // Fallback to Russian
  return JSON.parse(
    fs.readFileSync(path.join(CONFIGS_DIR, 'i18n', 'ru.json'), 'utf-8'),
  );
}

module.exports = { loadConfigs, loadWarpParams, loadI18n };
