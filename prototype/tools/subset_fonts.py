#!/usr/bin/env python3
"""Generate src/fonts.css: serif fonts subsetted to the characters the prototype
uses and embedded as base64, so index.html renders the same on any phone.

Run from prototype/ after `npm install` whenever UI copy changes:
    pip install fonttools brotli && python3 tools/subset_fonts.py
"""
import base64, io, re, sys
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
NM = ROOT / 'node_modules'
text = (ROOT / 'src' / 'app.html').read_text(encoding='utf8')
cjk = {ord(c) for c in text if ord(c) > 0x2000}
latin = set(range(0x20, 0x7F)) | {0xA5, 0xB7, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026}

def make(path, codepoints, features):
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = features
    font = TTFont(path)
    have = set(font.getBestCmap()) & codepoints
    if not have:
        return None, have
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=have)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode(), have

def face(family, weight, b64, cps):
    rng = ','.join(f'U+{c:x}' for c in sorted(cps))
    return (f"@font-face{{font-family:'{family}';font-style:normal;font-display:swap;font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng}}}\n")

out, total = [], 0
src = NM / '@fontsource-variable/source-serif-4/files/source-serif-4-latin-wght-normal.woff2'
b64, have = make(src, latin, ['kern', 'liga', 'onum', 'lnum', 'pnum', 'tnum'])
out.append(face('Source Serif 4', '200 900', b64, have)); total += len(b64)

pkg = NM / '@fontsource/noto-serif-sc'
for weight in (400, 700):
    css = (pkg / f'{weight}.css').read_text()
    done = set()
    for m in re.finditer(r'url\(\./files/([^)]+\.woff2)\)[^}]*?unicode-range:\s*([^;]+);', css):
        cps = set()
        for part in m.group(2).split(','):
            lo, _, hi = part.strip()[2:].partition('-')
            cps.update(range(int(lo, 16), int(hi or lo, 16) + 1))
        want = (cps & cjk) - done
        if not want:
            continue
        b64, have = make(pkg / 'files' / m.group(1), want, ['kern'])
        if b64:
            out.append(face('Noto Serif SC', weight, b64, have)); total += len(b64); done |= have
    missing = cjk - done
    print(f'weight {weight}: {len(done)} glyphs embedded, {len(missing)} not in font', file=sys.stderr)

(ROOT / 'src' / 'fonts.css').write_text(''.join(out))
print(f'wrote src/fonts.css, {total/1024:.0f} KB base64', file=sys.stderr)
