/**
 * Local preview of the web app: serves Index.html with a google.script.run
 * shim that calls Code.gs (running on the stubs in gas-stub.js).
 *
 *   node dev/server.js [--port 8080] [--now 2026-10-22T22:00:00Z] [--cache file] [--dist] [--fake-update]
 *
 * Sleeper logins/mutations are faked (never sent): log in with any
 * identifier + password "demo", then code "1234". Reads hit the real APIs.
 * The page's own fetches to Sleeper's GraphQL are rerouted to this server, so
 * the preview can never send a real login, whatever a test types into it.
 * Set DEMO_USER_ID to the Sleeper user id the fake login should resolve to.
 * --dist runs the single-file build (dist/SleeperAutopilot.gs) and serves its own
 * page, like the real deployment. Each request gets a fresh copy of the script
 * (as on Google) with storage kept between requests, so installed updates load.
 * --fake-update pretends GitHub has a newer build ("v99", visibly marked).
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const { loadGas } = require('./gas-stub');

const arg = (name, dflt) => {
  const i = process.argv.indexOf('--' + name);
  return i > 0 ? process.argv[i + 1] : dflt;
};
const port = Number(arg('port', 8080));
const nowArg = arg('now', null);
const now = nowArg ? (() => Date.parse(nowArg)) : (() => Date.now());

const b64 = (o) => Buffer.from(JSON.stringify(o)).toString('base64url');
const fakeToken = () => [b64({ alg: 'none' }), b64({ user_id: process.env.DEMO_USER_ID,
  exp: Math.floor(now() / 1000) + 60 * 86400 }), 'sig'].join('.');

const fakeUpdate = process.argv.includes('--fake-update');
const useDist = process.argv.includes('--dist');
const dist = path.join(__dirname, '..', 'dist', 'SleeperAutopilot.gs');

function fakeRemoteBuild() {
  return fs.readFileSync(dist, 'utf8')
    .replace(/\nvar BUILD_INFO = .*;\n/, '\nvar BUILD_INFO = ' + JSON.stringify({ id: 'preview', version: 99,
      title: 'Preview update', notes: [{ title: 'Preview update', items: ['Something new', 'Something better'] }] }) + ';\n')
    .replace('Sleeper Autopilot</div>\\n', 'Sleeper Autopilot v99</div>\\n');
}

function fakeGql(body) {
  const q = body.query;
  if (q.includes('league_transactions_filtered')) return { data: { league_transactions_filtered: [] } };
  if (q.includes('login_context')) {
    return { data: { login_context_by_email_or_phone_or_username: {
      user_id: process.env.DEMO_USER_ID, masked_email: 'j***@example.com' } } };
  }
  if (q.includes('login(')) {
    const p = body.variables.p;
    if (p === '1234') return { data: { login: { token: fakeToken() } } };
    if (p === 'demo') return { errors: [{ message: 'code required', code: 'code_verification_required' }], data: null };
    return { data: { login: null } };
  }
  if (q.includes('create_verification_code')) return { data: { create_verification_code: true } };
  if (q.includes('roster_update_starters')) return { data: { roster_update_starters: { roster_id: body.variables.rosterId } } };
  if (q.includes('submit_waiver_claim')) return { data: { submit_waiver_claim: { transaction_id: 'demo' } } };
  return undefined;
}

let props = {};  // the user's script storage, kept between requests
function freshGas() {
  return loadGas({
    now,
    props,
    file: useDist ? dist : undefined,
    fetch(url) {
      if (fakeUpdate && url.includes('raw.githubusercontent.com') && url.endsWith('SleeperAutopilot.gs')) {
        return { body: fakeRemoteBuild() };
      }
      return undefined;
    },
    cacheFile: arg('cache', path.join(__dirname, '.cache.json')),
    gql: fakeGql,
  });
}
function withGas(fn) {
  const gas = freshGas();
  try { return fn(gas); } finally { props = gas.__props._data; }
}

const shim = `<script>
const realFetch = window.fetch.bind(window);
window.fetch = (url, init) => realFetch(String(url).startsWith('https://api.sleeper.app/graphql') ? '/sleeper-graphql' : url, init);
window.google = { script: { run: (function make(ok, fail) {
  return new Proxy({}, { get(_, fn) {
    if (fn === 'withSuccessHandler') return (h) => make(h, fail);
    if (fn === 'withFailureHandler') return (h) => make(ok, h);
    return (...args) => fetch('/api/' + fn, { method: 'POST', body: JSON.stringify(args) })
      .then((r) => r.json()).then((r) => r.error ? fail && fail(new Error(r.error)) : ok && ok(r.value));
  } });
})() } };
</script>`;

http.createServer((req, res) => {
  if (req.method === 'POST' && req.url === '/sleeper-graphql') {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      const out = fakeGql(JSON.parse(body)) || { errors: [{ message: 'not faked in preview' }] };
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(out));
    });
    return;
  }
  if (req.method === 'POST' && req.url.startsWith('/api/')) {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      const fn = req.url.slice(5);
      let out;
      try {
        out = withGas((gas) => {
          if (fn.endsWith('_') || typeof gas[fn] !== 'function') throw new Error('No such function: ' + fn);
          return { value: gas[fn](...JSON.parse(body || '[]')) };
        });
      } catch (e) {
        out = { error: e.message };
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(out));
    });
    return;
  }
  const page = useDist ? withGas((gas) => gas.doGet().getContent())
                       : fs.readFileSync(path.join(__dirname, '..', 'Index.html'), 'utf8');
  const html = page.replace('<script>', shim + '<script>');
  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end(html);
}).listen(port, () => console.log(`preview on http://localhost:${port}`));
