'use strict';

const { loadWarpParams } = require('./config');
const { FORMATS } = require('./ports');

// ---------------------------------------------------------------------------
// Load AmneziaWG parameters from shared config
// ---------------------------------------------------------------------------
const _warpParams = loadWarpParams();
const _amneziaConf = _warpParams.amnezia;
const _wiresockConf = _warpParams.wiresock;
const _clashConf = _warpParams.clash;
const _i1Payloads = _warpParams.i1_payloads;
const _persistentKeepalive = _warpParams.persistent_keepalive || 25;

const AMNEZIA = {
  JC: _amneziaConf.Jc,
  JMIN: _amneziaConf.Jmin,
  JMAX: _amneziaConf.Jmax,
  S1: _amneziaConf.S1,
  S2: _amneziaConf.S2,
  H1: _amneziaConf.H1,
  H2: _amneziaConf.H2,
  H3: _amneziaConf.H3,
  H4: _amneziaConf.H4,
};

const WIRESOCK = {
  JC: _wiresockConf.Jc,
  JMIN: _wiresockConf.Jmin,
  JMAX: _wiresockConf.Jmax,
  S1: _wiresockConf.S1,
  S2: _wiresockConf.S2,
  H1: _wiresockConf.H1,
  H2: _wiresockConf.H2,
  H3: _wiresockConf.H3,
  H4: _wiresockConf.H4,
  MASKING: _wiresockConf.masking,
};

const CLASH = {
  JC: _clashConf.Jc,
  JMIN: _clashConf.Jmin,
  JMAX: _clashConf.Jmax,
  S1: _clashConf.S1,
  S2: _clashConf.S2,
  H1: _clashConf.H1,
  H2: _clashConf.H2,
  H3: _clashConf.H3,
  H4: _clashConf.H4,
  RESERVED: _clashConf.reserved,
  I1: _i1Payloads[0],
};

function randomI1() {
  return _i1Payloads[Math.floor(Math.random() * _i1Payloads.length)];
}

// ---------------------------------------------------------------------------
// WireGuard
// ---------------------------------------------------------------------------
function generateWireGuard(params) {
  const dns = params.dnsServers.join(', ');
  const allowed = params.allowedIps.join(', ');
  const config =
    '[Interface]\n' +
    `PrivateKey = ${params.privateKey}\n` +
    `Address = ${params.clientIpv4}/32, ${params.clientIpv6}/128\n` +
    `DNS = ${dns}\n` +
    `MTU = ${params.mtu}\n` +
    '\n' +
    '[Peer]\n' +
    `PublicKey = ${params.peerPublicKey}\n` +
    `AllowedIPs = ${allowed}\n` +
    `Endpoint = ${params.endpoint}\n` +
    `PersistentKeepalive = ${_persistentKeepalive}\n`;
  return { content: config, filename: 'warp-wireguard.conf' };
}

// ---------------------------------------------------------------------------
// AmneziaWG
// ---------------------------------------------------------------------------
function generateAmnezia(params) {
  const dns = params.dnsServers.join(', ');
  const allowed = params.allowedIps.join(', ');
  const i1 = randomI1();
  const config =
    '[Interface]\n' +
    `PrivateKey = ${params.privateKey}\n` +
    `Address = ${params.clientIpv4}, ${params.clientIpv6}\n` +
    `DNS = ${dns}\n` +
    `MTU = ${params.mtu}\n` +
    `S1 = ${AMNEZIA.S1}\n` +
    `S2 = ${AMNEZIA.S2}\n` +
    `Jc = ${AMNEZIA.JC}\n` +
    `Jmin = ${AMNEZIA.JMIN}\n` +
    `Jmax = ${AMNEZIA.JMAX}\n` +
    `H1 = ${AMNEZIA.H1}\n` +
    `H2 = ${AMNEZIA.H2}\n` +
    `H3 = ${AMNEZIA.H3}\n` +
    `H4 = ${AMNEZIA.H4}\n` +
    `I1 = ${i1}\n` +
    '\n' +
    '[Peer]\n' +
    `PublicKey = ${params.peerPublicKey}\n` +
    `AllowedIPs = ${allowed}\n` +
    `Endpoint = ${params.endpoint}\n` +
    `PersistentKeepalive = ${_persistentKeepalive}\n`;
  return { content: config, filename: 'warp-amnezia.conf' };
}

function generateAmneziaDeeplink(params) {
  const { content: confText } = generateAmnezia(params);
  const lastColon = params.endpoint.lastIndexOf(':');
  const host = params.endpoint.substring(0, lastColon);
  const port = params.endpoint.substring(lastColon + 1);

  const awgJson = {
    H1: String(AMNEZIA.H1),
    H2: String(AMNEZIA.H2),
    H3: String(AMNEZIA.H3),
    H4: String(AMNEZIA.H4),
    Jc: String(AMNEZIA.JC),
    Jmax: String(AMNEZIA.JMAX),
    Jmin: String(AMNEZIA.JMIN),
    S1: String(AMNEZIA.S1),
    S2: String(AMNEZIA.S2),
    allowed_ips: params.allowedIps,
    client_ip: `${params.clientIpv4}, ${params.clientIpv6}`,
    client_priv_key: params.privateKey,
    config: confText.replace(/\n/g, '\r\n'),
    hostName: host,
    mtu: params.mtu,
    port: parseInt(port, 10),
    server_pub_key: params.peerPublicKey,
  };

  const container = {
    containers: [
      {
        container: 'amnezia-awg',
        awg: {
          isThirdPartyConfig: true,
          last_config: JSON.stringify(awgJson),
          port,
          transport_proto: 'udp',
        },
      },
    ],
    defaultContainer: 'amnezia-awg',
    description: 'Cloudflare WARP',
    hostName: host,
  };

  const encoded = Buffer.from(JSON.stringify(container)).toString('base64');
  return `vpn://${encoded}`;
}

// ---------------------------------------------------------------------------
// Clash / Mihomo
// ---------------------------------------------------------------------------
function generateClash(params) {
  const lastColon = params.endpoint.lastIndexOf(':');
  const host = params.endpoint.substring(0, lastColon);
  const port = params.endpoint.substring(lastColon + 1);
  const dnsLines = params.dnsServers.map((s) => `      - ${s}`).join('\n');
  const fullTunnel = params.allowedIps.includes('0.0.0.0/0');

  let rules;
  if (fullTunnel) {
    rules = '  - MATCH,WARP';
  } else {
    const lines = params.allowedIps.map((cidr) => {
      const keyword = cidr.includes(':') ? 'IP-CIDR6' : 'IP-CIDR';
      return `  - ${keyword},${cidr},WARP`;
    });
    lines.push('  - MATCH,DIRECT');
    rules = lines.join('\n');
  }

  const config =
    'port: 7890\n' +
    'socks-port: 7891\n' +
    'allow-lan: false\n' +
    'mode: rule\n' +
    'log-level: info\n' +
    '\n' +
    'dns:\n' +
    '  enable: true\n' +
    '  nameserver:\n' +
    `${dnsLines}\n` +
    '\n' +
    'proxies:\n' +
    '  - name: WARP\n' +
    '    type: wireguard\n' +
    `    server: ${host}\n` +
    `    port: ${port}\n` +
    `    ip: ${params.clientIpv4}\n` +
    `    ipv6: ${params.clientIpv6}\n` +
    `    private-key: ${params.privateKey}\n` +
    `    public-key: ${params.peerPublicKey}\n` +
    '    udp: true\n' +
    '    remote-dns-resolve: true\n' +
    '    reserved: ' + JSON.stringify(CLASH.RESERVED) + '\n' +
    `    mtu: ${params.mtu}\n` +
    '    amnezia-wg-option:\n' +
    `      jc: ${CLASH.JC}\n` +
    `      jmin: ${CLASH.JMIN}\n` +
    `      jmax: ${CLASH.JMAX}\n` +
    `      s1: ${CLASH.S1}\n` +
    `      s2: ${CLASH.S2}\n` +
    `      h1: ${CLASH.H1}\n` +
    `      h2: ${CLASH.H2}\n` +
    `      h3: ${CLASH.H3}\n` +
    `      h4: ${CLASH.H4}\n` +
    `      i1: ${CLASH.I1}\n` +
    '\n' +
    'proxy-groups:\n' +
    '  - name: Proxy\n' +
    '    type: select\n' +
    '    proxies:\n' +
    '      - WARP\n' +
    '      - DIRECT\n' +
    '\n' +
    'rules:\n' +
    `${rules}\n`;
  return { content: config, filename: 'warp-clash.yaml' };
}

// ---------------------------------------------------------------------------
// WireSock
// ---------------------------------------------------------------------------
function generateWireSock(params) {
  const dns = params.dnsServers.join(', ');
  const fullTunnel = params.allowedIps.includes('0.0.0.0/0');

  const lines = [
    '[Interface]',
    `PrivateKey = ${params.privateKey}`,
    `Address = ${params.clientIpv4}/32`,
    `DNS = ${dns}`,
    `MTU = ${params.mtu}`,
    `S1 = ${WIRESOCK.S1}`,
    `S2 = ${WIRESOCK.S2}`,
    `Jc = ${WIRESOCK.JC}`,
    `Jmin = ${WIRESOCK.JMIN}`,
    `Jmax = ${WIRESOCK.JMAX}`,
    `H1 = ${WIRESOCK.H1}`,
    `H2 = ${WIRESOCK.H2}`,
    `H3 = ${WIRESOCK.H3}`,
    `H4 = ${WIRESOCK.H4}`,
    '',
    '# Protocol masking',
    `Id = ${WIRESOCK.MASKING.Id}`,
    `Ip = ${WIRESOCK.MASKING.Ip}`,
    `Ib = ${WIRESOCK.MASKING.Ib}`,
    '',
    '[Peer]',
    `PublicKey = ${params.peerPublicKey}`,
    `Endpoint = ${params.endpoint}`,
  ];

  if (fullTunnel) {
    lines.push('AllowedIPs = 0.0.0.0/0');
  } else {
    for (const cidr of params.allowedIps) {
      if (!cidr.includes(':')) {
        lines.push(`AllowedIPs = ${cidr}`);
      }
    }
  }

  lines.push(`PersistentKeepalive = ${_persistentKeepalive}`);

  return { content: lines.join('\n') + '\n', filename: 'warp-wiresock.conf' };
}

// ---------------------------------------------------------------------------
// Registry
// ---------------------------------------------------------------------------
const GENERATORS = {
  wireguard: generateWireGuard,
  amnezia: generateAmnezia,
  clash: generateClash,
  wiresock: generateWireSock,
};

// Static format metadata. Descriptions are resolved from i18n at render time.
const FORMAT_LABELS = {
  wireguard: { name: 'WireGuard', descKey: 'fmt_wireguard_desc' },
  amnezia: { name: 'AmneziaWG', descKey: 'fmt_amnezia_desc' },
  clash: { name: 'Clash', descKey: 'fmt_clash_desc' },
  wiresock: { name: 'WireSock', descKey: 'fmt_wiresock_desc' },
};

module.exports = { GENERATORS, FORMAT_LABELS, FORMATS, generateAmneziaDeeplink };
