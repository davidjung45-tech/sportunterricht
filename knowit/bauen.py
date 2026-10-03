"""Baut die Website „Know it – Anatomie und Training“ als statische Seiten (Netlify-fertig).

    python3 bauen.py              # → ausgabe/   (für Netlify)
    python3 bauen.py --vorschau   # → vorschau/  (zum Öffnen per Doppelklick)

Anpassen: einstellungen.json (Kauflinks, Preise, Impressum). Inhalte: daten/*.json (aus der bisherigen Website übernommen).
Design und Grundfunktionen (Video, Menü, Kauf-Dialog) teilt sich die Seite mit der Sportunterricht-Website (../website/statisch).
"""
import html
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

HIER = Path(__file__).resolve().parent
WEB = HIER.parent / 'website' / 'statisch'  # gemeinsames Designsystem
VORSCHAU = '--vorschau' in sys.argv
OUT = HIER / ('vorschau' if VORSCHAU else 'ausgabe')
E = json.loads((HIER / 'einstellungen.json').read_text())
DOMAIN = (E.get('domain') or '').rstrip('/')
KAUF = E.get('kaufen', {})
HEUTE = date.today()
VERSION = HEUTE.strftime('%Y%m%d')
WARNUNGEN, SITEMAP = [], []
esc = html.escape
AKTIV = ' aria-current="page"'

FARBE = {1: '#b0362b', 2: '#304f8f', 3: '#6b3f7e', 4: '#2f6a3c', 5: '#894b12', 6: '#a0284e', 7: '#0d6a72'}
KURZ = {1: 'Hüfte & Bein', 2: 'Schulter & Arm', 3: 'Rumpf & Hals', 4: 'Gelenke', 5: 'Skelett & Organe', 6: 'Trainingslehre', 7: 'Ernährung'}
PRODUKTE = json.loads((HIER / 'daten/produkte.json').read_text())
for p in PRODUKTE:
    p['preis'] = E.get('preise', {}).get(p['slug'], p['preis'])
    p['farbe'] = FARBE[p['band']]
    p['kurz'] = KURZ[p['band']]
NACH_BAND = {p['band']: p for p in PRODUKTE}
MUSKELN = json.loads((HIER / 'daten/muskeln.json').read_text())
KOSTENLOS = json.loads((HIER / 'daten/kostenlos.json').read_text())
FAQ_ALT = json.loads((HIER / 'daten/faq.json').read_text())


def euro(s):
    return float(s.replace('€', '').strip().replace('.', '').replace(',', '.'))


def fmt(x):
    return f'{x:.2f}'.replace('.', ',') + ' €'


PAKETE = [
    {'slug': 'muskel-atlas-paket', 'titel': 'Muskel-Atlas-Paket', 'unter': 'Alle 112 Muskeln: Hüfte & Bein, Schulter & Arm, Rumpf & Hals', 'baende': [1, 2, 3],
     'text': 'Die drei Muskel-Atlanten zusammen – jeder Muskel des Bewegungsapparats von Bein, Arm, Rumpf und Hals auf einer Seite, mit Lernkarten zum Ausdrucken.'},
    {'slug': 'komplettpaket', 'titel': 'Das Komplettpaket', 'unter': 'Alle 7 Bände der Reihe „Anatomie kompakt“', 'baende': [1, 2, 3, 4, 5, 6, 7],
     'text': 'Die ganze Reihe für Studium und Ausbildung: alle Muskeln, Gelenke, Skelett und Organe, Trainingslehre und Ernährung.'},
]
for pk in PAKETE:
    pk['preis'] = E.get('preise', {}).get(pk['slug'], '')
    pk['statt'] = fmt(sum(euro(NACH_BAND[b]['preis']) for b in pk['baende']))
    pk['spar'] = fmt(euro(pk['statt']) - euro(pk['preis'])) if pk['preis'] else ''
AB_PREIS = fmt(min(euro(p['preis']) for p in PRODUKTE))

ICON = {
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    'play': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.8v14.4c0 .8.9 1.3 1.6.8l11-7.2a1 1 0 000-1.6l-11-7.2C7.9 3.5 7 4 7 4.8z"/></svg>',
    'pfeil': '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
    'menue': '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    'buch': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 20.5v-15z"/><path d="M4 20.5A2.5 2.5 0 016.5 18H20v3H6.5A2.5 2.5 0 014 20.5z"/></svg>',
    'karten': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6.5" y="3.5" width="14" height="17" rx="2"/><path d="M3.5 7v12a2 2 0 002 2h10"/><path d="M10 9h7M10 13h5"/></svg>',
    'muskel': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 3c-2 4-2 9 1 13s7 5 9 5"/><path d="M11 3c1.5 3 2 6 1 9"/><circle cx="7" cy="3" r="1"/><circle cx="17" cy="21" r="1"/></svg>',
    'rechner': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.5" y="2.5" width="15" height="19" rx="2.5"/><rect x="7.5" y="5.5" width="9" height="4" rx="1"/><path d="M8 13h.01M12 13h.01M16 13h.01M8 17h.01M12 17h.01M16 17h.01"/></svg>',
    'plan': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="16" rx="2.5"/><path d="M8 2.5v4M16 2.5v4M3.5 9.5h17M8 14l2 2 4-4"/></svg>',
    'video': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="5" width="15" height="14" rx="3"/><path d="M17.5 10l4-2.5v9l-4-2.5"/></svg>',
    'student': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10l9-6 9 6-9 6-9-6z"/><path d="M7 12.5V17c0 1 2.2 3 5 3s5-2 5-3v-4.5"/></svg>',
    'drucken': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 9V3.5h11V9M6.5 17.5h-2a2 2 0 01-2-2V11a2 2 0 012-2h15a2 2 0 012 2v4.5a2 2 0 01-2 2h-2"/><rect x="6.5" y="14" width="11" height="6.5" rx="1"/></svg>',
}
LOGO = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="8" cy="6" r="2.6"/><circle cx="16" cy="18" r="2.6"/><path d="M9.8 7.8l4.4 8.4"/></svg>'
FELD = '<svg class="feld" viewBox="0 0 330 430" fill="none" stroke="#fff" stroke-width="4" aria-hidden="true"><circle cx="104" cy="88" r="14"/><path d="M92 100 L84 120 C88 150 90 186 86 210 M104 104 L100 116 C100 150 102 188 110 210"/><ellipse cx="100" cy="224" rx="11" ry="14"/><path d="M78 250 L124 250 M96 266 C102 300 104 350 102 384 M118 266 C114 300 114 350 118 384"/></svg>'

NAVI = [('ebooks/', 'E-Books', 'Anatomie kompakt, 7 Bände'), ('muskeln/', 'Muskel-Lexikon', '112 Muskeln mit Zeichnung'),
        ('lernkarten/', 'Lernkarten', 'online üben, kostenlos'), ('rechner/', 'Rechner', '1RM, Puls, Energiebedarf'), ('kostenlos/', 'Kostenlos', 'Lernskript & Leseproben')]


class Seite:
    def __init__(self, pfad):
        self.pfad = pfad.strip('/')
        teile = [x for x in self.pfad.split('/') if x]
        self.tiefe = len(teile) - 1 if self.pfad.endswith('.html') else len(teile)

    def zu(self, ziel):
        if ziel.startswith(('http', 'mailto:', '#')):
            return ziel
        pre = '../' * self.tiefe
        if ziel == '' or ziel.endswith('/'):
            return (pre + ziel + ('index.html' if VORSCHAU else '')) or './'
        return pre + ziel


def url_abs(pfad):
    return f'{DOMAIN}/{pfad.strip("/")}{"/" if pfad and not pfad.endswith((".html", ".pdf", ".xml")) else ""}' if DOMAIN else None


def bild(s, name):
    return s.zu('assets/bilder/' + name)


# ---------------------------------------------------------------- Kaufen

def kauf_knopf(s, slug, text='Jetzt kaufen', klasse='knopf primaer gross'):
    link = KAUF.get(slug, '')
    if link:
        return f'<a class="{klasse}" href="{esc(link)}" rel="noopener" data-kauf="{esc(slug)}">{text}</a>'
    WARNUNGEN.append(f'Kauf-Link fehlt: kaufen.{slug}')
    probe = next((f'downloads/leseprobe-{slug}.pdf' for p in PRODUKTE if p['slug'] == slug), 'kostenlos/')
    return f'<a class="{klasse}" href="{s.zu(probe)}" title="Der Shop startet in Kürze">Bald erhältlich – Leseprobe ansehen</a>'


def kauf_daten(s):
    d = {}
    for p in PRODUKTE:
        if KAUF.get(p['slug']):
            d[p['slug']] = {'t': f'Band {p["band"]}: {p["titel"]}', 'p': p['preis'], 'x': p['text'], 'u': KAUF[p['slug']],
                            'l': s.zu(f'downloads/leseprobe-{p["slug"]}.pdf'), 'c': bild(s, p['cover'])}
    for pk in PAKETE:
        if KAUF.get(pk['slug']):
            d[pk['slug']] = {'t': pk['titel'], 'p': pk['preis'], 's': pk['statt'], 'x': pk['text'], 'u': KAUF[pk['slug']], 'l': '', 'c': ''}
    return d


def kauf_dialog(s):
    daten = kauf_daten(s)
    if not daten:
        return ''
    return f'''<dialog class="dialog" id="kauf-dialog" aria-labelledby="kauf-titel">
<form method="dialog" class="dialog-zu"><button type="submit" aria-label="Dialog schließen"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></form>
<div class="kauf-kopf"><img id="kauf-cover" src="" alt="" width="84" height="119"><div><p class="oberzeile">Deine Bestellung</p><h2 id="kauf-titel">E-Book</h2><p class="preis"><span id="kauf-preis"></span> <s id="kauf-statt"></s></p></div></div>
<p id="kauf-text"></p>
<ul class="haken">
<li>{ICON['check']}<span><b>Sofort als PDF</b> – Download-Link direkt nach der Zahlung und per E-Mail</span></li>
<li>{ICON['check']}<span><b>Sichere Zahlung über Digistore24</b> – z. B. PayPal, Kreditkarte oder Lastschrift</span></li>
<li>{ICON['check']}<span><b>Rechnung inkl. USt.</b> bekommst du automatisch per E-Mail</span></li></ul>
<p class="klein">Vertragspartner ist die Digistore24 GmbH als Wiederverkäufer. Bei digitalen Inhalten erlischt das Widerrufsrecht, sobald du dem sofortigen Download zustimmst – das bestätigst du im nächsten Schritt. Es gelten die <a href="{s.zu('agb/')}">AGB</a> und die <a href="{s.zu('datenschutz/')}">Datenschutzerklärung</a>.</p>
<div class="knopfreihe"><a class="knopf primaer gross" id="kauf-weiter" href="#" rel="noopener">Weiter zur sicheren Zahlung {ICON['pfeil']}</a><a class="knopf" id="kauf-probe" href="#" download>{ICON['download']} Erst Leseprobe ansehen</a></div>
</dialog>
<script type="application/json" id="kauf-daten">{json.dumps(daten, ensure_ascii=False)}</script>'''


# ---------------------------------------------------------------- Seitengerüst

def kanalwechsel(s):
    """Gut sichtbarer Wechsel zwischen den beiden Kanal-Websites (oberste Leiste)."""
    return f'''<nav class="kanalwechsel" aria-label="Unsere Websites"><div class="wrap">
<span class="kw-label">Unsere Kanäle</span>
<a class="kw" href="{esc(E['sportunterricht_url'])}/"><span class="kw-punkt" style="background:#1f5bd8" aria-hidden="true"></span>Sportunterricht<small> · Spiele & Stundenplanung</small></a>
<a class="kw aktiv" href="{s.zu('')}" aria-current="true"><span class="kw-punkt" style="background:#b0362b" aria-hidden="true"></span>Know it<small> · Anatomie & Training</small></a>
</div></nav>'''


def seite(pfad, titel, beschreibung, inhalt, aktiv='', og='og-start.png', schema=None, noindex=False, voller_titel=False, skripte=(), koerper_klasse=''):
    s = Seite(pfad)
    t = titel if voller_titel else f'{titel} · Know it'
    kan = url_abs(pfad)
    og_url = f'{DOMAIN}/assets/og/{og}' if DOMAIN else s.zu(f'assets/og/{og}')
    cta_ziel = 'ebooks/'
    navi = ''.join(f'<li><a href="{s.zu(z)}"{AKTIV if aktiv == z else ""}>{n}</a></li>' for z, n, _ in NAVI if z != cta_ziel)
    menue = ''.join(f'<a href="{s.zu(z)}"{AKTIV if aktiv == z else ""}>{n}<small>{u}</small></a>' for z, n, u in NAVI)
    schema_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (schema or []))
    koerper = inhalt(s)
    dialog = kauf_dialog(s) if 'data-kauf=' in koerper else ''
    kopf = f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(t)}</title>
<meta name="description" content="{esc(beschreibung)}">
{f'<link rel="canonical" href="{kan}">' if kan else ''}
{'<meta name="robots" content="noindex, follow">' if noindex else ''}
<meta name="theme-color" content="#13211b">
<meta property="og:type" content="website"><meta property="og:locale" content="de_DE"><meta property="og:site_name" content="Know it – Anatomie und Training">
<meta property="og:title" content="{esc(titel)}"><meta property="og:description" content="{esc(beschreibung)}">
<meta property="og:image" content="{og_url}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
{f'<meta property="og:url" content="{kan}">' if kan else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{s.zu('assets/icon.svg')}" type="image/svg+xml">
<link rel="preload" href="{s.zu('assets/fonts/barlow-700.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{s.zu('assets/fonts/atkinson-400.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{s.zu('assets/site.css')}?v={VERSION}">
<script src="{s.zu('assets/site.js')}?v={VERSION}" defer></script>
<script src="{s.zu('assets/knowit.js')}?v={VERSION}" defer></script>
{''.join(f'<script src="{s.zu("assets/" + x)}?v={VERSION}" defer></script>' for x in skripte)}
{schema_html}
</head>
<body{f' class="{koerper_klasse}"' if koerper_klasse else ''}>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
{kanalwechsel(s)}
<header class="kopf"><div class="wrap">
<a class="logo" href="{s.zu('')}"><span class="logo-zeichen ki">{LOGO}</span>Know it</a>
<nav class="navi" aria-label="Hauptnavigation"><ul>{navi}</ul></nav>
<a class="knopf blau klein kopf-cta" href="{s.zu('ebooks/')}"{AKTIV if aktiv == 'ebooks/' else ''}><span class="cta-lang">E-Books ab {AB_PREIS}</span><span class="cta-kurz" aria-hidden="true">E-Books</span></a>
<details class="menue"><summary aria-label="Menü öffnen">{ICON['menue']}</summary><nav class="menue-liste" aria-label="Menü">{menue}<a href="{s.zu('lernplan/')}">Lernplan<small>bis zur Prüfung</small></a><a href="{s.zu('ueber/')}">Über mich<small></small></a><a href="{s.zu('faq/')}">Häufige Fragen<small></small></a><a href="{esc(E['sportunterricht_url'])}/">Zu Sportunterricht<small>Spiele & Stundenplanung</small></a></nav></details>
</div></header>
<main id="inhalt">
'''
    fuss = f'''{dialog}</main>
<footer class="fuss"><div class="wrap">
<a class="kanal-tipp" href="{esc(E['sportunterricht_url'])}/"><span class="kanal-tipp-logo" aria-hidden="true">S</span><span><small>Auch von DJ</small><b>Sportunterricht – Spiele, Stundenplaner & Werkzeuge für die Halle</b></span>{ICON['pfeil']}</a>
<div class="fuss-raster">
<div><a class="logo" href="{s.zu('')}"><span class="logo-zeichen ki">{LOGO}</span>Know it</a>
<p>Anatomie, Physiologie und Training – kurz, bildhaft und prüfungsnah erklärt.</p></div>
<div><h2 class="fuss-titel">E-Books</h2><ul>{''.join(f'<li><a href="{s.zu("ebooks/" + p["slug"] + "/")}">{esc(p["titel"])}</a></li>' for p in PRODUKTE)}{''.join(f'<li><a href="{s.zu("ebooks/" + pk["slug"] + "/")}">{pk["titel"]}</a></li>' for pk in PAKETE)}</ul></div>
<div><h2 class="fuss-titel">Lernen</h2><ul><li><a href="{s.zu('muskeln/')}">Muskel-Lexikon</a></li><li><a href="{s.zu('lernkarten/')}">Lernkarten online</a></li><li><a href="{s.zu('lernplan/')}">Lernplan bis zur Prüfung</a></li><li><a href="{s.zu('rechner/')}">Trainings- & Ernährungsrechner</a></li><li><a href="{s.zu('kostenlos/')}">Kostenlos</a></li><li><a href="{E['youtube']}" rel="noopener">YouTube-Kanal</a></li></ul></div>
<div><h2 class="fuss-titel">Info</h2><ul><li><a href="{s.zu('ueber/')}">Über mich</a></li><li><a href="{s.zu('faq/')}">Häufige Fragen</a></li><li><a href="{esc(E['sportunterricht_url'])}/">Sportunterricht</a></li></ul></div>
</div>
<div class="fuss-unten"><span>© {HEUTE.year} Know it – Anatomie und Training · Ohne Tracking, ohne Werbe-Cookies</span><span><a href="{s.zu('impressum/')}">Impressum</a> · <a href="{s.zu('datenschutz/')}">Datenschutz</a> · <a href="{s.zu('agb/')}">AGB & Widerruf</a></span></div>
</div></footer>
</body>
</html>
'''
    ziel = OUT / pfad / 'index.html' if not pfad.endswith('.html') else OUT / pfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(kopf + koerper + fuss)
    if not noindex and not pfad.endswith('404.html'):
        SITEMAP.append(pfad)


# ---------------------------------------------------------------- Bausteine

def video_block(vid, name, farbe, kompakt=False):
    if not vid:
        return ''
    hinweis = 'Lädt von YouTube' if kompakt else 'Beim Abspielen wird das Video von YouTube geladen; dabei gelten die Datenschutzbestimmungen von Google.'
    return f'''<div class="video-wrap"><div class="video{' kompakt' if kompakt else ''}" data-video="{vid}" style="--vfarbe:{farbe}">
<button type="button" class="video-start" aria-label="Video „{esc(name)}“ abspielen">{FELD}<span class="play">{ICON['play']}</span><b>{'Abspielen' if kompakt else 'Video ansehen'}</b><small>{hinweis}</small></button></div>
<p class="video-alt"><a href="https://www.youtube.com/watch?v={vid}" target="_blank" rel="noopener">Video lädt nicht? Direkt auf YouTube ansehen<span class="sr-only"> (neues Fenster)</span></a></p></div>'''


def buchkarte(s, p):
    return f'''<article class="ki-buch" style="--bf:{p['farbe']}">
<a class="ki-buch-bild" href="{s.zu('ebooks/' + p['slug'] + '/')}" tabindex="-1" aria-hidden="true"><img src="{bild(s, p['cover'])}" alt="" width="250" height="353" loading="lazy"></a>
<div class="ki-buch-text"><span class="marke">Band {p['band']}</span><h3><a href="{s.zu('ebooks/' + p['slug'] + '/')}">{esc(p['titel'])}</a></h3>
<p>{esc(kuerzen(p['text'], 150))}</p>
<div class="ki-buch-fuss"><span class="preis">{p['preis']}</span><a class="ki-probe" href="{s.zu('downloads/leseprobe-' + p['slug'] + '.pdf')}" download>{ICON['download']}<span>Leseprobe</span></a></div></div></article>'''


def kuerzen(t, n):
    t = (t or '').strip()
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0].rstrip(',;:–-') + ' …'


def paket_banner(s, pk, h='h2', knopf=True):
    covers = ''.join(f'<img src="{bild(s, NACH_BAND[b]["cover"])}" alt="" width="110" height="155" loading="lazy">' for b in pk['baende'])
    inhalt = ''.join(f'<li>{ICON["check"]}<span>Band {b}: {esc(NACH_BAND[b]["titel"])}</span></li>' for b in pk['baende'])
    k = f'<div class="knopfreihe">{kauf_knopf(s, pk["slug"], pk["titel"] + " kaufen", "knopf pro gross")}<a class="knopf gross hell-rand" href="{s.zu("ebooks/" + pk["slug"] + "/")}">Details</a></div>' if knopf else ''
    return f'''<div class="komplett ki-paket"><div><p class="oberzeile">{esc(pk['unter'])}</p><{h}>{pk['titel']}</{h}>
<p class="paket-text">{esc(pk['text'])}</p><ul>{inhalt}</ul>
<p class="preis">{pk['preis']} <s>{pk['statt']}</s> {f'<span class="marke gelb">Du sparst {pk["spar"]}</span>' if pk['spar'] else ''}</p>{k}</div>
<div class="komplett-bilder">{covers}</div></div>'''


def faq_liste(s):
    kontakt = f'<a href="mailto:{E["email"]}">{esc(E["email"])}</a>' if E.get('email') else 'die E-Mail-Adresse im Impressum'
    l = [(f['frage'], f['antwort'].replace('an die E-Mail-Adresse im Impressum', 'an ' + kontakt)) for f in FAQ_ALT]
    l.insert(2, ('Gibt es die Bände auch im Paket?', f'<p>Ja. Das <a href="{s.zu("ebooks/muskel-atlas-paket/")}">Muskel-Atlas-Paket</a> enthält die Bände 1 bis 3 (alle 112 Muskeln) für {PAKETE[0]["preis"]} statt {PAKETE[0]["statt"]}, das <a href="{s.zu("ebooks/komplettpaket/")}">Komplettpaket</a> alle sieben Bände für {PAKETE[1]["preis"]} statt {PAKETE[1]["statt"]}.</p>'))
    l.insert(5, ('Kann ich auch online lernen?', f'<p>Ja, kostenlos: Im <a href="{s.zu("muskeln/")}">Muskel-Lexikon</a> stehen Ursprung, Ansatz, Innervation und Funktion aller 112 Muskeln, und mit den <a href="{s.zu("lernkarten/")}">Lernkarten</a> fragst du dich selbst ab – dein Lernstand bleibt auf deinem Gerät gespeichert.</p>'))
    return l


def faq_html(liste):
    return '<div class="faq">' + ''.join(f'<details><summary>{esc(f)}</summary><div class="antwort">{a}</div></details>' for f, a in liste) + '</div>'


# ---------------------------------------------------------------- Startseite

def startseite():
    z = E['zahlen']

    def inhalt(s):
        stapel = ''.join(f'<img src="{bild(s, p["cover"])}" alt="" width="200" height="283">' for p in PRODUKTE[::-1])
        waehler = {p['slug']: {'t': f'Band {p["band"]}: {p["titel"]}', 'p': p['preis'], 'u': s.zu('ebooks/' + p['slug'] + '/'), 'c': bild(s, p['cover']), 'x': p['fuer_wen'] or p['text']} for p in PRODUKTE}
        for pk in PAKETE:
            waehler[pk['slug']] = {'t': pk['titel'], 'p': f'{pk["preis"]} statt {pk["statt"]}', 'u': s.zu('ebooks/' + pk['slug'] + '/'), 'c': bild(s, NACH_BAND[pk['baende'][0]]['cover']), 'x': pk['text']}
        innen = [('seite-muskel-band1.jpg', 'Eine Seite pro Muskel', 'Zeichnung, Steckbrief, Merkhilfe, Prüfungsfalle, Praxis und Kurz-Check.'),
                 ('seite-kapitel-band6.jpg', 'Eine Doppelseite pro Thema', 'Diagramme, Richtwerte und Transfer in den Sport – hier Trainingslehre.'),
                 ('seite-bewegung-band1.jpg', 'Übersichten zum Wiederholen', '„Wer macht welche Bewegung?“ – ideal kurz vor der Prüfung.'),
                 ('lernkarten-band2.jpg', 'Lernkarten zum Ausdrucken', 'Vorne Zeichnung und Fragen, hinten die Antworten.')]
        galerie = ''.join(f'<figure><img src="{bild(s, b)}" alt="Beispielseite: {esc(t)}" width="331" height="468" loading="lazy"><figcaption><b>{esc(t)}</b><br>{esc(x)}</figcaption></figure>' for b, t, x in innen)
        knoepfe = [('muskel-atlas-huefte-bein', 'Muskeln von Hüfte und Bein', 'Band 1'), ('muskel-atlas-schulter-arm', 'Muskeln von Schulter und Arm', 'Band 2'),
                   ('muskel-atlas-rumpf-hals', 'Muskeln von Rumpf, Atmung, Hals', 'Band 3'), ('muskel-atlas-paket', 'Alle Muskeln für die Anatomie-Prüfung', 'Paket'),
                   ('gelenke-kompakt', 'Gelenke, Bänder, Verletzungen', 'Band 4'), ('skelett-organe-kompakt', 'Herz, Kreislauf, Atmung, Organe', 'Band 5'),
                   ('trainingslehre-kompakt', 'Training planen und steuern', 'Band 6'), ('ernaehrung-kompakt', 'Ernährung und Sporternährung', 'Band 7'),
                   ('komplettpaket', 'Alles – fürs ganze Studium', 'Paket')]
        wk = ''.join(f'<button type="button" aria-pressed="false" data-ziel="{k}">{esc(t)}<small>{u}</small></button>' for k, t, u in knoepfe)
        return f'''<section class="hero ki-hero"><div class="wrap">
<div><p class="oberzeile">Anatomie · Physiologie · Training · Ernährung</p>
<h1>Anatomie verstehen. <em>Prüfung bestehen.</em></h1>
<p class="einleitung">Sieben E-Books, die Prüfungswissen so aufbereiten, wie du es lernst: eine Seite pro Muskel, eine Doppelseite pro Gelenk und Thema – mit eigenen Zeichnungen, Merkhilfen, Prüfungsfallen, Lernkarten und QR-Codes zu den Videos.</p>
<div class="knopfreihe"><a class="knopf primaer gross" href="#ebooks">{ICON['buch']} E-Books ab {AB_PREIS}</a><a class="knopf gross" href="{s.zu('kostenlos/')}">{ICON['download']} Kostenlose Leseproben</a></div>
<ul class="hero-vorteile"><li>{ICON['check']}<span>Sofort als PDF – Handy, Tablet, Ausdruck</span></li><li>{ICON['check']}<span>Zu jedem Band eine Leseprobe</span></li><li>{ICON['check']}<span>Sichere Zahlung über Digistore24</span></li></ul></div>
<div class="buecherstapel ki-stapel" aria-hidden="true">{stapel}</div>
</div></section>

<section class="abschnitt eng"><div class="wrap"><div class="zahlen">
<div class="zahl"><b>{esc(z['aufrufe'])}</b><span>Videoaufrufe seit {esc(z['seit'])}</span></div>
<div class="zahl"><b>{esc(z['videos'])}</b><span>Videos auf YouTube</span></div>
<div class="zahl"><b>{esc(z['lernzeit'])}</b><span>Stunden Lernzeit mit den Videos</span></div>
<div class="zahl"><b>{len(MUSKELN)}</b><span>Muskeln mit eigener Zeichnung</span></div>
</div></div></section>

<section class="abschnitt"><div class="wrap"><div class="waehler" id="waehler">
<p class="oberzeile">In 5 Sekunden</p><h2>Welches Buch brauchst du?</h2>
<div class="waehler-knoepfe" role="group" aria-label="Was lernst du gerade?">{wk}</div>
<div class="waehler-ergebnis" id="waehler-ergebnis" aria-live="polite"></div>
<script type="application/json" id="waehler-daten">{json.dumps(waehler, ensure_ascii=False)}</script>
</div></div></section>

<section class="abschnitt hell" id="ebooks"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Die Reihe „Anatomie kompakt“</p><h2>Sieben E-Books für Studium, Ausbildung und Training</h2>
<p class="einleitung">Für Sportwissenschaft, Physiotherapie, Medizin und Trainer:innen-Ausbildungen. Jeder Band mit Selbsttest-Fragen und Lösungen – und einer kostenlosen Leseprobe.</p></div>
<a class="knopf" href="{s.zu('ebooks/')}">Alle Bände im Vergleich</a></div>
<div class="ki-buecher">{''.join(buchkarte(s, p) for p in PRODUKTE)}</div>
</div></section>

<section class="abschnitt"><div class="wrap ki-pakete">
{paket_banner(s, PAKETE[1])}
<div class="ki-paket-klein"><div><p class="oberzeile">Für die Anatomie-Prüfung</p><h2>{PAKETE[0]['titel']}</h2><p>{esc(PAKETE[0]['text'])}</p>
<p class="preis">{PAKETE[0]['preis']} <s>{PAKETE[0]['statt']}</s></p>
<div class="knopfreihe">{kauf_knopf(s, PAKETE[0]['slug'], 'Muskel-Atlas-Paket kaufen', 'knopf primaer')}<a class="knopf" href="{s.zu('ebooks/muskel-atlas-paket/')}">Details</a></div></div>
<div class="mini-stapel" aria-hidden="true">{''.join(f'<img src="{bild(s, NACH_BAND[b]["cover"])}" alt="" width="90" height="127" loading="lazy">' for b in PAKETE[0]['baende'])}</div></div>
</div></section>

<section class="abschnitt hell"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Ein Blick ins Buch</p><h2>So lernt es sich mit „Anatomie kompakt“</h2></div></div>
<div class="seiten-vorschau ki-galerie">{galerie}</div>
</div></section>

<section class="abschnitt"><div class="wrap raster vier ki-vorteile">
<div class="karte"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['muskel']}</div><h3>Verstehen statt pauken</h3><p>Wer weiß, wo ein Muskel beginnt, wo er ansetzt und über welches Gelenk er zieht, leitet die Funktion ab.</p></div>
<div class="karte"><div class="symbol" style="background:var(--gelb-weich);color:var(--gelb)">{ICON['student']}</div><h3>Prüfungsnah</h3><p>Merkhilfen und typische Prüfungsfallen zu jedem Muskel, dazu Fragen zum Selbsttest mit Lösungen.</p></div>
<div class="karte"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['video']}</div><h3>Mit Video</h3><p>QR-Codes führen zu den passenden Videos des Kanals – Funktionstests und Übungen inklusive.</p></div>
<div class="karte"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['karten']}</div><h3>Lernkarten inklusive</h3><p>Zum Ausdrucken und Ausschneiden: vorne Zeichnung und Fragen, hinten die Antworten.</p></div>
</div></section>

<section class="abschnitt dunkel"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Kostenlos lernen</p><h2 style="color:#fff">Schon jetzt üben – ohne Anmeldung</h2>
<p class="einleitung">Alle 112 Muskeln mit Zeichnung im Lexikon, Lernkarten zum Abfragen direkt im Browser und ein Lernplan bis zur Prüfung.</p></div></div>
<form class="ki-suche" action="{s.zu('muskeln/')}" method="get" role="search"><label for="start-suche">Muskel, Knochenpunkt oder Nerv suchen</label><div><input type="search" id="start-suche" name="q" placeholder="z. B. Trochanter major, N. femoralis …"><button class="knopf pro" type="submit">Suchen</button></div></form>
<div class="raster drei" style="margin-top:22px">
<a class="karte link dunkel-karte" href="{s.zu('muskeln/')}"><h3>{ICON['muskel']} Muskel-Lexikon</h3><p>Ursprung, Ansatz, Innervation und Funktion – mit Schemazeichnung und Video.</p></a>
<a class="karte link dunkel-karte" href="{s.zu('lernkarten/')}"><h3>{ICON['karten']} Lernkarten online</h3><p>Karteikasten-Prinzip: Was du sicher weißt, kommt seltener, was hakt, öfter.</p></a>
<a class="karte link dunkel-karte" href="{s.zu('lernplan/')}"><h3>{ICON['plan']} Lernplan</h3><p>Prüfungsdatum eingeben – du bekommst einen Plan, was du wann lernst.</p></a>
</div></div></section>

<section class="abschnitt"><div class="wrap newsletter ki-gratis">
<div class="nl-kopf"><div class="gratis-cover"><img src="{bild(s, 'cover-gratis.jpg')}" alt="Cover des kostenlosen Lernskripts" width="200" height="283" loading="lazy"></div>
<div><p class="oberzeile">Kostenloses Lernskript</p><h2>{esc(KOSTENLOS['gratis']['titel'])}</h2></div>
<p class="einleitung" style="margin:0">{esc(KOSTENLOS['gratis']['text'])}</p></div>
<div class="nl-form"><b>Direkt herunterladen – ohne Anmeldung</b><p class="klein">{esc(KOSTENLOS['gratis']['info'])}</p>
<a class="knopf primaer gross" href="{s.zu('downloads/gratis-bewegungsausmass.pdf')}" download>{ICON['download']} Lernskript herunterladen</a>
<a class="knopf" href="{E['youtube']}?sub_confirmation=1" rel="noopener">{ICON['video']} Kanal abonnieren</a></div>
</div></section>

<section class="abschnitt hell"><div class="wrap autor">
<div class="autor-bild" aria-hidden="true">DJ</div>
<div><p class="oberzeile">Über mich</p><h2>Seit {esc(z['seit'])} erkläre ich Anatomie auf YouTube</h2>
<p class="einleitung">Ich bin David Jungreithmayr, Sportwissenschafter und Sporttherapeut – unter anderem beim FK Austria Wien und bei der U18-Handball-Nationalmannschaft. Heute unterrichte ich an einer AHS in Wien und an der Universität Wien. Viele von euch haben nach einer Zusammenfassung zum Ausdrucken gefragt – daraus ist die Reihe „Anatomie kompakt“ entstanden.</p>
<a class="knopf" href="{s.zu('ueber/')}">Mehr über mich</a></div></div></section>

<section class="abschnitt"><div class="wrap" style="max-width:860px">
<h2>Häufige Fragen</h2>{faq_html(faq_liste(s)[:6])}
<p style="margin-top:18px"><a href="{s.zu('faq/')}">Alle Fragen und Antworten</a></p></div></section>

<section class="abschnitt eng"><div class="wrap"><div class="ki-schluss">
<div><h2>Bereit für die Prüfung?</h2><p>Starte mit der kostenlosen Leseprobe – oder hol dir gleich alle sieben Bände.</p></div>
<div class="knopfreihe"><a class="knopf pro gross" href="{s.zu('ebooks/komplettpaket/')}">Komplettpaket · {PAKETE[1]['preis']}</a><a class="knopf gross hell-rand" href="{s.zu('kostenlos/')}">Leseproben</a></div>
</div></div></section>'''
    schema = [{'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Know it – Anatomie und Training', 'inLanguage': 'de', **({'url': DOMAIN + '/'} if DOMAIN else {})}]
    seite('', 'Know it – Anatomie, Physiologie, Training: E-Books & Muskel-Lexikon',
          f'Anatomie verstehen, Prüfung bestehen: sieben E-Books zu Muskeln, Gelenken, Organen, Trainingslehre und Ernährung ab {AB_PREIS} – dazu ein kostenloses Muskel-Lexikon mit Zeichnungen, Lernkarten und Lernplan.',
          inhalt, schema=schema, voller_titel=True)


# ---------------------------------------------------------------- E-Books

def ebooks_index():
    def inhalt(s):
        zeilen = ''.join(f'<tr><td><a href="{s.zu("ebooks/" + p["slug"] + "/")}"><b>Band {p["band"]} · {esc(p["titel"])}</b></a></td><td>{esc(p["fuer_wen"].split(".")[0] if p["fuer_wen"] else "")}</td><td>{esc(p["info"].split(" · ")[0])}</td><td><b>{p["preis"]}</b></td></tr>' for p in PRODUKTE)
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>E-Books</li></ol></nav>
<p class="oberzeile">Know it – Anatomie kompakt</p><h1>E-Books zum Lernen</h1>
<p class="einleitung">Jeder Band bündelt ein Thema so, wie du es für Prüfung und Praxis brauchst: eine Seite pro Muskel bzw. eine Doppelseite pro Gelenk oder Thema, eigene Zeichnungen und Diagramme, Merkhilfen, Prüfungsfallen und QR-Codes zu den Videos. Zu jedem Band gibt es eine kostenlose Leseprobe.</p>
<h2 class="sr-only">Alle Bände</h2><div class="ki-buecher" style="margin-top:26px">{''.join(buchkarte(s, p) for p in PRODUKTE)}</div>
<div class="ki-pakete" style="margin-top:30px">{paket_banner(s, PAKETE[1])}{paket_banner(s, PAKETE[0])}</div>
</div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Welcher Band für welche Prüfung?</h2><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table>
<thead><tr><th>Band</th><th>Für wen</th><th>Umfang</th><th>Preis</th></tr></thead><tbody>{zeilen}</tbody></table></div></div></section>'''
    seite('ebooks/', 'E-Books Anatomie, Physiologie, Training und Ernährung', f'Sieben E-Books der Reihe „Anatomie kompakt“: Muskel-Atlanten, Gelenke, Skelett & Organe, Trainingslehre, Ernährung – ab {AB_PREIS}, mit Leseproben und Paketpreisen.', inhalt, aktiv='ebooks/')


def produktseiten():
    for p in PRODUKTE:
        muskeln = [m for m in MUSKELN if m['band'] == p['band']]

        def inhalt(s, p=p, muskeln=muskeln):
            punkte = ''.join(f'<li>{ICON["check"]}<span>{esc(x)}</span></li>' for x in p['punkte'])
            figs = ''.join(f'<figure><img src="{bild(s, f["bild"])}" alt="{esc(f["alt"])}" width="331" height="468" loading="lazy"><figcaption>{esc(f["text"])}</figcaption></figure>' for f in p['vorschau'])
            kap = ''.join(f'<li><details><summary>{esc(k["titel"])}</summary><div>{esc(k["inhalt"])}</div></details></li>' for k in p['kapitel'])
            pakete = [pk for pk in PAKETE if p['band'] in pk['baende']]
            paket_tipp = ''.join(f'<li><a href="{s.zu("ebooks/" + pk["slug"] + "/")}"><b>{pk["titel"]}</b> – {pk["preis"]} statt {pk["statt"]}</a></li>' for pk in pakete)
            ml = ''
            if muskeln:
                ml = f'<h2>Alle Muskeln dieses Bandes – kostenlos im Lexikon</h2><p>Ursprung, Ansatz, Innervation und Funktion stehen frei zugänglich im Muskel-Lexikon. Im Buch kommen Merkhilfe, Prüfungsfalle, Funktionstest, Übungen und Kurz-Check dazu.</p><ul class="ki-muskelwolke">' + ''.join(f'<li><a href="{s.zu("muskeln/" + m["slug"] + "/")}">{esc(m["name"])}</a></li>' for m in muskeln) + '</ul>'
            andere = ''.join(buchkarte(s, x) for x in PRODUKTE if x['slug'] != p['slug'])
            leiste_knopf = kauf_knopf(s, p['slug'], 'Kaufen', 'knopf primaer') if KAUF.get(p['slug']) else f'<a class="knopf primaer" href="{s.zu("downloads/leseprobe-" + p["slug"] + ".pdf")}" download>Leseprobe</a>'
            return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('ebooks/')}">E-Books</a></li><li>{esc(p['titel'])}</li></ol></nav>
<div class="produkt"><div class="produkt-bild"><img src="{bild(s, p['cover'])}" alt="Cover: {esc(p['titel'])}" width="360" height="509"></div>
<div><p class="oberzeile buchfarbe" style="--buchfarbe:{p['farbe']}">Band {p['band']} · Know it – Anatomie kompakt</p><h1 style="font-size:clamp(2.2rem,5.5vw,3.6rem)">{esc(p['titel'])}</h1>
<p class="einleitung">{esc(p['text'])}</p>
<div class="kaufbox" id="kaufbox"><div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap"><span class="preis">{p['preis']}</span><span class="marke gruen">Sofort als PDF</span></div>
<ul>{punkte}</ul>
<div class="knopfreihe">{kauf_knopf(s, p['slug'])}<a class="knopf gross" href="{s.zu('downloads/leseprobe-' + p['slug'] + '.pdf')}" download>{ICON['download']} Leseprobe ({p['leseprobe_seiten']} Seiten)</a></div>
<p class="klein">{esc(p['info'])}</p></div>
{f'<div class="hinweisbox paket-hinweis"><h2 class="paket-hinweis-titel">Im Paket günstiger</h2><ul class="ohne-punkte">{paket_tipp}</ul></div>' if paket_tipp else ''}
<h2>Für wen ist dieses Buch?</h2><p>{esc(p['fuer_wen'])}</p>
<h2>So sieht es innen aus</h2><div class="seiten-vorschau">{figs}</div>
<h2>Das steckt drin</h2><ul class="kapitelliste">{kap}</ul>
<div class="hinweisbox"><h3>Probier es aus</h3><p>{esc(p['probe_text'])}</p>
<a class="knopf" href="{s.zu('downloads/leseprobe-' + p['slug'] + '.pdf')}" download>{ICON['download']} Leseprobe herunterladen</a></div>
{ml}
</div></div></div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Die anderen Bände</h2><div class="ki-buecher">{andere}</div></div></section>
<div class="kaufleiste" aria-label="Schnellkauf"><span><b>{esc(p['titel'])}</b><span class="preis">{p['preis']}</span></span>{leiste_knopf}</div>'''
        schema = [{'@context': 'https://schema.org', '@type': 'Product', 'name': p['titel'], 'description': p['text'], 'category': 'E-Book',
                   'brand': {'@type': 'Brand', 'name': 'Know it – Anatomie und Training'}, 'image': [f'{DOMAIN}/assets/bilder/{p["cover"]}'] if DOMAIN else [],
                   'offers': {'@type': 'Offer', 'price': p['preis'].replace(' €', '').replace(',', '.'), 'priceCurrency': 'EUR',
                              'availability': 'https://schema.org/InStock' if KAUF.get(p['slug']) else 'https://schema.org/PreOrder'}}]
        seite(f'ebooks/{p["slug"]}/', f'{p["titel"]} – E-Book (Band {p["band"]})', kuerzen(p['text'], 155), inhalt, aktiv='ebooks/', og=f'og-band{p["band"]}.png', schema=schema, koerper_klasse='mit-kaufleiste')


def paketseiten():
    for pk in PAKETE:
        def inhalt(s, pk=pk):
            zeilen = ''.join(f'<tr><td><a href="{s.zu("ebooks/" + NACH_BAND[b]["slug"] + "/")}">Band {b} · {esc(NACH_BAND[b]["titel"])}</a></td><td>{esc(NACH_BAND[b]["info"].split(" · ")[0])}</td><td>{NACH_BAND[b]["preis"]}</td></tr>' for b in pk['baende'])
            proben = ''.join(f'<li><a href="{s.zu("downloads/leseprobe-" + NACH_BAND[b]["slug"] + ".pdf")}" download>{ICON["download"]} Leseprobe Band {b}: {esc(NACH_BAND[b]["titel"])}</a></li>' for b in pk['baende'])
            leiste_knopf = kauf_knopf(s, pk['slug'], 'Kaufen', 'knopf primaer') if KAUF.get(pk['slug']) else f'<a class="knopf primaer" href="{s.zu("kostenlos/")}">Leseproben</a>'
            return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('ebooks/')}">E-Books</a></li><li>{pk['titel']}</li></ol></nav>
{paket_banner(s, pk, h='h1')}
<div class="raster zwei" style="margin-top:34px;align-items:start">
<div><h2>Was drin ist</h2><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table><thead><tr><th>Band</th><th>Umfang</th><th>Einzeln</th></tr></thead><tbody>{zeilen}
<tr><td><b>Zusammen</b></td><td></td><td><s>{pk['statt']}</s> <b>{pk['preis']}</b></td></tr></tbody></table></div></div>
<div><h2>Erst reinschauen?</h2><p>Zu jedem Band gibt es eine kostenlose Leseprobe mit echten Seiten aus dem Buch.</p><ul class="ki-proben">{proben}</ul>
<p style="margin-top:14px;color:var(--tinte-3)">Du bekommst alle PDFs sofort nach dem Kauf. Persönliche Lizenz – ausdrucken erlaubt, Weitergabe nicht.</p></div></div>
</div></section>
<div class="kaufleiste" aria-label="Schnellkauf"><span><b>{pk['titel']}</b><span class="preis">{pk['preis']}</span></span>{leiste_knopf}</div>'''
        seite(f'ebooks/{pk["slug"]}/', f'{pk["titel"]} – {pk["unter"]}', f'{pk["text"]} {pk["preis"]} statt {pk["statt"]}.'[:158], inhalt, aktiv='ebooks/', koerper_klasse='mit-kaufleiste')


# ---------------------------------------------------------------- Muskel-Lexikon

def lexikon():
    baende = sorted({m['band'] for m in MUSKELN})

    def eintrag(s, m):
        such = ' '.join([m['name'], m['deutsch'], m['kapitel'], m['oberzeile'], m['lernen']['ursprung'], m['lernen']['ansatz'], m['lernen']['innervation'], ' '.join(m['funktion'])])
        return (f'<li data-suche="{esc(such)}" data-innerv="{esc(m["lernen"]["innervation"])}" data-band="{m["band"]}"><a href="{s.zu("muskeln/" + m["slug"] + "/")}"><span class="mini{"" if m["video"] else " grau"}" style="background:{FARBE[m["band"]] if m["video"] else ""}">{m["nr"]:02d}<small>{"Video" if m["video"] else "Text"}</small></span>'
                f'<span><b>{esc(m["name"])}</b><small>{esc(m["deutsch"])} · {esc(m["kapitel"])}</small></span></a></li>')

    def inhalt(s):
        teile = ''
        for b in baende:
            p = NACH_BAND[b]
            gruppen, alt = '', None
            for m in [x for x in MUSKELN if x['band'] == b]:
                if m['kapitel_id'] != alt:
                    gruppen += ('</ul></div>' if alt else '') + f'<div class="m-gruppe" id="{m["kapitel_id"]}"><h3 class="m-kapitel">{esc(m["kapitel"])}</h3><ul class="liste">'
                    alt = m['kapitel_id']
                gruppen += eintrag(s, m)
            gruppen += '</ul></div>'
            teile += (f'<div class="m-band" id="band{b}"><h2 style="border-left:6px solid {p["farbe"]};padding-left:12px">{esc(p["kurz"])} <small style="font-size:.55em;color:var(--tinte-3)">· Band {b}</small></h2>{gruppen}'
                      f'<div class="ki-band-tipp" style="--bf:{p["farbe"]}"><img src="{bild(s, p["cover"])}" alt="" width="60" height="85" loading="lazy"><p>Alle Muskeln dieses Abschnitts mit Merkhilfe, Prüfungsfalle, Funktionstest und Lernkarten: <b>{esc(p["titel"])}</b> · {p["preis"]}</p><a class="knopf klein" href="{s.zu("ebooks/" + p["slug"] + "/")}">Zum Buch</a></div></div>')
        nerven = ['N. femoralis', 'N. obturatorius', 'N. ischiadicus', 'N. tibialis', 'N. fibularis', 'N. gluteus superior', 'N. gluteus inferior',
                  'N. musculocutaneus', 'N. medianus', 'N. ulnaris', 'N. radialis', 'N. axillaris', 'N. accessorius', 'N. phrenicus', 'Nn. intercostales']
        zaehl = [(n, sum(1 for m in MUSKELN if n.lower() in m['lernen']['innervation'].lower())) for n in nerven]
        nerv_chips = ''.join(f'<button type="button" data-nerv="{esc(n)}">{esc(n)} <small>{z}</small></button>' for n, z in zaehl if z)
        filter_knoepfe = '<button type="button" aria-pressed="true" data-band="">Alle</button>' + ''.join(f'<button type="button" aria-pressed="false" data-band="{b}">{esc(NACH_BAND[b]["kurz"])}</button>' for b in baende)
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Muskel-Lexikon</li></ol></nav>
<p class="oberzeile">Muskel-Lexikon · kostenlos</p><h1>{len(MUSKELN)} Muskeln von Bein, Arm, Rumpf und Hals</h1>
<p class="einleitung">Ursprung, Ansatz, Innervation und Funktion – mit Schemazeichnung und, wo vorhanden, Video. Such nach einem Muskel, einem Knochenpunkt oder einem Nerv.</p>
<div class="ki-lexikon-werkzeug"><label class="such-feld" for="m-suche">Suche<input type="search" id="m-suche" placeholder="z. B. Trochanter major, N. radialis, Schulterblatt …" autocomplete="off"></label>
<div class="stufenwahl ki-bandwahl" role="group" aria-label="Körperregion">{filter_knoepfe}</div></div>
<div class="ki-nerven"><span>Welche Muskeln versorgt der …</span><div class="chips-wahl" role="group" aria-label="Nerven-Schnellwahl">{nerv_chips}</div></div>
<p class="treffer" id="m-treffer" aria-live="polite">{len(MUSKELN)} Muskeln</p>
<p class="treffer" id="m-leer" hidden>Nichts gefunden. Tipp: nur einen Teil des Wortes eingeben, z. B. „femoral“ oder „Trochanter“.</p>
<div id="m-liste">{teile}</div>
<div class="hinweisbox" style="margin-top:10px"><h3>{ICON['karten']} Lernen statt nur lesen</h3><p>Mit den kostenlosen <a href="{s.zu('lernkarten/')}">Lernkarten</a> fragst du dich zu allen {len(MUSKELN)} Muskeln selbst ab – Ursprung, Ansatz, Innervation, Funktion.</p></div>
</div></section>'''
    seite('muskeln/', f'Muskel-Lexikon: {len(MUSKELN)} Muskeln mit Ursprung, Ansatz, Innervation', f'Kostenloses Muskel-Lexikon: Ursprung, Ansatz, Innervation und Funktion von {len(MUSKELN)} Muskeln von Bein, Arm, Rumpf und Hals – mit Schemazeichnung und Video.',
          inhalt, aktiv='muskeln/', og='og-muskeln.png', voller_titel=True)

    for m in MUSKELN:
        p = NACH_BAND[m['band']]
        nachbarn = [x for x in MUSKELN if x['kapitel_id'] == m['kapitel_id'] and x['slug'] != m['slug']]

        def inhalt(s, m=m, p=p, nachbarn=nachbarn):
            extras = ''.join(f'<li>{ICON["check"]}<span>{esc(x)}</span></li>' for x in m['extras'])
            weitere = ''.join(eintrag(s, x) for x in nachbarn)
            video = video_block(m['video'], m['name'], m['farbe']) or '<div class="hinweisbox"><p>Zu diesem Muskel gibt es noch kein eigenes Video.</p></div>'
            return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('muskeln/')}">Muskel-Lexikon</a></li><li>{esc(m['name'])}</li></ol></nav>
<p class="oberzeile">{esc(m['oberzeile'])}</p><h1>{esc(m['name'])}</h1><p class="einleitung">{esc(m['deutsch'])} – Ursprung, Ansatz, Innervation und Funktion</p>
<div class="spiel-kopf"><div>{video}</div><div class="zeichnung" role="img" aria-label="Schemazeichnung {esc(m['name'])} mit Ursprung und Ansatz">{m['zeichnung']}</div></div>
<div class="raster zwei" style="margin-top:28px;align-items:start"><div><h2>Steckbrief</h2>{m['steckbrief_html']}<div class="funktion"><h3>Funktion</h3>{m['funktion_html']}</div>
<p style="margin-top:14px"><a class="knopf" href="{s.zu('lernkarten/')}#muskel={m['slug']}">{ICON['karten']} Diesen Muskel abfragen</a></p></div>
<div><h2>Zum Lernen</h2><div class="gesperrt"><img src="{bild(s, p['cover'])}" alt="Cover: {esc(p['titel'])}" width="150" height="212" loading="lazy">
<div><p class="oberzeile">E-Book · Band {p['band']} · {p['preis']}</p><h3>{esc(p['titel'])}</h3><p>Im E-Book findest du zu diesem Muskel außerdem:</p><ul>{extras}</ul>
<div class="knopfreihe">{kauf_knopf(s, p['slug'], 'Jetzt kaufen', 'knopf pro gross')}<a class="knopf gross hell-rand" href="{s.zu('ebooks/' + p['slug'] + '/')}">Mehr zum Buch</a></div></div></div></div></div>
{f'<h2 style="margin-top:34px">Weitere Muskeln: {esc(m["kapitel"])}</h2><ul class="liste">{weitere}</ul>' if weitere else ''}
</div></section>'''
        beschreibung = f'{m["name"]} ({m["deutsch"]}): Ursprung, Ansatz, Innervation ({kuerzen(m["lernen"]["innervation"], 40)}) und Funktion – mit Schemazeichnung' + (' und Video.' if m['video'] else '.')
        seite(f'muskeln/{m["slug"]}/', f'{m["name"]} – Ursprung, Ansatz, Innervation', beschreibung[:158], inhalt, aktiv='muskeln/', og='og-muskeln.png')


# ---------------------------------------------------------------- Weitere Seiten

def kostenlosseite():
    def inhalt(s):
        proben = ''.join(f'''<a class="karte link ki-probe-karte" href="{s.zu('downloads/leseprobe-' + p['slug'] + '.pdf')}" download><img src="{bild(s, p['cover'])}" alt="" width="70" height="99" loading="lazy"><span><b>Leseprobe Band {p['band']}: {esc(p['titel'])}</b><small>{esc(KOSTENLOS['leseproben'].get(p['slug'], ''))}</small></span></a>''' for p in PRODUKTE)
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Kostenlos</li></ol></nav>
<h1>Kostenlos lernen</h1><p class="einleitung">Ein Lernskript zum Bewegungsausmaß, Leseproben aller Bände, das Muskel-Lexikon und Lernkarten zum Abfragen – ohne Anmeldung.</p>
<div class="newsletter" style="margin-top:26px"><div class="nl-kopf"><div class="gratis-cover"><img src="{bild(s, 'cover-gratis.jpg')}" alt="Cover des kostenlosen Lernskripts" width="200" height="283"></div>
<div><p class="oberzeile">Kostenloses Lernskript</p><h2>{esc(KOSTENLOS['gratis']['titel'])}</h2></div><p class="einleitung" style="margin:0">{esc(KOSTENLOS['gratis']['text'])}</p></div>
<div class="nl-form"><b>Direkt herunterladen – ohne Anmeldung</b><p class="klein">{esc(KOSTENLOS['gratis']['info'])}</p><a class="knopf primaer gross" href="{s.zu('downloads/gratis-bewegungsausmass.pdf')}" download>{ICON['download']} Lernskript herunterladen</a>
<a class="knopf" href="{E['youtube']}?sub_confirmation=1" rel="noopener">{ICON['video']} Kanal abonnieren</a></div></div>
</div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Leseproben aller Bände</h2><p class="einleitung">Echte Seiten aus jedem Buch – so siehst du genau, was dich erwartet.</p><div class="raster zwei">{proben}</div></div></section>
<section class="abschnitt"><div class="wrap raster drei">
<a class="karte link" href="{s.zu('muskeln/')}"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['muskel']}</div><h3>Muskel-Lexikon</h3><p>Alle {len(MUSKELN)} Muskeln mit Ursprung, Ansatz, Innervation, Funktion und Zeichnung.</p></a>
<a class="karte link" href="{s.zu('lernkarten/')}"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['karten']}</div><h3>Lernkarten</h3><p>Karteikarten und Quiz direkt im Browser – dein Lernstand bleibt auf deinem Gerät.</p></a>
<a class="karte link" href="{s.zu('lernplan/')}"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['plan']}</div><h3>Lernplan</h3><p>Vom heutigen Tag bis zur Prüfung: Was lerne ich wann?</p></a>
</div></section>'''
    seite('kostenlos/', 'Kostenlos: Lernskript, Leseproben, Lernkarten', 'Kostenloses Lernskript „Bewegungsausmaß“, Leseproben aller sieben E-Books, Muskel-Lexikon, Lernkarten und Lernplan – ohne Anmeldung.', inhalt, aktiv='kostenlos/')


def ueberseite():
    def inhalt(s):
        z = E['zahlen']
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Über mich</li></ol></nav>
<div class="autor"><div class="autor-bild" aria-hidden="true">DJ</div><div><p class="oberzeile">Über mich</p><h1>Hallo, ich bin DJ</h1>
<p class="autor-titel">David Jungreithmayr · Sportwissenschafter und Sporttherapeut</p>
<p class="einleitung">Ich unterrichte Bewegung und Sport an einer AHS in Wien und halte Lehrveranstaltungen an der Universität Wien. Seit {esc(z['seit'])} erkläre ich auf „Know it – Anatomie und Training“ Anatomie, Physiologie und Training.</p></div></div>
<div class="textseite" style="margin-top:30px">
<h2>Mein Werdegang</h2>
<p>Mag. Mag. David Jungreithmayr – studiert habe ich Sportwissenschaft (Bakkalaureat Leistungssport, Magister) und das Lehramt Bewegung und Sport sowie Psychologie und Philosophie. Anatomie und Training kenne ich nicht nur aus dem Hörsaal, sondern aus der Arbeit mit Leistungssportler:innen.</p>
<div class="werdegang">
<div class="karte"><h3>Spitzensport</h3><p>Sportwissenschafter und Sporttherapeut beim FK Austria Wien (2009–2012), Sporttherapeut der U18-Handball-Nationalmannschaft (2010–2012).</p></div>
<div class="karte"><h3>Ausbildungen</h3><p>Klassische Massage, Sportmassage und Sporttherapie, Nachwuchstrainer Fußball.</p></div>
<div class="karte"><h3>Lehre</h3><p>Externer Lehrbeauftragter an der Universität Wien, Lehrer für Bewegung und Sport an einer AHS in Wien, Vorträge an Pädagogischen Hochschulen, in der Lehrer:innenfortbildung und bei sportmedizinischen Fachgesellschaften (Trainingstherapie).</p></div>
<div class="karte"><h3>Publikationen &amp; Vorträge</h3><p>Fachbeiträge u. a. in „Sportphysiotherapie“ und „Running &amp; Fitness“ (Sport und Gesundheit, Marathon-Vorbereitung), das Buch „Gesundheitsförderung kompakt“ (2015), Vorträge auf Kongressen wie dem Internationalen Kongress für Sportphysiotherapie und dem HELLP-Symposium zu Bewegung und Gehirnentwicklung.</p></div>
</div>
<h2>Warum Know it?</h2>
<p>Anatomie wirkt beim ersten Lernen wie eine endlose Liste lateinischer Begriffe. Wer aber versteht, wo ein Muskel beginnt, wo er ansetzt und über welches Gelenk er zieht, kann seine Funktion ableiten statt auswendig zu lernen. Genau das zeigen die Videos – kurz, bildhaft und so, dass du es in der Prüfung wiedergeben kannst.</p>
<p>Die Videos wurden bisher rund {esc(z['aufrufe'])} Mal aufgerufen. Viele von euch haben nach einer Zusammenfassung zum Ausdrucken gefragt – daraus ist die Reihe „Anatomie kompakt“ entstanden.</p>
<div class="knopfreihe"><a class="knopf" href="{E['youtube']}" rel="noopener">{ICON['video']} Zum YouTube-Kanal</a><a class="knopf primaer" href="{s.zu('ebooks/')}">{ICON['buch']} Zu den E-Books</a></div>
<h2>Auch von mir: Sportunterricht</h2>
<p>Auf dem Kanal <b>Sportunterricht</b> zeige ich Spiele und Übungen für Bewegung und Sport in der Schule. Auf der <a href="{esc(E['sportunterricht_url'])}/">Sportunterricht-Website</a> gibt es dazu ein Spiele-Lexikon, einen Stundenplaner und Werkzeuge für die Halle.</p>
</div></div></section>'''
    seite('ueber/', 'Über mich – DJ, Know it', 'DJ unterrichtet Bewegung und Sport an einer AHS in Wien, hält Lehrveranstaltungen an der Universität Wien und erklärt seit 2016 Anatomie auf YouTube.', inhalt)


def faqseite():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap" style="max-width:860px">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Häufige Fragen</li></ol></nav>
<h1>Häufige Fragen</h1><p class="einleitung">Zu E-Books, Bezahlung, Nutzung und Datenschutz.</p>{faq_html(faq_liste(s))}</div></section>'''
    l = faq_liste(Seite('faq/'))
    seite('faq/', 'Häufige Fragen', 'Antworten zu Download, Bezahlung über Digistore24, Ausdrucken, Lizenz und Widerruf.', inhalt,
          schema=[{'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [{'@type': 'Question', 'name': f, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for f, a in l]}])


def rechtsseiten():
    name, anschrift = esc(E.get('name_voll') or 'Vor- und Nachname'), esc(E.get('anschrift') or 'Straße Nr., PLZ Ort, Österreich')
    mail = f'<a href="mailto:{E["email"]}">{esc(E["email"])}</a>' if E.get('email') else 'E-Mail-Adresse'
    if not all(E.get(k) for k in ('name_voll', 'anschrift', 'email')):
        WARNUNGEN.append('Impressum unvollständig: name_voll, anschrift, email in einstellungen.json eintragen.')
    digi = 'Digistore24 GmbH, St.-Godehard-Straße 32, 31139 Hildesheim, Deutschland'

    def impressum(s):
        return f'''<section class="abschnitt"><div class="wrap textseite">
<h1>Impressum</h1><h2>Angaben gemäß § 5 E-Commerce-Gesetz und § 25 Mediengesetz</h2>
<p><b>Medieninhaber und Diensteanbieter:</b><br>{name}<br>{anschrift}</p><p><b>Kontakt:</b> {mail}</p>
<p><b>Unternehmensgegenstand:</b> {esc(E.get('unternehmensgegenstand', ''))}</p>
{f'<p><b>UID-Nummer:</b> {esc(E["uid"])}</p>' if E.get('uid') else ''}
<p><b>Grundlegende Richtung (Blattlinie):</b> Information und Lernmaterialien zu Anatomie, Physiologie und Training.</p>
<h2>Verkauf</h2><p>Die E-Books werden über <b>{digi}</b>, als Wiederverkäufer vertrieben. Digistore24 ist Vertragspartner beim Kauf und für Zahlung, Rechnung und Umsatzsteuer zuständig.</p>
<h2>Gesundheitshinweis und Haftung</h2><p>Die Inhalte dienen dem Lernen und der Weiterbildung. Sie ersetzen keine ärztliche oder physiotherapeutische Untersuchung, Diagnose oder Behandlung. Für Inhalte verlinkter externer Seiten sind ausschließlich deren Betreiber verantwortlich.</p>
<h2>Urheberrecht</h2><p>Texte, Zeichnungen, Videos und E-Books sind urheberrechtlich geschützt. Jede Verwertung außerhalb der gekauften Lizenz braucht eine schriftliche Zustimmung.</p>
</div></section>'''

    def datenschutz(s):
        return f'''<section class="abschnitt"><div class="wrap textseite">
<h1>Datenschutzerklärung</h1><p>Kurz gesagt: Diese Website verwendet <b>keine Cookies, kein Tracking und keine Werbung</b>. Schriften werden von dieser Website selbst geladen, nicht von Google.</p>
<h2>Verantwortlicher</h2><p>{name}, {anschrift}, {mail}</p>
<h2>Hosting</h2><p>Die Website wird bei <b>Netlify, Inc.</b> (San Francisco, USA) gehostet. Beim Aufruf verarbeitet der Server technisch notwendige Daten (IP-Adresse, Zeitpunkt, aufgerufene Seite, Browser), um die Seite auszuliefern und vor Missbrauch zu schützen – Rechtsgrundlage ist unser berechtigtes Interesse an einem sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO). Die Übermittlung in die USA stützt sich auf das EU-US Data Privacy Framework bzw. Standardvertragsklauseln.</p>
<h2 id="youtube">YouTube-Videos (Zwei-Klick-Lösung)</h2><p>Videos werden erst geladen, wenn du auf „Video ansehen“ klickst. Erst dann wird eine Verbindung zu YouTube (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland) über die Domain youtube-nocookie.com aufgebaut; dabei gelten die Datenschutzbestimmungen von Google. Rechtsgrundlage ist deine Einwilligung durch den Klick (Art. 6 Abs. 1 lit. a DSGVO).</p>
<h2>Lernkarten, Lernplan und Rechner</h2><p>Lernstand, Lernplan und Eingaben in den Rechnern werden ausschließlich lokal in deinem Browser gespeichert (Local Storage) bzw. gar nicht gespeichert. Es gibt kein Konto und keinen Server, an den diese Daten gesendet werden. Du kannst sie jederzeit über die Knöpfe auf den Seiten oder in den Browser-Einstellungen löschen.</p>
<h2>Kauf über Digistore24</h2><p>Wenn du ein E-Book kaufst, wirst du zu Digistore24 weitergeleitet. Digistore24 verarbeitet als Vertragspartner die für den Kauf nötigen Daten (Art. 6 Abs. 1 lit. b DSGVO) nach seiner eigenen Datenschutzerklärung. Wir erhalten die für Auslieferung und Buchhaltung nötigen Bestelldaten.</p>
<h2>Kontakt per E-Mail</h2><p>Wenn du uns schreibst, verarbeiten wir deine Angaben, um deine Anfrage zu beantworten (Art. 6 Abs. 1 lit. b bzw. f DSGVO), und löschen sie, wenn sie nicht mehr gebraucht werden.</p>
<h2>Deine Rechte</h2><p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht, eine Einwilligung jederzeit zu widerrufen. Beschweren kannst du dich bei der österreichischen Datenschutzbehörde (www.dsb.gv.at).</p>
<p style="color:var(--tinte-3)">Stand: {HEUTE.strftime('%m/%Y')}</p></div></section>'''

    def agb(s):
        return f'''<section class="abschnitt"><div class="wrap textseite">
<h1>AGB, Nutzungsbedingungen &amp; Widerruf</h1>
<h2>1. Vertragspartner beim Kauf</h2><p>Alle Käufe werden über <b>{digi}</b>, abgewickelt. Digistore24 ist Wiederverkäufer und dein Vertragspartner; für den Kaufvertrag gelten die AGB von Digistore24, die dir im Bestellvorgang angezeigt werden.</p>
<h2>2. Nutzungsrechte an den E-Books</h2><ul><li>Du darfst das E-Book für dein eigenes Lernen nutzen, auf deinen Geräten speichern und für den eigenen Gebrauch ausdrucken.</li>
<li>Nicht erlaubt sind Weitergabe, Veröffentlichung, Weiterverkauf und das Hochladen auf Plattformen, in Lernplattformen oder Gruppen-Chats – auch nicht in Auszügen.</li></ul>
<h2>3. Widerrufsrecht bei digitalen Inhalten</h2><p>Verbraucher:innen haben grundsätzlich ein 14-tägiges Widerrufsrecht. Bei digitalen Inhalten, die nicht auf einem körperlichen Datenträger geliefert werden, erlischt es, wenn du ausdrücklich zustimmst, dass die Lieferung vor Ablauf der Widerrufsfrist beginnt, und bestätigst, dass du dadurch dein Widerrufsrecht verlierst. Diese Zustimmung holt Digistore24 im Bestellvorgang ein. Schau dir deshalb vorher gern die kostenlose Leseprobe an.</p>
<h2>4. Gesundheit</h2><p>Die Inhalte dienen dem Lernen. Die Übungen sind allgemeine Beispiele für gesunde Personen und ersetzen keine ärztliche oder physiotherapeutische Beratung. Für Schäden aus der Anwendung wird – soweit gesetzlich zulässig – keine Haftung übernommen.</p>
<h2>5. Kontakt</h2><p>{name}, {anschrift}, {mail}</p></div></section>'''
    seite('impressum/', 'Impressum', 'Impressum und Offenlegung gemäß E-Commerce-Gesetz und Mediengesetz.', impressum)
    seite('datenschutz/', 'Datenschutzerklärung', 'Keine Cookies, kein Tracking: So geht diese Website mit deinen Daten um.', datenschutz)
    seite('agb/', 'AGB, Nutzungsbedingungen & Widerruf', 'Nutzungsrechte an den E-Books und Widerrufsrecht bei digitalen Inhalten.', agb)


def dankeseite():
    def inhalt(s):
        kontakt = f'<a href="mailto:{E["email"]}">{esc(E["email"])}</a>' if E.get('email') else 'die E-Mail-Adresse im Impressum'
        return f'''<section class="abschnitt"><div class="wrap textseite">
<p class="oberzeile">Bestellung abgeschlossen</p><h1>Danke für deinen Kauf!</h1>
<p class="einleitung">Viel Erfolg beim Lernen! So geht es weiter:</p>
<ol class="haken" style="list-style:none">
<li>{ICON['check']}<span><b>Download:</b> Den Link zu deinen PDFs findest du auf der Bestätigungsseite von Digistore24 und in der E-Mail von Digistore24 – zusammen mit deiner Rechnung.</span></li>
<li>{ICON['check']}<span><b>Keine E-Mail da?</b> Schau bitte im Spam-Ordner nach. Wenn sie nach einer Stunde noch fehlt, schreib mir an {kontakt} – mit deiner Bestellnummer.</span></li>
<li>{ICON['check']}<span><b>Lerntipp:</b> Druck die Lernkarten aus dem Anhang aus und kombiniere sie mit den <a href="{s.zu('lernkarten/')}">Online-Lernkarten</a> und deinem <a href="{s.zu('lernplan/')}">Lernplan</a>.</span></li></ol>
</div></section>'''
    seite('danke/', 'Danke für deinen Kauf', 'Danke für deinen Kauf – so kommst du zu deinen E-Books.', inhalt, noindex=True)


def nicht_gefunden():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap nichtgefunden"><div>
<p class="gross">404</p><h1>Diese Seite gibt es nicht.</h1><p class="einleitung">Vielleicht hilft einer dieser Wege weiter:</p>
<div class="knopfreihe" style="justify-content:center"><a class="knopf primaer" href="{s.zu('')}">Zur Startseite</a><a class="knopf" href="{s.zu('muskeln/')}">Muskel-Lexikon</a><a class="knopf" href="{s.zu('ebooks/')}">E-Books</a></div></div></div></section>'''
    seite('404.html', 'Seite nicht gefunden', 'Diese Seite gibt es nicht.', inhalt, noindex=True)
    p = OUT / '404.html'
    t = p.read_text()
    for alt in ('href="assets/', 'src="assets/', 'href="muskeln/', 'href="ebooks/', 'href="kostenlos/', 'href="lernkarten/', 'href="lernplan/', 'href="rechner/',
                'href="ueber/', 'href="faq/', 'href="impressum/', 'href="datenschutz/', 'href="agb/', 'href="./"', 'src="assets/'):
        t = t.replace(alt, alt.replace('="', '="/').replace('/./', '/'))
    p.write_text(t)


# ---------------------------------------------------------------- Zusatzseiten (Lernkarten, Lernplan, Rechner) – siehe zusatz.py
from zusatz import lernkartenseite, lernplanseite, rechnerseite  # noqa: E402


# ---------------------------------------------------------------- Dateien

def dateien():
    OUT.mkdir(exist_ok=True)
    for x in OUT.iterdir():
        shutil.rmtree(x) if x.is_dir() else x.unlink()
    a = OUT / 'assets'
    a.mkdir()
    # Designsystem wie Sportunterricht + Know-it-Bausteine + Know-it-Erweiterungen
    (a / 'site.css').write_text((WEB / 'site.css').read_text() + '\n' + (HIER / 'statisch/knowit-teil.css').read_text() + '\n' + (HIER / 'statisch/knowit.css').read_text())
    shutil.copy(WEB / 'site.js', a / 'site.js')
    for js in ('knowit.js', 'lernkarten.js', 'lernplan.js', 'rechner.js'):
        shutil.copy(HIER / 'statisch' / js, a / js)
    shutil.copytree(HIER / 'statisch/fonts', a / 'fonts')
    shutil.copytree(HIER / 'statisch/bilder', a / 'bilder')
    shutil.copytree(HIER / 'statisch/og', a / 'og')
    shutil.copy(HIER / 'statisch/icon.svg', a / 'icon.svg')
    shutil.copytree(HIER / 'statisch/downloads', OUT / 'downloads')


def meta():
    if DOMAIN:
        urls = ''.join(f'<url><loc>{url_abs(p) if p else DOMAIN + "/"}</loc><lastmod>{HEUTE.isoformat()}</lastmod></url>' for p in SITEMAP)
        (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')
    else:
        (OUT / 'robots.txt').write_text('User-agent: *\nAllow: /\n')
    (OUT / '_headers').write_text('''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
/assets/fonts/*
  Cache-Control: public, max-age=31536000, immutable
/assets/*
  Cache-Control: public, max-age=86400
''')


def main():
    dateien()
    startseite()
    ebooks_index()
    produktseiten()
    paketseiten()
    lexikon()
    kostenlosseite()
    ueberseite()
    faqseite()
    rechtsseiten()
    dankeseite()
    lernkartenseite(seite, E, MUSKELN, NACH_BAND, ICON, esc)
    lernplanseite(seite, E, PRODUKTE, ICON, esc)
    rechnerseite(seite, E, NACH_BAND, ICON, esc)
    nicht_gefunden()
    meta()
    seiten = len(list(OUT.rglob('index.html')))
    groesse = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file()) / 1e6
    print(f'✓ Know it gebaut: {seiten} Seiten, {groesse:.1f} MB → {OUT}')
    for w in dict.fromkeys(WARNUNGEN):
        print('  ⚠', w)


if __name__ == '__main__':
    main()
