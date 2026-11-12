// Builds each prototype version into one self-contained HTML file:
// compiles its Tailwind CSS and inlines it (plus any embedded fonts).
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync, rmSync } from 'node:fs';

const here = p => new URL(p, import.meta.url);
const b64 = p => readFileSync(here(p)).toString('base64');
const versions = [
  { src: 'src/app.html', css: 'src/input.css', out: 'index.html' },
  { src: 'src/v2.html', css: 'src/v2.css', out: 'v2.html',
    font: `@font-face{font-family:'Outfit';font-weight:100 900;font-display:swap;src:url(data:font/woff2;base64,${
      b64('node_modules/@fontsource-variable/outfit/files/outfit-latin-wght-normal.woff2')}) format('woff2')}` },
];
for (const v of versions) {
  execFileSync('npx', ['tailwindcss', '-i', v.css, '-o', 'dist.css', '--minify'], { cwd: here('.'), stdio: 'ignore' });
  const css = readFileSync(here('dist.css'), 'utf8');
  const html = readFileSync(here(v.src), 'utf8');
  if (!html.includes('/*__CSS__*/')) throw new Error(`CSS placeholder missing in ${v.src}`);
  writeFileSync(here(v.out), html.replace('/*__FONT__*/', () => v.font || '').replace('/*__CSS__*/', () => css));
  console.log(`built ${v.out}`, (css.length / 1024).toFixed(1) + 'KB css');
}
rmSync(here('dist.css'), { force: true });
