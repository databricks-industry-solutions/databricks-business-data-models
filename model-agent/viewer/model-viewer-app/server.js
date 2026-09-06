#!/usr/bin/env node
'use strict';

const express = require('express');
const path = require('path');
const fs = require('fs');
const zlib = require('zlib');

const app = express();
const PORT = process.env.PORT || 8000;

const publicDir = path.join(__dirname, 'public');
const indexHtml = path.join(publicDir, 'index.html');

app.get('/api/health', (req, res) => {
  res.json({ ok: true });
});

// The bundled model ships gzipped (public/model.json.gz, ~3 MB) to keep the
// deployed artifact small. A raw public/model.json is also honoured if present.
const rawModelPath = path.join(publicDir, 'model.json');
const gzModelPath = path.join(publicDir, 'model.json.gz');
let gzBytesCache = null, rawBytesCache = null;
function hasBundledModel() { return fs.existsSync(gzModelPath) || fs.existsSync(rawModelPath); }
function gzBytes() { if (!gzBytesCache && fs.existsSync(gzModelPath)) gzBytesCache = fs.readFileSync(gzModelPath); return gzBytesCache; }

app.get('/model.json', (req, res) => {
  const acceptsGzip = (req.headers['accept-encoding'] || '').includes('gzip');
  res.set('Content-Type', 'application/json; charset=utf-8');
  res.set('Cache-Control', 'public, max-age=300');
  if (fs.existsSync(gzModelPath)) {
    if (acceptsGzip) { res.set('Content-Encoding', 'gzip'); return res.end(gzBytes()); }
    if (!rawBytesCache) rawBytesCache = zlib.gunzipSync(gzBytes());
    return res.end(rawBytesCache);
  }
  if (fs.existsSync(rawModelPath)) {
    if (acceptsGzip) {
      if (!gzBytesCache) gzBytesCache = zlib.gzipSync(fs.readFileSync(rawModelPath));
      res.set('Content-Encoding', 'gzip'); return res.end(gzBytesCache);
    }
    return res.sendFile(rawModelPath);
  }
  res.status(404).json({ error: 'not found' });
});

app.get('/api/bundled-models', (req, res) => {
  const models = [];
  if (hasBundledModel()) models.push({ path: '/model.json', label: 'ddx_gtm_small2_v7' });
  res.json({ models });
});

app.use('/static', express.static(path.join(publicDir, 'static')));
app.get(/.*/, (req, res) => res.sendFile(indexHtml));

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Model Viewer running on http://0.0.0.0:${PORT}`);
});
