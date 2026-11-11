// Inlines the compiled Tailwind CSS into a single self-contained index.html.
import { readFileSync, writeFileSync } from 'node:fs';
const css = readFileSync(new URL('./dist.css', import.meta.url), 'utf8');
const html = readFileSync(new URL('./src/app.html', import.meta.url), 'utf8');
if (!html.includes('/*__CSS__*/')) throw new Error('CSS placeholder missing');
writeFileSync(new URL('./index.html', import.meta.url), html.replace('/*__CSS__*/', () => css));
console.log('built index.html', (css.length / 1024).toFixed(1) + 'KB css');
