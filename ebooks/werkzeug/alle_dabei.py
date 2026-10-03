"""Band 6 „Alle dabei, alle sicher“ – Handbuch-Band mit Fließtext, Kästen, Spiel-Verweisen und Kopiervorlagen.

Quelle: ebooks/alle-dabei/einleitung.md und kapitel-1.md … kapitel-6.md (Format siehe _brief.md).
Wird von pdf.py aufgerufen (main), nutzt dessen Bausteine (Cover, Impressum, Reihe-Seite, QR).
"""
import html
import importlib
import re
import sys

import markdown

_m = sys.modules.get('__main__')
P = _m if hasattr(_m, 'karte') else importlib.import_module('pdf')

ORDNER = P.EBOOKS / 'alle-dabei'

ZAHL = {6: 'sechs', 7: 'sieben', 8: 'acht', 9: 'neun', 10: 'zehn'}
KASTEN = {'So sagst du es': 'k-ansage', 'Praxistipp': 'k-tipp', 'Achtung': 'k-achtung', 'Aus meiner Praxis': 'k-praxis'}

CSS = """
.hb p, .hb li, .einl p, .einl li { font-size: 9.3pt; line-height: 1.46; }
.hb p { margin: 0 0 2.2mm; orphans: 3; widows: 3; }
.hb h3 { font-size: 15pt; color: var(--f); margin: 6mm 0 2mm; page-break-after: avoid; }
.hb h4 { font-size: 11.5pt; margin: 4.5mm 0 1.5mm; page-break-after: avoid; }
.hb h3 + h4 { margin-top: 1mm; }
.hb ul, .hb ol { margin-bottom: 2.4mm; }
.hb table { font-size: 8.6pt; page-break-inside: auto; }
.hb td { line-height: 1.35; }
blockquote { margin: 3mm 0 3.4mm; padding: 2.4mm 3.5mm; border-radius: 1.6mm; page-break-inside: avoid; }
blockquote p { margin: 0 0 1mm !important; }
blockquote p:last-child { margin-bottom: 0 !important; }
blockquote strong:first-child { font-family: 'Barlow'; font-weight: 700; text-transform: uppercase; letter-spacing: .08em; font-size: 8pt; display: block; margin-bottom: .6mm; }
.k-ansage { background: color-mix(in srgb, var(--f) 9%, #fff); border-left: 2.6pt solid var(--f); }
.k-ansage strong:first-child { color: var(--f); }
.k-ansage p { font-style: italic; }
.k-tipp { background: #e9f4ec; border-left: 2.6pt solid #167a4b; }
.k-tipp strong:first-child { color: #167a4b; }
.k-achtung { background: #fbf0d2; border-left: 2.6pt solid #b88407; }
.k-achtung strong:first-child { color: #8a6200; }
.k-praxis { background: #f2f0eb; border-left: 2.6pt solid #8a8172; }
.k-praxis strong:first-child { color: #5f584c; }
.blick { background: var(--tinte); color: #fff; border-radius: 2mm; padding: 3.5mm 5mm 2mm; margin: 0 0 5mm; page-break-inside: avoid; }
.blick h3 { color: #fff !important; font-size: 12pt !important; margin: 0 0 1.5mm !important; letter-spacing: .06em; text-transform: uppercase; }
.blick ul { padding-left: 4.5mm; }
.blick li { margin-bottom: 1.2mm; }
.blick li::marker { color: color-mix(in srgb, var(--f) 45%, #fff); }
h4.fall { border-top: 0.8pt solid var(--linie); padding-top: 2.5mm; color: var(--f); }
.srefs { display: grid; grid-template-columns: 1fr 1fr; gap: 2.4mm 5mm; margin: 1mm 0 4mm; }
.sref { display: flex; gap: 2.6mm; align-items: flex-start; page-break-inside: avoid; border: 0.6pt solid var(--linie); border-radius: 1.6mm; padding: 2mm 2.4mm; font-size: 8.4pt; line-height: 1.35; }
.sref img { width: 14mm; height: 14mm; flex: none; }
.sref b { font-family: 'Barlow'; font-size: 11pt; display: block; line-height: 1.1; }
.sref small { display: block; color: var(--t3); font-size: 7.4pt; margin: .4mm 0 .8mm; }
.vorlage { page-break-before: always; page-break-after: always; border: 1pt dashed #9aa9a1; border-radius: 2mm; padding: 5mm 6mm; position: relative; }
.vorlage .vkopf { font-family: 'Barlow'; font-weight: 700; font-size: 7.6pt; letter-spacing: .14em; text-transform: uppercase; color: var(--f); border-bottom: 0.8pt solid var(--linie); padding-bottom: 1.5mm; margin-bottom: 3mm; display: flex; justify-content: space-between; }
.vorlage h4 { font-size: 17pt; margin: 0 0 3mm; color: var(--tinte); }
.vorlage p, .vorlage li { font-size: 9.6pt; line-height: 1.55; }
.vorlage table { font-size: 9pt; }
.vorlage td { height: 8.5mm; }
.vorlage hr { border: 0; border-top: 1.3pt dashed #6f8178; margin: 5mm 0; }
.vorlage li.check { margin-bottom: 1.2mm; }
.vorlage + .vorlage { page-break-before: auto; }
.spick { page-break-before: always; }
.spick h1 { font-size: 22pt; color: var(--f); text-transform: uppercase; margin-bottom: 1mm; }
.spick .raster { columns: 2; column-gap: 7mm; }
.spick .sk { break-inside: avoid; margin-bottom: 4mm; }
.spick h3 { font-size: 11.5pt; margin: 0 0 1.2mm; color: var(--f); }
.spick h3 span { color: var(--t3); font-size: 9pt; }
.spick ul { padding-left: 4mm; }
.spick li { font-size: 8.4pt; line-height: 1.38; margin-bottom: 1mm; }
.einl h3 { font-size: 13pt; color: var(--f); margin: 5mm 0 1.5mm; }
.toc li.vl { font-size: 8.4pt; padding: 1.1mm 0; }
.toc.vl2 { columns: 2; column-gap: 8mm; }
.toc.vl2 li { break-inside: avoid; }
.luecke { display: inline-block; border-bottom: 0.7pt solid #8a9c92; height: 3.2mm; vertical-align: -0.6mm; max-width: 100%; }
.zeile { display: block; border-bottom: 0.7pt solid #8a9c92; height: 6.5mm; }
.vorlage .zeile { height: 7.5mm; }
"""


def sref(vid, grund, fundorte, eintraege):
    e = eintraege.get(vid)
    wo = fundorte.get(vid)
    if not e or not wo:
        raise SystemExit(f'Band 6: Spiel {vid} nicht in der Reihe gefunden')
    band = next(b for b in P.REIHE if b['band'] == wo[0])
    stufe = e['meta'].get('Altersstufe', '')
    return (f'<div class="sref"><img src="{P.qr("https://www.youtube.com/watch?v=" + vid)}" alt=""/><div><b>{html.escape(e["name"])}</b>'
            f'<small>Band {wo[0]} „{html.escape(band["kurz"])}“ · Nr. {wo[1]} · {html.escape(stufe)}</small>{html.escape(grund)}</div></div>')


def render(text, fundorte, eintraege, vorlagen, buchtitel):
    # Spiel-Verweise: zusammenhängende Zeilen „- [[spiel:ID]] – Grund“ → Kartenraster
    def block(m):
        karten = [sref(i, g.strip(), fundorte, eintraege) for i, g in re.findall(r'^- \[\[spiel:([\w-]+)\]\]\s*[–-]\s*(.+)$', m.group(0), re.M)]
        return '<div class="srefs">' + ''.join(karten) + '</div>\n'
    text = re.sub(r'(?:^- \[\[spiel:[\w-]+\]\].*\n?)+', block, text, flags=re.M)
    if '[[spiel:' in text:
        raise SystemExit('Band 6: nicht umgewandelter Spiel-Verweis')
    # Schreiblinien: „______“ → echte Linie (sonst macht Markdown Kursivschrift daraus)
    text = re.sub(r'^_{8,}\s*$', '<span class="zeile"></span>', text, flags=re.M)
    text = re.sub(r'_{3,}', lambda m_: f'<span class="luecke" style="width:{min(len(m_.group(0)) * 1.5, 150):.0f}mm"></span>', text)
    h = markdown.markdown(text, extensions=['tables', 'sane_lists', 'md_in_html'])
    h = h.replace('<li>[ ] ', '<li class="check">')
    for label, cls in KASTEN.items():
        h = re.sub(rf'<blockquote>\s*<p><strong>{re.escape(label)}:</strong>', f'<blockquote class="{cls}"><p><strong>{label}</strong>', h)
    if re.search(r'<blockquote>', h):
        raise SystemExit('Band 6: Kasten ohne bekanntes Stichwort')
    h = re.sub(r'<h3>Auf einen Blick</h3>\s*(<ul>.*?</ul>)', r'<div class="blick"><h3>Auf einen Blick</h3>\1</div>', h, count=1, flags=re.S)
    h = re.sub(r'<h4>(Fall: .*?)</h4>', r'<h4 class="fall">\1</h4>', h)

    def vorlage(m):
        titel = re.search(r'<h4>Kopiervorlage: (.*?)</h4>', m.group(0))
        if not titel:
            raise SystemExit('Band 6: Kopiervorlage ohne Titel')
        n = len(vorlagen) + 1
        vorlagen.append(titel.group(1))
        kopf = f'<div class="vkopf"><span>Kopiervorlage {n} · {html.escape(buchtitel)}</span><span>Kopieren für den eigenen Unterricht erlaubt</span></div>'
        inner = m.group(1).replace(f'<h4>Kopiervorlage: {titel.group(1)}</h4>', f'<h4>{titel.group(1)}</h4>', 1)
        return f'<div class="vorlage" id="v{n}">{kopf}{inner}</div>'
    h = re.sub(r'<div class="vorlage">(.*?)</div>', vorlage, h, flags=re.S)
    # Kopiervorlagen ans Kapitelende (nach „Zum Weiterlesen“), damit der Fließtext nicht zerrissen wird
    bloecke = re.findall(r'<div class="vorlage" id="v\d+"><div class="vkopf">.*?</div>.*?</div>', h, flags=re.S)
    for x in bloecke:
        h = h.replace(x, '', 1)
    return h + ''.join(bloecke)


def blick_punkte(text):
    m = re.search(r'^### Auf einen Blick\s*\n(.*?)(?=^### )', text, re.M | re.S)
    return [re.sub(r'^- ', '', z).strip() for z in m.group(1).strip().splitlines() if z.startswith('- ')] if m else []


def baue_alle_dabei(b, fundorte):
    # Alle Einträge der Reihe (für Namen und Schulstufen der Verweise)
    eintraege = {}
    for x in P.REIHE:
        if x['slug'] in ('praktikum', 'alle-dabei'):
            continue
        buch = P.parse((P.EBOOKS / x['slug'] / 'inhalt.md').read_text())
        for k in buch['kapitel']:
            for e in k['eintraege']:
                eintraege.setdefault(e['id'], P.eintrag_aus_excel(e))

    kap_md = [(ORDNER / f'kapitel-{i}.md').read_text() for i in range(1, 100) if (ORDNER / f'kapitel-{i}.md').exists()]
    vorlagen = []
    teile, kopf_titel, spick = [], [], []
    for i, t in enumerate(kap_md):
        erste, rest = t.split('\n', 1)
        titel = erste.lstrip('# ').strip()
        kopf_titel.append(titel)
        spick.append((titel, blick_punkte(t)))
        start = len(vorlagen)
        inhalt = render(rest, fundorte, eintraege, vorlagen, b['titel'])
        n_v = len(vorlagen) - start
        k = P.kapitel_kopf(i, {'titel': titel}, 0, b['farbe'])
        if n_v:
            k = k.replace('</h2>', f'</h2><div class="kmeta">mit {n_v} Kopiervorlage{"n" if n_v > 1 else ""}</div>', 1)
        teile.append(k + f'<div class="hb">{inhalt}</div>')

    n_fall = sum(t.count('#### Fall:') for t in kap_md)
    einl = markdown.markdown((ORDNER / 'einleitung.md').read_text(), extensions=['tables', 'sane_lists'])
    for label, cls in KASTEN.items():
        einl = re.sub(rf'<blockquote>\s*<p><strong>{re.escape(label)}:</strong>', f'<blockquote class="{cls}"><p><strong>{label}</strong>', einl)
    einleitung = f'<section class="text-seite einl" id="einleitung"><h1>Bevor du loslegst</h1>{einl}</section>'

    def inhalt_seite(mit_seiten=True):
        z = [f'<section class="inhalt{"" if mit_seiten else " ohne-seiten"}"><h1>Inhalt</h1><ol class="toc">', '<li class="kap"><a href="#einleitung">Bevor du loslegst</a></li>']
        z += [f'<li class="kap"><a href="#k{i}">{html.escape(t)}</a></li>' for i, t in enumerate(kopf_titel)]
        z.append('<li class="kap"><a href="#spick">Das Wichtigste zum Mitnehmen</a></li>')
        z.append('<li class="kap"><a href="#v1">Kopiervorlagen</a></li>')
        z.append('</ol><ol class="toc vl2">')
        z += [f'<li class="vl"><span class="nr">{n}</span><a href="#v{n}">{html.escape(v)}</a></li>' for n, v in enumerate(vorlagen, 1)]
        z.append('</ol><ol class="toc"><li class="kap"><a href="#reihe">Die Praxis-Reihe &amp; der Autor</a></li></ol></section>')
        return ''.join(z)

    sk = ''.join(f'<div class="sk"><h3><span>{html.escape(t.split(" – ")[0])} · </span>{html.escape(t.split(" – ", 1)[1])}</h3><ul>{"".join("<li>" + html.escape(p_) + "</li>" for p_ in pk)}</ul></div>' for t, pk in spick)
    spickzettel = f'<section class="spick" id="spick"><h1>Das Wichtigste zum Mitnehmen</h1><p style="margin-bottom:5mm">Die Kernsätze aller {ZAHL.get(len(kap_md), len(kap_md))} Kapitel – zum Ausdrucken für das Konferenzzimmer oder die Praktikumsmappe.</p><div class="raster">{sk}</div></section>'

    zahlen = f'<div><b>{len(kap_md)}</b>Kapitel</div><div><b>{len(vorlagen)}</b>Kopiervorlagen</div><div><b>{n_fall}</b>Fallbeispiele</div><div><b>1–13</b>Schulstufe</div>'

    def deckblatt(probe=False):
        c = P.cover(b, 0, probe=probe)
        return re.sub(r'<div class="zahlen">.*?</div></div>', f'<div class="zahlen">{zahlen}</div>', c, flags=re.S)

    impressum = P.impressum(b).replace('<h4>Videos</h4>', '<h4>Kopiervorlagen</h4><p>Die Kopiervorlagen darfst du für deine eigenen Klassen und Gruppen kopieren. Die rechtlichen Hinweise beziehen sich auf Österreich (Stand Schuljahr 2026/27) und ersetzen weder Rechtsberatung noch ärztliche Einschätzung.</p><h4>Videos</h4>', 1)
    impressum = impressum.replace('Alle Spiele und Übungen wurden im Schulunterricht erprobt.', 'Alle Hinweise, Spiele und Übungen stammen aus der Unterrichtspraxis.')

    body = deckblatt() + impressum + inhalt_seite() + einleitung + ''.join(teile) + spickzettel + P.reihe_seite(b['slug'])
    doc_css = CSS
    voll = schreibe(b, body, 'alle-dabei.pdf', doc_css)

    # Leseprobe: Einleitung + Kapitel 2 (Angst) vollständig
    punkte = [f'{len(kap_md)} Kapitel: Sicherheit, Angst, Aggression, Motivation, Heterogenität, Nicht-Aktive, Koedukation, „Strafen“ und Rituale',
              f'{n_fall} Fallbeispiele von der Volksschule bis zur Oberstufe, wörtliche Formulierungen für die Halle',
              f'{len(vorlagen)} Kopiervorlagen: Hallencheck, Unfall-Notiz, Mutbarometer, Fairplay-Vertrag, Rollenkarten, Beobachtungsbögen u. v. m.',
              'Rechtliche Grundlagen für Österreich kompakt erklärt – Befreiung, Aufsicht, Beurteilung']
    probe_body = deckblatt(True) + inhalt_seite(False) + einleitung + teile[1] + P.leseprobe_ende(b, punkte) + P.reihe_seite(b['slug'])
    probe = schreibe(b, probe_body, 'alle-dabei-leseprobe.pdf', doc_css, probe=True)
    return voll, probe, f'{len(vorlagen)} Kopiervorlagen, {n_fall} Fälle'


def schreibe(b, body, name, extra, probe=False):
    P.OUT.mkdir(exist_ok=True)
    doc = (f'<html lang="de"><head><meta charset="utf-8"><title>{html.escape(b["titel"])}</title><meta name="author" content="David Jungreithmayr · Sportunterricht">'
           f'<meta name="keywords" content="Sportunterricht, Bewegung und Sport, Sicherheit, Angst, Aggression, Motivation, Heterogenität, Befreiung">'
           f'<style>{P.css(b["farbe"], P.fusszeile(b, probe))}{extra}</style></head><body>{body}</body></html>')
    pfad = P.OUT / name
    P.HTML(string=doc, base_url=str(P.EBOOKS)).write_pdf(pfad)
    return pfad


if __name__ == '__main__':  # nur Band 6 neu bauen: python3 werkzeug/alle_dabei.py [--final]
    import json
    fo = {k: tuple(v) for k, v in json.loads((P.OUT / 'fundorte.json').read_text()).items()}
    b = next(x for x in P.REIHE if x['slug'] == 'alle-dabei')
    v, pr, info = baue_alle_dabei(b, fo)
    P.cover_bild(v, 'alle-dabei-cover')
    print('✓', info, v.name, pr.name)
