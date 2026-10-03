"""Übernimmt die neuen illustrierten Bände aus knowit/quellen/ (nicht im Repository).

Erwartet je Band: bandN-voll.pdf, bandN-lernen.pdf, bandN-leseprobe.pdf
Erzeugt:
  daten/lernkarten.json                – alle Lernkarten (Fragen, Antworten, Vollband-Seite, Bild)
  daten/baende_neu.json                – je Band: Titel, Seitenzahl, Kartenzahl, Inhaltsverzeichnis
  statisch/bilder/lk/bN-NN.jpg         – Kartenbild
  statisch/bilder/muskeln/<slug>.jpg   – Illustration der Muskelseite (Muskel-Atlanten)
  statisch/bilder/cover-bandN.jpg, seite-*-bandN.jpg, lernkarten-bandN.jpg
  statisch/downloads/leseprobe-<slug>.pdf (verkleinert)
Aufruf: python3 werkzeug/neue_baende.py
"""
import json, re, io, sys
from pathlib import Path
import pymupdf
from PIL import Image

HIER = Path(__file__).resolve().parent.parent
Q = HIER / 'quellen'
BILD = HIER / 'statisch' / 'bilder'
DL = HIER / 'statisch' / 'downloads'
PRODUKTE = json.load(open(HIER / 'daten' / 'produkte.json'))
MUSKELN = json.load(open(HIER / 'daten' / 'muskeln.json'))
SLUG_BAND = {p['band']: p['slug'] for p in PRODUKTE}

# Muster für die Innenansichten je Band: (Muskel-/Bauseite, Kapitel-/Vertiefungsseite, Übersicht)
VORSCHAU_SEITEN = {
    1: (r'^01\s', r'Die drei Gesäßmuskeln', r'WER MACHT WELCHE BEWEGUNG'),
    2: (r'^01\s', r'^Sie ziehen vom Schulterblatt zum Oberarm', r'WER MACHT WELCHE BEWEGUNG'),
    3: (r'^01\s', r'^Der wichtigste Atemmuskel', r'WER MACHT WELCHE BEWEGUNG'),
    4: (r'KAPITEL 12 · BAU', r'^Kniegelenk · Bänder', r'WELCHES BAND BREMST WAS'),
    5: (r'KAPITEL 12 · ORGANE', r'KAPITEL 13 · ORGANE', r'DIE WICHTIGSTEN ZAHLEN'),
}


def norm(t):
    return re.sub(r'[^a-z0-9]', '', t.lower().replace('ß', 'ss').replace('musculi', 'mm').replace('musculus', 'm'))


def zeilen(seite):
    out, bilder = [], []
    for b in seite.get_text('dict')['blocks']:
        if b['type'] == 0:
            for ln in b['lines']:
                t = ''.join(s['text'] for s in ln['spans']).strip()
                if t:
                    out.append((ln['bbox'][0], ln['bbox'][1], ln['spans'][0]['size'], t, ln['spans'][0]['flags']))
        else:
            bilder.append(b['bbox'])
    return out, bilder


def karten_lesen(n):
    """Liest Vorder- und Rückseiten der Lernkarten-Druckvorlage."""
    doc = pymupdf.open(Q / f'band{n}-lernen.pdf')
    karten = {}
    for pno in range(doc.page_count):
        seite = doc[pno]
        z, bilder = zeilen(seite)
        koepfe = [(x, y, int(m.group(2))) for x, y, s, t, f in z for m in [re.match(r'BAND (\d+) · KARTE (\d+)', t)] if m]
        for kx, ky, nr in koepfe:
            drin = [e for e in z if kx - 6 <= e[0] <= kx + 270 and ky - 4 <= e[1] <= ky + 185]
            art = 'FRAGEN' if any(e[3] == 'FRAGEN' for e in drin) else 'ANTWORTEN' if any(e[3] == 'ANTWORTEN' for e in drin) else None
            if not art:
                continue
            k = karten.setdefault(nr, {'band': n, 'nr': nr})
            titel = [e for e in drin if 12 <= e[1] - ky <= 26 and abs(e[0] - kx) < 8]
            if titel:
                k['titel'] = titel[0][3]
            if art == 'FRAGEN':
                spalte = sorted([e for e in drin if e[0] > kx + 100 and e[1] > ky + 40 and not e[3].startswith('Vollband')], key=lambda e: e[1])
                fragen, akt = [], None
                for e in spalte:
                    if re.match(r'^\d\.\s', e[3]):
                        akt = [e[3][3:].strip()]; fragen.append(akt)
                    elif akt is not None:
                        akt.append(e[3])
                k['fragen'] = [re.sub(r'-\s+(?=[a-zäöü])', '', ' '.join(a)).replace('  ', ' ') for a in fragen]
                s = [e[3] for e in drin if e[3].startswith('Vollband S.')]
                if s:
                    k['seite'] = int(re.sub(r'\D', '', s[0]))
                # Kartenbild
                bb = [b for b in bilder if kx - 6 <= b[0] <= kx + 270 and ky <= b[1] <= ky + 185]
                if bb:
                    r = pymupdf.Rect(bb[0])
                    pix = seite.get_pixmap(clip=r, dpi=300)
                    ziel = BILD / 'lk' / f'b{n}-{nr:02d}.jpg'
                    ziel.parent.mkdir(parents=True, exist_ok=True)
                    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
                    im.thumbnail((440, 540))
                    im.save(ziel, 'JPEG', quality=82, optimize=True, progressive=True)
                    k['bild'] = f'lk/b{n}-{nr:02d}.jpg'
            else:
                ant, akt = [], None
                for e in sorted([e for e in drin if e[1] > ky + 40 and not e[3].startswith('Erkläre')], key=lambda e: (e[1], e[0])):
                    if re.fullmatch(r'\d', e[3]):
                        continue
                    # Antworttext steht rechts der Nummernkreise; mehrzeilig möglich
                    if akt is not None and e[1] - akt[1] < 12:
                        akt[0].append(e[3]); akt[1] = e[1]
                    else:
                        akt = [[e[3]], e[1]]; ant.append(akt)
                k['antworten'] = [re.sub(r'-\s+(?=[a-zäöü])', '', ' '.join(a[0])) for a in ant]
    liste = [karten[k] for k in sorted(karten)]
    for k in liste:
        assert len(k.get('fragen', [])) == 3 and len(k.get('antworten', [])) == 3, (n, k)
    return liste


def karten_lesen_b(n):
    """Älteres Kartenlayout (Band 5): vorne „B5 · KAP. x“, Titel, TESTE DICH + 3 Fragen;
    hinten Titel in Großbuchstaben, Fakten und „Lösungen: 1. … · 2. … · 3. …“."""
    doc = pymupdf.open(Q / f'band{n}-lernen.pdf')
    vorne, hinten = [], {}
    for pno in range(doc.page_count):
        seite = doc[pno]
        z, bilder = zeilen(seite)
        for kx, ky, t in [(x, y, t) for x, y, s, t, f in z if re.match(rf'B{n} · KAP\. ?\d+', t)]:
            drin = sorted([e for e in z if kx - 6 <= e[0] <= kx + 265 and ky - 4 <= e[1] <= ky + 168], key=lambda e: (e[1], e[0]))
            rechts = [e for e in drin if e[0] > kx + 90]
            teste = next((e[1] for e in rechts if e[3] == 'TESTE DICH'), ky + 52)
            kopf = [e for e in rechts if ky + 10 <= e[1] < teste and e[3] not in ('SKELETT', 'ORGANE', 'MUSKEL')]
            gross = max((e[2] for e in kopf), default=0)
            titel = [(0, 0, 0, ' '.join(e[3] for e in kopf if e[2] >= gross - 0.5))]
            unter = [(0, 0, 0, ' '.join(e[3] for e in kopf if e[2] < gross - 0.5))]
            fragen, akt = [], None
            for e in [e for e in rechts if e[1] > teste + 4]:
                if re.fullmatch(r'\d\.', e[3]):
                    continue
                if akt is not None and e[1] - akt[1] < 11:
                    akt[0].append(e[3]); akt[1] = e[1]
                else:
                    akt = [[e[3]], e[1]]; fragen.append(akt)
            k = {'band': n, 'kapitel': int(re.sub(r'\D', '', t.split('KAP.')[1])), 'titel': titel[0][3] if titel else '',
                 'untertitel': unter[0][3] if unter else '', 'fragen': [' '.join(a[0]) for a in fragen][:3]}
            bb = [b for b in bilder if kx - 6 <= b[0] <= kx + 265 and ky <= b[1] <= ky + 168]
            # Band 5 zeichnet die Abbildungen als Vektorgrafik → Bereich links neben dem Text rendern
            k['_bild'] = (pno, bb[0] if bb else (kx, ky + 12, kx + 102, ky + 152))
            vorne.append(k)
        for kx, ky in [(x, y) for x, y, s, t, f in z if t == f'B{n} · ZAHLEN']:
            drin = sorted([e for e in z if kx - 4 <= e[0] <= kx + 265 and ky - 4 <= e[1] <= ky + 168], key=lambda e: (e[1], e[0]))
            titel = [e for e in drin if e[2] > 14]
            if not titel:
                continue
            weisst = next((e[1] for e in drin if e[3] == 'WEISST DU ES?'), ky + 57)
            fr = [e[3] for e in drin if e[1] > weisst + 4 and e[0] > kx + 8 and not re.fullmatch(r'\d\.', e[3])]
            vorne.append({'band': n, 'kapitel': 0, 'titel': titel[0][3], 'untertitel': 'Nenne den Richtwert!', 'fragen': fr, 'zahlen': True})
        for kx, ky, t in [(x, y, t) for x, y, s, t, f in z if t == 'RÜCKSEITE']:
            x0 = kx - 223  # Kopfzeile links in derselben Karte
            kopf = [e for e in z if abs(e[1] - ky) < 3 and x0 - 10 <= e[0] <= x0 + 10 and e[3] != 'RÜCKSEITE']
            if not kopf:
                continue
            x0 = kopf[0][0]
            drin = sorted([e for e in z if x0 - 4 <= e[0] <= x0 + 265 and ky + 8 <= e[1] <= ky + 185], key=lambda e: (e[1], e[0]))
            text = ' '.join(e[3] for e in drin)
            loes = re.search(r'Lösungen:\s*1\.\s*(.*?)\s*·\s*2\.\s*(.*?)\s*·\s*3\.\s*(.*)$', text)
            fakten = text.split('Lösungen:')[0].strip()
            titel_h = kopf[0][3]
            for e in drin:
                if e[3].isupper() and e[1] - ky < 22:
                    titel_h += ' ' + e[3]; drin.remove(e)
            hinten[norm(titel_h)] = {'antworten': [g.strip() for g in loes.groups()] if loes else [], 'fakten': fakten}
    liste = []
    for i, k in enumerate(vorne, 1):
        h = hinten.get(norm(k['titel']), {})
        k['nr'] = i
        k['antworten'] = h.get('antworten', [])
        k['fakten'] = h.get('fakten', '')
        if k.pop('zahlen', False):
            rest = h.get('fakten', '')
            ant = []
            for i2, f in enumerate(k['fragen']):
                stamm = f.rstrip('?').strip()
                nxt = k['fragen'][i2 + 1].rstrip('?').strip() if i2 + 1 < len(k['fragen']) else None
                a = rest.split(stamm + ':', 1)[1] if stamm + ':' in rest else ''
                if nxt and nxt + ':' in a:
                    a = a.split(nxt + ':')[0]
                ant.append(a.strip())
            k['antworten'] = ant
            k['fakten'] = ''
        if '_bild' in k:
            pno, r = k.pop('_bild')
            pix = doc[pno].get_pixmap(clip=pymupdf.Rect(r), dpi=300)
            ziel = BILD / 'lk' / f'b{n}-{i:02d}.jpg'
            im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
            im.thumbnail((440, 540))
            im.save(ziel, 'JPEG', quality=82, optimize=True, progressive=True)
            k['bild'] = f'lk/b{n}-{i:02d}.jpg'
        assert len(k['fragen']) >= 3 and len(k['antworten']) == len(k['fragen']) and all(k['antworten']), (n, k)
        liste.append(k)
    return liste


def seite_bild(doc, pno, breite, ziel, q=82):
    pix = doc[pno].get_pixmap(dpi=150)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    im.thumbnail((breite, breite * 2))
    im.save(ziel, 'JPEG', quality=q, optimize=True, progressive=True)


def groesstes_bild(doc, pno, ziel, max_h=760):
    seite = doc[pno]
    infos = seite.get_image_info(xrefs=True)
    if not infos:
        return False
    gross = max(infos, key=lambda i: (i['bbox'][2] - i['bbox'][0]) * (i['bbox'][3] - i['bbox'][1]))
    pix = seite.get_pixmap(clip=pymupdf.Rect(gross['bbox']), dpi=220)
    im = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
    im.thumbnail((max_h, max_h))
    im.save(ziel, 'JPEG', quality=84, optimize=True, progressive=True)
    return True


def seite_mit(doc, muster, ab=4):
    for pno in range(ab, doc.page_count):
        if re.search(muster, doc[pno].get_text()[:400]):
            return pno
    return None


def leseprobe_verkleinern(n, slug):
    doc = pymupdf.open(Q / f'band{n}-leseprobe.pdf')
    try:
        doc.rewrite_images(dpi_threshold=160, dpi_target=150, quality=78)
    except Exception as e:  # ältere PyMuPDF-Version
        print('  (Bilder nicht verkleinert:', e, ')')
    ziel = DL / f'leseprobe-{slug}.pdf'
    doc.save(ziel, garbage=4, deflate=True, clean=True)
    return ziel.stat().st_size


def main():
    alle_karten, baende = [], {}
    for n in range(1, 8):
        if not (Q / f'band{n}-voll.pdf').exists():
            continue
        slug = SLUG_BAND[n]
        voll = pymupdf.open(Q / f'band{n}-voll.pdf')
        karten = karten_lesen(n)
        if not karten:
            karten = karten_lesen_b(n)
        print(f'Band {n}: {len(karten)} Karten, Vollband {voll.page_count} Seiten')
        # Muskelbilder (nur Muskel-Atlanten 1–3): Karte → Vollband-Seite → Illustration
        muskeln_band = [m for m in MUSKELN if m['band'] == n]
        zuordnung = 0
        for k in karten:
            m = next((m for m in muskeln_band if norm(m['name']) == norm(k['titel'])), None)
            if m:
                k['slug'] = m['slug']
                (BILD / 'muskeln').mkdir(exist_ok=True)
                if groesstes_bild(voll, k['seite'] - 1, BILD / 'muskeln' / f"{m['slug']}.jpg"):
                    zuordnung += 1
        if muskeln_band:
            fehlt = [m['name'] for m in muskeln_band if not any(k.get('slug') == m['slug'] for k in karten)]
            print(f'  Muskelbilder: {zuordnung}/{len(muskeln_band)}', 'fehlen: ' + ', '.join(fehlt) if fehlt else '')
        # Cover und Innenansichten
        seite_bild(voll, 0, 640, BILD / f'cover-band{n}.jpg')
        # Innenansichten passend zu den Bildunterschriften in daten/produkte.json
        muster = VORSCHAU_SEITEN[n]
        for art, m in zip(('muskel', 'kapitel', 'bewegung'), muster):
            pno = seite_mit(voll, m)
            assert pno is not None, (n, art, m)
            seite_bild(voll, pno, 1000, BILD / f'seite-{art}-band{n}.jpg')
        seite_bild(pymupdf.open(Q / f'band{n}-lernen.pdf'), 2, 1000, BILD / f'lernkarten-band{n}.jpg')
        groesse = leseprobe_verkleinern(n, slug)
        print(f'  Leseprobe: {groesse / 1e6:.1f} MB')
        baende[n] = {'slug': slug, 'titel': voll.metadata.get('title', ''), 'seiten': voll.page_count, 'karten': len(karten),
                     'leseprobe_seiten': pymupdf.open(Q / f'band{n}-leseprobe.pdf').page_count}
        alle_karten += karten
    json.dump(alle_karten, open(HIER / 'daten' / 'lernkarten.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(baende, open(HIER / 'daten' / 'baende_neu.json', 'w'), ensure_ascii=False, indent=1)
    print('Karten gesamt:', len(alle_karten))


if __name__ == '__main__':
    main()
