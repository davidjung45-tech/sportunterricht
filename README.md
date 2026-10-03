# Sportunterricht – Website & E-Book-Shop

Statische Website für den YouTube-Kanal **Sportunterricht** (@Sportunterricht2022): Startseite, Spiele-Lexikon mit 487 Videos, **Stundenplaner** mit druckbarem Stundenbild, **Werkzeuge für die Halle** (Zirkeltimer, Teams, Punkte, Zufall), **Merkliste mit Stationskarten**, sechs E-Book-Produktseiten, Komplettpaket, Gratis-PDF, Leseproben, Rechtsseiten. Verkauf über **Digistore24**. Kein Tracking, keine Werbe-Cookies.

## Was ist wo?

| Ordner / Datei | Wofür |
|---|---|
| `website/ausgabe/` | **Die fertige Website.** Genau dieser Ordner wird veröffentlicht. |
| `website/einstellungen.json` | Die eine Datei zum Ausfüllen: Domain, Impressum, E-Mail, Digistore24-Kauflinks. |
| `website/bauen.py` | Baut die Website neu (nach Änderungen an `einstellungen.json`). |
| `website/statisch/` | Design (`site.css`), Funktionen (`site.js`), Schriften. |
| `website/START-HIER.md` | Ausführliche Anleitung zum Livegang. |
| `ebooks/werkzeug/` | Baut die E-Book-PDFs aus den Buchtexten. |
| `netlify.toml` | Damit Netlify die Website direkt aus diesem Repository veröffentlicht. |

**Nicht im Repository** (absichtlich, weil das Repository öffentlich ist): die Buchtexte (`ebooks/spielesammlung/` usw.), die Vollversionen (`ebooks/ausgabe/`), die Verkaufsdateien (`website/verkauf/`) und die internen Unterlagen (`transfer/`). Wer das Repository auf **privat** stellt, kann sie dazulegen.

## Online stellen (einmalig, ca. 10 Minuten)

1. Auf [app.netlify.com](https://app.netlify.com) kostenlos anmelden → **Add new site → Import an existing project → GitHub** → Repository `sportunterricht` wählen.
2. Alle Felder so lassen, wie Netlify sie aus `netlify.toml` übernimmt → **Deploy**.
3. Unter *Domain management* die eigene Domain verbinden.

Danach geht jede Änderung, die in GitHub landet, automatisch online.

## Nach einer Änderung neu bauen

Voraussetzung: Python 3 mit `pip install weasyprint markdown qrcode openpyxl pillow` und `pdftoppm` (Poppler). Die Buchtexte müssen im Ordner `ebooks/` liegen.

```
cd ebooks && python3 werkzeug/pdf.py --final   # E-Books, Leseproben, Gratis-PDF
cd ../website && python3 bauen.py               # Website → website/ausgabe/
python3 bauen.py --vorschau                     # zum Anschauen per Doppelklick: website/vorschau/index.html
```

Am Ende listet `bauen.py` mit ⚠ alles auf, was noch fehlt (z. B. Kauflinks, Impressum).
