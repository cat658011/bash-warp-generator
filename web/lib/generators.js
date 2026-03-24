'use strict';

// ---------------------------------------------------------------------------
// AmneziaWG obfuscation payload (I1) — identical to the original bash script.
// ---------------------------------------------------------------------------
const AMNEZIA_I1 =
  '<b 0xc2000000011419fa4bb3599f336777de79f81ca9a8d80d91eeec0000' +
  '44c635cef024a885dcb66d1420a91a8c427e87d6cf8e08b563932f4494' +
  '12cddf77d3e2594ea1c7a183c238a89e9adb7ffa57c133e55c59bec101' +
  '634db90afb83f75b19fe703179e26a31902324c73f82d9354e1ed8da39' +
  'af610afcb27e6590a44341a0828e5a3d2f0e0f7b0945d7bf3402feea0' +
  'ee6332e19bdf48ffc387a97227aa97b205a485d282cd66d1c384bafd63' +
  'dc42f822c4df2109db5b5646c458236ddcc01ae1c493482128bc0830c9' +
  'e1233f0027a0d262f92b49d9d8abd9a9e0341f6e1214761043c021d7aa' +
  '8c464b9d865f5fbe234e49626e00712031703a3e23ef82975f014ee1e1' +
  'dc428521dc23ce7c6c13663b19906240b3efe403cf30559d798871557e' +
  '4e60e86c29ea4504ed4d9bb8b549d0e8acd6c334c39bb8fb42ede68fb' +
  '2aadf00cfc8bcc12df03602bbd4fe701d64a39f7ced112951a83b1dbbe' +
  '6cd696dd3f15985c1b9fef72fa8d0319708b633cc4681910843ce753fa' +
  'c596ed9945d8b839aeff8d3bf0449197bd0bb22ab8efd5d63eb4a95db' +
  '8d3ffc796ed5bcf2f4a136a8a36c7a0c65270d511aebac733e61d4140' +
  '50088a1c3d868fb52bc7e57d3d9fd132d78b740a6ecdc6c24936e92c28' +
  '672dbe00928d89b891865f885aeb4c4996d50c2bbbb7a99ab5de02ac89' +
  'b3308e57bcecf13f2da0333d1420e18b66b4c23d625d836b538fc0c221' +
  'd6bd7f566a31fa292b85be96041d8e0bfe655d5dc1afed23eb8f2b3446' +
  '561bbee7644325cc98d31cea38b865bdcc507e48c6ebdc7553be7bd6ab' +
  '963d5a14615c4b81da7081c127c791224853e2d19bafdc0d9f3f3a6de8' +
  '98d14abb0e2bc849917e0a599ed4a541268ad0e60ea4d147dc33d17fa8' +
  '2f22aa505ccb53803a31d10a7ca2fea0b290a52ee92c7bf4aab7cea4e3' +
  'c07b1989364eed87a3c6ba65188cd349d37ce4eefde9ec43bab4b4dc79' +
  'e03469c2ad6b902e28e0bbbbf696781ad4edf424ffb35ce0236d373629' +
  '008f142d04b5e08a124237e03e3149f4cdde92d7fae581a1ac332e26b2' +
  'c9c1a6bdec5b3a9c7a2a870f7a0c25fc6ce245e029b686e346c6d862a' +
  'd8df6d9b62474fbc31dbb914711f78074d4441f4e6e9edca3c52315a5c' +
  '0653856e23f681558d669f4a4e6915bcf42b56ce36cb7dd3983b0b1d6f' +
  'df0f8efddb68e7ca0ae9dd4570fe6978fbb524109f6ec957ca61f1767e' +
  'f74eb803b0f16abd0087cf2d01bc1db1c01d97ac81b3196c934586963f' +
  'e7cf2d310e0739621e8bd00dc23fded18576d8c8f285d7bb5f43b547af' +
  '3c76235de8b6f757f817683b2151600b11721219212bf27558edd439e7' +
  '3fce951f61d582320e5f4d6c315c71129b719277fc144bbe8ded25ab6d' +
  '29b6e189c9bd9b16538faf60cc2aab3c3bb81fc2213657f2dd0ceb9b3b' +
  '871e1423d8d3e8cc008721ef03b28e0ee7bb66b8f2a2ac01ef88df1f21' +
  'ed49bf1ce435df31ac34485936172567488812429c269b49ee9e3d99652' +
  'b51a7a614b7c460bf0d2d64d8349ded7345bedab1ea0a766a8470b1242' +
  'f38d09f7855a32db39516c2bd4bcc538c52fa3a90c8714d4b006a15d9c' +
  '7a7d04919a1cab48da7cce0d5de1f9e5f8936cffe469132991c6eb84c5' +
  '191d1bcf69f70c58d9a7b66846440a9f0eef25ee6ab62715b50ca7bef0' +
  'bc3013d4b62e1639b5028bdf757454356e9326a4c76dabfb497d451a3a' +
  '1d2dbd46ec283d255799f72dfe878ae25892e25a2542d3ca9018394d8c' +
  'a35b53ccd94947a8>';

// AmneziaWG constants
const AMNEZIA = {
  JC: 120, JMIN: 23, JMAX: 911,
  S1: 0, S2: 0,
  H1: 1, H2: 2, H3: 3, H4: 4,
};

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
    `Endpoint = ${params.endpoint}\n`;
  return { content: config, filename: 'warp-wireguard.conf' };
}

// ---------------------------------------------------------------------------
// AmneziaWG
// ---------------------------------------------------------------------------
function generateAmnezia(params) {
  const dns = params.dnsServers.join(', ');
  const allowed = params.allowedIps.join(', ');
  const config =
    '[Interface]\n' +
    `PrivateKey = ${params.privateKey}\n` +
    `S1 = ${AMNEZIA.S1}\n` +
    `S2 = ${AMNEZIA.S2}\n` +
    `Jc = ${AMNEZIA.JC}\n` +
    `Jmin = ${AMNEZIA.JMIN}\n` +
    `Jmax = ${AMNEZIA.JMAX}\n` +
    `H1 = ${AMNEZIA.H1}\n` +
    `H2 = ${AMNEZIA.H2}\n` +
    `H3 = ${AMNEZIA.H3}\n` +
    `H4 = ${AMNEZIA.H4}\n` +
    `MTU = ${params.mtu}\n` +
    `I1 = ${AMNEZIA_I1}\n` +
    `Address = ${params.clientIpv4}, ${params.clientIpv6}\n` +
    `DNS = ${dns}\n` +
    '\n' +
    '[Peer]\n' +
    `PublicKey = ${params.peerPublicKey}\n` +
    `AllowedIPs = ${allowed}\n` +
    `Endpoint = ${params.endpoint}\n`;
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
// Clash
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
    `    mtu: ${params.mtu}\n` +
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

const FORMAT_LABELS = {
  wireguard: { name: 'WireGuard', desc: 'Стандартный WireGuard конфиг (.conf)' },
  amnezia: { name: 'AmneziaWG', desc: 'AmneziaWG с защитой от DPI' },
  clash: { name: 'Clash', desc: 'Конфиг прокси Clash / Clash Meta' },
  wiresock: { name: 'WireSock', desc: 'WireSock для Windows' },
};

module.exports = { GENERATORS, FORMAT_LABELS, generateAmneziaDeeplink };
