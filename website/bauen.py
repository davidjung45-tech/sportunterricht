"""Baut die komplette Website „Sportunterricht“ als statische Seiten (Netlify-fertig).

    python3 bauen.py              # → ausgabe/        (für Netlify: saubere URLs wie /ebooks/)
    python3 bauen.py --vorschau   # → vorschau/       (zum lokalen Öffnen: Links zeigen auf …/index.html)

Einzige Datei zum Anpassen: einstellungen.json (Domain, Impressum-Daten, Digistore24-Kauflinks, Newsletter).
Daten kommen automatisch aus der Stammdaten-Excel (über die App) und aus den E-Book-PDFs.
"""
import html
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent
APP = HIER.parent / 'sportunterricht-app-v2'
EBOOKS = HIER.parent / 'ebooks'
PDFS = EBOOKS / 'ausgabe'
sys.path.insert(0, str(EBOOKS / 'werkzeug'))
import pdf as buchpdf  # noqa: E402  (Reihe, Preise, Kartenlogik, Excel-Overrides)
from buch import parse, stufen_text  # noqa: E402
from weasyprint import HTML  # noqa: E402

ARTIFACT = '--artifact' in sys.argv   # kompakte Vorschau für claude.ai (ohne dünne Lexikon-Seiten, Videos öffnen YouTube)
VORSCHAU = '--vorschau' in sys.argv or ARTIFACT
OUT = HIER / ('artifact' if ARTIFACT else 'vorschau' if VORSCHAU else 'ausgabe')
E = json.loads((HIER / 'einstellungen.json').read_text())
DOMAIN = (E.get('domain') or '').rstrip('/')
KAUF = E.get('kaufen', {})
WARNUNGEN = []
HEUTE = date.today()
esc = html.escape

# Die App (sportunterricht-app-v2) ist optional: Fehlt sie, baut die Website trotzdem vollständig –
# Videodaten kommen dann aus ebooks/werkzeug/alle_videos.json, Anleitungen aus den E-Book-Texten (inhalt.md),
# und unter /app/ steht eine Hinweisseite statt der App.
APP_DA = (APP / 'dist' / 'index.html').exists()
SCHRIFTEN = HIER / 'statisch/fonts'


def lade_json(*kandidaten, leer=None):
    for k in kandidaten:
        if k.exists():
            return json.loads(k.read_text())
    return leer


def anleitungen_aus_buechern():
    """Ersatz für anleitungen.json: Kurzdaten jedes Spiels aus den Spielbänden (inhalt.md)."""
    namen = {'spielesammlung': '50 kreative & kooperative Spiele', 'aufwaermen': 'Aufwärmen in 5 Minuten',
             'turnen': 'Turnen sicher unterrichten', 'fitness': 'Fit im Schulsport'}
    anl = {}
    for slug, buchname in namen.items():
        datei = EBOOKS / slug / 'inhalt.md'
        if not datei.exists():
            continue
        for k in parse(datei.read_text())['kapitel']:
            for e in k['eintraege']:
                if not e['id'] or e['id'] in anl:
                    continue
                ab = dict(e['abschnitte'])
                m = e['meta']
                anl[e['id']] = {'name': e['name'], 'beschreibung': ab.get('Spielbeschreibung') or ab.get('Zielbewegung') or '',
                                'lernziel': m.get('Lernziel', ''), 'materialText': m.get('Material', ''), 'gruppe': m.get('Gruppengröße', ''),
                                'buch': buchname, 'methodik': bool(ab.get('Methodische Reihe')),
                                'dauer': m.get('Dauer', ''), 'stundenteil': m.get('Stundenteil', ''), 'intensitaet': m.get('Intensität', '')}
    return anl


VIDEOS = [v for v in lade_json(APP / 'src/generated/videos.json', EBOOKS / 'werkzeug/alle_videos.json', leer=[])
          if not v.get('ausgeblendet') and re.fullmatch(r'[\w-]{11}', v.get('id', ''))]
ANL = lade_json(APP / 'src/generated/anleitungen.json') or anleitungen_aus_buechern()
FUNDORTE = lade_json(PDFS / 'fundorte.json', leer={})
REIHE = buchpdf.REIHE
KOMPLETT = buchpdf.KOMPLETT
N_BAENDE, BAENDE_WORT = buchpdf.N_BAENDE, buchpdf.BAENDE_WORT
SPIELBAENDE = [b for b in REIHE if b['slug'] not in ('praktikum', 'alle-dabei')]
BUCH_NACH_NAME = {'50 kreative & kooperative Spiele': 'spielesammlung', 'Aufwärmen in 5 Minuten': 'aufwaermen',
                  'Turnen sicher unterrichten': 'turnen', 'Fit im Schulsport': 'fitness'}
BAND = {b['slug']: b for b in REIHE}

THEMA = {
    'fangen': ('Fangen & Laufen', '#c8402a'), 'kleine_spiele': ('Kleine Spiele', '#1f5bd8'), 'ball': ('Ballspiele', '#a4480f'),
    'kooperation': ('Kooperation', '#167a4b'), 'turnen': ('Turnen & Akrobatik', '#5b3fa8'), 'koordination': ('Koordination', '#0d6f78'),
    'kraft': ('Kraft & Fitness', '#8a3d12'), 'leichtathletik': ('Leichtathletik', '#a3274f'), 'rueckschlag': ('Rückschlagspiele', '#255f91'),
    'ausdruck': ('Tanz & Ausdruck', '#8c3582'), 'parkour': ('Parkour & Trendsport', '#4b5c10'), 'schwimmen': ('Schwimmen', '#0b6597'),
}
MATERIAL = {'standard': 'Standard-Hallenmaterial', 'tore': 'Tore, Körbe oder Netz', 'matten': 'Matten & Bänke', 'geraete': 'Turngeräte', 'schwimmbad': 'Schwimmbad'}

# ---------------------------------------------------------------- Hilfen


def slugify(t):
    t = t.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    t = unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')[:70] or 'spiel'


def zahl_de(n):
    return f'{n:,}'.replace(',', '.')


def mio(n):
    return f'{n / 1_000_000:.1f}'.replace('.', ',') + ' Mio.'


def saetze(text, n=2):
    teile = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ„"])', (text or '').strip())
    return ' '.join(teile[:n])


def datum_iso(d):
    try:
        return datetime.strptime(d, '%b %d, %Y').date().isoformat()
    except (ValueError, TypeError):
        return None


def dauer_iso(sek):
    m, s = divmod(int(sek or 0), 60)
    return f'PT{m}M{s}S'


def pdf_seiten(p):
    try:
        out = subprocess.run(['pdfinfo', str(p)], capture_output=True, text=True).stdout
        return int(re.search(r'Pages:\s+(\d+)', out).group(1))
    except Exception:  # noqa: BLE001
        return None


class Seite:
    """Eine Seite unter einem Pfad wie 'ebooks/turnen/' – kennt ihre Tiefe für relative Links."""

    def __init__(self, pfad):
        self.pfad = pfad.strip('/')
        teile = [x for x in self.pfad.split('/') if x]
        # 'ebooks/turnen/' liegt zwei Ordner tief; eine Datei wie '404.html' liegt im Wurzelordner (Tiefe 0)
        self.tiefe = len(teile) - 1 if self.pfad.endswith('.html') else len(teile)

    def zu(self, ziel):
        """Relativer Link zu einem Ziel-Pfad ('' = Startseite, 'ebooks/' = Ordner, 'downloads/x.pdf' = Datei)."""
        pre = '../' * self.tiefe
        if ziel.startswith(('http', 'mailto:', '#')):
            return ziel
        if ziel == '' or ziel.endswith('/'):
            return (pre + ziel + ('index.html' if VORSCHAU else '')) or './'
        return pre + ziel


def url_abs(pfad):
    return f'{DOMAIN}/{pfad.strip("/")}{"/" if pfad and not pfad.endswith((".html", ".pdf", ".xml")) else ""}' if DOMAIN else None


ICON = {
    'raum': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="4.5" width="19" height="15" rx="2"/><path d="M12 4.5v15"/><circle cx="12" cy="12" r="2.5"/><rect x="5" y="7.5" width="4" height="2" rx=".5"/><rect x="15" y="14.5" width="4" height="2" rx=".5"/></svg>',
    'pause': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="13" cy="4.5" r="2"/><path d="M8 21l2.5-6.5L13 16v5M10.5 14.5L12 9l-4 1.5L6.5 13M12 9l3 2.5 3.5.5"/></svg>',
    'herz': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 7 4.5c2 0 3.6 1.1 5 3 1.4-1.9 3-3 5-3 3.6 0 5.6 3.5 4.3 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/></svg>',
    'timer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="13.5" r="7.5"/><path d="M12 9.5v4l2.5 2M9.5 2.5h5M12 2.5V6"/></svg>',
    'teams': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="8" cy="8" r="3"/><circle cx="16.5" cy="9" r="2.5"/><path d="M2.5 19.5c.6-3.3 2.7-5 5.5-5s4.9 1.7 5.5 5M14 14.7c.8-.4 1.6-.6 2.5-.6 2.3 0 4 1.4 4.5 4.4"/></svg>',
    'punkte': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M12 5v14M6.5 10.5h2v4M15.5 10.5h2l-2 4h2"/></svg>',
    'planer': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3.5" y="4.5" width="17" height="16" rx="2.5"/><path d="M8 2.5v4M16 2.5v4M3.5 9.5h17M7.5 13.5h4M7.5 16.5h7"/></svg>',
    'drucken': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6.5 9V3.5h11V9M6.5 17.5h-2a2 2 0 01-2-2V11a2 2 0 012-2h15a2 2 0 012 2v4.5a2 2 0 01-2 2h-2"/><rect x="6.5" y="14" width="11" height="6.5" rx="1"/></svg>',
    'check': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    'play': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.8v14.4c0 .8.9 1.3 1.6.8l11-7.2a1 1 0 000-1.6l-11-7.2C7.9 3.5 7 4 7 4.8z"/></svg>',
    'pfeil': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4v11M7 10l5 5 5-5M5 20h14"/></svg>',
    'menue': '<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    'buch': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 016.5 3H20v15H6.5A2.5 2.5 0 004 20.5v-15z"/><path d="M4 20.5A2.5 2.5 0 016.5 18H20v3H6.5A2.5 2.5 0 014 20.5z"/></svg>',
    'handy': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M11 18.5h2"/></svg>',
    'video': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2.5" y="5" width="15" height="14" rx="3"/><path d="M17.5 10l4-2.5v9l-4-2.5"/></svg>',
    'schule': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10l9-6 9 6-9 6-9-6z"/><path d="M7 12.5V17c0 1 2.2 3 5 3s5-2 5-3v-4.5"/></svg>',
    'zufall': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8.5" cy="8.5" r="1.3" fill="currentColor"/><circle cx="15.5" cy="15.5" r="1.3" fill="currentColor"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/></svg>',
    'student': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h6l1 4H8l1-4z"/><rect x="5" y="7" width="14" height="14" rx="2"/><path d="M9 12h6M9 16h4"/></svg>',
}
LOGO_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M12 5v14"/><circle cx="12" cy="12" r="3"/></svg>'
FELD = '<svg class="feld" viewBox="0 0 400 260" fill="none" stroke="#fff" stroke-width="4" aria-hidden="true"><rect x="10" y="10" width="380" height="240" rx="6"/><path d="M200 10v240"/><circle cx="200" cy="130" r="42"/><rect x="10" y="80" width="60" height="100"/><rect x="330" y="80" width="60" height="100"/></svg>'

NAVI = [('spiele/', 'Spiele', 'über 480 Videos mit Filter'), ('planer/', 'Stunde planen', 'in 10 Sekunden, druckbar'),
        ('werkzeuge/', 'Werkzeuge', 'Timer, Teams, Punkte, Zufall'), ('ebooks/', 'E-Books', 'die Praxis-Reihe'), ('app/', 'App', 'die App fürs Handy'),
        ('schulen/', 'Für Schulen', 'Schullizenz'), ('ueber/', 'Über mich', '')]


if not APP_DA:
    NAVI = [x for x in NAVI if x[0] != 'app/']


def kauf_knopf(s, schluessel, text='Jetzt kaufen', klasse='knopf primaer gross'):
    link = KAUF.get(schluessel, '')
    if link:
        # Ohne JavaScript führt der Link direkt zu Digistore24; mit JavaScript öffnet sich vorher der Kauf-Dialog (site.js)
        return f'<a class="{klasse}" href="{esc(link)}" rel="noopener" data-kauf="{esc(schluessel)}">{text}</a>'
    WARNUNGEN.append(f'Kauf-Link fehlt: kaufen.{schluessel}')
    return f'<a class="{klasse}" href="{s.zu("kostenlos/")}#newsletter" title="Der Shop startet in Kürze">Bald erhältlich – benachrichtigen</a>'


def seite(pfad, titel, beschreibung, inhalt, aktiv='', og='og-start.png', schema=None, noindex=False, voller_titel=False, skripte=()):
    s = Seite(pfad)
    t = titel if voller_titel else f'{titel} · Sportunterricht'
    kan = url_abs(pfad)
    og_url = f'{DOMAIN}/assets/og/{og}' if DOMAIN else s.zu(f'assets/og/{og}')
    cta_ziel = 'app/' if APP_DA else 'planer/'  # der blaue Knopf oben rechts – steht dann nicht noch einmal in der Leiste
    navi = ''.join(f'<li><a href="{s.zu(z)}"{AKTIV if aktiv == z else ""}>{n}</a></li>' for z, n, _ in NAVI if z != cta_ziel)
    menue = ''.join(f'<a href="{s.zu(z)}"{AKTIV if aktiv == z else ""}>{n}<small>{u}</small></a>' for z, n, u in NAVI)
    schema_html = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (schema or []))
    kopf = f'''<!doctype html>
<html lang="de-AT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(t)}</title>
<meta name="description" content="{esc(beschreibung)}">
{f'<link rel="canonical" href="{kan}">' if kan else ''}
{'<meta name="robots" content="noindex, follow">' if noindex else ''}
<meta name="theme-color" content="#13211b">
<meta property="og:type" content="website">
<meta property="og:locale" content="de_AT">
<meta property="og:site_name" content="Sportunterricht">
<meta property="og:title" content="{esc(titel)}">
<meta property="og:description" content="{esc(beschreibung)}">
<meta property="og:image" content="{og_url}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
{f'<meta property="og:url" content="{kan}">' if kan else ''}
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{s.zu('assets/icons/icon-192.png')}" type="image/png">
<link rel="apple-touch-icon" href="{s.zu('assets/icons/apple-touch-icon.png')}">
<link rel="preload" href="{s.zu('assets/fonts/barlow-700.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{s.zu('assets/fonts/atkinson-400.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{s.zu('assets/site.css')}?v={VERSION}">
{'<script>window.SU_ARTIFACT = true</script>' if ARTIFACT else ''}
<script src="{s.zu('assets/site.js')}?v={VERSION}" defer></script>
{''.join(f'<script src="{s.zu("assets/" + x)}?v={VERSION}" defer></script>' for x in skripte)}
{schema_html}
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<header class="kopf"><div class="wrap">
<a class="logo" href="{s.zu('')}"><span class="logo-zeichen">{LOGO_SVG}</span>Sportunterricht</a>
<nav class="navi" aria-label="Hauptnavigation"><ul>{navi}</ul></nav>
{f'<a class="knopf blau klein kopf-cta" href="{s.zu("app/")}">App öffnen</a>' if APP_DA else f'<a class="knopf blau klein kopf-cta" href="{s.zu("planer/")}"{AKTIV if aktiv == "planer/" else ""}><span class="cta-lang">Stunde planen</span><span class="cta-kurz" aria-hidden="true">Planen</span></a>'}
<a class="merk-link" href="{s.zu('merkliste/')}"{AKTIV if aktiv == 'merkliste/' else ''}>{ICON['herz']}<span class="sr-only">Merkliste</span><span class="merk-zahl" hidden></span></a>
<details class="menue"><summary aria-label="Menü öffnen">{ICON['menue']}</summary><nav class="menue-liste" aria-label="Menü">{menue}<a href="{s.zu('raumplaner/')}">Raumplaner<small>Geräteaufbau planen</small></a><a href="{s.zu('bewegte-pause/')}">Bewegte Pause<small>ohne Material, mit Timer</small></a><a href="{s.zu('kostenlos/')}">Kostenlos<small>Gratis-PDF & Leseproben</small></a></nav></details>
</div></header>
<main id="inhalt">
'''
    fuss = f'''{kauf_dialog(s)}</main>
<footer class="fuss"><div class="wrap">
<div class="fuss-raster">
<div><a class="logo" href="{s.zu('')}"><span class="logo-zeichen">{LOGO_SVG.replace('#fff', '#13211b')}</span>Sportunterricht</a>
<p>Spiele, Stundenbilder und Ideen für Bewegung und Sport – aus der Praxis, für die Praxis.</p></div>
<div><h2 class="fuss-titel">Entdecken</h2><ul><li><a href="{s.zu('spiele/')}">Spiele-Lexikon</a></li><li><a href="{s.zu('planer/')}">Stundenplaner</a></li><li><a href="{s.zu('werkzeuge/')}">Werkzeuge für die Halle</a></li><li><a href="{s.zu('raumplaner/')}">Raumplaner</a></li><li><a href="{s.zu('bewegte-pause/')}">Bewegte Pause</a></li><li><a href="{s.zu('merkliste/')}">Merkliste</a></li><li><a href="{s.zu('app/')}">App</a></li>{f'<li><a href="{s.zu("pro/")}">App Pro</a></li>' if APP_DA else ''}<li><a href="{s.zu('kostenlos/')}">Kostenlos</a></li><li><a href="{E['youtube']}" rel="noopener">YouTube-Kanal</a></li></ul></div>
<div><h2 class="fuss-titel">E-Books</h2><ul>{''.join(f'<li><a href="{s.zu("ebooks/" + b["slug"] + "/")}">{esc(b["kurz"])}</a></li>' for b in REIHE)}<li><a href="{s.zu('ebooks/komplettpaket/')}">Komplettpaket</a></li></ul></div>
<div><h2 class="fuss-titel">Info</h2><ul><li><a href="{s.zu('schulen/')}">Für Schulen</a></li><li><a href="{s.zu('ueber/')}">Über mich</a></li><li><a href="{s.zu('faq/')}">Häufige Fragen</a></li>{f'<li><a href="{esc(E["partnerprogramm_url"])}" rel="noopener">Partnerprogramm</a></li>' if E.get('partnerprogramm_url') else ''}</ul></div>
</div>
<div class="fuss-unten"><span>© {HEUTE.year} Sportunterricht · Ohne Tracking, ohne Werbe-Cookies</span><span><a href="{s.zu('impressum/')}">Impressum</a> · <a href="{s.zu('datenschutz/')}">Datenschutz</a> · <a href="{s.zu('agb/')}">AGB & Widerruf</a></span></div>
</div></footer>
</body>
</html>
'''
    ziel = OUT / pfad / 'index.html' if not pfad.endswith('.html') else OUT / pfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    koerper = inhalt(s)
    if 'data-kauf=' not in koerper:  # Kauf-Dialog nur auf Seiten mit Kauf-Knopf
        fuss = fuss.replace(kauf_dialog(s), '', 1)
    text = kopf + koerper + fuss
    if ARTIFACT:  # Downloads sind in der Vorschau gesperrt → PDFs im neuen Tab öffnen
        text = text.replace(' download>', ' target="_blank" rel="noopener">')
    ziel.write_text(text)
    if not noindex and not pfad.endswith('404.html'):
        SITEMAP.append(pfad)


def kauf_daten(s):
    """Alles, was der Kauf-Dialog über ein Produkt wissen muss – nur Produkte mit hinterlegtem Kauflink."""
    daten = {}
    for b in REIHE:
        if KAUF.get(b['slug']):
            daten[b['slug']] = {'t': f'Band {b["band"]}: {b["titel"]}', 'p': b['preis'], 'x': b['unter'], 'u': KAUF[b['slug']],
                                'l': s.zu(f'downloads/leseprobe-{b["slug"]}.pdf'), 'c': cover(s, b['slug'])}
    if KAUF.get('komplettpaket'):
        daten['komplettpaket'] = {'t': 'Das Komplettpaket', 'p': KOMPLETT['preis'], 's': KOMPLETT['statt'], 'u': KAUF['komplettpaket'], 'l': '',
                                  'x': f'Alle {BAENDE_WORT} Bände der Praxis-Reihe plus Bonus-Jahresplaner.', 'c': ''}
    for k, name in (('pro_jahr', 'App Pro – Jahr'), ('pro_monat', 'App Pro – Monat'), ('pro_praktikum', 'Praktikums-Pass')):
        if KAUF.get(k) and APP_DA:
            daten[k] = {'t': name, 'p': '', 'x': 'Freischaltung mit Bestellnummer und Lizenzschlüssel aus der Kaufbestätigung.', 'u': KAUF[k], 'l': '', 'c': ''}
    return daten


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


SITEMAP = []
AKTIV = ' aria-current="page"'
VERSION = HEUTE.strftime('%Y%m%d')

# ---------------------------------------------------------------- Bücher

TEXTE = {
    'spielesammlung': {
        'fuer': 'Für alle, die jede Woche Sport unterrichten und schnell ein Spiel brauchen, das sicher funktioniert – in der Volksschule genauso wie in der Unterstufe.',
        'punkte': ['Die 50 meistgesehenen Einzelspiele des Kanals – ausgewählt nach über 2 Millionen echten Aufrufen',
                   'Sechs Kapitel: Aufwärmen, Kooperation, (fast) ohne Material, große Gruppen, kleine Hallen, Abschluss',
                   'Jedes Spiel mit Ansagetext zum Vorlesen, Varianten und Sicherheitshinweis',
                   'Übersichten nach Stundenteil und „ganz ohne Material“ zum schnellen Nachschlagen'],
    },
    'aufwaermen': {
        'fuer': 'Für den Stundenbeginn: Die Klasse soll in einer Minute in Bewegung sein – ohne langes Erklären, ohne Aufbau, ohne Wartezeit.',
        'punkte': ['40 Fang-, Lauf-, Staffel- und Reaktionsspiele', 'Eigenes Kapitel für kleine Hallen und große Gruppen',
                   '„Aufwärmen mit System“: welcher Einstieg zu welchem Stundenthema passt', 'Realistische Spielzeiten statt Videolängen'],
    },
    'turnen': {
        'fuer': 'Für alle, die Turnen sicher und mit gutem Gefühl unterrichten wollen – auch ohne Turnvergangenheit. Ideal für Praktikum und Berufseinstieg.',
        'punkte': ['30 Übungen an Boden, Kasten, Reck, Barren, Ringen und Minitramp',
                   'Jede Übung mit methodischer Reihe, Hilfestellung und typischen Fehlern',
                   'Sicherheitsregeln, Griffe der Hilfestellung und fertige Stationspläne',
                   'Checkliste für den Geräteaufbau vor der Stunde'],
    },
    'fitness': {
        'fuer': 'Für Stunden, in denen Kraft, Ausdauer und Koordination im Mittelpunkt stehen – mit Spaß statt Drill, vom Tabata bis zum Hallentriathlon.',
        'punkte': ['35 Übungen und Spielformen für Kraft, Ausdauer, Koordination und Leichtathletik',
                   'Sechs fertige Zirkel und Trainingspläne für die ganze Stunde', 'Belastung und Pausen altersgerecht erklärt',
                   'Trendformate wie Hyrox goes School und Crosstraining im Turnsaal'],
    },
    'praktikum': {
        'fuer': 'Für Lehramtsstudierende in Praktikum und Unterrichtspraktischen Studien – und für alle, die ihre ersten Stundenbilder schreiben.',
        'punkte': ['12 fertige Stundenbilder: 6 × Volksschule, 6 × Sekundarstufe I', 'Verlaufsplanung im Tabellenformat plus Ablauf im Detail',
                   'Leitfaden: Lernziele formulieren, Lehrplanbezug Österreich, Organisation, Differenzierung, Reflexion',
                   'Jedes Spiel mit Verweis auf die ausführliche Anleitung und QR-Code zur Video-Demo'],
    },
    'alle-dabei': {
        'fuer': 'Für alle, deren Stunden nicht an der Übung scheitern, sondern an Angst, Konflikten, fehlender Motivation, sehr unterschiedlichen Kindern oder der vollen Bank – und für alle, die Sicherheit, Recht, Koedukation und den Umgang mit Fehlverhalten einmal kompakt geklärt haben wollen.',
        'punkte': ['9 Kapitel: Sicherheit, Angst, Aggression, Motivation, Heterogenität, Nicht-Aktive, Koedukation, „Strafen“ und Rituale',
                   'Wörtliche Formulierungen für die Halle und 27 Fallbeispiele von der Volksschule bis zur Oberstufe',
                   '13 Kopiervorlagen: Hallencheck, Unfall-Notiz, Mutbarometer, Fairplay-Vertrag, Rollenkarten, Reaktionsleiter, Rituale-Plakat …',
                   'Rechtliches für Österreich kompakt: Aufsicht, Befreiung, Beurteilung, Erziehungsmittel, getrennter und gemeinsamer Unterricht (Stand 2026/27)'],
    },
}


def lade_alle_dabei():
    ordner = EBOOKS / 'alle-dabei'
    kapitel, alle_vl = [], []
    dateien = sorted(ordner.glob('kapitel-*.md'), key=lambda f: int(re.search(r'\d+', f.stem).group()))
    for f in dateien:
        text = f.read_text()
        titel = text.split('\n', 1)[0].lstrip('# ').strip()
        faelle = len(re.findall(r'^#### Fall:', text, re.M))
        vl = re.findall(r'^#### Kopiervorlage: (.+)$', text, re.M)
        alle_vl += vl
        info = f'Auf einen Blick · Verstehen · Vorbeugen · Handeln in der Situation · {faelle} Fallbeispiele · passende Spiele · Checkliste' + (f' · Kopiervorlage{"n" if len(vl) > 1 else ""}: {", ".join(vl)}' if vl else '')
        kapitel.append((titel, info))
    k2 = (ordner / 'kapitel-2.md').read_text()
    blick = re.search(r'^### Auf einen Blick\s*\n(.*?)(?=^### )', k2, re.M | re.S).group(1)
    punkte = [z[2:].strip() for z in blick.strip().splitlines() if z.startswith('- ')]
    ansage = re.search(r'^> \*\*So sagst du es:\*\* (.+)$', k2, re.M).group(1)
    return {'kapitel': kapitel, 'anzahl': len(dateien), 'stufen': '1–13', 'muster': None, 'vorlagen': alle_vl,
            'auszug': {'titel': k2.split('\n', 1)[0].lstrip('# ').strip(), 'punkte': punkte, 'ansage': ansage}}


def lade_buecher():
    daten = {}
    for b in REIHE:
        slug = b['slug']
        if slug == 'alle-dabei':
            daten[slug] = lade_alle_dabei()
        elif slug == 'praktikum':
            leit = parse((EBOOKS / 'praktikum/leitfaden.md').read_text())
            stunden = json.loads((EBOOKS / 'praktikum/stunden.json').read_text())
            kapitel = [(k['titel'], []) for k in leit['kapitel']]
            kapitel.append(('Teil 2 – 12 fertige Stundenbilder', [f'{st["titel"]} ({st["stufe"]}. Schulstufe)' for st in stunden]))
            daten[slug] = {'kapitel': kapitel, 'anzahl': 12, 'stufen': '1–8', 'muster': None, 'stunden': stunden}
        else:
            buch = parse((EBOOKS / slug / 'inhalt.md').read_text())
            je = [[buchpdf.eintrag_aus_excel(e) for e in k['eintraege']] for k in buch['kapitel']]
            alle = [e for k in je for e in k]
            kapitel = [(k['titel'], [e['name'] for e in je[i]]) for i, k in enumerate(buch['kapitel'])]
            daten[slug] = {'kapitel': kapitel, 'anzahl': len(alle), 'stufen': buchpdf.stufen_bereich(alle), 'muster': alle[0], 'alle': alle}
        daten[slug]['seiten'] = pdf_seiten(PDFS / f'{slug}.pdf')
        daten[slug]['probe_seiten'] = pdf_seiten(PDFS / f'{slug}-leseprobe.pdf')
    return daten


BUECHER = lade_buecher()


def cover(s, slug):
    return s.zu(f'assets/cover/{slug}.webp')


# ---------------------------------------------------------------- Dateien & Bilder

def kopiere_dateien():
    OUT.mkdir(exist_ok=True)
    for x in OUT.iterdir():  # Inhalt leeren, Ordner behalten (ein laufender Vorschau-Server bleibt gültig)
        shutil.rmtree(x) if x.is_dir() else x.unlink()
    (OUT / 'assets/fonts').mkdir(parents=True)
    # Atkinson Hyperlegible Next (ungestrichene Null) + Barlow Condensed, beide OFL – liegen in statisch/fonts
    for datei in SCHRIFTEN.iterdir():
        shutil.copy(datei, OUT / 'assets/fonts' / datei.name)
    if (APP / 'public/icons').exists():
        shutil.copytree(APP / 'public/icons', OUT / 'assets/icons')
    else:
        icons_erzeugen(OUT / 'assets/icons')
    shutil.copy(HIER / 'statisch/site.css', OUT / 'assets/site.css')
    for js in ('site.js', 'planer.js', 'werkzeuge.js', 'merkliste.js', 'karten.js', 'pause.js', 'raumplaner.js'):
        shutil.copy(HIER / 'statisch' / js, OUT / 'assets' / js)
    # App unter /app/ (ohne App-Ordner: Hinweisseite, siehe app_platzhalter())
    if APP_DA:
        shutil.copytree(APP / 'dist', OUT / 'app')
    if APP_DA and ARTIFACT:  # In der claude.ai-Vorschau sind YouTube-Einbettung und Service Worker gesperrt → App schaltet auf Links um
        app = OUT / 'app/index.html'
        h = app.read_text(encoding='utf-8')
        assert '<head>' in h
        h = h.replace('<head>', '<head><script>window.SU_ARTIFACT = true</script>', 1)
        h = re.sub(r'<link rel="manifest"[^>]*>', '', h)
        app.write_text(h, encoding='utf-8')
        for rest in ('sw.js', 'manifest.webmanifest'):
            (OUT / 'app' / rest).unlink(missing_ok=True)
    # Leseproben, Gratis-PDF (öffentlich). Die Vollversionen liefert Digistore24 aus – sie gehören NICHT auf die Website.
    dl = OUT / 'downloads'
    dl.mkdir()
    if not (PDFS / 'gratis-5-spiele.pdf').exists():
        sys.exit('Die E-Book-PDFs fehlen. Bitte zuerst bauen:  cd ebooks && python3 werkzeug/pdf.py --final')
    for b in REIHE:
        shutil.copy(PDFS / f'{b["slug"]}-leseprobe.pdf', dl / f'leseprobe-{b["slug"]}.pdf')
    shutil.copy(PDFS / 'gratis-5-spiele.pdf', dl / 'gratis-5-spiele.pdf')
    # Cover als WebP
    from PIL import Image
    (OUT / 'assets/cover').mkdir()
    for slug in [b['slug'] for b in REIHE] + ['jahresplaner', 'gratis-5-spiele']:
        pdf = PDFS / f'{slug}.pdf'
        tmp = HIER / f'.tmp-{slug}'
        subprocess.run(['pdftoppm', '-png', '-r', '100', '-f', '1', '-l', '1', '-singlefile', str(pdf), str(tmp)], check=True)
        im = Image.open(f'{tmp}.png').convert('RGB')
        im.thumbnail((560, 800))
        name = 'gratis' if slug == 'gratis-5-spiele' else slug
        im.save(OUT / f'assets/cover/{name}.webp', 'WEBP', quality=86, method=6)
        im.save(OUT / f'assets/cover/{name}.png', optimize=True)
        Path(f'{tmp}.png').unlink()
    # Netlify-Funktion für die Lizenzprüfung
    if not ARTIFACT:
        if (APP / 'netlify').exists():
            shutil.copytree(APP / 'netlify', OUT / 'netlify')
        else:
            shutil.copytree(HIER / 'netlify/functions', OUT / 'netlify/functions')


def icons_erzeugen(ziel):
    """Favicon und Home-Bildschirm-Symbol (nur nötig, wenn der App-Ordner fehlt)."""
    ziel.mkdir(parents=True, exist_ok=True)
    svg = LOGO_SVG.replace('viewBox="0 0 24 24"', 'viewBox="-4 -4 32 32" width="512" height="512"').replace('aria-hidden="true"', 'xmlns="http://www.w3.org/2000/svg"')
    doc = f'<html><head><style>@page {{ size: 512px 512px; margin: 0 }} body {{ margin: 0; background: #13211b }} svg {{ display: block }}</style></head><body>{svg}</body></html>'
    tmp = HIER / '.tmp-icon.pdf'
    HTML(string=doc).write_pdf(tmp)
    subprocess.run(['pdftoppm', '-png', '-r', '72', '-singlefile', str(tmp), str(HIER / '.tmp-icon')], check=True)
    from PIL import Image
    im = Image.open(HIER / '.tmp-icon.png').convert('RGB')
    for name, groesse in (('icon-192.png', 192), ('icon-512.png', 512), ('apple-touch-icon.png', 180)):
        im.resize((groesse, groesse), Image.LANCZOS).save(ziel / name, optimize=True)
    tmp.unlink()
    (HIER / '.tmp-icon.png').unlink()


def og_bilder():
    """Vorschaubilder für WhatsApp, Facebook & Co. (1200 × 630)."""
    (OUT / 'assets/og').mkdir(parents=True, exist_ok=True)
    css = f'''@font-face {{ font-family: B; font-weight: 700; src: url('{(SCHRIFTEN / 'barlow-700.woff2').as_uri()}'); }}
@font-face {{ font-family: A; src: url('{(HIER / 'statisch/fonts/atkinson-400.woff2').as_uri()}'); }}
@page {{ size: 1200px 630px; margin: 0; }} body {{ margin: 0; }}
.o {{ width: 1200px; height: 630px; background: #13211b; color: #fff; position: relative; overflow: hidden; font-family: A; }}
.o .t {{ position: absolute; left: 70px; top: 70px; width: 600px; }}
.o small {{ font-family: B; letter-spacing: .2em; font-size: 22px; color: #6ddca5; text-transform: uppercase; }}
.o h1 {{ font-family: B; font-size: 78px; line-height: .98; margin: 18px 0 20px; text-transform: uppercase; }}
.o p {{ font-size: 27px; line-height: 1.35; color: #c9d8cf; margin: 0; }}
.o .b {{ position: absolute; right: 60px; top: 70px; display: flex; }}
.o .b img {{ width: 230px; margin-left: -120px; box-shadow: 0 20px 40px rgba(0,0,0,.5); border-radius: 6px; }}
.o .f {{ position: absolute; left: 70px; bottom: 56px; font-family: B; font-size: 26px; letter-spacing: .06em; color: #fff; }}
.o .strich {{ position: absolute; left: 0; bottom: 0; height: 12px; width: 100%; background: linear-gradient(90deg,#1f5bd8,#c8402a,#5b3fa8,#b8531a,#167a4b,#0f6d7a); }}'''
    cov = lambda slug: (OUT / f'assets/cover/{slug}.png').as_uri()  # noqa: E731
    alle5 = [b['slug'] for b in REIHE]
    bilder = {
        'og-start': ('Sportunterricht', 'Spiele, Stundenbilder & Ideen für Bewegung und Sport', 'Über 470 Video-Demos · kostenlose App · E-Book-Reihe', alle5),
        'og-spiele': ('Spiele-Lexikon', 'Über 470 Spiele und Übungen mit Video', 'Nach Schulstufe, Stundenteil und Material filtern – kostenlos', ['spielesammlung', 'aufwaermen']),
        'og-pro': ('App Pro', 'Die Stunde in 10 Sekunden – mit Ansagetext und Stundenbild', 'Kostenlos starten, Pro ab 2,49 € im Monat', ['praktikum']),
        'og-kostenlos': ('Kostenlos', '5 Spiele, die immer funktionieren', 'Gratis-PDF mit Video-Demos und Ansagetexten', ['gratis']),
        'og-schulen': ('Für Schulen', 'Die ganze Praxis-Reihe für die Fachgruppe', 'Schullizenz für alle Sportlehrkräfte einer Schule', alle5),
        'og-komplettpaket': ('Komplettpaket', f'Alle {N_BAENDE} Bände + Jahresplaner', f'{KOMPLETT["preis"]} statt {KOMPLETT["statt"]}', alle5),
    }
    for b in REIHE:
        bilder[f'og-{b["slug"]}'] = (f'Band {b["band"]}', b['titel'], f'{b["preis"]} · sofort als PDF', [b['slug']])
    for name, (klein, titel, unter, cs) in bilder.items():
        imgs = ''.join(f'<img src="{cov(c)}">' for c in cs[-5:])
        doc = f'<html><head><style>{css}</style></head><body><div class="o"><div class="t"><small>{esc(klein)}</small><h1>{esc(titel)}</h1><p>{esc(unter)}</p></div><div class="b">{imgs}</div><div class="f">SPORTUNTERRICHT · YOUTUBE @SPORTUNTERRICHT2022</div><div class="strich"></div></div></body></html>'
        tmp = HIER / f'.tmp-{name}.pdf'
        HTML(string=doc).write_pdf(tmp)
        subprocess.run(['pdftoppm', '-png', '-r', '72', '-singlefile', str(tmp), str(OUT / f'assets/og/{name}')], check=True)
        tmp.unlink()


def aushang():
    """A4-Aushang fürs Lehrerzimmer mit QR-Code."""
    ziel = DOMAIN or E['youtube']
    anzeige = DOMAIN.replace('https://', '').replace('http://', '') if DOMAIN else 'youtube.com/@Sportunterricht2022'
    doc = f'''<html lang="de"><head><meta charset="utf-8"><style>
@font-face {{ font-family: B; font-weight: 700; src: url('{(SCHRIFTEN / 'barlow-700.woff2').as_uri()}'); }}
@font-face {{ font-family: A; src: url('{(HIER / 'statisch/fonts/atkinson-400.woff2').as_uri()}'); }}
@font-face {{ font-family: A; font-weight: 700; src: url('{(HIER / 'statisch/fonts/atkinson-700.woff2').as_uri()}'); }}
@page {{ size: A4; margin: 0; }}
body {{ margin: 0; font-family: A; color: #13211b; }}
.o {{ background: #13211b; color: #fff; padding: 22mm 18mm 16mm; position: relative; overflow: hidden; height: 118mm; box-sizing: border-box; }}
.o svg {{ position: absolute; right: -30mm; bottom: -20mm; width: 150mm; opacity: .22; }}
small {{ font-family: B; letter-spacing: .22em; font-size: 12pt; color: #6ddca5; }}
h1 {{ font-family: B; font-size: 50pt; line-height: .95; margin: 6mm 0 5mm; text-transform: uppercase; }}
.o p {{ font-size: 15pt; color: #c9d8cf; max-width: 150mm; margin: 0; }}
.u {{ padding: 12mm 18mm; display: flex; gap: 12mm; }}
.l {{ flex: 1; }}
.l div {{ border-left: 4pt solid; padding: 1mm 0 1mm 5mm; margin-bottom: 7mm; }}
.l b {{ font-family: B; font-size: 20pt; display: block; }}
.l span {{ font-size: 12pt; color: #46574f; }}
.q {{ width: 62mm; text-align: center; }}
.q img {{ width: 62mm; }}
.q b {{ display: block; font-family: B; font-size: 15pt; margin-top: 2mm; }}
.q span {{ font-size: 10pt; color: #46574f; }}
.f {{ position: absolute; bottom: 0; left: 0; right: 0; height: 6mm; background: linear-gradient(90deg,#1f5bd8,#c8402a,#5b3fa8,#b8531a,#167a4b); }}
</style></head><body>
<div class="o">{FELD}<small>FÜR DAS SPORT-TEAM</small><h1>Keine Idee für die nächste Sportstunde?</h1><p>Über 470 Spiele und Übungen mit Video – kostenlos, nach Schulstufe und Material sortiert. Dazu eine App, die eine ganze Stunde in 10 Sekunden plant.</p></div>
<div class="u"><div class="l">
<div style="border-color:#1f5bd8"><b>Spiele-Lexikon</b><span>Jedes Spiel mit Video-Demo, Schulstufe, Material und Stundenteil</span></div>
<div style="border-color:#c8402a"><b>App für Handy & Tablet</b><span>Stunde planen, Timer, Teams einteilen, Stundenmodus in der Halle – auch offline</span></div>
<div style="border-color:#167a4b"><b>Gratis-PDF</b><span>5 Spiele, die immer funktionieren – ohne Material, mit Ansagetext</span></div>
<div style="border-color:#5b3fa8"><b>Praxis-Reihe & Schullizenz</b><span>E-Books für die ganze Fachgruppe</span></div>
</div><div class="q"><img src="{buchpdf.qr(ziel)}"><b>{esc(anzeige)}</b><span>QR-Code scannen oder Adresse eingeben</span></div></div>
<div class="f"></div></body></html>'''
    HTML(string=doc).write_pdf(OUT / 'downloads/aushang-lehrerzimmer.pdf')


# ---------------------------------------------------------------- Spiele-Lexikon

def lade_spiele():
    spiele, gesehen = [], set()
    for v in sorted(VIDEOS, key=lambda x: -x['aufrufe']):
        a = ANL.get(v['id'])
        name = (a or {}).get('name') or v['titel']
        slug = slugify(name)
        basis, i = slug, 2
        while slug in gesehen:
            slug, i = f'{basis}-{i}', i + 1
        gesehen.add(slug)
        phasen = v.get('phasen') or [v['phase']]
        if a and a.get('stundenteil'):  # Buch-Angabe ist genauer als die Video-Kategorie
            phasen = [x.strip() for x in a['stundenteil'].split(',') if x.strip() in ('Aufwärmen', 'Hauptteil', 'Abschluss')] or phasen
        spielzeit = v.get('spielzeit')
        if not spielzeit and a:
            mz = re.match(r'\s*(\d+)\s*[–-]\s*(\d+)\s*Minuten', a.get('dauer') or '')
            spielzeit = [int(mz.group(1)), int(mz.group(2))] if mz else None
        dauer = f'{spielzeit[0]}–{spielzeit[1]} min' if spielzeit else ''
        buch_slug = BUECHER_SLUG.get((a or {}).get('buch', ''), '')
        ort = FUNDORTE.get(v['id'])
        spiele.append({
            'v': v, 'a': a, 'name': name, 'slug': slug, 'phasen': phasen, 'dauer': dauer, 'spielzeit': spielzeit,
            'material': 'Kein Material' if v.get('ohneMaterial') else MATERIAL.get(v['material'], 'Standard-Hallenmaterial'),
            'stufe': stufen_text(v['stufeVon'], v['stufeBis']), 'buch': buch_slug, 'ort': ort,
            'farbe': THEMA.get((v['tags'] or ['kleine_spiele'])[0], THEMA['kleine_spiele'])[1],
        })
    return spiele


BUECHER_SLUG = BUCH_NACH_NAME
SPIELE = lade_spiele()


def video_block(sp, farbe, kompakt=False):
    """Zwei-Klick-Video: Erst nach dem Klick wird YouTube (nocookie) geladen. Darunter immer ein Direktlink,
    falls die Einbettung blockiert ist (Werbeblocker, Firmen-/Schulnetz, lokal geöffnete Datei, claude.ai-Vorschau)."""
    v = sp['v']
    hinweis = 'Lädt von YouTube' if kompakt else 'Beim Abspielen wird das Video von YouTube geladen; dabei gelten die Datenschutzbestimmungen von Google.'
    return f'''<div class="video-wrap"><div class="video{' kompakt' if kompakt else ''}" data-video="{v['id']}" style="--vfarbe:{farbe}">
<button type="button" class="video-start" aria-label="Video „{esc(sp['name'])}“ abspielen">{FELD}
<span class="play">{ICON['play']}</span><b>{'Abspielen' if kompakt else 'Video ansehen'}</b>
<small>{hinweis}</small></button></div>
<p class="video-alt"><a href="https://www.youtube.com/watch?v={v['id']}" target="_blank" rel="noopener">Video lädt nicht? Direkt auf YouTube ansehen<span class="sr-only"> (neues Fenster)</span></a></p></div>'''


def video_raster(s, n=6):
    """Die meistgesehenen Spiele mit ausführlicher Anleitung – für die Startseite."""
    auswahl = [x for x in SPIELE if x['a'] and not x['v'].get('sammel')][:n]
    karten = ''
    for x in auswahl:
        v = x['v']
        karten += f'''<article class="videokarte">{video_block(x, x['farbe'], kompakt=True)}
<div class="videokarte-text"><h3><a href="{s.zu('spiele/' + x['slug'] + '/')}">{esc(x['name'])}</a></h3>
<p>{x['stufe']} · {', '.join(x['phasen'])} · {zahl_de(v['aufrufe'])} Aufrufe</p>{merk_knopf(v['id'], x['name'], klein=True)}</div></article>'''
    return f'<div class="videoraster">{karten}</div>'


def aehnliche(sp, n=6):
    v = sp['v']
    def punkte(x):
        w = x['v']
        if w['id'] == v['id']:
            return -1
        p = len(set(w['tags']) & set(v['tags'])) * 3 + (2 if w['stufeVon'] <= v['stufeBis'] and w['stufeBis'] >= v['stufeVon'] else -3)
        p += len(set(x['phasen']) & set(sp['phasen'])) + (2 if x['a'] else 0)
        return p + min(w['aufrufe'], 200000) / 200000
    return sorted(SPIELE, key=punkte, reverse=True)[:n]


def listeneintrag(s, x, mit_daten=False):
    v = x['v']
    buch = f' · <span class="buchmarke">Anleitung im E-Book</span>' if x['a'] else ''
    thema = THEMA.get((v['tags'] or ['kleine_spiele'])[0], THEMA['kleine_spiele'])[0]
    daten = ''
    if mit_daten:
        daten = (f' data-von="{v["stufeVon"]}" data-bis="{v["stufeBis"]}" data-phasen="{" ".join(x["phasen"])}" data-themen="{" ".join(v["tags"])}"'
                 f' data-ohne="{1 if v.get("ohneMaterial") else 0}" data-anl="{1 if x["a"] else 0}" data-suche="{esc((x["name"] + " " + v["titel"] + " " + thema).lower())}"')
    ziel = f'href="https://www.youtube.com/watch?v={v["id"]}" rel="noopener"' if ARTIFACT and not x['a'] else f'href="{s.zu("spiele/" + x["slug"] + "/")}"'
    return f'<li{daten}><a {ziel}><span class="mini" style="background:{x["farbe"]}" title="{esc(thema)}" aria-hidden="true">{v["stufeVon"]}–{v["stufeBis"]}<small>Stufe</small></span><span><b>{esc(x["name"])}</b><small>{x["stufe"]} · {", ".join(x["phasen"])}{buch}</small></span></a></li>'


def lexikon_index():
    themen_opt = ''.join(f'<option value="{k}">{t}</option>' for k, (t, _) in THEMA.items())
    stufen_opt = ''.join(f'<option value="{i}">{i}. Schulstufe</option>' for i in range(1, 14))

    def inhalt(s):
        eintraege = ''.join(listeneintrag(s, x, True) for x in SPIELE)
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Spiele-Lexikon</li></ol></nav>
<div class="kopfzeile"><div><p class="oberzeile">Spiele-Lexikon</p><h1>{len(SPIELE)} Spiele und Übungen mit Video</h1>
<p class="einleitung">Alle Videos des Kanals, sortiert nach Beliebtheit. Filtere nach Schulstufe, Stundenteil und Thema – oder such direkt nach einem Spiel.</p></div>
{f'<a class="knopf" href="{s.zu("app/")}">{ICON["handy"]} In der App planen</a>' if APP_DA else ''}</div>
<form class="filter" id="filter" role="search" onsubmit="return false">
<label>Suche<input type="search" id="f-suche" placeholder="z. B. Brennball, Staffel, Rolle …" autocomplete="off"></label>
<label>Schulstufe<select id="f-stufe"><option value="">alle</option>{stufen_opt}</select></label>
<label>Stundenteil<select id="f-phase"><option value="">alle</option><option>Aufwärmen</option><option>Hauptteil</option><option>Abschluss</option></select></label>
<label>Thema<select id="f-thema"><option value="">alle</option>{themen_opt}</select></label>
<div class="schalter"><label><input type="checkbox" id="f-ohne"> ganz ohne Material</label><label><input type="checkbox" id="f-anl"> mit ausführlicher Anleitung</label></div>
</form>
<p class="treffer" id="treffer" aria-live="polite">{len(SPIELE)} Spiele</p>
<ul class="liste" id="liste">{eintraege}</ul>
<button type="button" class="knopf mehr-laden" id="mehr" hidden>Weitere Spiele anzeigen</button>
<p class="treffer" id="leer" hidden>Kein Spiel passt zu allen Filtern. Tipp: Nimm einen Filter weg oder such nach einem anderen Wort.</p>
</div></section>'''
    seite('spiele/', 'Spiele-Lexikon: über 470 Spiele für den Sportunterricht mit Video', f'{len(SPIELE)} Spiele und Übungen für Bewegung und Sport mit Video-Demo – filterbar nach Schulstufe, Stundenteil, Thema und Material. Kostenlos.',
          inhalt, aktiv='spiele/', og='og-spiele.png', voller_titel=True,
          schema=[{'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'Spiele-Lexikon Sportunterricht', 'inLanguage': 'de-AT', 'numberOfItems': len(SPIELE)}])


def lexikon_seiten():
    for sp in SPIELE:
        v, a = sp['v'], sp['a']
        if ARTIFACT and not a:
            continue
        themen = [THEMA[t][0] for t in v['tags'] if t in THEMA]

        def inhalt(s, sp=sp, v=v, a=a, themen=themen):
            fakten = [('Schulstufe', sp['stufe']), ('Stundenteil', ', '.join(sp['phasen'])), ('Material', (a or {}).get('materialText') or sp['material'])]
            if sp['dauer']:
                fakten.append(('Spielzeit', sp['dauer']))
            if a and a.get('gruppe'):
                fakten.append(('Gruppe', a['gruppe']))
            fakten.append(('Thema', ', '.join(themen) or 'Kleine Spiele'))
            if v.get('intensitaet'):
                fakten.append(('Intensität', v['intensitaet']))
            app_knopf = f'<a class="knopf" href="{s.zu("app/")}#spiel/{v["id"]}">{ICON["handy"]} In der App öffnen</a>' if APP_DA else ''
            app_box = (f'''<div class="hinweisbox"><h3>Direkt in eine Stunde einbauen</h3><p>Die kostenlose App schlägt dir passende Spiele für Aufwärmen, Hauptteil und Abschluss vor – mit Timer, Teameinteilung und Stundenmodus für die Halle.</p>
<a class="knopf blau" href="{s.zu('app/')}#spiel/{v['id']}">{ICON['handy']} In der App öffnen</a></div>''' if APP_DA else
                       f'''<div class="hinweisbox"><h3>Mehr Spiele für deine Stunde</h3><p>Im Spiele-Lexikon findest du alle {len(VIDEOS)} Videos – filterbar nach Schulstufe, Stundenteil, Thema und Material.</p>
<a class="knopf blau" href="{s.zu('spiele/')}">{ICON['video']} Zum Spiele-Lexikon</a></div>''')
            fakten_html = ''.join(f'<div><dt>{k}</dt><dd>{esc(str(w))}</dd></div>' for k, w in fakten)
            if a:
                b = BAND.get(sp['buch'])
                ort = sp['ort']
                verweis = f'Band {ort[0]}, Nr. {ort[1]}' if ort else f'Band {b["band"]}'
                text = f'''<h2>Worum geht’s?</h2>
{f'<p><b>Lernziel:</b> {esc(a["lernziel"])}</p>' if a.get('lernziel') else ''}
<p>{esc(saetze(a.get('beschreibung'), 2))}</p>
<div class="hinweisbox gruen"><h3>Die ganze Anleitung</h3><p>Ausführliche Beschreibung, <b>Ansagetext zum Vorlesen</b>, Varianten zum Leichter- und Schwerermachen{', methodische Reihe, Hilfestellung' if a.get('methodik') else ''} und Sicherheitshinweis findest du im E-Book <b>„{esc(b["titel"])}“</b> ({verweis}){' und in der App mit Pro' if APP_DA else ''}.</p>
<div class="knopfreihe"><a class="knopf primaer" href="{s.zu('ebooks/' + b['slug'] + '/')}">{ICON['buch']} Zum E-Book · {b["preis"]}</a>{app_knopf}</div></div>'''
            else:
                text = f'''<h2>Worum geht’s?</h2>
<p>„{esc(v['titel'])}“ ist ein Video für den Sportunterricht der {sp['stufe']} und passt vor allem in den Stundenteil <b>{', '.join(sp['phasen'])}</b>. Material: {esc(sp['material'])}. Im Video siehst du den Ablauf so, wie er im echten Unterricht funktioniert.</p>
{app_box}'''
            weitere = ''.join(listeneintrag(s, x) for x in aehnliche(sp))
            return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('spiele/')}">Spiele-Lexikon</a></li><li>{esc(sp['name'])}</li></ol></nav>
<div class="spiel-kopf"><div>{video_block(sp, sp['farbe'])}</div>
<div><p class="oberzeile">{esc(', '.join(themen) or 'Spiel')}</p><h1 style="font-size:clamp(2rem,5vw,3.2rem)">{esc(sp['name'])}</h1><dl class="fakten">{fakten_html}</dl>
<div class="knopfreihe">{merk_knopf(v['id'], sp['name'])}<a class="knopf" href="{s.zu('planer/')}">{ICON['planer']} Stunde planen</a></div></div></div>
<div class="textseite" style="margin-top:28px">{text}</div>
</div></section>
<section class="abschnitt eng hell"><div class="wrap"><h2>Das könnte auch passen</h2><ul class="liste">{weitere}</ul>
<p style="margin-top:18px"><a href="{s.zu('spiele/')}">Alle Spiele im Lexikon {ICON['pfeil'].replace('<svg', '<svg width="16" height="16" style="vertical-align:-2px"')}</a></p></div></section>'''
        beschreibung = (f'{sp["name"]}: {saetze((a or {}).get("beschreibung"), 1)}' if a else f'{sp["name"]} – Video für den Sportunterricht ({sp["stufe"]}, {", ".join(sp["phasen"])}).')[:158]
        schema = [{'@context': 'https://schema.org', '@type': 'VideoObject', 'name': sp['name'], 'description': beschreibung,
                   'thumbnailUrl': [f'https://i.ytimg.com/vi/{v["id"]}/hqdefault.jpg'], 'uploadDate': datum_iso(v.get('datum')) or '2020-01-01',
                   'duration': dauer_iso(v.get('sekunden')), 'embedUrl': f'https://www.youtube-nocookie.com/embed/{v["id"]}',
                   'contentUrl': f'https://www.youtube.com/watch?v={v["id"]}', 'inLanguage': 'de',
                   'interactionStatistic': {'@type': 'InteractionCounter', 'interactionType': {'@type': 'WatchAction'}, 'userInteractionCount': v['aufrufe']}}]
        if DOMAIN:
            schema.append({'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Start', 'item': DOMAIN + '/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Spiele-Lexikon', 'item': DOMAIN + '/spiele/'},
                {'@type': 'ListItem', 'position': 3, 'name': sp['name']}]})
        # Seiten ohne eigene Anleitung sind dünn → nicht indexieren, aber für Menschen nützlich
        seite(f'spiele/{sp["slug"]}/', f'{sp["name"]} – Spiel für den Sportunterricht', beschreibung, inhalt, aktiv='spiele/', og='og-spiele.png', schema=schema, noindex=not a)


# ---------------------------------------------------------------- Bausteine

def buchkarte(s, b):
    d = BUECHER[b['slug']]
    return f'''<a class="buch" href="{s.zu('ebooks/' + b['slug'] + '/')}"><div class="buch-bild"><img src="{cover(s, b['slug'])}" alt="Cover: {esc(b['titel'])}" width="280" height="396" loading="lazy"></div>
<div class="buch-text"><span class="marke">Band {b['band']} · {d['anzahl']} {b['einheit']}</span><h3>{esc(b['titel'])}</h3><p>{esc(b['text'])}</p>
<div class="buch-fuss"><span class="preis">{b['preis']}</span><span class="mehr">Ansehen {ICON['pfeil'].replace('<svg', '<svg width="18" height="18"')}</span></div></div></a>'''


def komplett_banner(s, mit_knopf=True, h='h2'):
    bilder = ''.join(f'<img src="{cover(s, b["slug"])}" alt="" width="120" height="170" loading="lazy">' for b in REIHE)
    knopf = f'<div class="knopfreihe">{kauf_knopf(s, "komplettpaket", "Komplettpaket kaufen", "knopf pro gross")}<a class="knopf gross" style="background:transparent;color:#fff;border-color:#3a4d43" href="{s.zu("ebooks/komplettpaket/")}">Details</a></div>' if mit_knopf else ''
    return f'''<div class="komplett"><div><p class="oberzeile">Alle {BAENDE_WORT} Bände</p><{h}>Das Komplettpaket</{h}>
<ul><li>{ICON['check']}<span>Alle {N_BAENDE} Bände der Praxis-Reihe – {sum(BUECHER[b['slug']]['anzahl'] for b in SPIELBAENDE)} Spiele und Übungen, 12 Stundenbilder und der Band „Alle dabei, alle sicher“ mit {len(BUECHER['alle-dabei']['vorlagen'])} Kopiervorlagen</span></li>
<li>{ICON['check']}<span>Bonus: <b>Jahresplaner</b> mit zehn Monatsschwerpunkten und Vorlage zum Ausfüllen</span></li>
<li>{ICON['check']}<span>Sofort als PDF – für Handy, Tablet und zum Ausdrucken</span></li></ul>
<p class="preis">{KOMPLETT['preis']} <s>{KOMPLETT['statt']}</s></p>{knopf}</div>
<div class="komplett-bilder">{bilder}</div></div>'''


def newsletter_block(s):
    if E.get('newsletter_formular_url'):
        form = f'''<form class="nl-form" action="{esc(E['newsletter_formular_url'])}" method="post" target="_blank">
<label for="nl-mail"><b>Deine E-Mail-Adresse</b></label><input type="email" id="nl-mail" name="{esc(E.get('newsletter_feldname_email') or 'email')}" required autocomplete="email" placeholder="name@schule.at">
<label class="zustimmung"><input type="checkbox" required> <span>Ja, schick mir das Gratis-PDF und etwa einmal im Monat neue Spiele und Stundenideen. Abmelden geht jederzeit mit einem Klick. Details in der <a href="{s.zu('datenschutz/')}">Datenschutzerklärung</a>.</span></label>
<button class="knopf primaer gross" type="submit">Gratis-PDF anfordern</button>
<p class="klein">Du bekommst gleich eine E-Mail zur Bestätigung (Double-Opt-in).</p></form>'''
    else:
        WARNUNGEN.append('Newsletter nicht eingerichtet (newsletter_formular_url) – Gratis-PDF wird direkt zum Download angeboten.')
        form = f'''<div class="nl-form"><b>Direkt herunterladen – ohne Anmeldung</b><p class="klein">PDF, {pdf_seiten(PDFS / 'gratis-5-spiele.pdf')} Seiten, druckbar</p>
<a class="knopf primaer gross" href="{s.zu('downloads/gratis-5-spiele.pdf')}" download>{ICON['download']} Gratis-PDF herunterladen</a>
<a class="knopf" href="{E['youtube']}?sub_confirmation=1" rel="noopener">{ICON['video']} Kanal abonnieren für neue Spiele</a></div>'''
    return f'''<div class="newsletter" id="newsletter"><div class="nl-kopf">
<div class="gratis-cover"><img src="{cover(s, 'gratis')}" alt="Cover des Gratis-PDFs „5 Spiele, die immer funktionieren“" width="200" height="283"></div>
<div><p class="oberzeile">Kostenlos</p><h2>5 Spiele, die immer funktionieren</h2></div>
<p class="einleitung" style="margin:0">Ohne Material, für jede Halle, in einer Minute erklärt – mit Video-Demo, Ansagetext und Varianten. Mein Starterpaket für Tage, an denen nichts nach Plan läuft.</p></div>{form}</div>'''


def faq_html(eintraege):
    return '<div class="faq">' + ''.join(f'<details><summary>{esc(f)}</summary><div class="antwort">{a}</div></details>' for f, a in eintraege) + '</div>'


def faq_schema(eintraege):
    return {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': f, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub('<[^>]+>', '', a)}} for f, a in eintraege]}


def faq_liste(s):
    kontakt = f'<a href="mailto:{E["email"]}">{E["email"]}</a>' if E.get('email') else 'die E-Mail-Adresse im Impressum'
    pro_werbefrei = f'Für <a href="{s.zu("pro/")}">App Pro</a> stelle ich die Videos nach und nach werbefrei direkt in der App bereit.' if APP_DA else ''
    liste = [
        ('Wie bekomme ich das E-Book nach dem Kauf?', '<p>Direkt nach der Zahlung erscheint der Download-Link auf der Bestätigungsseite, und du bekommst ihn zusätzlich per E-Mail von Digistore24. Das PDF funktioniert auf Handy, Tablet und Laptop – und du darfst es für deinen eigenen Unterricht ausdrucken.</p>'),
        ('Wer ist mein Vertragspartner und wie kann ich bezahlen?', '<p>Der Verkauf läuft über <b>Digistore24</b> (Digistore24 GmbH, Hildesheim) als Wiederverkäufer. Digistore24 kümmert sich um Zahlung, Rechnung und Umsatzsteuer; du kannst mit den üblichen Zahlungsarten wie PayPal, Kreditkarte oder Lastschrift bezahlen. Die Rechnung bekommst du automatisch per E-Mail.</p>'),
        ('Darf ich die Bücher ausdrucken und in der Halle verwenden?', '<p>Ja, ausdrücklich. In den Bänden 1, 2 und 4 steht jedes Spiel vollständig auf einer Seite, in Band 3 beginnt jede Übung auf einer eigenen Seite – so kannst du genau die Karte ausdrucken, die du heute brauchst. Die Kopiervorlagen in Band 6 darfst du für deine eigenen Klassen kopieren.</p>'),
        ('Darf ich das E-Book an Kolleg:innen weitergeben?', f'<p>Die Einzellizenz gilt für dich und deinen eigenen Unterricht. Für die ganze Fachgruppe gibt es eine günstige <a href="{s.zu("schulen/")}">Schullizenz</a> – dann dürft ihr die PDFs auch intern auf dem Schulserver ablegen.</p>'),
        ('Warum sehe ich bei den Videos manchmal Werbung?', f'<p>Die Videos liegen auf YouTube, und YouTube spielt dort Werbung aus – auch wenn ein Video auf einer anderen Seite eingebettet ist. Darauf habe ich keinen Einfluss, und die Einnahmen finanzieren den kostenlosen Kanal. <b>Diese Website selbst</b> hat keine Werbung und kein Tracking. {pro_werbefrei}</p>'),
        ('Was ist der Unterschied zwischen der kostenlosen App und Pro?', f'<p>Kostenlos bekommst du alle Spiele mit Video, Suche, Filter, Timer, Teams, Punkte und den Stundenmodus – und drei komplette Stunden pro Monat. Pro schaltet unbegrenzt viele Stunden, die ganzen Anleitungen mit Ansagetext, das Stundenbild fürs Praktikum und den Klassen-Verlauf frei. <a href="{s.zu("pro/")}">Alle Details</a>.</p>'),
        ('Funktioniert die App auch am Handy und ohne Internet?', '<p>Ja – sie ist fürs Handy gemacht. Öffne sie einmal im Browser und wähle „Zum Home-Bildschirm hinzufügen“ (iPhone: Teilen-Symbol, Android: Menü mit den drei Punkten). Danach startet sie wie eine normale App und funktioniert auch in der Halle ohne Netz. Nur die Videos brauchen Internet.</p>'),
        ('Werden Daten meiner Schüler:innen gespeichert?', '<p>Nein. Die App braucht kein Konto; Klassen, Stunden und Namenslisten bleiben nur auf deinem Gerät. Es gibt keinen Server, auf dem Schülerdaten landen.</p>'),
        ('Wie kündige ich App Pro?', '<p>Im Monats- und Jahresabo jederzeit zum Ende des bezahlten Zeitraums – über den Link in deiner Kaufbestätigung von Digistore24. Der Praktikums-Pass ist eine Einmalzahlung und läuft automatisch aus.</p>'),
        ('Kann ich ein E-Book zurückgeben?', f'<p>Bei digitalen Inhalten erlischt das Widerrufsrecht, sobald du dem sofortigen Download ausdrücklich zustimmst – das ist gesetzlich so geregelt. Schau dir deshalb vorher gern die kostenlose Leseprobe an. Wenn trotzdem etwas nicht passt, schreib mir an {kontakt}.</p>'),
        ('Passen die Inhalte zum österreichischen Lehrplan?', '<p>Das Praktikums-Kit bezieht sich ausdrücklich auf die Lehrpläne für Volksschule und Sekundarstufe I in Österreich, Band 6 erklärt die österreichischen Regeln zu Aufsicht, Befreiung und Beurteilung. Die Spiele und Übungen der anderen Bände funktionieren genauso in Deutschland und der Schweiz – die Schulstufen-Angaben entsprechen den Klassen 1 bis 13.</p>'),
        ('Kann ich E-Books und App von der Steuer absetzen?', '<p>Arbeitsmittel für den Unterricht können als Werbungskosten absetzbar sein. Die Rechnung von Digistore24 hast du dafür automatisch. Ob und wie viel, klärst du im Zweifel mit deiner Steuerberatung.</p>'),
        ('Ich habe einen Fehler gefunden oder eine Spielidee.', f'<p>Sehr gern! In der App gibt es bei jedem Spiel „Passt etwas nicht? Rückmelden“. Oder schreib mir an {kontakt}. Jede Rückmeldung landet in meiner Datenbank und macht App und Bücher für alle besser.</p>'),
    ]
    if not APP_DA:  # Fragen zur App erst zeigen, wenn die App online ist
        liste = [x for x in liste if not any(w in x[0] for w in ('App', 'Pro', 'Handy'))]
    if E.get('studierenden_code'):
        liste.append(('Gibt es einen Rabatt für Studierende?', f'<p>Ja: Mit dem Code <b>{esc(E["studierenden_code"])}</b> bekommst du im Checkout einen Rabatt auf alle E-Books.</p>'))
    return liste


# ---------------------------------------------------------------- Seiten

def kanal_seit():
    if E.get('kanal_seit'):
        return E['kanal_seit']
    jahre = [datum_iso(v.get('datum')) for v in VIDEOS]
    return min(j for j in jahre if j)[:4]


def kuerzen(t, n):
    t = (t or '').strip()
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0].rstrip(',;:–-') + ' …'


def zufall_daten():
    out = []
    for x in SPIELE:
        a = x['a']
        if not a:
            continue
        out.append({'n': x['name'], 's': x['slug'], 'v': x['v']['stufeVon'], 'b': x['v']['stufeBis'], 'st': x['stufe'].replace(' Schulstufe', ''),
                    'd': x['dauer'], 'm': kuerzen(a.get('materialText') or x['material'], 70), 'p': x['phasen'],
                    't': a.get('lernziel') or saetze(a.get('beschreibung'), 1), 'f': x['farbe']})
    return out


def startseite():
    views = sum(v['aufrufe'] for v in VIDEOS)

    def inhalt(s):
        pfeil = ICON['pfeil'].replace('<svg', '<svg width="18" height="18"')
        if APP_DA:
            hero_text = f'''<p class="einleitung">Über {len(VIDEOS) // 10 * 10} Spiele mit Video, eine kostenlose App, die dir eine ganze Stunde plant, und E-Books mit allem, was du in der Halle brauchst – von einem Sportlehrer, der selbst jede Woche in der Halle steht.</p>
<div class="knopfreihe"><a class="knopf primaer gross" href="{s.zu('app/')}">{ICON['handy']} Stunde planen – kostenlos</a><a class="knopf gross" href="{s.zu('spiele/')}">Spiele entdecken</a></div>'''
            hero_klein = 'Kein Konto nötig · funktioniert am Handy und offline · diese Website ist werbe- und trackingfrei'
            mitte_karte = f'''<a class="karte link" href="{s.zu('app/')}"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['handy']}</div><h3>Die App</h3><p>Schulstufe, Dauer, Hallengröße wählen – die App stellt Aufwärmen, Hauptteil und Abschluss zusammen. Mit Timer, Teams und Stundenmodus.</p><span class="mehr">App öffnen {pfeil}</span></a>'''
        else:
            hero_text = f'''<p class="einleitung">Über {len(VIDEOS) // 10 * 10} Spiele mit Video, ein Stundenplaner, der dir eine ganze Stunde zusammenstellt, Werkzeuge für die Halle und E-Books mit allem, was du brauchst – von einem Sportlehrer, der selbst jede Woche in der Halle steht.</p>
<div class="knopfreihe"><a class="knopf primaer gross" href="{s.zu('planer/')}">{ICON['planer']} Stunde planen – kostenlos</a><a class="knopf gross" href="{s.zu('spiele/')}">Spiele entdecken</a></div>'''
            hero_klein = 'Kostenlos und ohne Anmeldung · funktioniert am Handy · diese Website ist werbe- und trackingfrei'
            mitte_karte = f'''<a class="karte link" href="{s.zu('planer/')}"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['planer']}</div><h3>Der Stundenplaner</h3><p>Schulstufe, Dauer und Material wählen – fertig ist die Stunde mit Aufwärmen, Hauptteil und Abschluss. Spiele tauschen, als Stundenbild drucken, per Link teilen.</p><span class="mehr">Stunde planen {pfeil}</span></a>'''
        stapel = ''.join(f'<img src="{cover(s, b["slug"])}" alt="" width="230" height="325">' for b in REIHE)
        buecher = ''.join(buchkarte(s, b) for b in REIHE)
        daten = json.dumps(zufall_daten(), ensure_ascii=False, separators=(',', ':'))
        waehler = json.dumps({b['slug']: {'t': b['titel'], 'p': b['preis'], 'u': s.zu('ebooks/' + b['slug'] + '/'), 'c': cover(s, b['slug']), 'x': TEXTE[b['slug']]['fuer']} for b in REIHE}
                             | {'komplettpaket': {'t': 'Das Komplettpaket', 'p': KOMPLETT['preis'], 'u': s.zu('ebooks/komplettpaket/'), 'c': cover(s, 'spielesammlung'), 'x': f'Alle {BAENDE_WORT} Bände plus Jahresplaner – für alle, die das ganze Schuljahr abdecken wollen.'}}, ensure_ascii=False)
        app_teaser = f'''<section class="abschnitt"><div class="wrap app-teaser">
<div><p class="oberzeile">Die App</p><h2>Die ganze Stunde in 10 Sekunden</h2>
<p class="einleitung">Schulstufe, Dauer, Hallengröße und Thema wählen – fertig ist die Stunde mit Aufwärmen, Hauptteil und Abschluss. Die App achtet auf das Alter, auf realistische Spielzeiten und darauf, dass sich mit derselben Klasse nichts wiederholt.</p>
<ul class="haken"><li>{ICON['check']}<span><b>Stundenmodus für die Halle:</b> großer Timer, nächstes Spiel, Ansage – am Handy in der Hosentasche</span></li>
<li>{ICON['check']}<span><b>Werkzeuge:</b> Teams einteilen, Punkte zählen, Zufallsauswahl, Intervall-Timer</span></li>
<li>{ICON['check']}<span><b>Stundenbild fürs Praktikum</b> mit Lernzielen, Organisation und Lehrplanbezug (Pro)</span></li>
<li>{ICON['check']}<span><b>Kein Konto, keine Schülerdaten</b> auf einem Server – alles bleibt auf deinem Gerät</span></li></ul>
<div class="knopfreihe"><a class="knopf primaer gross" href="{s.zu('app/')}">App kostenlos öffnen</a><a class="knopf gross" href="{s.zu('pro/')}">Was kann Pro?</a></div></div>
<div class="telefon" aria-hidden="true"><div class="telefon-schirm"><div class="telefon-kopf"><small>3. Schulstufe · 50 min · ganze Halle</small><b>Deine Stunde</b></div>
<div class="telefon-block" style="--b:#b88407"><small>0–3′ Einstieg</small><b>Begrüßung & Stundenziel</b></div>
<div class="telefon-block" style="--b:#c8402a"><small>3–10′ Aufwärmen</small><b>Kettenfangen</b></div>
<div class="telefon-block" style="--b:#1f5bd8"><small>10–25′ Hauptteil</small><b>Flussüberquerung</b></div>
<div class="telefon-block" style="--b:#1f5bd8"><small>25–38′ Hauptteil</small><b>Menschenmemory</b></div>
<div class="telefon-block" style="--b:#167a4b"><small>38–45′ Abschluss</small><b>Sortieren</b></div>
<div class="telefon-knopf">▶ Stunde starten</div></div></div>
</div></section>'''
        return f'''<section class="hero"><div class="wrap">
<div><p class="oberzeile">Bewegung und Sport · Volksschule bis Oberstufe</p>
<h1>Weniger Vorbereitung. <em>Mehr Bewegungszeit.</em></h1>
{hero_text}
<p class="hero-klein">{hero_klein}</p></div>
<div class="buecherstapel" aria-hidden="true">{stapel}</div>
</div></section>

<section class="abschnitt eng"><div class="wrap"><div class="zahlen">
<div class="zahl"><b>{esc(E['abonnenten'])}+</b><span>Abonnent:innen auf YouTube</span></div>
<div class="zahl"><b>{mio(views)}</b><span>Videoaufrufe seit {kanal_seit()}</span></div>
<div class="zahl"><b>{len(VIDEOS)}</b><span>Spiele und Übungen mit Video</span></div>
<div class="zahl"><b>{sum(BUECHER[b['slug']]['anzahl'] for b in SPIELBAENDE)}</b><span>ausgearbeitete Anleitungen in der E-Book-Reihe</span></div>
</div></div></section>
{spiel_der_woche(s)}

<section class="abschnitt"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Drei Wege zur nächsten Stunde</p><h2>Such dir aus, wie viel du vorbereiten willst</h2></div></div>
<div class="raster drei">
<a class="karte link" href="{s.zu('spiele/')}"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['video']}</div><h3>Spiele-Lexikon</h3><p>Alle {len(VIDEOS)} Videos, filterbar nach Schulstufe, Stundenteil, Thema und Material. Kostenlos, ohne Anmeldung.</p><span class="mehr">Spiele finden {ICON['pfeil'].replace('<svg', '<svg width="18" height="18"')}</span></a>
{mitte_karte}
<a class="karte link" href="{s.zu('ebooks/')}"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['buch']}</div><h3>Die Praxis-Reihe</h3><p>{BAENDE_WORT.capitalize()} E-Books mit Ansagetexten, Varianten, Sicherheitshinweisen und QR-Codes zu jedem Video – plus ein Band für die schwierigen Situationen im Turnsaal.</p><span class="mehr">E-Books ansehen {ICON['pfeil'].replace('<svg', '<svg width="18" height="18"')}</span></a>
</div></div></section>

<section class="abschnitt dunkel" id="zufall"><div class="wrap zufall">
<div class="zufall-steuerung"><p class="oberzeile">Keine Idee für morgen?</p><h2 style="color:#fff">Ein Spiel, sofort.</h2>
<p class="einleitung">Wähl die Schulstufe – du bekommst ein erprobtes Spiel mit Video und Anleitung. Passt nicht? Einfach noch einmal.</p>
<div class="stufenwahl" role="group" aria-label="Schulstufe">
<button type="button" data-stufe="1-4" aria-pressed="true">Volksschule</button><button type="button" data-stufe="5-8" aria-pressed="false">Unterstufe</button><button type="button" data-stufe="9-13" aria-pressed="false">Oberstufe</button><button type="button" data-stufe="1-13" aria-pressed="false">egal</button></div>
<button type="button" class="knopf pro gross" id="zufall-los" style="align-self:flex-start">{ICON['zufall']} Anderes Spiel</button></div>
<div class="spielkarte" id="spielkarte" aria-live="polite"><h3>Robin Hood</h3><p>Lade die Seite mit JavaScript, um Spiele zufällig vorzuschlagen – oder stöbere im <a href="{s.zu('spiele/')}">Spiele-Lexikon</a>.</p></div>
<script type="application/json" id="zufall-daten">{daten}</script>
<script type="application/json" id="zufall-basis">{json.dumps({'spiele': s.zu('spiele/'), 'vorschau': VORSCHAU})}</script>
</div></section>

<section class="abschnitt" id="werkzeuge"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Für die Halle</p><h2>Dein Handy als Assistent</h2>
<p class="einleitung">Werkzeuge, die in jeder Stunde gebraucht werden – groß, schnell, ohne Anmeldung. Namen, Punkte und Pläne bleiben auf deinem Gerät.</p></div>
<a class="knopf" href="{s.zu('werkzeuge/')}">Alle Werkzeuge</a></div>
<div class="raster drei werkzeug-karten">
<a class="karte link" href="{s.zu('werkzeuge/')}#timer"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['timer']}</div><h3>Zirkeltimer</h3><p>Tabata, Stationen, Runden – mit großem Countdown und Signalton beim Wechsel.</p></a>
<a class="karte link" href="{s.zu('werkzeuge/')}#teams"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['teams']}</div><h3>Teams</h3><p>Gleich große Teams in Sekunden – mit Namen oder nur nach Anzahl, inkl. Leibchenfarbe.</p></a>
<a class="karte link" href="{s.zu('werkzeuge/')}#punkte"><div class="symbol" style="background:var(--gelb-weich);color:var(--gelb)">{ICON['punkte']}</div><h3>Punkte</h3><p>Anzeigetafel für bis zu vier Teams. Großer Plus-Knopf, auch mit verschwitzten Fingern.</p></a>
<a class="karte link" href="{s.zu('werkzeuge/')}#zufall"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['zufall']}</div><h3>Zufall</h3><p>Würfel, Münze, Zahl oder Name ziehen – fair und ohne Diskussion.</p></a>
<a class="karte link" href="{s.zu('raumplaner/')}"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['raum']}</div><h3>Raumplaner</h3><p>Geräte maßstabsgetreu in die Halle ziehen – mit Materialliste zum Aufbauen und Ausdrucken.</p></a>
<a class="karte link" href="{s.zu('bewegte-pause/')}"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['pause']}</div><h3>Bewegte Pause</h3><p>Ein Spiel ganz ohne Material mit Video und Timer – für zwischendurch, auf Knopfdruck.</p></a>
</div></div></section>

<section class="abschnitt" id="videos"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Die beliebtesten Videos</p><h2>Direkt ansehen, morgen nachspielen</h2>
<p class="einleitung">Die meistgesehenen Spiele des Kanals – jedes mit ausführlicher Anleitung im Spiele-Lexikon und im E-Book.</p></div>
<a class="knopf" href="{s.zu('spiele/')}">Alle {len(VIDEOS)} Videos</a></div>
{video_raster(s)}
</div></section>
{app_teaser if APP_DA else ''}

<section class="abschnitt hell"><div class="wrap">
<div class="kopfzeile"><div><p class="oberzeile">Die Praxis-Reihe</p><h2>{BAENDE_WORT.capitalize()} E-Books für die Halle</h2><p class="einleitung">Jedes Spiel mit Video-Demo per QR-Code, Ansagetext zum Vorlesen, Varianten und Sicherheitshinweis – dazu ein Band für Sicherheit, Angst, Konflikte, Motivation und Nicht-Aktive. Zu jedem Band gibt es eine kostenlose Leseprobe.</p></div><a class="knopf" href="{s.zu('ebooks/')}">Alle E-Books</a></div>
<div class="buecher">{buecher}</div>
<div style="margin-top:26px">{komplett_banner(s)}</div>
</div></section>

<section class="abschnitt"><div class="wrap"><div class="waehler" id="waehler">
<p class="oberzeile">In 5 Sekunden</p><h2>Welcher Band passt zu dir?</h2>
<div class="waehler-knoepfe" role="group" aria-label="Was trifft auf dich zu?">
<button type="button" aria-pressed="false" data-ziel="spielesammlung">Ich brauche schnell Spiele, die sicher funktionieren<small>für jede Stunde, jede Halle</small></button>
<button type="button" aria-pressed="false" data-ziel="aufwaermen">Mir fehlen gute Einstiege<small>Klasse sofort in Bewegung</small></button>
<button type="button" aria-pressed="false" data-ziel="turnen">Turnen macht mich nervös<small>Hilfestellung, Sicherheit, Methodik</small></button>
<button type="button" aria-pressed="false" data-ziel="fitness">Fitness ohne Drill<small>Zirkel, Ausdauer, Koordination</small></button>
<button type="button" aria-pressed="false" data-ziel="praktikum">Ich bin im Praktikum<small>Stundenbilder schreiben</small></button>
<button type="button" aria-pressed="false" data-ziel="alle-dabei">Meine Klasse ist eine Herausforderung<small>Angst, Konflikte, Motivation, volle Bank</small></button>
<button type="button" aria-pressed="false" data-ziel="komplettpaket">Ich will alles<small>fürs ganze Schuljahr</small></button></div>
<div class="waehler-ergebnis" id="waehler-ergebnis" aria-live="polite"></div>
<script type="application/json" id="waehler-daten">{waehler}</script>
</div></div></section>

<section class="abschnitt hell"><div class="wrap raster zwei">
<div class="karte"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['student']}</div><h3>Für Studierende</h3><p>Das Praktikums-Kit bringt 12 fertige Stundenbilder und einen Leitfaden für Lernziele, Lehrplanbezug, Organisation und Reflexion{' – dazu der Praktikums-Pass für die App' if APP_DA else ''}.</p><a class="knopf" href="{s.zu('ebooks/praktikum/')}">Zum Praktikums-Kit</a></div>
<div class="karte"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['schule']}</div><h3>Für Schulen</h3><p>Die ganze Reihe für die Fachgruppe: Schullizenz mit Rechnung an die Schule, Ablage auf dem Schulserver erlaubt. Plus ein Aushang fürs Lehrerzimmer.</p><a class="knopf" href="{s.zu('schulen/')}">Schullizenz ansehen</a></div>
</div></section>

<section class="abschnitt"><div class="wrap">{newsletter_block(s)}</div></section>

<section class="abschnitt hell"><div class="wrap autor">
<div class="autor-bild" aria-hidden="true">DJ</div>
<div><p class="oberzeile">Über mich</p><h2>Aus der Halle, für die Halle</h2>
<p class="einleitung">Ich bin DJ, unterrichte Bewegung und Sport an einer AHS in Wien, leite Wintersportwochen und bilde an der Universität angehende Sportlehrer:innen aus. Auf YouTube zeige ich seit {kanal_seit()} Spiele und Übungen so, wie sie im echten Unterricht funktionieren – mit echten Klassen, in echten Hallen.</p>
<a class="knopf" href="{s.zu('ueber/')}">Mehr über mich</a></div></div></section>

<section class="abschnitt"><div class="wrap" style="max-width:860px">
<h2>Häufige Fragen</h2>{faq_html(faq_liste(s)[:5])}
<p style="margin-top:18px"><a href="{s.zu('faq/')}">Alle Fragen und Antworten</a></p></div></section>'''
    schema = [{'@context': 'https://schema.org', '@type': 'WebSite', 'name': 'Sportunterricht', 'inLanguage': 'de-AT', **({'url': DOMAIN + '/'} if DOMAIN else {})},
              {'@context': 'https://schema.org', '@type': 'Person', 'name': E.get('name_voll') or 'DJ', 'jobTitle': 'Lehrer für Bewegung und Sport', 'sameAs': [E['youtube']]}]
    seite('', 'Sportunterricht – Spiele, Stundenbilder & E-Books für Bewegung und Sport',
          f'Über {len(VIDEOS) // 10 * 10} Spiele mit Video, eine kostenlose App für die Stundenplanung und E-Books für Bewegung und Sport – von der Volksschule bis zur Oberstufe.',
          inhalt, og='og-start.png', schema=schema, voller_titel=True)


def ebooks_index():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>E-Books</li></ol></nav>
<p class="oberzeile">Die Praxis-Reihe</p><h1>E-Books für Bewegung und Sport</h1>
<p class="einleitung">{BAENDE_WORT.capitalize()} Bände: Vier Spielebände, in denen jedes Spiel Schulstufe, Gruppengröße, Material, realistische Spielzeit, Lernziel, Ansagetext, Varianten, Sicherheitshinweis und QR-Code zur Video-Demo hat. Dazu das Praktikums-Kit mit 12 Stundenbildern und „Alle dabei, alle sicher“ für die schwierigen Situationen im Turnsaal. Sofort als PDF – zu jedem Band gibt es eine kostenlose Leseprobe.</p>
<h2 class="sr-only">Alle Bände</h2><div class="buecher" style="margin-top:26px">{''.join(buchkarte(s, b) for b in REIHE)}</div>
<div style="margin-top:30px">{komplett_banner(s)}</div>
</div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Welcher Band für welche Situation?</h2><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table>
<thead><tr><th>Band</th><th>Ideal, wenn …</th><th>Schulstufe</th><th>Umfang</th><th>Preis</th></tr></thead><tbody>
{''.join(f'<tr><td><a href="{s.zu("ebooks/" + b["slug"] + "/")}"><b>{b["band"]} · {esc(b["kurz"])}</b></a></td><td>{esc(TEXTE[b["slug"]]["fuer"])}</td><td>{BUECHER[b["slug"]]["stufen"]}</td><td>{BUECHER[b["slug"]]["anzahl"]} {b["einheit"]} · {BUECHER[b["slug"]]["seiten"]} Seiten</td><td><b>{b["preis"]}</b></td></tr>' for b in REIHE)}
</tbody></table></div></div></section>'''
    seite('ebooks/', 'E-Books für den Sportunterricht – die Praxis-Reihe', f'{BAENDE_WORT.capitalize()} E-Books für Bewegung und Sport: Spiele, Aufwärmen, Turnen, Fitness, Praktikums-Kit und „Alle dabei, alle sicher“ – mit Leseproben.', inhalt, aktiv='ebooks/', og='og-start.png')


def muster_html(e, farbe):
    m = e['meta']
    meta = ''.join(f'<div><span>{lab}</span>{esc(str(m.get(k, "")))}</div>' for k, lab in buchpdf.META_ANZEIGE if m.get(k))
    teile = []
    for label, text in e['abschnitte']:
        if not text:
            continue
        if label == 'So erklärst du es':
            teile.append(f'<h4>So erklärst du es</h4><div class="ansage">{buchpdf.md(text)}</div>')
        elif label == 'Sicherheitshinweis':
            teile.append(f'<div class="hinweisbox gelb" style="padding:10px 14px;margin-top:10px"><b>Sicherheit:</b> {esc(text)}</div>')
        else:
            teile.append(f'<h4>{"Leichter / schwerer" if label.startswith("Variationen") else esc(label)}</h4>{buchpdf.md(text)}')
    lz = f'<p><b>Lernziel:</b> {esc(m["Lernziel"])}</p>' if m.get('Lernziel') else ''
    return f'<div class="eintrag-muster" style="--akzent:{farbe};--buchfarbe:{farbe}"><h3>{e["nr"]} · {esc(e["name"])}</h3><div class="meta">{meta}</div>{lz}{"".join(teile)}</div>'


def produktseiten():
    for b in REIHE:
        d = BUECHER[b['slug']]
        t = TEXTE[b['slug']]

        def inhalt(s, b=b, d=d, t=t):
            kap = ''.join(f'<li><details><summary>{esc(k)}{f" <span class=chip>{len(n)}</span>" if n and not isinstance(n, str) else ""}</summary><div>{esc(n) if isinstance(n, str) else ", ".join(esc(x) for x in n) if n else "Leitfaden-Kapitel mit Beispielen, Tabellen und Checklisten."}</div></details></li>' for k, n in d['kapitel'])
            if d.get('auszug'):
                a = d['auszug']
                muster = (f'<h2>Ein Blick ins Buch</h2><p>So beginnt jedes Kapitel – hier „{esc(a["titel"].split(" – ", 1)[1])}“, das komplett in der kostenlosen Leseprobe steht:</p>'
                          f'<div class="eintrag-muster" style="--akzent:{b["farbe"]};--buchfarbe:{b["farbe"]}"><h3>Auf einen Blick</h3><ul>{"".join("<li>" + esc(x) + "</li>" for x in a["punkte"])}</ul>'
                          f'<h4>So sagst du es</h4><div class="ansage"><p>{esc(a["ansage"])}</p></div>'
                          f'<p style="margin-top:12px"><b>Kopiervorlagen im Buch:</b> {esc(", ".join(d["vorlagen"]))}.</p></div>')
            elif d.get('muster'):
                muster = f'<h2>So sieht jeder Eintrag aus</h2><p>Ein vollständiges Beispiel aus dem Buch – genau so ist jede Seite aufgebaut:</p>{muster_html(d["muster"], b["farbe"])}'
            else:
                st = d['stunden'][0]
                zeilen = ''.join(f'<tr><td><b>{x["von"]}–{x["bis"]}′</b></td><td>{x["phase"]}</td><td><b>{esc(x["titel"])}</b></td><td>{esc(x.get("lernziel") or "")}</td></tr>' for x in st['bloecke'])
                muster = f'<h2>So sieht ein Stundenbild aus</h2><p>Stundenbild 1 · {st["stufe"]}. Schulstufe · „{esc(st["titel"])}“ – im Buch mit Organisation, Material, Differenzierung, Sicherheit und Lehrplanbezug in jeder Zeile, plus einer Seite „Ablauf im Detail“.</p><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table><thead><tr><th>Zeit</th><th>Phase</th><th>Inhalt</th><th>Lernziel</th></tr></thead><tbody>{zeilen}</tbody></table></div>'
            andere = ''.join(buchkarte(s, x) for x in REIHE if x['slug'] != b['slug'])
            punkte = ''.join(f'<li>{ICON["check"]}<span>{esc(p)}</span></li>' for p in t['punkte'])
            return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('ebooks/')}">E-Books</a></li><li>{esc(b['kurz'])}</li></ol></nav>
<div class="produkt"><div class="produkt-bild"><img src="{cover(s, b['slug'])}" alt="Cover: {esc(b['titel'])}" width="360" height="509"></div>
<div><p class="oberzeile buchfarbe" style="--buchfarbe:{b['farbe']}">Band {b['band']} der Praxis-Reihe</p><h1 style="font-size:clamp(2.2rem,5.5vw,3.6rem)">{esc(b['titel'])}</h1>
<p class="einleitung">{esc(b['unter'])}</p>
<div class="kaufbox"><div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap"><span class="preis">{b['preis']}</span><span class="marke gruen">Sofort als PDF</span></div>
<ul>{punkte}</ul>
<div class="knopfreihe">{kauf_knopf(s, b['slug'])}<a class="knopf gross" href="{s.zu('downloads/leseprobe-' + b['slug'] + '.pdf')}" download>{ICON['download']} Leseprobe ({d['probe_seiten']} Seiten)</a></div>
<p class="klein">{d['anzahl']} {b['einheit']} · {d['seiten']} Seiten A4 · {d['stufen']}. Schulstufe · Einzellizenz für deinen eigenen Unterricht · sichere Zahlung über Digistore24</p></div>
<h2>Für wen ist dieser Band?</h2><p>{esc(t['fuer'])}</p>
<h2>Das steckt drin</h2><ul class="kapitelliste">{kap}</ul>
{muster}
<div class="hinweisbox" style="margin-top:26px"><h3>Tipp: Im Komplettpaket sparst du</h3><p>Alle {BAENDE_WORT} Bände plus Jahresplaner für {KOMPLETT['preis']} statt {KOMPLETT['statt']}.</p><a class="knopf" href="{s.zu('ebooks/komplettpaket/')}">Zum Komplettpaket</a></div>
</div></div></div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Die anderen Bände</h2><div class="buecher">{andere}</div></div></section>'''
        schema = [{'@context': 'https://schema.org', '@type': 'Product', 'name': b['titel'], 'description': b['unter'], 'category': 'E-Book',
                   'brand': {'@type': 'Brand', 'name': 'Sportunterricht'}, 'image': [f'{DOMAIN}/assets/cover/{b["slug"]}.png'] if DOMAIN else [],
                   'offers': {'@type': 'Offer', 'price': b['preis'].replace(' €', '').replace(',', '.'), 'priceCurrency': 'EUR',
                              'availability': 'https://schema.org/InStock' if KAUF.get(b['slug']) else 'https://schema.org/PreOrder', **({'url': url_abs(f'ebooks/{b["slug"]}/')} if DOMAIN else {})}}]
        seite(f'ebooks/{b["slug"]}/', f'{b["titel"]} – E-Book für den Sportunterricht', f'{b["unter"]}. {d["anzahl"]} {b["einheit"]}, {b["preis"]}, sofort als PDF – mit kostenloser Leseprobe.'[:158],
              inhalt, aktiv='ebooks/', og=f'og-{b["slug"]}.png', schema=schema, voller_titel=True)


def komplettseite():
    def inhalt(s):
        zeilen = ''.join(f'<tr><td><a href="{s.zu("ebooks/" + b["slug"] + "/")}">Band {b["band"]} · {esc(b["titel"])}</a></td><td>{BUECHER[b["slug"]]["anzahl"]} {b["einheit"]}</td><td>{b["preis"]}</td></tr>' for b in REIHE)
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('ebooks/')}">E-Books</a></li><li>Komplettpaket</li></ol></nav>
{komplett_banner(s, h='h1')}
<div class="raster zwei" style="margin-top:34px;align-items:start">
<div><h2>Was drin ist</h2><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table><thead><tr><th>Band</th><th>Umfang</th><th>Einzeln</th></tr></thead><tbody>{zeilen}
<tr><td><b>Bonus: Jahresplaner</b> – zehn Monatsschwerpunkte mit je vier Ideen für Volksschule und Sekundarstufe I, plus Vorlage zum Ausfüllen</td><td>6 Seiten</td><td>nur im Paket</td></tr>
<tr><td><b>Zusammen</b></td><td></td><td><s>{KOMPLETT['statt']}</s> <b>{KOMPLETT['preis']}</b></td></tr></tbody></table></div></div>
<div><h2>Für wen?</h2><p>Für alle, die das ganze Schuljahr abdecken wollen: vom Aufwärmen über Turnen und Fitness bis zu den großen Spielen, dazu Sicherheit, Motivation und der Umgang mit schwierigen Situationen – und für Studierende, die neben dem Praktikums-Kit gleich die Anleitungen zu allen Spielen der Stundenbilder haben wollen.</p>
<div class="knopfreihe">{kauf_knopf(s, 'komplettpaket', 'Komplettpaket kaufen')}</div>
<p style="margin-top:14px;color:var(--tinte-3)">Du bekommst alle {N_BAENDE + 1} PDFs sofort nach dem Kauf. Einzellizenz für deinen eigenen Unterricht – für die ganze Fachgruppe gibt es die <a href="{s.zu('schulen/')}">Schullizenz</a>.</p></div></div>
</div></section>'''
    schema = [{'@context': 'https://schema.org', '@type': 'Product', 'name': 'Komplettpaket Praxis-Reihe Sportunterricht', 'description': f'Alle {BAENDE_WORT} E-Books der Praxis-Reihe plus Jahresplaner.',
               'brand': {'@type': 'Brand', 'name': 'Sportunterricht'}, 'offers': {'@type': 'Offer', 'price': KOMPLETT['preis'].replace(' €', '').replace(',', '.'), 'priceCurrency': 'EUR',
                                                                                  'availability': 'https://schema.org/InStock' if KAUF.get('komplettpaket') else 'https://schema.org/PreOrder'}}]
    seite('ebooks/komplettpaket/', f'Komplettpaket – alle {N_BAENDE} E-Books für den Sportunterricht', f'Alle {BAENDE_WORT} Bände der Praxis-Reihe plus Jahresplaner für {KOMPLETT["preis"]} statt {KOMPLETT["statt"]} – sofort als PDF.', inhalt, aktiv='ebooks/', og='og-komplettpaket.png', schema=schema, voller_titel=True)


def pro_preise():
    txt = (APP / 'src/views/Pro.jsx').read_text()
    return [dict(zip(('id', 'name', 'preis', 'zusatz'), m)) for m in re.findall(r"\{ id: '(\w+)', name: '([^']+)', preis: '([^']+)', zusatz: '([^']+)'", txt)]


def proseite():
    preise = pro_preise()

    def inhalt(s):
        tarife = ''
        for p in preise:
            emp = p['id'] == 'jahr'
            tarife += f'''<div class="tarif{' empfohlen' if emp else ''}">{'<span class="marke gelb">Beliebteste Wahl</span>' if emp else ''}<h3>{esc(p['name'])}</h3><span class="preis">{p['preis']}</span><p>{esc(p['zusatz'])}</p>{kauf_knopf(s, 'pro_' + p['id'], 'Pro ' + p['name'].split('-')[0].lower() + ' kaufen' if p['id'] != 'praktikum' else 'Praktikums-Pass kaufen', 'knopf ' + ('pro' if emp else 'primaer'))}</div>'''
        zeilen = [('Alle Spiele mit Video, Suche und Filter', 'ja', 'ja'), ('Stunde planen (Aufwärmen, Hauptteil, Abschluss)', 'ja', 'ja'),
                  ('Timer, Teams, Punkte, Zufall, Stundenmodus', 'ja', 'ja'), ('Stunden starten, speichern und teilen', '3 pro Monat', 'unbegrenzt'),
                  ('Ganze Spielanleitung mit Varianten und Sicherheit', 'Kurzfassung', 'ja'), ('Ansagetext zum Vorlesen', '–', 'ja'),
                  ('Stundenbild fürs Praktikum (bearbeitbar, druckbar)', '–', 'ja'), ('Klassen-Verlauf: nichts doppelt spielen', '–', 'ja'),
                  ('Videos werbefrei direkt in der App', '–', 'nach und nach')]
        tab = ''.join(f'<tr><td>{a}</td><td{" class=ja" if b == "ja" else ""}>{"✓" if b == "ja" else b}</td><td{" class=ja" if c == "ja" else ""}>{"✓" if c == "ja" else c}</td></tr>' for a, b, c in zeilen)
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('app/')}">App</a></li><li>Pro</li></ol></nav>
<div class="kopfzeile"><div><p class="oberzeile">App Pro</p><h1>Die Stunde steht. Du erklärst nur noch.</h1>
<p class="einleitung">Pro macht aus dem Stundenvorschlag eine fertige Stunde: mit Ansagetexten zum Vorlesen, der ganzen Anleitung zu jedem Spiel und dem Stundenbild fürs Praktikum.</p></div>
<a class="knopf gross" href="{s.zu('app/')}">Erst kostenlos testen</a></div>
<div class="tarife">{tarife}</div>
<p style="color:var(--tinte-3);margin-top:12px">Preise inkl. USt. Abos jederzeit zum Ende des Zeitraums kündbar. Der Praktikums-Pass ist eine Einmalzahlung für 6 Monate.</p>
</div></section>
<section class="abschnitt hell"><div class="wrap raster zwei" style="align-items:start">
<div><h2>Kostenlos und Pro im Vergleich</h2><div class="tabelle-wrap" tabindex="0" role="region" aria-label="Tabelle (seitlich scrollbar)"><table><thead><tr><th>Funktion</th><th>Kostenlos</th><th>Pro</th></tr></thead><tbody>{tab}</tbody></table></div></div>
<div><h2>So schaltest du Pro frei</h2><ol class="haken" style="list-style:none">
<li>{ICON['check']}<span><b>Tarif wählen und bezahlen</b> – sicher über Digistore24.</span></li>
<li>{ICON['check']}<span><b>E-Mail öffnen:</b> Dort stehen deine Bestellnummer und dein Lizenzschlüssel.</span></li>
<li>{ICON['check']}<span><b>In der App</b> auf „Pro“ tippen und beides eingeben – fertig. Das geht auf jedem deiner Geräte.</span></li></ol>
<div class="hinweisbox"><h3>Werbung in den Videos?</h3><p>Auf YouTube spielt YouTube Werbung aus – auch bei eingebetteten Videos. Für Pro stelle ich die Videos nach und nach werbefrei direkt in der App bereit. Die Website und die App selbst sind immer werbefrei.</p></div></div>
</div></section>
<section class="abschnitt"><div class="wrap" style="max-width:860px"><h2>Fragen zu Pro</h2>{faq_html([f for f in faq_liste(s) if any(w in f[0] for w in ('Pro', 'Handy', 'Schüler', 'Werbung', 'Vertragspartner'))])}</div></section>'''
    seite('pro/', 'App Pro – Stundenplanung mit Ansagetext und Stundenbild', 'Sportunterricht Pro: unbegrenzt Stunden planen, ganze Spielanleitungen mit Ansagetext, Stundenbild fürs Praktikum und Klassen-Verlauf. Ab 2,49 € im Monat.', inhalt, aktiv='app/', og='og-pro.png')


# ---------------------------------------------------------------- Planer, Werkzeuge, Merkliste

def merk_knopf(vid, name, klein=False):
    """Herz-Knopf: merkt ein Spiel auf diesem Gerät (localStorage, siehe site.js)."""
    return (f'<button type="button" class="merken{" klein" if klein else ""}" data-merk="{vid}" aria-pressed="false" '
            f'aria-label="„{esc(name)}“ merken">{ICON["herz"]}<span>Merken</span></button>')


def spiele_daten(nur=None):
    """Kompakte Spieldaten für Planer und Merkliste (nur öffentliche Angaben – keine Ansagetexte aus den Büchern)."""
    out = []
    for x in SPIELE:
        if nur is not None and x['v']['id'] not in nur:
            continue
        v, a = x['v'], x['a'] or {}
        e = {'i': v['id'], 'n': x['name'], 's': x['slug'], 'von': v['stufeVon'], 'bis': v['stufeBis'], 'ph': x['phasen'],
             'm': 'ohne' if v.get('ohneMaterial') or re.match(r'\s*(kein|ohne)', a.get('materialText') or '', re.I) else v.get('material', 'standard'),
             'mt': kuerzen(a.get('materialText') or x['material'], 130),
             'th': v.get('tags') or [], 'f': x['farbe'], 'au': v['aufrufe']}
        if x['a']:
            e.update({'a': 1, 'lz': a.get('lernziel', ''), 'tx': saetze(a.get('beschreibung'), 2), 'gr': a.get('gruppe', ''), 'b': x['buch']})
        if x.get('spielzeit'):
            e['d'] = x['spielzeit']
        out.append(e)
    return json.dumps(out, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')


def basis_daten(s):
    return json.dumps({'spiele': s.zu('spiele/'), 'qr': s.zu('assets/qr/'), 'planer': s.zu('planer/'), 'merkliste': s.zu('merkliste/'),
                       'ebooks': s.zu('ebooks/'), 'vorschau': VORSCHAU, 'artifact': ARTIFACT,
                       'baende': {b['slug']: {'t': b['titel'], 'k': b['kurz'], 'n': b['band'], 'p': b['preis']} for b in REIHE}}, ensure_ascii=False)


def qr_codes():
    """QR-Code je Video (für die Stationskarten der Merkliste) – zeigt auf das YouTube-Video."""
    import qrcode
    ziel = OUT / 'assets/qr'
    ziel.mkdir(parents=True, exist_ok=True)
    for x in SPIELE:
        q = qrcode.QRCode(border=2, error_correction=qrcode.constants.ERROR_CORRECT_M)
        q.add_data(f'https://youtu.be/{x["v"]["id"]}')
        q.make(fit=True)
        m = q.get_matrix()
        pfad = []
        for y, zeile in enumerate(m):  # zusammenhängende Pixel einer Zeile als ein Rechteck → kleine Dateien
            xi = 0
            while xi < len(zeile):
                if zeile[xi]:
                    start = xi
                    while xi < len(zeile) and zeile[xi]:
                        xi += 1
                    pfad.append(f'M{start} {y}h{xi - start}v1h-{xi - start}z')
                else:
                    xi += 1
        n = len(m)
        (ziel / f'{x["v"]["id"]}.svg').write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges"><rect width="{n}" height="{n}" fill="#fff"/><path d="{"".join(pfad)}"/></svg>')


def planerseite():
    mit = [x for x in SPIELE if x['a'] and x.get('spielzeit')]
    themen = sorted({t for x in mit for t in (x['v'].get('tags') or []) if t in THEMA}, key=lambda t: list(THEMA).index(t))

    def inhalt(s):
        stufen = ''.join(f'<option value="{i}"{" selected" if i == 5 else ""}>{i}. Schulstufe</option>' for i in range(1, 14))
        th = ''.join(f'<option value="{k}">{THEMA[k][0]}</option>' for k in themen)
        return f'''<section class="abschnitt eng keindruck"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Stunde planen</li></ol></nav>
<div class="kopfzeile"><div><p class="oberzeile">Stundenplaner · kostenlos</p><h1>Deine Stunde in 10 Sekunden</h1>
<p class="einleitung">Schulstufe, Dauer und Material wählen – der Planer stellt aus {len(mit)} erprobten Spielen eine Stunde mit Aufwärmen, Hauptteil und Abschluss zusammen. Mit realistischen Spielzeiten, Lernzielen und Video zu jedem Spiel. Passt etwas nicht? Austauschen. Fertig? Als Stundenbild drucken.</p></div></div>
<form class="planer-form" id="planer-form">
<label>Schulstufe<select name="stufe" id="p-stufe">{stufen}</select></label>
<label>Dauer<select name="dauer" id="p-dauer"><option value="45">45 Minuten</option><option value="50" selected>50 Minuten</option><option value="90">90 Minuten (Doppelstunde)</option><option value="100">100 Minuten (Doppelstunde)</option></select></label>
<label>Schwerpunkt<select name="thema" id="p-thema"><option value="">gemischt</option>{th}</select></label>
<fieldset class="planer-material"><legend>Was gibt es in deiner Halle? <small>(Bälle, Hütchen, Reifen & Co. setzt der Planer voraus)</small></legend>
<label><input type="checkbox" name="mat" value="matten" checked> Matten & Bänke</label>
<label><input type="checkbox" name="mat" value="tore" checked> Tore, Körbe, Netz</label>
<label><input type="checkbox" name="mat" value="geraete"> Turngeräte</label>
<label><input type="checkbox" name="ohne" id="p-ohne"> nur Spiele ganz ohne Material</label></fieldset>
<button class="knopf primaer gross" type="submit">{ICON['zufall']} Stunde planen</button>
</form>
<noscript><p class="hinweisbox">Der Stundenplaner braucht JavaScript. Ohne JavaScript findest du alle Spiele im <a href="{s.zu('spiele/')}">Spiele-Lexikon</a>.</p></noscript>
</div></section>
<section class="abschnitt eng hell" id="planer-bereich" hidden><div class="wrap">
<div id="planer-ergebnis" aria-live="polite"></div>
</div></section>
<div id="stundenbild" class="nur-druck"></div>
<div id="karten-druck" class="nur-druck"></div>
<section class="abschnitt keindruck"><div class="wrap raster drei">
<div class="karte"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['student']}</div><h3>Fürs Praktikum</h3><p>„Stundenbild drucken“ macht aus deiner Stunde eine A4-Verlaufsplanung mit Zeit, Phase, Inhalt, Organisation und Lernziel – mit Platz für deine Notizen.</p></div>
<div class="karte"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['pfeil']}</div><h3>Teilen per Link</h3><p>Jede Stunde hat einen eigenen Link. Schick ihn an Kolleg:innen oder speichere ihn als Lesezeichen – die Stunde bleibt genau so.</p></div>
<div class="karte"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['buch']}</div><h3>Die ganze Anleitung</h3><p>Ansagetext, Varianten und Sicherheitshinweis zu jedem Spiel stehen in der <a href="{s.zu('ebooks/')}">Praxis-Reihe</a> – zum Ausdrucken für die Halle.</p></div>
</div></section>
<script type="application/json" id="spiele-daten">{spiele_daten()}</script>
<script type="application/json" id="seiten-basis">{basis_daten(s)}</script>'''
    seite('planer/', 'Stundenplaner für den Sportunterricht – Stunde in 10 Sekunden', 'Kostenloser Stundenplaner für Bewegung und Sport: Schulstufe, Dauer und Material wählen, fertige Stunde mit Aufwärmen, Hauptteil und Abschluss bekommen – als Stundenbild druckbar.',
          inhalt, aktiv='planer/', skripte=('karten.js', 'planer.js'), voller_titel=True)


def werkzeugeseite():
    def inhalt(s):
        teams_opt = ''.join(f'<option{" selected" if i == 2 else ""}>{i}</option>' for i in range(2, 9))
        tab = lambda k, t, ico: f'<button type="button" role="tab" id="tab-{k}" aria-controls="{k}" aria-selected="false" tabindex="-1">{ICON[ico]}<span>{t}</span></button>'  # noqa: E731
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Werkzeuge</li></ol></nav>
<p class="oberzeile">Für die Halle · kostenlos</p><h1>Werkzeuge für die Halle</h1>
<p class="einleitung">Zirkeltimer, Teameinteilung, Punktezähler und Zufall – gemacht fürs Handy in der Hosentasche. Keine Anmeldung, keine Werbung; Namen und Punkte bleiben auf deinem Gerät. Tipp: Seite zum Home-Bildschirm hinzufügen.</p>
<p class="werkzeug-mehr">Außerdem: <a href="{s.zu('raumplaner/')}">{ICON['raum']} Raumplaner</a> <a href="{s.zu('bewegte-pause/')}">{ICON['pause']} Bewegte Pause</a></p>
<div class="werkzeug-tabs" role="tablist" aria-label="Werkzeug wählen">{tab('timer', 'Timer', 'timer')}{tab('teams', 'Teams', 'teams')}{tab('punkte', 'Punkte', 'punkte')}{tab('zufall', 'Zufall', 'zufall')}</div>

<section class="werkzeug" id="timer" role="tabpanel" aria-labelledby="tab-timer">
<h2>Timer &amp; Zirkeltraining</h2>
<div class="timer" id="t-box" data-phase="bereit">
<p class="t-phase" id="t-phase">Bereit</p><p class="t-zeit" id="t-zeit" role="timer" aria-live="off">01:00</p><p class="t-info" id="t-info">&nbsp;</p>
<div class="t-balken" aria-hidden="true"><i id="t-fortschritt"></i></div>
<div class="knopfreihe t-knoepfe"><button type="button" class="knopf pro gross" id="t-start">Start</button><button type="button" class="knopf gross" id="t-reset">Zurück</button><button type="button" class="knopf gross" id="t-vollbild">Vollbild</button></div>
</div>
<form class="t-form" id="t-form" onsubmit="return false">
<fieldset class="t-modus"><legend>Modus</legend>
<label><input type="radio" name="modus" value="countdown" checked> Countdown</label>
<label><input type="radio" name="modus" value="intervall"> Intervall / Zirkel</label></fieldset>
<div class="t-countdown" id="t-countdown"><div class="chips-wahl" role="group" aria-label="Schnellwahl">
<button type="button" data-sek="30">30 s</button><button type="button" data-sek="60">1 min</button><button type="button" data-sek="120">2 min</button><button type="button" data-sek="180">3 min</button><button type="button" data-sek="300">5 min</button><button type="button" data-sek="600">10 min</button></div>
<div class="t-felder"><label>Minuten<input type="number" id="t-min" min="0" max="99" value="1" inputmode="numeric"></label><label>Sekunden<input type="number" id="t-sek" min="0" max="59" value="0" inputmode="numeric"></label></div></div>
<div class="t-intervall" id="t-intervall" hidden><div class="chips-wahl" role="group" aria-label="Vorlagen">
<button type="button" data-vorlage="20,10,1,8,0">Tabata 20/10 × 8</button><button type="button" data-vorlage="40,20,8,1,0">Zirkel 8 Stationen 40/20</button><button type="button" data-vorlage="30,30,6,2,60">6 Stationen × 2 Runden</button><button type="button" data-vorlage="45,15,10,1,0">10 Stationen 45/15</button></div>
<div class="t-felder"><label>Belastung (s)<input type="number" id="t-arbeit" min="5" max="600" value="40" inputmode="numeric"></label><label>Pause / Wechsel (s)<input type="number" id="t-pause" min="0" max="600" value="20" inputmode="numeric"></label>
<label>Stationen<input type="number" id="t-stationen" min="1" max="30" value="8" inputmode="numeric"></label><label>Runden<input type="number" id="t-runden" min="1" max="20" value="1" inputmode="numeric"></label>
<label>Pause zwischen Runden (s)<input type="number" id="t-rundenpause" min="0" max="900" value="60" inputmode="numeric"></label></div>
<p class="t-summe" id="t-summe"></p></div>
<label class="zustimmung"><input type="checkbox" id="t-ton" checked> <span>Signalton (3-2-1-Piepsen und Wechselsignal)</span></label>
</form>
</section>

<section class="werkzeug" id="teams" role="tabpanel" aria-labelledby="tab-teams">
<h2>Teams einteilen</h2>
<div class="raster zwei" style="align-items:start"><div>
<label class="feld" for="tm-namen">Namen – einer pro Zeile <small>(oder leer lassen und unten die Anzahl wählen)</small></label>
<textarea id="tm-namen" rows="8" placeholder="Anna&#10;Ben&#10;Can&#10;…"></textarea>
<div class="t-felder"><label>Personen (ohne Namen)<input type="number" id="tm-anzahl" min="2" max="80" value="24" inputmode="numeric"></label><label>Anzahl Teams<select id="tm-teams">{teams_opt}</select></label></div>
<label class="zustimmung"><input type="checkbox" id="tm-merken"> <span>Namen auf diesem Gerät merken (werden nirgends hochgeladen)</span></label>
<div class="knopfreihe"><button type="button" class="knopf primaer gross" id="tm-los">{ICON['zufall']} Teams bilden</button></div></div>
<div><div id="tm-ergebnis" class="teams-ergebnis" aria-live="polite"><p class="leer">Hier erscheinen die Teams – gleich groß, zufällig gemischt, mit Leibchenfarbe.</p></div></div></div>
</section>

<section class="werkzeug" id="punkte" role="tabpanel" aria-labelledby="tab-punkte">
<h2>Punkte zählen</h2>
<div class="knopfreihe" style="margin-bottom:14px"><label class="inline">Teams <select id="pk-anzahl"><option>2</option><option>3</option><option>4</option></select></label><button type="button" class="knopf" id="pk-reset">Alles auf 0</button></div>
<div class="punkte" id="pk-tafel"></div>
<p class="klein">Tipp: Teamnamen antippen und ändern. Der Spielstand bleibt erhalten, auch wenn du die Seite schließt.</p>
</section>

<section class="werkzeug" id="zufall" role="tabpanel" aria-labelledby="tab-zufall">
<h2>Zufall</h2>
<div class="raster zwei" style="align-items:stretch">
<div class="karte zufallskarte"><h3>Würfel</h3><p class="wuerfel" id="z-wuerfel" aria-live="polite">–</p><div class="knopfreihe"><button type="button" class="knopf primaer" id="z-wuerfeln">Würfeln</button><button type="button" class="knopf" id="z-muenze">Münze werfen</button></div></div>
<div class="karte zufallskarte"><h3>Zahl ziehen</h3><p class="wuerfel" id="z-zahl" aria-live="polite">–</p><div class="t-felder"><label>von<input type="number" id="z-von" value="1" inputmode="numeric"></label><label>bis<input type="number" id="z-bis" value="28" inputmode="numeric"></label></div><button type="button" class="knopf primaer" id="z-ziehen">Ziehen</button></div>
<div class="karte zufallskarte" style="grid-column:1/-1"><h3>Name ziehen <small>(ohne Wiederholung, aus der Namensliste bei „Teams“)</small></h3><p class="wuerfel klein-text" id="z-name" aria-live="polite">–</p><p class="klein" id="z-rest"></p><div class="knopfreihe"><button type="button" class="knopf primaer" id="z-name-los">Name ziehen</button><button type="button" class="knopf" id="z-name-neu">Neu starten</button></div></div>
</div>
</section>
</div></section>'''
    seite('werkzeuge/', 'Werkzeuge für die Halle: Zirkeltimer, Teams, Punkte, Zufall', 'Kostenlose Werkzeuge für den Sportunterricht: Intervall- und Zirkeltimer mit Signalton, faire Teameinteilung, Punktezähler und Zufallsauswahl – fürs Handy, ohne Anmeldung.',
          inhalt, aktiv='werkzeuge/', skripte=('werkzeuge.js',), voller_titel=True)


def merklisteseite():
    def inhalt(s):
        return f'''<section class="abschnitt eng keindruck"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Merkliste</li></ol></nav>
<p class="oberzeile">Deine Sammlung</p><h1>Merkliste</h1>
<p class="einleitung">Alle Spiele, die du mit {ICON['herz'].replace('<svg', '<svg width="20" height="20" style="vertical-align:-3px"')} gemerkt hast – gespeichert nur auf diesem Gerät. Drucke sie als Stationskarten mit QR-Code zum Video: Karte an die Station, Handy dran, Video läuft.</p>
<div id="merk-leer" class="hinweisbox"><h2 style="font-size:1.5rem">Noch nichts gemerkt</h2><p>Tippe bei einem Spiel auf „Merken“ – im <a href="{s.zu('spiele/')}">Spiele-Lexikon</a>, bei den Videos auf der Startseite oder im <a href="{s.zu('planer/')}">Stundenplaner</a>.</p></div>
<div id="merk-inhalt" hidden>
<div class="knopfreihe" style="margin:18px 0"><button type="button" class="knopf primaer gross" id="merk-drucken">{ICON['drucken']} Stationskarten drucken</button><button type="button" class="knopf gross" id="merk-leeren">Liste leeren</button></div>
<p class="klein">4 Karten pro A4-Seite, jede mit QR-Code zum Video. Im Druckfenster „Hintergrundgrafiken“ einschalten, dann sind die Farben dabei.</p>
<ul class="liste merk-liste" id="merk-liste"></ul></div>
</div></section>
<div id="karten-druck" class="nur-druck"></div>
<script type="application/json" id="spiele-daten">{spiele_daten()}</script>
<script type="application/json" id="seiten-basis">{basis_daten(s)}</script>'''
    seite('merkliste/', 'Merkliste', 'Deine gemerkten Spiele – als Stationskarten mit QR-Code zum Video druckbar.', inhalt, aktiv='merkliste/', skripte=('karten.js', 'merkliste.js'), noindex=True)


# ---------------------------------------------------------------- Spiel der Woche, Bewegte Pause, Raumplaner

WOCHE_START = date(2024, 1, 1)  # ein Montag – ab hier werden die Wochen gezählt (gleiche Rechnung in site.js)


def woche_liste():
    """Alle Spiele mit Anleitung, fest sortiert – das Spiel der Woche wechselt jeden Montag automatisch (ohne Neubau)."""
    l = sorted([x for x in SPIELE if x['a'] and x.get('spielzeit')], key=lambda x: x['v']['id'])
    return [{'i': x['v']['id'], 'n': x['name'], 's': x['slug'], 'st': x['stufe'], 'd': x['spielzeit'], 'p': x['phasen'],
             'lz': x['a'].get('lernziel', ''), 'f': x['farbe']} for x in l]


def woche_index(heute, n):
    wochen = (heute - WOCHE_START).days // 7
    return (wochen * 37) % n  # 37 ist teilerfremd zur Anzahl → jedes Spiel kommt dran, bevor sich etwas wiederholt


def spiel_der_woche(s):
    l = woche_liste()
    if not l:
        return ''
    g = l[woche_index(HEUTE, len(l))]
    kw = HEUTE.isocalendar()[1]
    return f'''<section class="abschnitt eng" id="spiel-der-woche"><div class="wrap">
<div class="woche" style="--wfarbe:{g['f']}" data-basis="{s.zu('spiele/')}" data-vorschau="{1 if VORSCHAU else 0}">
<div class="woche-video"><div class="video kompakt" data-video="{g['i']}" style="--vfarbe:{g['f']}"><button type="button" class="video-start" aria-label="Video „{esc(g['n'])}“ abspielen">{FELD}<span class="play">{ICON['play']}</span><b>Abspielen</b><small>Lädt von YouTube</small></button></div></div>
<div class="woche-text"><p class="oberzeile">Spiel der Woche · <span class="woche-kw">KW {kw}</span></p>
<h2 class="woche-name">{esc(g['n'])}</h2>
<div class="chips"><span class="chip woche-st">{g['st']}</span><span class="chip woche-d">{g['d'][0]}–{g['d'][1]} min</span><span class="chip woche-p">{', '.join(g['p'])}</span></div>
<p class="woche-lz">{esc(g['lz'])}</p>
<div class="knopfreihe"><a class="knopf primaer woche-link" href="{s.zu('spiele/' + g['s'] + '/')}">Zum Spiel</a>{merk_knopf(g['i'], g['n'], klein=True)}</div>
<p class="klein">Jeden Montag ein neues Spiel aus dem Kanal – mit Video und Lernziel.</p></div></div>
<script type="application/json" id="woche-daten">{json.dumps(l, ensure_ascii=False, separators=(',', ':'))}</script>
</div></section>'''


def pauseseite():
    def inhalt(s):
        ohne = [x for x in SPIELE if x['v'].get('ohneMaterial') or re.match(r'\s*(kein|ohne)', (x['a'] or {}).get('materialText') or '', re.I)]
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('werkzeuge/')}">Werkzeuge</a></li><li>Bewegte Pause</li></ol></nav>
<p class="oberzeile">Zwischendurch · ganz ohne Material</p><h1>Bewegte Pause</h1>
<p class="einleitung">Ein paar Minuten Bewegung, wenn die Konzentration weg ist: Du bekommst ein Spiel ganz ohne Material aus dem Kanal – mit Video und Timer. Für Turnsaal, Pausenhof oder ein freigeräumtes Klassenzimmer.</p>
<form class="planer-form pause-form" id="pause-form">
<label>Alter<select id="pa-stufe"><option value="1-4">Volksschule (1.–4.)</option><option value="5-8">Unterstufe (5.–8.)</option><option value="1-13" selected>alle</option></select></label>
<fieldset class="planer-material"><legend>Platz</legend><label><input type="checkbox" id="pa-eng" checked> wenig Platz <small>(keine Fang-, Lauf- und Turnspiele)</small></label></fieldset>
<fieldset class="planer-material"><legend>Dauer</legend>
<label><input type="radio" name="pa-min" value="3"> 3 min</label><label><input type="radio" name="pa-min" value="5" checked> 5 min</label><label><input type="radio" name="pa-min" value="10"> 10 min</label></fieldset>
<button class="knopf primaer gross" type="submit">{ICON['zufall']} Spiel ziehen</button>
</form>
<div id="pause-ergebnis" class="pause-ergebnis" aria-live="polite" hidden></div>
<div class="hinweisbox" style="margin-top:22px"><h2 style="font-size:1.4rem">Sicher in der Klasse</h2><p>Tische und Taschen aus dem Weg, Abstand zu Kanten und Fenstern, Tempo „gehen statt laufen“. Fang- und Laufspiele nur im Turnsaal oder im Freien.</p></div>
<noscript><p class="hinweisbox">Die Bewegte Pause braucht JavaScript. Alle Spiele ohne Material findest du im <a href="{s.zu('spiele/')}?ohne=1">Spiele-Lexikon</a>.</p></noscript>
</div></section>
<script type="application/json" id="spiele-daten">{spiele_daten({x['v']['id'] for x in ohne})}</script>
<script type="application/json" id="seiten-basis">{basis_daten(s)}</script>'''
    seite('bewegte-pause/', 'Bewegte Pause – Spiele ohne Material mit Timer', 'Bewegungspause für Schule und Turnsaal: ein Spiel ganz ohne Material mit Video und Timer – auf Knopfdruck, für Volksschule und Unterstufe.',
          inhalt, aktiv='werkzeuge/', skripte=('pause.js',), voller_titel=True)


def raumplanerseite():
    def inhalt(s):
        return f'''<section class="abschnitt eng keindruck"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li><a href="{s.zu('werkzeuge/')}">Werkzeuge</a></li><li>Raumplaner</li></ol></nav>
<div class="kopfzeile"><div><p class="oberzeile">Geräteaufbau planen · kostenlos</p><h1>Raumplaner für die Halle</h1>
<p class="einleitung">Zieh Geräte maßstabsgetreu in deine Halle, verschiebe und drehe sie – fertig ist der Aufbauplan für Stationen, Gerätelandschaft oder Zirkel. Die Materialliste zählt automatisch mit. Drucken, als Bild speichern oder als Link teilen.</p></div></div>
</div></section>
<section class="abschnitt eng raumplaner-bereich"><div class="wrap">
<div class="rp" id="rp">
<div class="rp-leiste keindruck" id="rp-leiste" role="toolbar" aria-label="Geräte – antippen oder in die Halle ziehen"></div>
<div class="rp-werkzeug keindruck">
<label class="inline">Halle <select id="rp-halle"><option value="2700x1500">Einzelhalle 27 × 15 m</option><option value="4400x2200">Zweifachhalle 44 × 22 m</option><option value="4500x2700">Dreifachhalle 45 × 27 m</option><option value="900x700">Klassenzimmer 9 × 7 m</option><option value="eigene">eigene Maße …</option></select></label>
<span class="rp-eigen" id="rp-eigen" hidden><label class="inline">Länge <input type="number" id="rp-l" min="4" max="80" step="0.5" value="27"> m</label><label class="inline">Breite <input type="number" id="rp-b" min="3" max="60" step="0.5" value="15"> m</label></span>
<label class="inline"><input type="checkbox" id="rp-linien" checked> Linien</label>
<label class="inline"><input type="checkbox" id="rp-raster"> Raster 1 m</label>
<label class="inline">Vorlage <select id="rp-vorlage"><option value="">– wählen –</option><option value="zirkel">Zirkel mit 8 Stationen</option><option value="geraete">Gerätelandschaft Turnen</option><option value="spiel">Zwei Spielfelder</option><option value="leer">Leere Halle</option></select></label>
</div>
<div class="rp-auswahl keindruck" id="rp-auswahl" hidden role="group" aria-label="Ausgewähltes Gerät">
<b id="rp-auswahl-name"></b>
<button type="button" class="knopf klein" data-aktion="drehen">⟳ Drehen</button>
<button type="button" class="knopf klein" data-aktion="kopie">⧉ Kopieren</button>
<button type="button" class="knopf klein" data-aktion="text" id="rp-text-knopf" hidden>✎ Text</button>
<button type="button" class="knopf klein" data-aktion="loeschen">✕ Entfernen</button>
</div>
<div class="rp-druckkopf" id="rp-druckkopf" aria-hidden="true"><h2 id="rp-druck-titel">Raumplan</h2><p id="rp-druck-notizen"></p></div>
<div class="rp-flaeche" id="rp-flaeche"><svg id="rp-svg" role="application" aria-label="Hallenplan. Gerät auswählen und mit den Pfeiltasten verschieben, R dreht, Entf löscht." xmlns="http://www.w3.org/2000/svg"></svg></div>
<p class="klein keindruck" id="rp-hilfe">Tipp: Gerät antippen oder in die Halle ziehen. Zum Löschen aus der Halle hinausziehen. Tastatur: Pfeiltasten verschieben, R dreht, Entf entfernt, Strg+Z macht rückgängig.</p>
<div class="knopfreihe keindruck"><button type="button" class="knopf" id="rp-zurueck" disabled>↶ Rückgängig</button><button type="button" class="knopf primaer" id="rp-drucken">{ICON['drucken']} Drucken</button><button type="button" class="knopf" id="rp-bild">{ICON['download']} Als Bild speichern</button><button type="button" class="knopf" id="rp-link">Link kopieren</button><button type="button" class="knopf" id="rp-neu">Alles leeren</button></div>
<p class="planer-meldung keindruck" id="rp-meldung" role="status" hidden></p>
<div class="rp-unten"><div class="rp-material"><h2>Materialliste</h2><ul id="rp-liste" class="rp-liste"><li class="leer">Noch keine Geräte in der Halle.</li></ul></div>
<div class="rp-notiz"><h2><label for="rp-titel">Titel &amp; Notizen</label></h2><input id="rp-titel" class="rp-titel" placeholder="z. B. 3b – Gerätelandschaft Springen" maxlength="80"><textarea id="rp-notizen" rows="4" placeholder="Aufbau-Teams, Sicherheit, Ablauf …"></textarea></div></div>
<p class="klein">Gerätemaße sind typische Richtwerte – miss im Zweifel in deiner Halle nach. Der Plan wird nur auf diesem Gerät gespeichert.</p>
</div>
<noscript><p class="hinweisbox">Der Raumplaner braucht JavaScript.</p></noscript>
</div></section>'''
    seite('raumplaner/', 'Raumplaner für den Turnsaal – Geräteaufbau planen', 'Kostenloser Raumplaner für den Sportunterricht: Geräte maßstabsgetreu in die Halle ziehen, drehen und anordnen – mit Materialliste, Druck und Link zum Teilen.',
          inhalt, aktiv='werkzeuge/', skripte=('raumplaner.js',), voller_titel=True)


def dankeseite():
    """Danke-Seite nach dem Kauf – in Digistore24 als „Danke-Seite“ (Thank-you-URL) eintragen."""
    def inhalt(s):
        kontakt = f'<a href="mailto:{E["email"]}">{esc(E["email"])}</a>' if E.get('email') else 'die E-Mail-Adresse im Impressum'
        return f'''<section class="abschnitt"><div class="wrap textseite">
<p class="oberzeile">Bestellung abgeschlossen</p><h1>Danke für deinen Kauf!</h1>
<p class="einleitung">Schön, dass du mit der Praxis-Reihe arbeitest. So geht es weiter:</p>
<ol class="haken" style="list-style:none">
<li>{ICON['check']}<span><b>Download:</b> Den Link zu deinen PDFs findest du auf der Bestätigungsseite von Digistore24 und in der E-Mail von Digistore24 – zusammen mit deiner Rechnung.</span></li>
<li>{ICON['check']}<span><b>Keine E-Mail da?</b> Schau bitte im Spam-Ordner nach. Wenn sie nach einer Stunde noch fehlt, schreib mir an {kontakt} – mit deiner Bestellnummer.</span></li>
<li>{ICON['check']}<span><b>Ausdrucken erlaubt:</b> für deinen eigenen Unterricht, so oft du willst.</span></li></ol>
<div class="raster drei" style="margin-top:26px">
<a class="karte link" href="{s.zu('planer/')}"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['planer']}</div><h3>Stunde planen</h3><p>Alle Spiele aus den Büchern stecken im Stundenplaner – mit Video und Stundenbild zum Drucken.</p></a>
<a class="karte link" href="{s.zu('raumplaner/')}"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['raum']}</div><h3>Raumplaner</h3><p>Den Geräteaufbau für deine Stationen planen und als Blatt ausdrucken.</p></a>
<a class="karte link" href="{s.zu('werkzeuge/')}"><div class="symbol" style="background:var(--rot-weich);color:var(--rot)">{ICON['timer']}</div><h3>Werkzeuge</h3><p>Zirkeltimer, Teams, Punkte und Zufall – fürs Handy in der Halle.</p></a></div>
</div></section>'''
    seite('danke/', 'Danke für deinen Kauf', 'Danke für deinen Kauf – so kommst du zu deinen E-Books.', inhalt, noindex=True)


def app_platzhalter():
    """Hinweisseite unter /app/, solange der App-Ordner nicht im Projekt liegt – kein toter Link."""
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap raster zwei" style="align-items:center">
<div><nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>App</li></ol></nav>
<p class="oberzeile">Die App</p><h1>Die Stunde in 10 Sekunden – bald hier</h1>
<p class="einleitung">Die App fürs Handy kommt bald. Das Wichtigste kannst du schon jetzt direkt hier nutzen: den Stundenplaner und die Werkzeuge für die Halle – kostenlos und ohne Anmeldung.</p>
<div class="knopfreihe"><a class="knopf primaer gross" href="{s.zu('planer/')}">{ICON['planer']} Stunde planen</a><a class="knopf gross" href="{s.zu('werkzeuge/')}">{ICON['timer']} Werkzeuge</a></div></div>
<div class="karte"><h2 style="font-size:1.6rem">Schon jetzt kostenlos</h2><ul class="haken">
<li>{ICON['check']}<span>{len(VIDEOS)} Spiele und Übungen mit Video, filterbar nach Schulstufe und Stundenteil</span></li>
<li>{ICON['check']}<span>Zirkeltimer, Teameinteilung, Punktezähler und Zufall</span></li>
<li>{ICON['check']}<span>Gratis-PDF „5 Spiele, die immer funktionieren“</span></li>
<li>{ICON['check']}<span>Leseproben aller E-Books</span></li></ul>
<a class="knopf" href="{s.zu('kostenlos/')}">Zu den Gratis-Inhalten</a></div>
</div></section>'''
    seite('app/', 'App – Stunde in 10 Sekunden planen', 'Die Sportunterricht-App stellt eine ganze Stunde passend zu Schulstufe, Dauer und Halle zusammen.', inhalt, aktiv='app/', noindex=True)


def kostenlosseite():
    def inhalt(s):
        proben = ''.join(f'<a class="karte link" href="{s.zu("downloads/leseprobe-" + b["slug"] + ".pdf")}" download style="display:grid;grid-template-columns:70px 1fr;gap:14px;align-items:center"><img src="{cover(s, b["slug"])}" alt="" width="70" height="99" loading="lazy" style="border-radius:4px;box-shadow:var(--schatten)"><span><b>Leseprobe Band {b["band"]}</b><br><small style="color:var(--tinte-3)">{esc(b["titel"])} · {BUECHER[b["slug"]]["probe_seiten"]} Seiten PDF</small></span></a>' for b in REIHE)
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Kostenlos</li></ol></nav>
<h1>Kostenlos für deinen Unterricht</h1><p class="einleitung">Alles hier ist gratis und ohne Konto nutzbar. Wenn es dir hilft, erzähl es im Lehrerzimmer weiter – dafür gibt es unten einen Aushang zum Ausdrucken.</p>
<div style="margin-top:30px">{newsletter_block(s)}</div></div></section>
<section class="abschnitt hell"><div class="wrap"><h2>Leseproben aller Bände</h2><p class="einleitung">Inhaltsverzeichnis, Einleitung und die ersten Einträge – so siehst du genau, was dich erwartet.</p><div class="raster drei">{proben}</div></div></section>
<section class="abschnitt"><div class="wrap raster drei">
<div class="karte"><div class="symbol" style="background:var(--gruen-weich);color:var(--gruen)">{ICON['handy']}</div><h3>Die App</h3><p>Stunden planen, Timer, Teams, Stundenmodus – kostenlos, mit drei kompletten Stunden pro Monat.</p><a class="knopf" href="{s.zu('app/')}">App öffnen</a></div>
<div class="karte"><div class="symbol" style="background:var(--blau-weich);color:var(--blau)">{ICON['video']}</div><h3>Spiele-Lexikon</h3><p>Alle {len(VIDEOS)} Videos mit Filter nach Schulstufe, Stundenteil und Material.</p><a class="knopf" href="{s.zu('spiele/')}">Spiele finden</a></div>
<div class="karte"><div class="symbol" style="background:var(--gelb-weich);color:var(--gelb)">{ICON['download']}</div><h3>Aushang fürs Lehrerzimmer</h3><p>Ein A4-Plakat mit QR-Code – für alle Kolleg:innen, die Ideen suchen.</p><a class="knopf" href="{s.zu('downloads/aushang-lehrerzimmer.pdf')}" download>Aushang herunterladen</a></div>
</div></section>'''
    seite('kostenlos/', 'Kostenlos: Gratis-PDF, Leseproben und App', 'Gratis-PDF „5 Spiele, die immer funktionieren“, Leseproben aller E-Books, die kostenlose App und ein Aushang fürs Lehrerzimmer.', inhalt, og='og-kostenlos.png')


def schulenseite():
    mail = E.get('email')

    def anfrage(betreff):
        if not mail:
            WARNUNGEN.append('E-Mail fehlt (email) – Anfrage-Knöpfe auf „Für Schulen“ zeigen aufs Impressum.')
            return None
        body = ('Liebe:r DJ,\n\nwir interessieren uns für die Schullizenz.\n\nSchule: \nAnzahl Sportlehrkräfte: \nGewünscht: E-Books / E-Books + App Pro / Workshop\n'
                'Rechnungsadresse: \nAnsprechperson: \n\nViele Grüße')
        from urllib.parse import quote
        return f'mailto:{mail}?subject={quote(betreff)}&body={quote(body)}'

    def inhalt(s):
        link = anfrage('Anfrage Schullizenz Sportunterricht') or s.zu('impressum/')
        karten = [
            ('Schullizenz E-Books', E['schullizenz_preis'], 'einmalig', [f'Alle {N_BAENDE} Bände + Jahresplaner', 'für alle Sportlehrkräfte einer Schule', 'Ablage auf Schulserver oder Schul-Cloud (intern) erlaubt', 'Rechnung an die Schule']),
            ('E-Books + App Pro', E['schullizenz_pro_preis'], 'pro Schuljahr', ['alles aus der Schullizenz E-Books', 'App Pro für bis zu 15 Lehrkräfte', 'neue Bände während der Laufzeit inklusive', 'Rechnung an die Schule']),
            ('Workshop fürs Team', 'auf Anfrage', 'SCHILF / Fachgruppe', ['kreative & kooperative Spiele in der Praxis', 'sicher Turnen unterrichten: Hilfestellung & Stationen', 'vor Ort in Wien oder online', 'inkl. Schullizenz E-Books']),
        ]
        k = ''
        for i, (t, p, z, pkt) in enumerate(karten):
            li = ''.join(f'<li style="display:flex;gap:8px">{ICON["check"].replace("<svg", "<svg width=18 height=18 style=flex:none;margin-top:4px;color:var(--gruen)")}<span>{esc(x)}</span></li>' for x in pkt)
            k += f'<div class="tarif{" empfohlen" if i == 1 else ""}"><h3>{t}</h3><span class="preis">{p}</span><p>{z}</p><ul style="list-style:none;padding:0;margin:0 0 12px;display:grid;gap:6px">{li}</ul><a class="knopf {"pro" if i == 1 else "primaer"}" href="{link}">Angebot anfordern</a></div>'
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Für Schulen</li></ol></nav>
<p class="oberzeile">Für Schulen und Fachgruppen</p><h1>Die ganze Praxis-Reihe für euer Sport-Team</h1>
<p class="einleitung">Eine Lizenz, alle Kolleg:innen: Die E-Books dürfen intern auf dem Schulserver liegen, und jede Lehrkraft kann sie für den eigenen Unterricht nutzen und ausdrucken. Bezahlt wird bequem auf Rechnung.</p>
<h2 class="sr-only">Angebote</h2><div class="tarife" style="margin-top:26px">{k}</div>
<p style="color:var(--tinte-3);margin-top:12px">Preise inkl. USt. „Angebot anfordern“ öffnet eine vorbereitete E-Mail – du bekommst ein Angebot mit Rechnung für die Schule.</p>
</div></section>
<section class="abschnitt hell"><div class="wrap raster zwei" style="align-items:center">
<div><h2>Aushang fürs Lehrerzimmer</h2><p class="einleitung">Ein A4-Plakat mit QR-Code zum Spiele-Lexikon, zur App und zum Gratis-PDF. Ausdrucken, aufhängen – die Kolleg:innen werden es dir danken.</p><a class="knopf primaer gross" href="{s.zu('downloads/aushang-lehrerzimmer.pdf')}" download>{ICON['download']} Aushang (PDF)</a></div>
<div class="karte"><h3>Warum eine Schullizenz?</h3><ul class="haken"><li>{ICON['check']}<span>Einheitliche Ideen und Standards im ganzen Team – gut für Fachgruppen-Absprachen und Jahresplanung</span></li><li>{ICON['check']}<span>Junglehrer:innen und Studierende im Praktikum haben sofort bewährtes Material</span></li><li>{ICON['check']}<span>Rechtssicher: Weitergabe im Kollegium ausdrücklich erlaubt</span></li></ul></div>
</div></section>'''
    seite('schulen/', 'Schullizenz für den Sportunterricht – E-Books für die ganze Fachgruppe', 'Schullizenz für die Praxis-Reihe: alle E-Books für alle Sportlehrkräfte einer Schule, optional mit App Pro und Workshop. Rechnung an die Schule.', inhalt, aktiv='schulen/', og='og-schulen.png', voller_titel=True)


def ueberseite():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Über mich</li></ol></nav>
<div class="autor"><div class="autor-bild" aria-hidden="true">DJ</div><div><p class="oberzeile">Über mich</p><h1>Hallo, ich bin DJ.</h1>
<p class="einleitung">Ich unterrichte Bewegung und Sport an einer AHS in Wien, leite regelmäßig Wintersportwochen und halte an der Universität Wien Lehrveranstaltungen für angehende Sportlehrer:innen – unter anderem die Unterrichtspraktischen Studien.</p></div></div>
<div class="textseite" style="margin-top:30px">
<h2>Warum es diesen Kanal gibt</h2>
<p>In den ersten Jahren habe ich viel Zeit damit verbracht, Spiele zu suchen, die wirklich funktionieren: nicht nur auf dem Papier, sondern mit 28 Kindern in einer halben Halle, nach der großen Pause, mit dem Material, das eben da ist. Seit {kanal_seit()} zeige ich auf YouTube genau solche Spiele – gefilmt im echten Unterricht, kurz erklärt, sofort nachmachbar. Inzwischen sind es über {len(VIDEOS) // 10 * 10} Videos mit {mio(sum(v["aufrufe"] for v in VIDEOS))} Aufrufen und rund {esc(E["abonnenten"])} Abonnent:innen.</p>
<h2>Was mir wichtig ist</h2>
<ul class="haken"><li>{ICON['check']}<span><b>Bewegungszeit vor Erklärzeit.</b> Ein gutes Spiel ist in einer Minute erklärt. Deshalb gibt es zu jedem Spiel einen Ansagetext zum Vorlesen.</span></li>
<li>{ICON['check']}<span><b>Alle machen mit.</b> Möglichst kein Ausscheiden, keine langen Wartezeiten, Varianten für Schwächere und Stärkere.</span></li>
<li>{ICON['check']}<span><b>Sicherheit ist kein Kleingedrucktes.</b> Jede Übung mit Sicherheitshinweis, jede Turnübung mit Hilfestellung und typischen Fehlern.</span></li>
<li>{ICON['check']}<span><b>Echte Daten statt Bauchgefühl.</b> Die Spielesammlung besteht aus den Spielen, die sich Kolleg:innen am häufigsten angesehen haben.</span></li>
<li>{ICON['check']}<span><b>Datensparsam.</b> Die App braucht kein Konto, und diese Website kommt ohne Tracking und Werbe-Cookies aus.</span></li></ul>
<h2>Die Praxis-Reihe</h2>
<p>Aus den beliebtesten Videos und meinen Unterlagen aus Schule und Universität ist die <a href="{s.zu('ebooks/')}">Praxis-Reihe</a> entstanden: {BAENDE_WORT} E-Books, die du ausdrucken und in die Halle mitnehmen kannst – vom Spiel für morgen bis zum Umgang mit Angst, Konflikten und Sportverweigerung. Und weil die Planung oft am Vorabend am Handy passiert, gibt es die <a href="{s.zu('app/')}">App</a>, die eine ganze Stunde in Sekunden zusammenstellt.</p>
<h2>Kontakt</h2>
<p>{f'Schreib mir an <a href="mailto:{E["email"]}">{E["email"]}</a> – ich freue mich über Rückmeldungen, Spielideen und Anfragen für Workshops.' if E.get('email') else 'Kontaktdaten findest du im <a href="' + s.zu('impressum/') + '">Impressum</a>.'} Neue Videos gibt es auf <a href="{E['youtube']}" rel="noopener">YouTube</a>.</p>
</div></div></section>'''
    seite('ueber/', 'Über mich – DJ, Sportlehrer in Wien', 'DJ unterrichtet Bewegung und Sport an einer AHS in Wien, bildet an der Universität Wien Sportlehrer:innen aus und zeigt auf YouTube Spiele aus dem echten Unterricht.', inhalt, aktiv='ueber/')


def faqseite():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap" style="max-width:860px">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Häufige Fragen</li></ol></nav>
<h1>Häufige Fragen</h1><p class="einleitung">Zu E-Books, App, Bezahlung und Datenschutz. Deine Frage ist nicht dabei? {f'Schreib mir an <a href="mailto:{E["email"]}">{E["email"]}</a>.' if E.get('email') else ''}</p>
{faq_html(faq_liste(s))}</div></section>'''
    seite('faq/', 'Häufige Fragen', 'Antworten zu E-Books, App Pro, Bezahlung über Digistore24, Schullizenz, Werbung in Videos und Datenschutz.', inhalt, schema=[faq_schema(faq_liste(Seite('faq/')))])


# ---------------------------------------------------------------- Rechtliches (Vorlagen – bitte prüfen lassen)

def ph(wert, platzhalter):
    if wert:
        return esc(wert)
    return f'<span class="platzhalter">{esc(platzhalter)}</span>'


def vorlage_hinweis():
    fehlt = [k for k in ('name_voll', 'anschrift', 'email') if not E.get(k)]
    if fehlt:
        WARNUNGEN.append(f'Impressum unvollständig: {", ".join(fehlt)} in einstellungen.json eintragen.')
        return '<div class="vorlage-hinweis"><b>Vorlage – noch nicht vollständig.</b> Gelb markierte Stellen in <code>einstellungen.json</code> ausfüllen und die Texte vor dem Livegang von einer Fachperson (z. B. WKO-Gründerservice oder Rechtsberatung) prüfen lassen.</div>'
    return ''


def rechtsseiten():
    name = ph(E.get('name_voll'), 'Vor- und Nachname')
    anschrift = ph(E.get('anschrift'), 'Straße Nr., PLZ Ort, Österreich')
    mail = f'<a href="mailto:{E["email"]}">{esc(E["email"])}</a>' if E.get('email') else ph('', 'E-Mail-Adresse')

    def impressum(s):
        return f'''<section class="abschnitt"><div class="wrap textseite">{vorlage_hinweis()}
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 E-Commerce-Gesetz und § 25 Mediengesetz</h2>
<p><b>Medieninhaber und Diensteanbieter:</b><br>{name}<br>{anschrift}</p>
<p><b>Kontakt:</b> {mail}</p>
<p><b>Unternehmensgegenstand:</b> {esc(E.get('unternehmensgegenstand', ''))}</p>
{f'<p><b>UID-Nummer:</b> {esc(E["uid"])}</p>' if E.get('uid') else ''}
<p><b>Grundlegende Richtung (Blattlinie):</b> Information, Unterrichtsideen und Unterrichtsmaterialien rund um Bewegung und Sport in der Schule.</p>
<h2>Verkauf</h2>
<p>Die E-Books und App-Lizenzen werden über <b>Digistore24 GmbH</b>, St.-Godehard-Straße 32, 31139 Hildesheim, Deutschland, als Wiederverkäufer vertrieben. Digistore24 ist Vertragspartner beim Kauf und für Zahlung, Rechnung und Umsatzsteuer zuständig.</p>
<h2>Haftung</h2>
<p>Die Spiele und Übungen wurden im Schulunterricht erprobt. Sie ersetzen nicht die Einschätzung der Lehrkraft vor Ort; beachte die geltenden Sicherheitsbestimmungen für den Schulsport und deine Aufsichtspflicht. Für Inhalte verlinkter externer Seiten sind ausschließlich deren Betreiber verantwortlich.</p>
<h2>Urheberrecht</h2>
<p>Texte, Videos, Grafiken und E-Books sind urheberrechtlich geschützt. Jede Verwertung außerhalb der gekauften Lizenz braucht eine schriftliche Zustimmung.</p>
</div></section>'''

    def datenschutz(s):
        app_datenschutz = '''<h2>Die App</h2><p>Die App speichert alles – Klassen, Stunden, Merkliste, Namenslisten – ausschließlich lokal auf deinem Gerät (Local Storage). Es gibt kein Konto und keinen Server, auf dem diese Daten landen. Beim Freischalten von Pro werden Bestellnummer und Lizenzschlüssel an unsere Prüffunktion und von dort an Digistore24 übermittelt, um die Lizenz zu prüfen; wir speichern sie nicht. Rückmeldungen („Passt etwas nicht?“) verschickst du selbst per E-Mail oder kopierst sie.</p>''' if APP_DA else ''
        nl = ''
        if E.get('newsletter_formular_url'):
            nl = '''<h2>Newsletter</h2><p>Wenn du dich für den Newsletter anmeldest, verarbeiten wir deine E-Mail-Adresse auf Grundlage deiner Einwilligung (Art. 6 Abs. 1 lit. a DSGVO), um dir das Gratis-PDF und etwa monatlich neue Ideen zu schicken. Die Anmeldung erfolgt im Double-Opt-in-Verfahren. Der Versand läuft über unseren Newsletter-Dienstleister als Auftragsverarbeiter <span class="platzhalter">Name und Sitz des Anbieters eintragen</span>. Du kannst dich jederzeit über den Link in jeder E-Mail abmelden; dann wird deine Adresse gelöscht.</p>'''
        return f'''<section class="abschnitt"><div class="wrap textseite">{vorlage_hinweis()}
<h1>Datenschutzerklärung</h1>
<p>Kurz gesagt: Diese Website verwendet <b>keine Cookies, kein Tracking und keine Werbung</b>. Schriften werden von dieser Website selbst geladen, nicht von Google.</p>
<h2>Verantwortlicher</h2><p>{name}, {anschrift}, {mail}</p>
<h2>Hosting</h2><p>Die Website wird bei <b>Netlify, Inc.</b> (San Francisco, USA) gehostet. Beim Aufruf verarbeitet der Server technisch notwendige Daten (IP-Adresse, Zeitpunkt, aufgerufene Seite, Browser), um die Seite auszuliefern und vor Missbrauch zu schützen – Rechtsgrundlage ist unser berechtigtes Interesse an einem sicheren Betrieb (Art. 6 Abs. 1 lit. f DSGVO). Die Übermittlung in die USA stützt sich auf <span class="platzhalter">EU-US Data Privacy Framework bzw. Standardvertragsklauseln – beim Einrichten im Netlify-Konto prüfen</span>.</p>
<h2>YouTube-Videos (Zwei-Klick-Lösung)</h2><p>Videos werden erst geladen, wenn du auf „Video ansehen“ klickst. Erst dann wird eine Verbindung zu YouTube (Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland) über die Domain youtube-nocookie.com aufgebaut; dabei gelten die Datenschutzbestimmungen von Google. Rechtsgrundlage ist deine Einwilligung durch den Klick (Art. 6 Abs. 1 lit. a DSGVO).</p>
<h2>Kauf über Digistore24</h2><p>Wenn du ein E-Book oder App Pro kaufst, wirst du zu Digistore24 weitergeleitet. Digistore24 verarbeitet als Vertragspartner die für den Kauf nötigen Daten (Art. 6 Abs. 1 lit. b DSGVO) nach seiner eigenen Datenschutzerklärung. Wir erhalten die für die Auslieferung und Buchhaltung nötigen Bestelldaten.</p>
{app_datenschutz}
{nl}
<h2>Kontakt per E-Mail</h2><p>Wenn du uns schreibst, verarbeiten wir deine Angaben, um deine Anfrage zu beantworten (Art. 6 Abs. 1 lit. b bzw. f DSGVO), und löschen sie, wenn sie nicht mehr gebraucht werden.</p>
<h2>Deine Rechte</h2><p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch sowie das Recht, eine Einwilligung jederzeit zu widerrufen. Beschweren kannst du dich bei der österreichischen Datenschutzbehörde (www.dsb.gv.at).</p>
<p style="color:var(--tinte-3)">Stand: {HEUTE.strftime('%m/%Y')}</p>
</div></section>'''

    def agb(s):
        app_agb = '''<h2>3. App Pro</h2><p>App Pro gibt es als Monats- oder Jahresabo sowie als Praktikums-Pass (Einmalzahlung, 6 Monate). Abos verlängern sich automatisch und sind jederzeit zum Ende des bezahlten Zeitraums über den Link in der Kaufbestätigung kündbar. Die Freischaltung erfolgt mit Bestellnummer und Lizenzschlüssel auf deinen eigenen Geräten.</p>
''' if APP_DA else ''
        n = 3 if APP_DA else 2
        return f'''<section class="abschnitt"><div class="wrap textseite">{vorlage_hinweis()}
<h1>AGB, Nutzungsbedingungen & Widerruf</h1>
<h2>1. Vertragspartner beim Kauf</h2><p>Alle Käufe (E-Books, App Pro, Komplettpaket) werden über <b>Digistore24 GmbH</b>, St.-Godehard-Straße 32, 31139 Hildesheim, Deutschland, abgewickelt. Digistore24 ist Wiederverkäufer und dein Vertragspartner; für den Kaufvertrag gelten die AGB von Digistore24, die dir im Bestellvorgang angezeigt werden.</p>
<h2>2. Nutzungsrechte an den E-Books</h2><ul>
<li><b>Einzellizenz:</b> Du darfst das E-Book für deinen eigenen Unterricht und deine Vorbereitung nutzen, auf deinen Geräten speichern und für den eigenen Gebrauch ausdrucken.</li>
<li>Nicht erlaubt sind Weitergabe, Veröffentlichung, Weiterverkauf und das Hochladen auf öffentlich zugängliche Plattformen – auch nicht in Auszügen.</li>
<li><b>Schullizenz:</b> Alle Lehrkräfte der lizenzierten Schule dürfen die E-Books für ihren Unterricht nutzen; die Ablage auf einem internen, zugangsgeschützten Schulserver oder in der Schul-Cloud ist erlaubt.</li></ul>
{app_agb}<h2>{n + 1}. Widerrufsrecht bei digitalen Inhalten</h2><p>Verbraucher:innen haben grundsätzlich ein 14-tägiges Widerrufsrecht. Bei digitalen Inhalten, die nicht auf einem körperlichen Datenträger geliefert werden, erlischt es, wenn du ausdrücklich zustimmst, dass die Lieferung vor Ablauf der Widerrufsfrist beginnt, und bestätigst, dass du dadurch dein Widerrufsrecht verlierst. Diese Zustimmung holt Digistore24 im Bestellvorgang ein. Schau dir deshalb vorher gern die kostenlosen Leseproben an.</p>
<h2>{n + 2}. Sicherheit im Unterricht</h2><p>Die Inhalte sind im Schulunterricht erprobte Anregungen. Die Verantwortung für Organisation, Sicherheit und Aufsicht in der konkreten Stunde bleibt bei der unterrichtenden Lehrkraft. Für Unfälle oder Schäden bei der Durchführung wird – soweit gesetzlich zulässig – keine Haftung übernommen.</p>
<h2>{n + 3}. Kontakt</h2><p>{name}, {anschrift}, {mail}</p>
</div></section>'''
    seite('impressum/', 'Impressum', 'Impressum und Offenlegung gemäß E-Commerce-Gesetz und Mediengesetz.', impressum, noindex=not E.get('name_voll'))
    seite('datenschutz/', 'Datenschutzerklärung', 'Keine Cookies, kein Tracking: So geht diese Website mit deinen Daten um.', datenschutz)
    seite('agb/', 'AGB, Nutzungsbedingungen & Widerruf', 'Nutzungsrechte an den E-Books, App Pro und Widerrufsrecht bei digitalen Inhalten.', agb)


def nicht_gefunden():
    def inhalt(s):
        return f'''<section class="abschnitt"><div class="wrap nichtgefunden"><div>
<p class="gross">404</p><h1>Hier ist Aus.</h1><p class="einleitung">Diese Seite gibt es nicht (mehr). Vielleicht hilft einer dieser Wege weiter:</p>
<div class="knopfreihe" style="justify-content:center"><a class="knopf primaer" href="/">Zur Startseite</a><a class="knopf" href="/spiele/">Spiele-Lexikon</a><a class="knopf" href="/ebooks/">E-Books</a><a class="knopf" href="/app/">App</a></div></div></div></section>'''
    seite('404.html', 'Seite nicht gefunden', 'Diese Seite gibt es nicht.', inhalt, noindex=True)
    # 404 liegt im Wurzelordner, wird aber unter beliebigen Pfaden ausgeliefert → absolute Pfade verwenden
    p = OUT / '404.html'
    t = p.read_text()
    for alt in ('href="assets/', 'src="assets/', 'href="spiele/', 'href="ebooks/', 'href="app/', 'href="schulen/', 'href="ueber/', 'href="kostenlos/',
                'href="pro/', 'href="faq/', 'href="impressum/', 'href="datenschutz/', 'href="agb/', 'href="./"'):
        t = t.replace(alt, alt.replace('="', '="/').replace('/./', '/'))
    p.write_text(t)


def meta_dateien():
    heute = HEUTE.isoformat()
    if DOMAIN:
        urls = ''.join(f'<url><loc>{url_abs(p) if p else DOMAIN + "/"}</loc><lastmod>{heute}</lastmod></url>' for p in SITEMAP)
        (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
        (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')
    else:
        WARNUNGEN.append('Domain fehlt (domain) – keine sitemap.xml, keine kanonischen URLs. Nach dem Eintragen neu bauen.')
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
    (OUT / 'netlify.toml').write_text('''# Netlify-Einstellungen (werden automatisch gelesen)
[build]
  publish = "."
  functions = "netlify/functions"

[[headers]]
  for = "/*"
  [headers.values]
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
    X-Frame-Options = "SAMEORIGIN"
    Permissions-Policy = "camera=(), microphone=(), geolocation=(), interest-cohort=()"

[[headers]]
  for = "/assets/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"

[[headers]]
  for = "/assets/fonts/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"

[[headers]]
  for = "/app/sw.js"
  [headers.values]
    Cache-Control = "no-cache"

[[headers]]
  for = "/downloads/*"
  [headers.values]
    Cache-Control = "public, max-age=86400"
''')


# ---------------------------------------------------------------- Verkaufsdateien & YouTube-Links (nicht Teil der Website)

def verkaufsdateien():
    """Dateien zum Hochladen bei Digistore24 – liegen bewusst NICHT im öffentlichen Website-Ordner."""
    import zipfile
    ziel = HIER / 'verkauf'
    if ziel.exists():
        shutil.rmtree(ziel)
    (ziel / 'einzeln').mkdir(parents=True)
    for b in REIHE:
        shutil.copy(PDFS / f'{b["slug"]}.pdf', ziel / 'einzeln' / f'Band{b["band"]}-{b["slug"]}.pdf')
    liesmich = (f'Sportunterricht – Die Praxis-Reihe\n\nDanke für deinen Kauf! Enthalten:\n'
                + ''.join(f'  Band {b["band"]}: {b["titel"]}\n' for b in REIHE)
                + '  Bonus: Jahresplaner Bewegung und Sport\n\nEinzellizenz: für deinen eigenen Unterricht, ausdrucken erlaubt, Weitergabe nicht.\n'
                + 'Für das ganze Kollegium gibt es die Schullizenz.\n')
    for name, text in [('Komplettpaket-Sportunterricht.zip', liesmich),
                       ('Schullizenz-Sportunterricht.zip', liesmich.replace('Einzellizenz: für deinen eigenen Unterricht, ausdrucken erlaubt, Weitergabe nicht.\nFür das ganze Kollegium gibt es die Schullizenz.\n',
                        'SCHULLIZENZ: Alle Lehrkräfte der lizenzierten Schule dürfen die PDFs für ihren Unterricht nutzen und ausdrucken.\nAblage auf einem internen, zugangsgeschützten Schulserver bzw. in der Schul-Cloud ist erlaubt; öffentliche Weitergabe nicht.\nLizenziert für (Schule): ______________________________\n'))]:
        with zipfile.ZipFile(ziel / name, 'w', zipfile.ZIP_DEFLATED) as z:
            for b in REIHE:
                z.write(PDFS / f'{b["slug"]}.pdf', f'Band{b["band"]}-{b["slug"]}.pdf')
            z.write(PDFS / 'jahresplaner.pdf', 'Bonus-Jahresplaner.pdf')
            if name.startswith('Schullizenz'):  # Komplettpaket: nur PDFs – Bedingung für den ermäßigten E-Book-Steuersatz bei Digistore24
                z.writestr('LIESMICH.txt', text)
    print(f'✓ Verkaufsdateien → {ziel}')


def youtube_links():
    """Tabelle mit Textbausteinen für die Videobeschreibungen – der größte Hebel für Besucher auf der Website."""
    import csv
    basis = DOMAIN or 'https://DEINE-DOMAIN.at'
    with open(HIER / 'youtube-beschreibungen.csv', 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Video_ID', 'Titel', 'Aufrufe', 'Link zur Spielseite', 'Textbaustein für die Videobeschreibung (ganz oben einfügen)', 'Angepinnter Kommentar'])
        for x in SPIELE:
            url = f'{basis}/spiele/{x["slug"]}/'
            if x['a']:
                b = BAND[x['buch']]
                text = f'Anleitung mit Ansagetext, Varianten und Sicherheitshinweis: {url}\nIm E-Book „{b["titel"]}“ ({b["preis"]}): {basis}/ebooks/{b["slug"]}/\nStunde in 10 Sekunden planen (kostenlose App): {basis}/app/'
                kommentar = f'Die ganze Anleitung zum Ausdrucken findest du hier: {url}'
            else:
                text = f'Mehr als {len(VIDEOS) // 10 * 10} Spiele mit Filter nach Schulstufe: {basis}/spiele/\nStunde in 10 Sekunden planen (kostenlose App): {basis}/app/\nGratis-PDF „5 Spiele, die immer funktionieren“: {basis}/kostenlos/'
                kommentar = f'Passende Spiele für deine Stunde findest du hier: {url}'
            w.writerow([x['v']['id'], x['v']['titel'], x['v']['aufrufe'], url, text, kommentar])
    print(f'✓ YouTube-Textbausteine → {HIER / "youtube-beschreibungen.csv"}')


# ---------------------------------------------------------------- Los geht's

def main():
    kopiere_dateien()
    og_bilder()
    aushang()
    startseite()
    ebooks_index()
    produktseiten()
    komplettseite()
    if APP_DA:
        proseite()
    else:
        app_platzhalter()
        WARNUNGEN.append('App-Ordner sportunterricht-app-v2 fehlt – unter /app/ steht eine Hinweisseite, /pro/ wird nicht gebaut.')
    kostenlosseite()
    planerseite()
    werkzeugeseite()
    merklisteseite()
    pauseseite()
    raumplanerseite()
    dankeseite()
    qr_codes()
    schulenseite()
    ueberseite()
    faqseite()
    rechtsseiten()
    lexikon_index()
    lexikon_seiten()
    nicht_gefunden()
    meta_dateien()
    if not VORSCHAU:
        verkaufsdateien()
        youtube_links()
    for f in HIER.glob('.tmp-*'):
        f.unlink()
    if ARTIFACT:  # Startseite ohne eigenes Dokumentgerüst (claude.ai ergänzt es beim Veröffentlichen)
        p = OUT / 'index.html'
        t = p.read_text()
        for tag in ('<!doctype html>', '<html lang="de-AT">', '<head>', '</head>', '<body>', '</body>', '</html>'):
            t = t.replace(tag, '')
        t = re.sub(r'<title>.*?</title>', '<title>Sportunterricht Website</title>', t, count=1)
        p.write_text(t.strip() + '\n')
    seiten = len(list(OUT.rglob('index.html')))
    groesse = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file()) / 1e6
    print(f'✓ Website gebaut: {seiten} Seiten, {groesse:.1f} MB → {OUT}')
    for w in dict.fromkeys(WARNUNGEN):
        print('  ⚠', w)


if __name__ == '__main__':
    main()
