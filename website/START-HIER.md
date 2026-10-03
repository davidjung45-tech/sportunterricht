# Sportunterricht – Start hier

Alles, was du brauchst, um Website, E-Book-Shop und App online zu bringen. Die Reihenfolge unten ist die, in der es am wenigsten Arbeit macht.

## Neu (Oktober 2026) – Raumplaner, Bewegte Pause, Spiel der Woche

- **Raumplaner** (`/raumplaner/`): Halle wählen (27 × 15, 44 × 22, 45 × 27 m, Klassenzimmer oder eigene Maße), 22 Geräte und Planungssymbole antippen oder in die Halle ziehen, verschieben, drehen, kopieren, zum Löschen hinausziehen. Rückgängig, Vorlagen (Zirkel, Gerätelandschaft, zwei Spielfelder), Materialliste mit automatischer Zählung, Druck auf ein A4-Querblatt, Export als Bild (PNG) und Link zum Teilen. Gerätemaße sind typische Richtwerte.
- **Bewegte Pause** (`/bewegte-pause/`): Spiel ganz ohne Material aus dem Kanal mit Video und 3-/5-/10-Minuten-Timer; „wenig Platz“ blendet Fang-, Lauf- und Turnspiele aus.
- **Spiel der Woche** auf der Startseite: wechselt jeden Montag automatisch (im Browser berechnet – kein Neubau nötig); jedes der 155 Spiele kommt dran, bevor sich eines wiederholt.
- **Planer**: „Stationskarten drucken“ (die Spiele der Stunde als Karten mit QR-Code) und „Alle merken“.

## Neu (Oktober 2026) – Werkzeuge für Lehrkräfte und Studierende

- **Stundenplaner** (`/planer/`): Schulstufe, Dauer (45/50/90/100 min), Schwerpunkt und Hallenausstattung wählen → fertige Stunde aus den 155 Spielen der Praxis-Reihe, mit Zeitleiste, Lernzielen und Video zu jedem Spiel. Jedes Spiel lässt sich austauschen; die Zeiten ergeben immer genau die Stundendauer (inkl. Einstieg, Puffer, Ausklang). „Stundenbild drucken“ liefert eine A4-Verlaufsplanung fürs Praktikum, „Link kopieren“ einen Link genau zu dieser Stunde. Gibt es für eine Schulstufe zu wenige Spiele (11.–13.), weicht der Planer um höchstens zwei Stufen aus und sagt das dazu.
- **Werkzeuge für die Halle** (`/werkzeuge/`): Countdown und Zirkel-/Intervalltimer (Tabata, Stationen, Runden) mit Signalton, Vibration, Vollbild und ohne dass der Bildschirm ausgeht; faire Teameinteilung mit Leibchenfarben; Punktetafel für 2–4 Teams; Würfel, Münze, Zahl und Name ziehen ohne Wiederholung.
- **Merkliste** (♥ oben rechts): Spiele merken – im Lexikon, auf der Startseite und im Planer – und als **Stationskarten** drucken (4 pro A4-Seite, QR-Code führt direkt zum Video).
- Datenschutz: Alles läuft im Browser. Namen, Punkte und Merkliste bleiben nur auf dem jeweiligen Gerät; Namen werden nur gespeichert, wenn man das ausdrücklich anhakt.

## Neu (Oktober 2026)

- **Videos auf der Startseite:** Die 6 meistgesehenen Spiele mit Anleitung laufen direkt auf der Startseite. Unter jedem Video steht „Video lädt nicht? Direkt auf YouTube ansehen“ – falls ein Werbeblocker oder das Schulnetz YouTube sperrt.
- **Videos in der Vorschau:** Wenn du die Website per Doppelklick öffnest (`vorschau/index.html`), öffnen Videos jetzt YouTube in einem neuen Tab. Vorher kam dort YouTube-„Fehler 153“, weil eine lokal geöffnete Datei keine Absender-Adresse hat. Auf der echten Domain laufen die Videos direkt auf der Seite.
- **Kauf-Fenster:** „Jetzt kaufen“ zeigt zuerst eine kurze Zusammenfassung (Produkt, Preis, was du bekommst, Hinweis zum Widerrufsrecht) und führt dann zu Digistore24. Es erscheint, sobald der Kauflink in `einstellungen.json` steht.
- **404-Seite repariert:** Die Seite „Nicht gefunden“ hatte vorher kein Design und keine funktionierenden Links.
- **Ohne App-Ordner baubar:** Fehlt `sportunterricht-app-v2`, steht unter `/app/` eine Hinweisseite, die App-Knöpfe sind ausgeblendet und `/pro/` wird nicht gebaut. Sobald der App-Ordner wieder neben `website/` liegt, ist alles automatisch wieder da.
- **Ohne Excel baubar:** Fehlt die Stammdaten-Excel, kommen die Texte aus den `inhalt.md`-Dateien der Bände.

## Was ist wo?

| Ordner / Datei | Wofür |
|---|---|
| `sportunterricht-app-v2/data/Sportunterricht_Stammdaten.xlsx` | **Die eine Datei für Korrekturen.** Schulstufen, Stundenteile, Spielzeiten, Material, Texte aller Spiele. Gilt für App, Website und E-Books. |
| `website/ausgabe/` | Die fertige Website zum Hochladen (inkl. App unter `/app/` und Lizenzprüfung). |
| `website/einstellungen.json` | Die einzige Datei, die du für die Website ausfüllst: Domain, Impressum, Kauflinks, Newsletter. |
| `website/verkauf/` | Die PDFs zum Hochladen bei Digistore24 (Einzelbände, Komplettpaket, Schullizenz). **Nicht** auf die Website legen. |
| `website/youtube-beschreibungen.csv` | Fertige Textbausteine für deine Videobeschreibungen und angepinnten Kommentare. |
| `website/vorschau/index.html` | Die Website zum Anschauen am Laptop (Doppelklick). |
| `ebooks/ausgabe/` | Alle PDFs inkl. Leseproben, Gratis-PDF, Jahresplaner und Cover. |
| `ebooks/*/pruefliste.md` | Die Stellen, die du vor dem Verkauf fachlich gegenlesen solltest. |
| `sportunterricht-app-v2/` | Quellcode der App (für spätere Änderungen). |

## 1. Fehler korrigieren (z. B. „Dirigent“ in der 12. Schulstufe)

1. `Sportunterricht_Stammdaten.xlsx` öffnen (liegt in `sportunterricht-app-v2/data/`, eine Kopie bekommst du auch direkt im Chat), Blatt **Videos**.
2. Spiel suchen (Strg+F), `Stufe_von` / `Stufe_bis` ändern, bei Bedarf `Aufwärmen` / `Hauptteil` / `Abschluss` auf `ja` oder `nein` setzen.
3. `Stufe_Quelle` auf `DJ` und `Geprüft` auf `ja` setzen – die Zeile wird grün. So siehst du, was schon kontrolliert ist.
4. Datei speichern und mir schicken – ich baue App, Website und E-Books neu. (Selbst neu bauen geht auch, siehe ganz unten.)

**Der Dirigent ist bereits korrigiert** (1.–8. Schulstufe). Außerdem hält sich die App jetzt streng an die Schulstufen: Ein Spiel für die 1.–8. wird der 12. Schulstufe nie mehr vorgeschlagen. Nur wenn es für eine Stufe zu wenige Spiele gibt, weicht sie um höchstens zwei Stufen aus und sagt das dazu.

**Kolleg:innen helfen mit:** In der App steht bei jedem Spiel „Passt etwas nicht? Rückmelden“. Die Meldungen sammeln sich unter *Meine → Einstellungen → Rückmeldungen* und lassen sich als Tabelle kopieren und direkt in die Excel einfügen.

## 2. Werbefrei für zahlende Kund:innen

YouTube zeigt bei monetarisierten Videos **immer** Werbung – auch eingebettet auf deiner Website (auch im datensparsamen Modus). Abschalten geht nur, indem du die Monetarisierung des Videos ausschaltest. Deshalb:

- **Auf YouTube bleibt alles wie es ist** und verdient weiter.
- **Für Pro-Kund:innen** lädst du dieselben Videos zusätzlich bei **Bunny Stream** (oder Vimeo) hoch. Die Adresse trägst du in der Excel-Spalte `Werbefreie_Video_URL` ein. Die App spielt dann für Pro dieses Video ab, für alle anderen weiter YouTube.
- Kosten bei Bunny Stream: rund 1 Cent pro GB Speicher und 1 Cent pro GB Auslieferung in Europa, mindestens 1 $ im Monat. Für ein paar hundert Pro-Kund:innen sind das wenige Euro im Monat.
- Tipp: Fang mit den 50 Videos der Spielesammlung an – die werden am meisten angesehen.

## 3. Livegang in 7 Schritten

**Schritt 1 – Domain.** Eine kurze Domain reservieren (z. B. über world4you, easyname oder direkt bei Netlify).

**Schritt 2 – Digistore24.** Konto anlegen (kostenlos, 7,9 % + 1 € pro Verkauf). Produkte anlegen:

| Produkt | Preis | Datei aus `website/verkauf/` |
|---|---|---|
| Band 1 – 50 Spiele | 14,90 € | `einzeln/Band1-spielesammlung.pdf` |
| Band 2 – Aufwärmen | 9,90 € | `einzeln/Band2-aufwaermen.pdf` |
| Band 3 – Turnen | 14,90 € | `einzeln/Band3-turnen.pdf` |
| Band 4 – Fitness | 12,90 € | `einzeln/Band4-fitness.pdf` |
| Band 5 – Praktikums-Kit | 19,90 € | `einzeln/Band5-praktikum.pdf` |
| Band 6 – Alle dabei, alle sicher | 24,90 € | `einzeln/Band6-alle-dabei.pdf` |
| Komplettpaket (alle 6 Bände + Jahresplaner) | 59,90 € | `Komplettpaket-Sportunterricht.zip` |
| App Pro Jahr (Abo) | 29,90 €/Jahr | Lizenzschlüssel automatisch |
| App Pro Monat (Abo) | 3,99 €/Monat | Lizenzschlüssel automatisch |
| Praktikums-Pass | 9,90 € einmalig | Lizenzschlüssel automatisch |

Bei den drei Pro-Produkten in Digistore24 die automatische Lizenzschlüssel-Auslieferung aktivieren. Die Schullizenz verkaufst du am einfachsten per Angebot und Rechnung (Datei `Schullizenz-Sportunterricht.zip`).

**Schritt 3 – einstellungen.json ausfüllen.** Domain, Name, Anschrift, E-Mail und die zehn Kauflinks von Digistore24 (`https://www.digistore24.com/product/…`). Leere Felder zeigen auf der Website „Bald erhältlich“ statt eines kaputten Knopfs.

**Schritt 4 – App auf „echte“ Lizenzen umstellen.** In `sportunterricht-app-v2/src/config.js`: `proModus: 'digistore'` und `kontaktEmail` eintragen. (Oder mir schicken, ich mache das.)

**Schritt 5 – Neu bauen und hochladen.** Kostenloses Netlify-Konto. Den Ordner `website/ausgabe/` per Netlify CLI (`netlify deploy --prod`) oder über ein Git-Repository veröffentlichen – nur so wird auch die Lizenzprüfung (`netlify/functions/lizenz.mjs`) mit hochgeladen. Für einen ersten Test ohne Kauf reicht Drag & Drop auf app.netlify.com/drop.

**Schritt 6 – Lizenzprüfung verbinden.** In Digistore24 einen API-Schlüssel nur mit Leserechten erzeugen. In Netlify unter *Site configuration → Environment variables* eintragen: `DS_API_KEY` (der Schlüssel) und `DS_PRODUKT_IDS` (die Produkt-IDs der drei Pro-Produkte, mit Komma getrennt). Kund:innen schalten Pro dann mit **Bestellnummer + Lizenzschlüssel** aus der Kaufbestätigung frei; beendete Abos und Erstattungen erkennt die App automatisch bei der nächsten Prüfung (alle 14 Tage).

**Schritt 7 – Reichweite.** Die Textbausteine aus `youtube-beschreibungen.csv` in die Beschreibungen deiner 30 meistgesehenen Videos kopieren (ganz oben) und als angepinnten Kommentar setzen. Die Sitemap (`/sitemap.xml`) in der Google Search Console einreichen. Den Aushang (`/downloads/aushang-lehrerzimmer.pdf`) ins eigene Lehrerzimmer hängen.

## Vor dem Verkauf: bitte prüfen

- [ ] Die **Prüflisten** in `ebooks/aufwaermen`, `ebooks/turnen`, `ebooks/fitness` durchgehen – vor allem Hilfestellung und Sicherheit bei Band 3.
- [ ] **Band 6** einmal ganz lesen: Rechtshinweise (Stand 2026/27) mit den aktuellen Vorgaben deiner Bildungsdirektion abgleichen, Erste-Hilfe-Passagen und die „Aus meiner Praxis“-Kästen auf deine eigenen Erfahrungen anpassen. Die Texte stehen in `ebooks/alle-dabei/kapitel-1.md` bis `kapitel-9.md`.
- [ ] **Impressum, Datenschutz, AGB** sind sorgfältige Vorlagen, gelb markierte Stellen ausfüllen und einmal von einer Fachperson prüfen lassen (z. B. WKO-Gründerservice).
- [ ] **Steuer:** Digistore24 ist Wiederverkäufer – du bekommst eine Gutschrift und verkaufst streng genommen an Digistore24. Wie das bei dir als Lehrer mit Nebeneinkünften zu versteuern ist (Einkommensteuer, Kleinunternehmerregelung), einmal mit der Steuerberatung klären.
- [ ] **Nebenbeschäftigung:** Als Bundes- bzw. Landeslehrer ggf. eine erwerbsmäßige Nebenbeschäftigung der Dienstbehörde melden.
- [ ] **Uni-Lehrauftrag:** Das Praktikums-Kit nicht in deinen eigenen Lehrveranstaltungen bewerben oder verpflichtend machen – das wäre ein Interessenkonflikt. Auf den Kanal und die Gratis-Inhalte hinweisen ist unproblematisch.
- [ ] Schullizenz-Preise (149 € / 249 €) und Workshop-Angebot in `einstellungen.json` bzw. auf der Seite „Für Schulen“ an deine Vorstellungen anpassen.

## Selbst neu bauen (optional)

Voraussetzungen: Node.js und Python 3 (mit `weasyprint`, `openpyxl`, `qrcode`, `markdown`, `Pillow`).

```
cd sportunterricht-app-v2 && npm install && npm run build   # App aus der Excel
cd ../ebooks && python3 werkzeug/pdf.py --final             # E-Books
cd ../website && python3 bauen.py                           # Website + Verkaufsdateien
```
