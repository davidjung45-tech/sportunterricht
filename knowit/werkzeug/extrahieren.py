"""Einmalig: liest die Inhalte aus der alten, fertig gebauten Know-it-Website (ZIP) in Datendateien.

    python3 werkzeug/extrahieren.py <ordner-der-alten-website>

Ergebnis: daten/produkte.json, daten/muskeln.json – ab dann ist bauen.py die einzige Quelle.
Fachinhalte (Steckbriefe, Zeichnungen, Funktionen) werden 1:1 übernommen, nichts wird umformuliert.
"""
import html
import json
import re
import sys
from pathlib import Path

ALT = Path(sys.argv[1])
HIER = Path(__file__).resolve().parent.parent
D = HIER / 'daten'


def main_html(p):
    t = p.read_text()
    return t[t.index('<main'):t.index('</main>')]


def text(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s or '')).strip()


def eins(muster, s, gruppe=1, flags=re.S):
    m = re.search(muster, s, flags)
    return m.group(gruppe) if m else ''


# ---------------------------------------------------------------- Muskeln
idx = main_html(ALT / 'muskeln/index.html')
reihenfolge, kapitel = [], {}
for band in re.finditer(r'<div class="m-band" id="band(\d)">(.*?)(?=<div class="m-band"|$)', idx, re.S):
    b = int(band.group(1))
    for gr in re.finditer(r'<div class="m-gruppe" id="(b\dk\d+)"><h3 class="m-kapitel">(.*?)</h3><ul class="liste">(.*?)</ul>', band.group(2), re.S):
        for li in re.finditer(r'<a href="\.\./muskeln/([^/]+)/"><span class="mini[^"]*">(\d+)<small>(.*?)</small></span><span><b>(.*?)</b><small>(.*?)</small>', gr.group(3)):
            slug = li.group(1)
            reihenfolge.append(slug)
            kapitel[slug] = {'band': b, 'kapitel_id': gr.group(1), 'kapitel': text(gr.group(2)), 'nr': int(li.group(2)),
                             'deutsch': text(li.group(5)).split(' · ')[0]}

def zeichnung(m):
    i = m.find('<div class="zeichnung">')
    if i < 0:
        return ''
    i += len('<div class="zeichnung">')
    ende = re.compile(r'</svg>\s*</div>').search(m, i)  # Ende der äußeren Grafik (auch mit Zeilenumbruch davor)
    return m[i:ende.start()] + '</svg>' if ende else ''


def lernfelder(teile):
    """Ursprung/Ansatz/Innervation für das Lernquiz – bei Muskeln mit mehreren Köpfen zusammengefasst, Wortlaut unverändert."""
    out = {}
    for feld in ('ursprung', 'ansatz', 'innervation'):
        werte = []
        for t in teile:
            if t[feld]:
                werte.append((t['titel'] + ': ' if len(teile) > 1 and t['titel'] not in ('Gemeinsam', 'Steckbrief') else '') + t[feld])
            elif feld == 'ursprung' and t['weitere'] and t['titel'].startswith('Ursprün'):
                werte += [k + ': ' + v for k, v in t['weitere'].items()]
        out[feld] = ' · '.join(dict.fromkeys(werte))
    return out


muskeln = []
for slug in reihenfolge:
    m = main_html(ALT / 'muskeln' / slug / 'index.html')
    teile = []
    for t in re.finditer(r'<div class="teil">(.*?)</div>', m, re.S):
        dl = dict((text(k), text(v)) for k, v in re.findall(r'<dt>(.*?)</dt><dd>(.*?)</dd>', t.group(1), re.S))
        teile.append({'titel': text(eins(r'<h3>(.*?)</h3>', t.group(1))), 'ursprung': dl.get('Ursprung', ''), 'ansatz': dl.get('Ansatz', ''),
                      'innervation': dl.get('Innervation', ''), 'weitere': {k: v for k, v in dl.items() if k not in ('Ursprung', 'Ansatz', 'Innervation')}})
    funktion_ul = eins(r'<div class="funktion"><h3>Funktion</h3>(<ul>.*?</ul>)</div>', m)
    muskeln.append({
        'slug': slug, **kapitel[slug],
        'name': text(eins(r'<h1>(.*?)</h1>', m)),
        'oberzeile': text(eins(r'<p class="oberzeile">(.*?)</p>', m)),
        'video': eins(r'data-video="([\w-]{11})"', m),
        'farbe': eins(r'--vfarbe:(#[0-9a-fA-F]{3,6})', m) or '#a8322a',
        'zeichnung': zeichnung(m),
        'steckbrief_html': eins(r'(<div class="steckbrief">.*?</dl></div></div>)', m),
        'teile': teile,
        'lernen': lernfelder(teile),
        'funktion_html': funktion_ul,
        'funktion': [text(x) for x in re.findall(r'<li>(.*?)</li>', funktion_ul, re.S)],
        'extras': [text(x) for x in re.findall(r'<li><svg.*?</svg><span>(.*?)</span></li>', eins(r'<div class="gesperrt">(.*?)</div></div>', m), re.S)],
    })
(D / 'muskeln.json').write_text(json.dumps(muskeln, ensure_ascii=False, indent=1))
print(len(muskeln), 'Muskeln,', sum(1 for x in muskeln if x['video']), 'mit Video,', sum(1 for x in muskeln if not x['zeichnung']), 'ohne Zeichnung')

# ---------------------------------------------------------------- Produkte
produkte = []
for slug in re.findall(r'href="\.\./ebooks/([^/]+)/"', main_html(ALT / 'ebooks/index.html')):
    if slug in [p['slug'] for p in produkte]:
        continue
    m = main_html(ALT / 'ebooks' / slug / 'index.html')
    figs = [{'bild': eins(r'assets/bilder/([^"]+)"', f), 'alt': html.unescape(eins(r'alt="([^"]*)"', f)), 'text': text(eins(r'<figcaption>(.*?)</figcaption>', f))}
            for f in re.findall(r'<figure>(.*?)</figure>', m, re.S)]
    kap = [{'titel': text(eins(r'<summary>(.*?)(?:<span|</summary>)', k)), 'inhalt': text(eins(r'<div>(.*?)</div>', k))}
           for k in re.findall(r'<details>(.*?)</details>', m, re.S)]
    produkte.append({
        'slug': slug,
        'band': int(eins(r'Band (\d) · Know it', m)),
        'titel': text(eins(r'<h1[^>]*>(.*?)</h1>', m)),
        'text': text(eins(r'<p class="einleitung">(.*?)</p>', m)),
        'preis': text(eins(r'<span class="preis">(.*?)</span>', m)),
        'punkte': [text(x) for x in re.findall(r'<li><svg.*?</svg><span>(.*?)</span></li>', eins(r'<div class="kaufbox">(.*?)</div>\s*<h2', m), re.S)],
        'info': text(eins(r'<p class="klein">(.*?)</p>', m)),
        'leseprobe_seiten': int(eins(r'Leseprobe \((\d+) Seiten\)', m) or 0),
        'fuer_wen': text(eins(r'<h2>Für wen ist dieses Buch\?</h2>\s*<p>(.*?)</p>', m)),
        'vorschau': figs,
        'kapitel': kap,
        'probe_text': text(eins(r'<h3>Probier es aus</h3><p>(.*?)</p>', m)),
        'cover': 'cover-band' + eins(r'Band (\d) · Know it', m) + '.jpg',
    })
(D / 'produkte.json').write_text(json.dumps(produkte, ensure_ascii=False, indent=1))
for p in produkte:
    print(p['band'], p['slug'], p['preis'], len(p['punkte']), 'Punkte,', len(p['kapitel']), 'Kapitel,', len(p['vorschau']), 'Bilder,', p['info'][:40])

# Kostenlos-Seite: Beschreibungen der Leseproben und des Gratis-PDFs
k = main_html(ALT / 'kostenlos/index.html')
proben = {eins(r'leseprobe-([\w-]+)\.pdf', blk): text(eins(r'<p>(.*?)</p>', blk)) for blk in re.split(r'<h[23][^>]*>Leseprobe: ', k)[1:]}
gratis = {'titel': text(eins(r'<h2>(Bewegungsausmaß.*?)</h2>', k)), 'text': text(eins(r'<h2>Bewegungsausmaß.*?</h2>\s*<p[^>]*>(.*?)</p>', k)), 'info': text(eins(r'(PDF, \d+ Seiten[^<]*)', k))}
(D / 'kostenlos.json').write_text(json.dumps({'leseproben': proben, 'gratis': gratis}, ensure_ascii=False, indent=1))
print('Leseproben-Texte:', len(proben), '| Gratis:', gratis['titel'], gratis['info'])

# FAQ: Frage + Antwort (Antwort als HTML, Links werden in bauen.py ersetzt)
f = main_html(ALT / 'faq/index.html')
faq = [{'frage': text(q), 'antwort': a.strip()} for q, a in re.findall(r'<details><summary>(.*?)</summary><div class="antwort">(.*?)</div></details>', f, re.S)]
(D / 'faq.json').write_text(json.dumps(faq, ensure_ascii=False, indent=1))
print('FAQ:', len(faq))
