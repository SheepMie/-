#!/usr/bin/env python3
"""Generate embedded font CSS for a prototype version: Chinese (and for v1, Latin)
faces subsetted to the characters that version's source uses, as base64, so the
built HTML renders the same on any phone.

Run from prototype/ after `npm install` whenever UI copy changes:
    pip install fonttools brotli
    python3 tools/subset_fonts.py v1     # -> src/fonts.css
    python3 tools/subset_fonts.py v3     # -> src/v3/fonts.css
"""
import base64, io, re, sys
from pathlib import Path
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
NM = ROOT / 'node_modules'
LATIN = set(range(0x20, 0x7F)) | {0xA5, 0xB7, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026}
# cjk entries: (fontsource package, weight file to read, family name, declared font-weight)
VERSIONS = {
    'v1': dict(src='src/app.html', out='src/fonts.css',
               latin=[('@fontsource-variable/source-serif-4/files/source-serif-4-latin-wght-normal.woff2', 'Source Serif 4', '200 900')],
               cjk=[('noto-serif-sc', 400, 'Noto Serif SC', '400'), ('noto-serif-sc', 700, 'Noto Serif SC', '700')]),
    'v3': dict(src='src/v3/app.html', out='src/v3/fonts.css', latin=[],
               cjk=[('noto-sans-sc', 900, 'Noto Sans SC', '400'), ('noto-serif-sc', 500, 'Noto Serif SC', '400 700')]),
}

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

def build(name):
    v = VERSIONS[name]
    text = (ROOT / v['src']).read_text(encoding='utf8')
    cjk = {ord(c) for c in text if ord(c) > 0x2000}
    out, total = [], 0
    for path, family, weight in v['latin']:
        b64, have = make(NM / path, LATIN, ['kern', 'liga', 'onum', 'lnum', 'pnum', 'tnum'])
        out.append(face(family, weight, b64, have)); total += len(b64)
    for pkg_name, file_weight, family, weight in v['cjk']:
        pkg = NM / '@fontsource' / pkg_name
        css = (pkg / f'{file_weight}.css').read_text()
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
                out.append(face(family, weight, b64, have)); total += len(b64); done |= have
        print(f'{name} {family} {file_weight}: {len(done)} glyphs embedded, {len(cjk - done)} not in font', file=sys.stderr)
    (ROOT / v['out']).write_text(''.join(out))
    print(f"wrote {v['out']}, {total/1024:.0f} KB base64", file=sys.stderr)

for name in (sys.argv[1:] or list(VERSIONS)):
    build(name)
