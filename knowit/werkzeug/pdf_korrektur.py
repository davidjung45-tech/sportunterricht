"""Korrigiert die Know-it-PDFs in knowit/quellen/ (nicht im Repository):

  · „DJ“ → „David Jungreithmayr“ (Cover, Copyright, „Über den Autor“, Lernkarten-Hinweis)
  · Fußzeile „ · ENTWURF – vor Verkauf prüfen“ entfernt

Die betroffenen Zeilen werden entfernt und in der eingebetteten Originalschrift (gleiche Größe,
Farbe und Grundlinie) neu gesetzt. Die Originale landen einmalig in quellen/original/.
Aufruf: python3 werkzeug/pdf_korrektur.py   (danach: python3 werkzeug/neue_baende.py && python3 bauen.py)
"""
import re
import shutil
from pathlib import Path
import pymupdf

Q = Path(__file__).resolve().parent.parent / 'quellen'
NAME = 'David Jungreithmayr'
ENTWURF = ' · ENTWURF – vor Verkauf prüfen'


def schrift(doc, seite, fontname, cache):
    """Eingebettete Schrift der Seite als Puffer holen (Teilmenge – Glyphen werden geprüft)."""
    for xref, _, _, basis, *_ in seite.get_fonts(full=True):
        if basis.split('+')[-1] == fontname:
            if xref not in cache:
                name, ext, typ, puffer = doc.extract_font(xref)
                cache[xref] = puffer
            return xref, cache[xref]
    return None, None


def neu(text):
    t = re.sub(r'\bDJ\b', NAME, text)
    return t.replace(ENTWURF, '').replace(ENTWURF.strip(' ·'), '').rstrip(' ·')


def korrigiere(datei):
    doc = pymupdf.open(datei)
    cache, geaendert = {}, 0
    for seite in doc:
        aufgaben = []  # (bbox, ursprung, text, schriftname, größe, farbe)
        absaetze = []
        for b in seite.get_text('dict')['blocks']:
            zeilen = b.get('lines', [])
            for i, z in enumerate(zeilen):
                text = ''.join(s['text'] for s in z['spans'])
                if not (re.search(r'\bDJ\b', text) or 'ENTWURF' in text):
                    continue
                s = z['spans'][0]
                if text.startswith('DJ unterrichtet'):
                    # Fließtext: ganzen Absatz neu umbrechen
                    absaetze.append((zeilen[i:], s))
                    break
                if text.startswith('DJ · ') and 'YouTube:' in text:
                    # Cover: Das Titelbild enthält die alte Zeile als Bild – „YouTube: …“ muss exakt an der alten Stelle bleiben
                    yt_x = next((c['origin'][0] for sp in seite.get_text('rawdict')['blocks'] for zl in sp.get('lines', []) if zl['bbox'] == z['bbox']
                                 for spn in zl['spans'] for i2, c in enumerate(spn['chars']) if c['c'] == 'Y' and ''.join(ch['c'] for ch in spn['chars'][i2:i2 + 8]) == 'YouTube:'), None)
                    aufgaben.append((pymupdf.Rect(z['bbox']), s['origin'], ('COVER', yt_x, text[text.index('YouTube:'):]), s['font'], s['size'], s['color']))
                    continue
                aufgaben.append((pymupdf.Rect(z['bbox']), s['origin'], neu(text), s['font'], s['size'], s['color']))
        # unsichtbare Textreste (z. B. unter einer überdeckten Fußzeile) nur entfernen, nicht neu setzen
        sichtbar = {tuple(round(v) for v in z['bbox']) for b in seite.get_text('dict')['blocks'] for z in b.get('lines', [])}
        versteckt = []
        for b in seite.get_text('dict', flags=0, clip=pymupdf.INFINITE_RECT())['blocks']:
            for z in b.get('lines', []):
                tx = ''.join(s['text'] for s in z['spans'])
                if (re.search(r'\bDJ\b', tx) or 'ENTWURF' in tx) and tuple(round(v) for v in z['bbox']) not in sichtbar:
                    versteckt.append(pymupdf.Rect(z['bbox']))
        if not aufgaben and not absaetze and not versteckt:
            continue
        for r in versteckt:
            seite.add_redact_annot(r + (-0.5, 0.8, 0.5, -0.8), fill=False)
            geaendert += 1
        for r, ursprung, text, *_ in aufgaben:
            # Cover-Zeile über die ganze Breite leeren (in Band 1 liegt dort ein überlagerter Textrest)
            breit = pymupdf.Rect(r.x0, r.y0, seite.rect.width, r.y1) if isinstance(text, tuple) else r
            seite.add_redact_annot(breit + (-0.5, 0.8, 0.5, -0.8), fill=False)
        absatz_daten = []
        for zeilen, s in absaetze:
            gleich = [z for z in zeilen if z['spans'][0]['font'] == s['font'] and abs(z['spans'][0]['size'] - s['size']) < 0.1]
            # nur zusammenhängende Zeilen desselben Absatzes (gleiche Schrift, Abstand < 1,6 Zeilen)
            abs_z = [gleich[0]]
            for z in gleich[1:]:
                if z['bbox'][1] - abs_z[-1]['bbox'][1] < s['size'] * 1.6:
                    abs_z.append(z)
            text = ' '.join(''.join(sp['text'] for sp in z['spans']) for z in abs_z)
            rechts = max(z['bbox'][2] for z in abs_z)
            box = pymupdf.Rect(abs_z[0]['bbox'][0], abs_z[0]['bbox'][1], max(rechts, abs_z[0]['bbox'][0] + 400), abs_z[-1]['bbox'][3])
            for z in abs_z:
                seite.add_redact_annot(pymupdf.Rect(z['bbox']) + (-0.5, 0.8, 0.5, -0.8), fill=False)
            absatz_daten.append((box, abs_z[0]['spans'][0]['origin'], neu(text), s, abs_z[1]['bbox'][1] - abs_z[0]['bbox'][1] if len(abs_z) > 1 else s['size'] * 1.3))
        seite.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE, text=pymupdf.PDF_REDACT_TEXT_REMOVE)

        for r, ursprung, text, fname, groesse, farbe in aufgaben:
            if isinstance(text, tuple):
                bild_text_entfernen(doc, seite, r)
            setze_zeile(doc, seite, cache, r, ursprung, text, fname, groesse, farbe)
            geaendert += 1
        for box, ursprung, text, s, abstand in absatz_daten:
            setze_absatz(doc, seite, cache, box, ursprung, text, s, abstand)
            geaendert += 1
    if geaendert:
        tmp = datei.with_suffix('.tmp.pdf')
        doc.save(tmp, garbage=3, deflate=True)
        doc.close()
        tmp.replace(datei)
    return geaendert


def bild_text_entfernen(doc, seite, zeile_r):
    """Das Titelbild enthält Reste der alten Autorenzeile (eingebrannt). Diese Pixel mit der Hintergrundfarbe übermalen."""
    import io
    from PIL import Image
    for info in seite.get_image_info(xrefs=True):
        br = pymupdf.Rect(info['bbox'])
        if not br.intersects(zeile_r + (-2, -6, 2, 6)) or not info['xref']:
            continue
        pix = pymupdf.Pixmap(doc, info['xref'])
        if pix.alpha or pix.n != 3:
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix, 0)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        sx, sy = pix.width / br.width, pix.height / br.height
        y0, y1 = int((zeile_r.y0 - 4 - br.y0) * sy), int((zeile_r.y1 + 4 - br.y0) * sy)
        x1 = int((min(br.x1, 400) - br.x0) * sx)
        if x1 <= 0 or y0 < 0:
            continue
        px = im.load()
        bg = px[max(0, x1 - 1), max(0, y0 - 6)]
        dist = lambda c: sum(abs(a - b) for a, b in zip(c, bg))
        treffer = [(x, y) for y in range(y0, min(y1, pix.height)) for x in range(0, x1) if dist(px[x, y]) > 90]
        if not treffer:
            continue
        xa, xb = min(x for x, _ in treffer), max(x for x, _ in treffer)
        ya, yb = min(y for _, y in treffer), max(y for _, y in treffer)
        for y in range(max(0, ya - 3), min(pix.height, yb + 4)):
            for x in range(max(0, xa - 3), min(pix.width, xb + 4)):
                px[x, y] = bg
        # verirrte schwarze Beschriftungen in Zeilenhöhe (Band 4, Leseprobe: „außen“/„innen“) ebenfalls entfernen
        dunkel = sorted({x for y in range(max(0, ya - 12), min(pix.height, yb + 12)) for x in range(pix.width) if max(px[x, y]) < 70})
        gruppen, akt = [], []
        for x in dunkel:
            if akt and x - akt[-1] > 15:
                gruppen.append(akt); akt = []
            akt.append(x)
        if akt:
            gruppen.append(akt)
        for g in gruppen:
            ys = [y for y in range(max(0, ya - 12), min(pix.height, yb + 12)) for x in (g[0], g[len(g) // 2], g[-1]) if max(px[x, y]) < 70]
            ys += [y for y in range(max(0, ya - 12), min(pix.height, yb + 12)) for x in g if max(px[x, y]) < 70][:0]
            alle_y = [y for y in range(max(0, ya - 12), min(pix.height, yb + 12)) if any(max(px[x, y]) < 70 for x in g)]
            if not alle_y:
                continue
            ga, gb = min(alle_y), max(alle_y)
            hinter = px[g[0], max(0, ga - 5)]
            for y in range(max(0, ga - 2), min(pix.height, gb + 3)):
                for x in range(max(0, g[0] - 2), min(pix.width, g[-1] + 3)):
                    px[x, y] = hinter
        puffer = io.BytesIO(); im.save(puffer, 'PNG')
        seite.replace_image(info['xref'], stream=puffer.getvalue())
        return True
    return False


def farbe_rgb(c):
    return ((c >> 16) & 255) / 255, ((c >> 8) & 255) / 255, (c & 255) / 255


def font_obj(doc, seite, cache, fname, text):
    xref, puffer = schrift(doc, seite, fname, cache)
    if puffer:
        f = pymupdf.Font(fontbuffer=puffer)
        fehlt = [ch for ch in set(text) if not f.has_glyph(ord(ch))]
        if not fehlt:
            return f, puffer
        print(f'    Schrift {fname}: fehlende Zeichen {fehlt} – Ersatzschrift')
    return pymupdf.Font('helv'), None


def setze_zeile(doc, seite, cache, r, ursprung, text, fname, groesse, farbe):
    if isinstance(text, tuple):
        # Cover: kurze Fassung, damit die Zeile nicht in die Illustration läuft (Bände 4/5: Füße rechts unten)
        text = NAME + ' · Sportlehrer in Wien · ' + text[2]
    f, puffer = font_obj(doc, seite, cache, fname, text)
    rechts_max = seite.rect.width - r.x0  # gleicher Rand wie links
    g = groesse
    while f.text_length(text, fontsize=g) > rechts_max - r.x0 and g > groesse * 0.8:
        g -= 0.1
    tw = pymupdf.TextWriter(seite.rect, color=farbe_rgb(farbe))
    tw.append(ursprung, text, font=f, fontsize=g)
    tw.write_text(seite)


def setze_absatz(doc, seite, cache, box, ursprung, text, s, abstand):
    f, puffer = font_obj(doc, seite, cache, s['font'], text)
    breite = box.width
    woerter, zeilen, akt = text.split(), [], ''
    for w in woerter:
        probe = (akt + ' ' + w).strip()
        if f.text_length(probe, fontsize=s['size']) <= breite:
            akt = probe
        else:
            zeilen.append(akt)
            akt = w
    zeilen.append(akt)
    tw = pymupdf.TextWriter(seite.rect, color=farbe_rgb(s['color']))
    x, y = ursprung
    for i, z in enumerate(zeilen):
        tw.append((x, y + i * abstand), z, font=f, fontsize=s['size'])
    tw.write_text(seite)


def main():
    (Q / 'original').mkdir(exist_ok=True)
    for datei in sorted(Q.glob('band*.pdf')):
        sicherung = Q / 'original' / datei.name
        if not sicherung.exists():
            shutil.copy2(datei, sicherung)
        else:
            shutil.copy2(sicherung, datei)  # immer vom Original ausgehen
        n = korrigiere(datei)
        print(f'{datei.name}: {n} Stellen korrigiert')
    # öffentliche PDFs, die nicht aus quellen/ stammen (Gratis-Lernskript, Leseproben Band 6 und 7)
    dl = Q.parent / 'statisch' / 'downloads'
    for name in ('gratis-bewegungsausmass.pdf', 'leseprobe-trainingslehre-kompakt.pdf', 'leseprobe-ernaehrung-kompakt.pdf'):
        datei, sicherung = dl / name, Q / 'original' / ('download-' + name)
        if not datei.exists():
            continue
        if not sicherung.exists():
            shutil.copy2(datei, sicherung)
        else:
            shutil.copy2(sicherung, datei)
        print(f'{name}: {korrigiere(datei)} Stellen korrigiert')


if __name__ == '__main__':
    main()
