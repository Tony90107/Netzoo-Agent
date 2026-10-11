// Run: node this_file.mjs /path/to/netzoo_agent
// Bundles the real transport into a temporary directory; network is simulated.
import { createRequire } from 'node:module';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { resolve, join } from 'node:path';
const root = resolve(process.argv[2]);
const require = createRequire(join(root, 'desktop/package.json'));
const { build } = require('esbuild');
const dir = await mkdtemp(join(tmpdir(), 'netzoo-audit-transport-'));
try {
  const outfile = join(dir, 'session.cjs');
  await build({ entryPoints: [join(root, 'desktop/src/transport/session.ts')],
    bundle: true, platform: 'node', format: 'cjs', outfile });
  const { SessionSocket, emptySession } = require(outfile);
  class FakeSocket {
    constructor() { this.readyState = 3; }
    send(text) { if (this.readyState !== 1) return; this.sent = text; }
    close() {}
  }
  globalThis.WebSocket = FakeSocket;
  let state = { ...emptySession('audit'), connection: 'reconnecting', view: { prompt_kind: 'main' } };
  const client = new SessionSocket({ baseUrl: 'http://127.0.0.1:1', socketUrl: 'ws://127.0.0.1:1', token: 'test' },
    'audit', apply => { state = apply(state); });
  client.open();
  client.answer('Use my data');
  console.log(JSON.stringify({ case: 'F5_send_during_disconnect', view: state.view,
    busy: state.busy, entries: state.entries.map(x => x.text), sent: client.socket.sent ?? null }));
  globalThis.fetch = async () => ({ ok: false, status: 503, json: async () => ({ detail: 'unavailable' }) });
  await client.cancel();
  console.log(JSON.stringify({ case: 'F6_cancel_http_503', lastEntry: state.entries.at(-1),
    errorEntries: state.entries.filter(x => x.kind === 'error').length }));
} finally {
  await rm(dir, { recursive: true, force: true });
}
