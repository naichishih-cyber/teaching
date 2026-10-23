"""Build the en/, zh-hant/ and zh-hans/ versions of the site from the French pages.

Run from the repository root:  python3 -I _i18n/build.py
French pages at the root are the source. Every visible text, alt text,
aria-label, <title> and meta description is looked up in translations.py;
anything without a translation is listed so it can be added.
"""
import html, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from translations import T

PAGES = ['index.html', 'chinois.html', 'anglais.html', 'entreprises.html', 'ateliers.html', 'parcours.html']
LANGS = {  # code: (folder, html lang, switcher label)
    'fr': ('', 'fr', 'FR'),
    'en': ('en', 'en', 'EN'),
    'zh-hant': ('zh-hant', 'zh-Hant', '繁'),
    'zh-hans': ('zh-hans', 'zh-Hans', '简'),
}
SITE = 'https://ns-b24.pages.dev/'


def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def switcher(cur, up, page, dark):
    on, off = ('#FFFFFF', '#B7D3C5') if dark else ('#1F4A3D', '#4B5355')
    parts = []
    for code, (folder, _, label) in LANGS.items():
        href = up + (folder + '/' if folder else '') + page
        active = code == cur
        font = "'Noto Sans TC', sans-serif" if label in '繁简' else "'Inter', sans-serif"
        parts.append(
            f'<a href="{href}" hreflang="{LANGS[code][1]}"{" aria-current=\"page\"" if active else ""} '
            f'style="display: inline-flex; align-items: center; justify-content: center; min-width: 32px; min-height: 44px; '
            f'text-decoration: none; color: {on if active else off}; font: {600 if active else 500} 13px {font}">{label}</a>')
    return '\n<span aria-hidden="true">|</span>\n'.join(parts)


def alternates(page, up):
    out = []
    for code, (folder, lang, _) in LANGS.items():
        path = (folder + '/' if folder else '') + ('' if page == 'index.html' else page)
        out.append(f'<link rel="alternate" hreflang="{lang}" href="{SITE}{path}">')
    out.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{"" if page == "index.html" else page}">')
    return '\n'.join(out)


def localize(src, page, code, missing):
    folder, lang, _ = LANGS[code]
    up = '../' if folder else ''
    t = T.get(code, {})
    s = src

    def tr(raw):
        key = html.unescape(raw).strip()
        if not key or code == 'fr':
            return raw
        if key in t:
            lead = raw[:len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()):]
            return lead + esc(t[key]) + trail
        if re.search(r'[A-Za-zÀ-ÿ]{2,}', key) and key not in T['same']:
            missing.add(key)
        return raw

    head, body = s.split('</head>', 1)
    head = re.sub(r'(<title>)(.*?)(</title>)', lambda m: m.group(1) + tr(m.group(2)) + m.group(3), head)
    head = re.sub(r'(<meta name="description" content=")([^"]*)(")', lambda m: m.group(1) + tr(m.group(2)).replace('"', '&quot;') + m.group(3), head)
    body = re.sub(r'(>)([^<>]+)(<)', lambda m: m.group(1) + tr(m.group(2)) + m.group(3), body)
    body = re.sub(r'( (?:alt|aria-label|placeholder|title)=")([^"]*)(")', lambda m: m.group(1) + tr(m.group(2)).replace('"', '&quot;') + m.group(3), body)
    s = head + '</head>' + body

    s = s.replace('<html lang="fr">', f'<html lang="{lang}">', 1)
    # language switcher, linking to this same page in each language
    s = re.sub(r'(<div role="group" aria-label="[^"]*"([^>]*)>\n).*?(</div>)',
               lambda m: m.group(1) + switcher(code, up, page, '#7FA595' in m.group(2)) + '\n' + m.group(3), s, count=1, flags=re.S)
    # hreflang alternates
    s = re.sub(r'\n<link rel="alternate" hreflang=.*?(?=\n<link rel="preconnect")', '', s, flags=re.S)
    s = s.replace('\n<link rel="preconnect"', '\n' + alternates(page, up) + '\n<link rel="preconnect"', 1)
    if folder:
        s = s.replace('src="assets/', 'src="../assets/')
    if code.startswith('zh'):
        # CJK has no true italics; keep headings upright
        s = s.replace('</style>', 'h1{font-style:normal !important}\n</style>', 1)
    if code == 'zh-hans':
        s = s.replace('Noto+Sans+TC', 'Noto+Sans+SC').replace("'Noto Sans TC'", "'Noto Sans SC'").replace('lang="zh-Hant"', 'lang="zh-Hans"')
    return s


def main():
    missing = {}
    for page in PAGES:
        src = open(page, encoding='utf-8').read()
        for code, (folder, _, _) in LANGS.items():
            miss = set()
            out = localize(src, page, code, miss)
            if folder:
                os.makedirs(folder, exist_ok=True)
            open(os.path.join(folder, page) if folder else page, 'w', encoding='utf-8').write(out)
            for k in miss:
                missing.setdefault(code, set()).add(k)
    for code, keys in missing.items():
        print(f'[{code}] {len(keys)} untranslated:')
        for k in sorted(keys):
            print('   ', k)
    if not missing:
        print('All text translated.')


if __name__ == '__main__':
    main()
