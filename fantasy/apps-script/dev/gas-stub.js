/**
 * Minimal stand-ins for the Apps Script services Code.gs uses, so it can run
 * under Node for tests and local previews. Limits mirror the real quotas
 * (9 KB property values, 100 KB cache values) so chunking bugs show up here.
 *
 * Safety: every Sleeper GraphQL request is intercepted. Mutations and logins
 * are never sent to Sleeper; tests decide what they return via `gql`. Apps
 * Script API calls (self-update) are never sent either: answer them via `fetch`.
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const { execFileSync } = require('child_process');

function httpSync(url, params) {
  const args = ['-sS', '-L', '--max-time', '120', '-X', (params.method || 'get').toUpperCase(),
                '-w', '\n%{http_code}', '-A', 'Mozilla/5.0 (compatible; Google-Apps-Script)'];
  for (const [k, v] of Object.entries(params.headers || {})) args.push('-H', `${k}: ${v}`);
  if (params.payload) args.push('-H', `Content-Type: ${params.contentType}`, '--data-binary', params.payload);
  args.push(url);
  const out = execFileSync('curl', args, { maxBuffer: 200 * 1024 * 1024 }).toString('utf8');
  const cut = out.lastIndexOf('\n');
  return { code: Number(out.slice(cut + 1)), text: out.slice(0, cut) };
}

function parseCsv(text) {
  const rows = [];
  let row = [], field = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') { if (text[i + 1] === '"') { field += '"'; i++; } else q = false; } else field += c;
    } else if (c === '"') q = true;
    else if (c === ',') { row.push(field); field = ''; }
    else if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; }
    else if (c !== '\r') field += c;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  return rows;
}

function makeCache(file, now) {
  let data = {};
  if (file && fs.existsSync(file)) data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const save = () => file && fs.writeFileSync(file, JSON.stringify(data));
  const live = (k) => data[k] && data[k].exp > now() ? data[k].v : null;
  const put = (k, v, s) => {
    if (Buffer.byteLength(v) > 100 * 1024) throw new Error(`cache value too large for ${k}`);
    data[k] = { v, exp: now() + (s || 600) * 1000 };
  };
  return {
    get: (k) => live(k),
    getAll: (ks) => Object.fromEntries(ks.filter((k) => live(k) !== null).map((k) => [k, live(k)])),
    put: (k, v, s) => { put(k, v, s); save(); },
    putAll: (m, s) => { for (const [k, v] of Object.entries(m)) put(k, v, s); save(); },
    remove: (k) => { delete data[k]; save(); },
    _data: data,
  };
}

function makeProps(initial) {
  const data = { ...(initial || {}) };
  const check = () => {
    for (const [k, v] of Object.entries(data)) {
      if (Buffer.byteLength(v) > 9 * 1024) throw new Error(`property value too large: ${k}`);
    }
    const total = Object.entries(data).reduce((n, [k, v]) => n + Buffer.byteLength(k + v), 0);
    if (total > 500 * 1024) throw new Error('property store over 500 KB');
  };
  return {
    getProperty: (k) => (k in data ? data[k] : null),
    setProperty: (k, v) => { data[k] = String(v); check(); },
    setProperties: (m) => { for (const [k, v] of Object.entries(m)) data[k] = String(v); check(); },
    deleteProperty: (k) => { delete data[k]; },
    getProperties: () => ({ ...data }),
    _data: data,
  };
}

/**
 * Load Code.gs into a sandbox.
 * opts.gql(body, headers) -> object | undefined: answer for intercepted GraphQL
 *   calls (undefined = let read-only queries through, never mutations/logins).
 * opts.now: function returning epoch ms (lets tests rewind time).
 */
function loadGas(opts = {}) {
  const now = opts.now || (() => Date.now());
  const calls = { gql: [], fetch: [] };
  const triggers = [];
  const cache = makeCache(opts.cacheFile, now);
  const props = makeProps(opts.props);
  const RealDate = Date;
  class FakeDate extends RealDate {
    constructor(...a) { if (a.length) super(...a); else super(now()); }
    static now() { return now(); }
  }
  const gas = {
    UrlFetchApp: {
      fetch(url, params = {}) {
        calls.fetch.push(url);
        const hooked = opts.fetch ? opts.fetch(url, params) : undefined;
        if (hooked !== undefined) {
          const text = typeof hooked.body === 'string' ? hooked.body : JSON.stringify(hooked.body || {});
          return { getResponseCode: () => hooked.code || 200, getContentText: () => text };
        }
        if (url.startsWith('https://script.googleapis.com/')) {
          throw new Error('test harness refused to call the Apps Script API: ' + url);
        }
        if (url.startsWith('https://api.sleeper.app/graphql')) {
          const body = JSON.parse(params.payload);
          calls.gql.push({ body, headers: params.headers || {} });
          const canned = opts.gql ? opts.gql(body, params.headers || {}) : undefined;
          let res;
          if (canned !== undefined) res = { code: canned.__status || 200, text: JSON.stringify(canned) };
          else if (/^\s*mutation|login\(/.test(body.query)) {
            throw new Error('test harness refused to send a Sleeper login/mutation: ' + body.query.slice(0, 60));
          } else res = httpSync(url, params);
          return { getResponseCode: () => res.code, getContentText: () => res.text };
        }
        const res = httpSync(url, params);
        return { getResponseCode: () => res.code, getContentText: () => res.text };
      },
    },
    CacheService: { getUserCache: () => cache },
    PropertiesService: { getUserProperties: () => props },
    LockService: { getUserLock: () => ({ tryLock: () => true, releaseLock() {} }) },
    ScriptApp: {
      getOAuthToken: () => 'ya29.test',
      getScriptId: () => 'SCRIPT_ID',
      getService: () => ({ getUrl: () => 'https://script.google.com/macros/s/DEPLOY_ID/exec' }),
      getProjectTriggers: () => triggers.slice(),
      newTrigger: (fn) => ({ timeBased: () => ({ everyMinutes: (n) => ({ create: () => {
        const t = { getHandlerFunction: () => fn, minutes: n }; triggers.push(t); return t; } }) }) }),
      deleteTrigger: (t) => triggers.splice(triggers.indexOf(t), 1),
    },
    HtmlService: {
      createHtmlOutput: (content) => {
        const out = { setTitle: () => out, addMetaTag: () => out, getContent: () => content };
        return out;
      },
      createHtmlOutputFromFile: (name) => {
        const content = fs.readFileSync(path.join(__dirname, '..', name + '.html'), 'utf8');
        const out = { setTitle: () => out, addMetaTag: () => out, getContent: () => content };
        return out;
      },
    },
    Utilities: {
      sleep: (ms) => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, Math.min(ms, 50)),
      base64Decode: (s) => Array.from(Buffer.from(s, 'base64')),
      newBlob: (bytes) => ({ getDataAsString: () => Buffer.from(bytes).toString('utf8') }),
      parseCsv,
    },
    console, Date: FakeDate, Map, JSON, Math,
  };
  const ctx = vm.createContext(gas);
  const file = opts.file || path.join(__dirname, '..', 'Code.gs');
  vm.runInContext(fs.readFileSync(file, 'utf8'), ctx, { filename: path.basename(file) });
  ctx.__calls = calls;
  ctx.__props = props;
  ctx.__cache = cache;
  ctx.__triggers = triggers;
  return ctx;
}

module.exports = { loadGas, parseCsv };
