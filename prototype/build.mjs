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
// v3 is hand-written CSS (no Tailwind): inline its @imports where they stand so the
// Hallmark stamp stays on line 1, then append the embedded fonts.
const latinFace = (family, weight, file) =>
  `@font-face{font-family:'${family}';font-weight:${weight};font-display:swap;src:url(data:font/woff2;base64,${b64(file)}) format('woff2')}`;
{
  const dir = 'src/v3/';
  const css = readFileSync(here(dir + 'app.css'), 'utf8')
    .replace(/@import url\("\.\/([\w.-]+)"\);/g, (_, f) => readFileSync(here(dir + f), 'utf8').trim())
    + latinFace('League Gothic', '400', 'node_modules/@fontsource/league-gothic/files/league-gothic-latin-400-normal.woff2')
    + latinFace('Newsreader', '200 800', 'node_modules/@fontsource-variable/newsreader/files/newsreader-latin-wght-normal.woff2')
    + readFileSync(here(dir + 'fonts.css'), 'utf8');
  const html = readFileSync(here(dir + 'app.html'), 'utf8');
  if (!html.includes('/*__CSS__*/')) throw new Error('CSS placeholder missing in v3');
  writeFileSync(here('v3.html'), html.replace('/*__CSS__*/', () => css));
  console.log('built v3.html', (css.length / 1024).toFixed(1) + 'KB css');
}
for (const v of versions) {
  execFileSync('npx', ['tailwindcss', '-i', v.css, '-o', 'dist.css', '--minify'], { cwd: here('.'), stdio: 'ignore' });
  const css = readFileSync(here('dist.css'), 'utf8');
  const html = readFileSync(here(v.src), 'utf8');
  if (!html.includes('/*__CSS__*/')) throw new Error(`CSS placeholder missing in ${v.src}`);
  writeFileSync(here(v.out), html.replace('/*__FONT__*/', () => v.font || '').replace('/*__CSS__*/', () => css));
  console.log(`built ${v.out}`, (css.length / 1024).toFixed(1) + 'KB css');
}
rmSync(here('dist.css'), { force: true });
