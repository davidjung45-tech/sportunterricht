"""Gemeinsames Werkzeug für alle E-Books: Markdown lesen/schreiben im einheitlichen Format
(siehe ../FORMAT.md) und Einträge mit den Stammdaten aus der Excel-Datei abgleichen."""
import re

META = ['Altersstufe', 'Gruppengröße', 'Material', 'Dauer', 'Video-Demo', 'Stundenteil', 'Intensität', 'Lernziel']
ABSCHNITTE = ['Spielbeschreibung', 'Zielbewegung', 'Methodische Reihe', 'Hilfestellung', 'Typische Fehler',
              'So erklärst du es', 'Variationen/Differenzierung', 'Sicherheitshinweis']


def video_id(link):
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})', link or '')
    return m.group(1) if m else None


def parse_eintrag(block):
    """block beginnt mit '### N. Titel'"""
    kopf = re.match(r'### (\d+)\. (.+)', block)
    nr, name = int(kopf.group(1)), kopf.group(2).strip()
    meta = {}
    for k in META:
        m = re.search(rf'^\*\*{re.escape(k)}:\*\*[ \t]*(.*)$', block, re.M)
        if m:
            meta[k] = m.group(1).strip()
    abschnitte = []
    # Abschnitte: **Label:** am Zeilenende, Inhalt bis zum nächsten **Label:** oder Blockende
    teile = re.split(r'^\*\*([^*\n]+):\*\*[ \t]*$', block, flags=re.M)
    for i in range(1, len(teile), 2):
        label = teile[i].strip()
        text = teile[i + 1].strip()
        text = re.sub(r'\n-{3,}\s*$', '', text).strip()
        if label in META:
            continue
        abschnitte.append((label, text))
    return {'nr': nr, 'name': name, 'meta': meta, 'abschnitte': abschnitte, 'id': video_id(meta.get('Video-Demo'))}


def parse(md):
    """Zerlegt ein Buch in Titel, Einleitung und Kapitel. Kapitel enthalten Einträge und/oder freien Text."""
    titel = re.search(r'^# (.+)$', md, re.M).group(1).strip()
    rest = md.split('\n', 1)[1] if md.startswith('# ') else md[md.index('\n# ') + 1:].split('\n', 1)[1]
    teile = re.split(r'^(## .+)$', rest, flags=re.M)
    buch = {'titel': titel, 'einleitung': teile[0].strip(), 'kapitel': []}
    for i in range(1, len(teile), 2):
        kopf = teile[i][3:].strip()
        inhalt = teile[i + 1]
        bloecke = re.split(r'^(?=### \d+\. )', inhalt, flags=re.M)
        einleitung = bloecke[0].strip().strip('-').strip()
        eintraege = [parse_eintrag(b) for b in bloecke[1:] if b.strip()]
        buch['kapitel'].append({'titel': kopf, 'text': einleitung, 'eintraege': eintraege})
    return buch


def render_eintrag(e):
    z = [f"### {e['nr']}. {e['name']}", '']
    for k in META:
        if e['meta'].get(k):
            z.append(f"**{k}:** {e['meta'][k]}")
    z.append('')
    for label, text in e['abschnitte']:
        if not text:
            continue
        z += [f'**{label}:**', text, '']
    z += ['---', '']
    return '\n'.join(z)


def render(buch):
    z = [f"# {buch['titel']}", '', buch['einleitung'], '']
    for k in buch['kapitel']:
        z += [f"## {k['titel']}", '']
        if k['text']:
            z += [k['text'], '']
        for e in k['eintraege']:
            z.append(render_eintrag(e))
    return '\n'.join(z).rstrip() + '\n'


def alle_eintraege(buch):
    return [e for k in buch['kapitel'] for e in k['eintraege']]


def stufen_text(von, bis):
    return f'{von}.–{bis}. Schulstufe' if von != bis else f'{von}. Schulstufe'
