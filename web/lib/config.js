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

module.exports = { loadConfigs };
