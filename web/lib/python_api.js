'use strict';

const DEFAULT_BASE = 'http://127.0.0.1:8787';

function generationApiBase() {
  return process.env.GENERATION_API_URL || DEFAULT_BASE;
}

async function generateViaPython(payload) {
  const response = await fetch(`${generationApiBase()}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `Generation API failed: ${response.status}`);
  }
  return data;
}

module.exports = { generateViaPython };
