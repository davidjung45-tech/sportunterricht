# Know it – Website: Start hier

## Was ist wo?

| Datei / Ordner | Wofür |
|---|---|
| `ausgabe/` | **Die fertige Website.** Diesen Ordner (als ZIP) bei Netlify hochladen. |
| `einstellungen.json` | Die eine Datei zum Ausfüllen: **Digistore24-Kauflinks**, Preise, Impressum, Adresse der Website. |
| `bauen.py` | Baut die Website neu: `python3 bauen.py` (zum Anschauen per Doppelklick: `python3 bauen.py --vorschau` → `vorschau/index.html`). |
| `daten/` | Inhalte: 7 Bände, 112 Muskeln (Steckbriefe, Zeichnungen, Video-IDs), FAQ, Leseproben-Texte – 1:1 aus der bisherigen Website übernommen. |
| `statisch/` | Bilder, Leseproben, Gratis-PDF, Schriften, Know-it-Design und -Funktionen. Das Grund-Design teilt sich die Seite mit Sportunterricht (`../website/statisch/`). |

## Was die neue Website kann

- **Startseite auf Verkauf ausgerichtet:** Preisanker „E-Books ab 17,90 €“ ganz oben, „Welches Buch brauchst du?“ (9 Knöpfe → passende Empfehlung), alle 7 Bände mit Leseprobe, **Komplettpaket** und **Muskel-Atlas-Paket** mit Ersparnis, Blick ins Buch, Vorteile, kostenlose Werkzeuge, FAQ, Abschluss-Aufruf.
- **Produktseiten:** Kaufbox, Paket-Hinweis, Innenansichten, Kapitel, Leseprobe, alle Muskeln des Bandes verlinkt, am Handy eine **Kaufleiste**, die beim Scrollen unten bleibt.
- **Kauf-Fenster** vor dem Wechsel zu Digistore24 (wie bei Sportunterricht) – erscheint, sobald die Kauflinks eingetragen sind.
- **Muskel-Lexikon:** 112 Muskeln mit Zeichnung, Steckbrief, Video; Suche, Filter nach Körperregion, **Nerven-Schnellwahl** („Welche Muskeln versorgt der N. femoralis?“). Jede Muskelseite verkauft den passenden Band.
- **Lernkarten** (`/lernkarten/`): Karteikarten nach dem Karteikasten-Prinzip und Quiz (Innervation, Ansatz, Ursprung) – Lernstand bleibt auf dem Gerät.
- **Lernplan** (`/lernplan/`): Prüfungsdatum + Themen + Lerntage → Plan mit Wiederholungstagen, abhaken, drucken, als Kalender-Datei (.ics).
- **Rechner** (`/rechner/`): 1RM (Epley/Brzycki), Trainingspuls (Karvonen), Energiebedarf (Mifflin-St Jeor × PAL) – mit Rechenweg und Gesundheitshinweis.
- **Kanal-Wechsler** ganz oben auf beiden Websites (Sportunterricht ↔ Know it) und ein Querverweis im Fuß.

## Livegang (wie bei Sportunterricht)

1. Bei Netlify ein **neues Projekt** anlegen und es **`knowit-anatomie`** nennen → Adresse `https://knowit-anatomie.netlify.app` (kostenlos). Ist der Name vergeben, sag mir den neuen – ich trage ihn ein.
2. Die ZIP-Datei der Website in den Kasten „Drop a folder, .zip“ ziehen.
3. Bei Digistore24 die 7 Bände und die 2 Pakete anlegen, Danke-Seite: `https://knowit-anatomie.netlify.app/danke/`, und mir die 9 Bestell-Links schicken.

## Vor dem Verkauf bitte prüfen

- **Paketpreise sind Vorschläge:** Komplettpaket 79,90 € (statt 131,30 €), Muskel-Atlas-Paket 44,90 € (statt 59,70 €) – in `einstellungen.json` unter `preise` änderbar. Die Paket-Dateien (ZIP mit den PDFs) legst du bei Digistore24 an; nur PDFs hinein (E-Book-Steuersatz).
- **Zahlen auf der Startseite** (4 Mio. Aufrufe, 500 Videos, 120.000 Stunden Lernzeit) stammen von der bisherigen Website – bitte einmal mit YouTube Studio abgleichen (`einstellungen.json` → `zahlen`).
- **Rechtstexte** (Impressum, Datenschutz, AGB) wie gehabt von einer Fachperson prüfen lassen.
