#!/usr/bin/env node
/**
 * Build Ganjafy V2 Worker
 * Combines: data layer + HTML + frontend JS + backend
 * into single cloudflare-worker-ganjafy.js
 * 
 * Usage: node build-ganjafy-v2.js
 */
const fs = require('fs');
const path = require('path');

const dir = __dirname;

// Read components
const dataLayer = fs.readFileSync(path.join(dir, 'cloudflare-worker-ganjafy-v2.js'), 'utf8');
const htmlFile = fs.readFileSync(path.join(dir, 'ganjafy-v2-html.js'), 'utf8');
const jsFile = fs.readFileSync(path.join(dir, 'ganjafy-v2-frontend.js'), 'utf8');
const backend = fs.readFileSync(path.join(dir, 'ganjafy-v2-backend.js'), 'utf8');

// Extract HTML template string
const htmlMatch = htmlFile.match(/export const DASHBOARD_HTML = `([\s\S]*?)`;/);
if (!htmlMatch) { console.error('Failed to extract HTML'); process.exit(1); }
const html = htmlMatch[1];

// Extract frontend JS string
const jsMatch = jsFile.match(/export const FRONTEND_JS = `([\s\S]*?)`;/);
if (!jsMatch) { console.error('Failed to extract JS'); process.exit(1); }
const js = jsMatch[1];

// Combine HTML + inline script
const fullHTML = html.replace('</body>', js + '\n</body>');

// Build final worker (string concatenation to avoid template literal issues)
const parts = [];
parts.push(dataLayer);
parts.push('');
parts.push('// ═══════════════════════════════════════════════════════════════');
parts.push('// HTML DASHBOARD (V2)');
parts.push('// ═══════════════════════════════════════════════════════════════');
parts.push('');
parts.push('const DASHBOARD_HTML = `' + fullHTML + '`;');
parts.push('');
parts.push(backend);

const worker = parts.join('\n');

// Backup V1 and write
const finalPath = path.join(dir, 'cloudflare-worker-ganjafy.js');
const backupPath = path.join(dir, 'cloudflare-worker-ganjafy-v1-backup.js');
if (fs.existsSync(finalPath)) {
    fs.copyFileSync(finalPath, backupPath);
    console.log('✅ V1 backed up to:', backupPath);
}
fs.writeFileSync(finalPath, worker);
console.log('✅ Ganjafy V2 worker built!');
console.log('📏 Size:', (worker.length / 1024).toFixed(1), 'KB');
console.log('🚀 Deploy: wrangler deploy -c wrangler-ganjafy.toml');
