"""Zusatzseiten für Know it: Lernkarten (Karteikasten + Quiz), Lernplan bis zur Prüfung, Trainings- und Ernährungsrechner.

Alle Fachinhalte stammen aus daten/muskeln.json (Steckbriefe der Muskel-Atlanten). Die Rechner nutzen nur
etablierte, auf der Seite genannte Schätzformeln. Gespeichert wird ausschließlich lokal im Browser.
"""
import json


def lernkartenseite(seite, E, MUSKELN, NACH_BAND, ICON, esc):
    daten = [{'s': m['slug'], 'n': m['name'], 'd': m['deutsch'], 'b': m['band'], 'k': m['kapitel'], 'ki': m['kapitel_id'],
              'u': m['lernen']['ursprung'], 'a': m['lernen']['ansatz'], 'i': m['lernen']['innervation'], 'f': m['funktion']} for m in MUSKELN]
    baende = sorted({m['band'] for m in MUSKELN})

    def inhalt(s):
        bw = '<button type="button" aria-pressed="true" data-band="">Alle</button>' + ''.join(f'<button type="button" aria-pressed="false" data-band="{b}">{esc(NACH_BAND[b]["kurz"])}</button>' for b in baende)
        basis = {'muskeln': s.zu('muskeln/'), 'vorschau': s.zu('muskeln/').endswith('index.html'),
                 'baende': {b: {'t': NACH_BAND[b]['titel'], 'u': s.zu('ebooks/' + NACH_BAND[b]['slug'] + '/'), 'p': NACH_BAND[b]['preis']} for b in baende}}
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Lernkarten</li></ol></nav>
<p class="oberzeile">Lernkarten · kostenlos</p><h1>Muskeln lernen mit Lernkarten</h1>
<p class="einleitung">Ursprung, Ansatz, Innervation und Funktion aller {len(MUSKELN)} Muskeln – als Karteikarten oder als Quiz. Nach dem Karteikasten-Prinzip kommt, was du sicher weißt, seltener dran und was hakt, öfter. Dein Lernstand bleibt auf diesem Gerät.</p>
<div class="lk-steuer">
<div class="stufenwahl ki-bandwahl" role="group" aria-label="Körperregion">{bw}</div>
<label class="inline">Kapitel <select id="lk-kapitel"><option value="">alle Kapitel</option></select></label>
<div class="lk-modus" role="group" aria-label="Lernmodus"><button type="button" aria-pressed="true" data-modus="karten">{ICON['karten']} Karteikarten</button><button type="button" aria-pressed="false" data-modus="quiz">Quiz</button></div>
<label class="inline" id="lk-quizfeld-label" hidden>Gefragt wird <select id="lk-quizfeld"><option value="i">Innervation</option><option value="a">Ansatz</option><option value="u">Ursprung</option></select></label>
</div>
<div class="lk-fortschritt" id="lk-fortschritt" aria-live="polite"></div>
<div class="lk-bereich" id="lk-bereich"><p class="hinweisbox">Die Lernkarten brauchen JavaScript. Alle Inhalte findest du auch im <a href="{s.zu('muskeln/')}">Muskel-Lexikon</a>.</p></div>
<div class="knopfreihe" style="margin-top:14px"><button type="button" class="knopf klein" id="lk-reset">Lernstand dieser Auswahl zurücksetzen</button></div>
<div class="hinweisbox" style="margin-top:22px"><h2 style="font-size:1.4rem">Tipp: Erst verstehen, dann abfragen</h2><p>Schau dir zu jedem Muskel die Zeichnung im Lexikon an: Wo liegt der Ursprung, wo der Ansatz, über welches Gelenk zieht er? Dann ergibt sich die Funktion fast von selbst. Merkhilfen und typische Prüfungsfallen zu jedem Muskel stehen in den <a href="{s.zu('ebooks/muskel-atlas-paket/')}">Muskel-Atlanten</a>.</p></div>
</div></section>
<script type="application/json" id="lk-daten">{json.dumps(daten, ensure_ascii=False, separators=(',', ':')).replace('</', '<' + chr(92) + '/')}</script>
<script type="application/json" id="lk-basis">{json.dumps(basis, ensure_ascii=False)}</script>'''
    seite('lernkarten/', 'Lernkarten Anatomie: Muskeln abfragen (Ursprung, Ansatz, Innervation)', f'Kostenlose Lernkarten und Quiz zu {len(MUSKELN)} Muskeln: Ursprung, Ansatz, Innervation und Funktion abfragen – mit Karteikasten-Prinzip, direkt im Browser.',
          inhalt, aktiv='lernkarten/', skripte=('lernkarten.js',), voller_titel=True)


def lernplanseite(seite, E, PRODUKTE, ICON, esc):
    daten = [{'b': p['band'], 't': p['titel'], 'f': p['farbe'], 'k': [k['titel'] for k in p['kapitel'] if not k['titel'].startswith('Anhang')]} for p in PRODUKTE]

    def inhalt(s):
        boxen = ''.join(f'<label><input type="checkbox" name="lp-band" value="{p["band"]}"{" checked" if p["band"] <= 3 else ""}> Band {p["band"]}: {esc(p["titel"])} <small>({len([k for k in p["kapitel"] if not k["titel"].startswith("Anhang")])} Kapitel)</small></label>' for p in PRODUKTE)
        tage = ''.join(f'<label><input type="checkbox" name="lp-tag" value="{i}"{" checked" if i < 5 else ""}> {t}</label>' for i, t in enumerate(['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']))
        return f'''<section class="abschnitt eng keindruck"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Lernplan</li></ol></nav>
<p class="oberzeile">Lernplan · kostenlos</p><h1>Dein Lernplan bis zur Prüfung</h1>
<p class="einleitung">Prüfungsdatum eingeben, Themen und Lerntage wählen – du bekommst einen Plan, welches Kapitel du an welchem Tag lernst, mit Wiederholungstagen vor der Prüfung. Abhaken, ausdrucken oder in deinen Kalender übernehmen.</p>
<form class="planer-form lp-form" id="lp-form">
<label>Prüfungsdatum<input type="date" id="lp-datum" required></label>
<label>Wiederholungstage vor der Prüfung<select id="lp-wdh"><option>0</option><option>1</option><option selected>2</option><option>3</option><option>5</option><option>7</option></select></label>
<fieldset class="planer-material lp-tage"><legend>An diesen Tagen lerne ich</legend>{tage}</fieldset>
<fieldset class="planer-material lp-baende"><legend>Diese Themen kommen in der Prüfung</legend>{boxen}</fieldset>
<button class="knopf primaer gross" type="submit">{ICON['plan']} Lernplan erstellen</button></form>
</div></section>
<section class="abschnitt eng hell" id="lp-bereich" hidden><div class="wrap"><div id="lp-ergebnis" aria-live="polite"></div></div></section>
<div id="lp-druck" class="nur-druck"></div>
<script type="application/json" id="lp-daten">{json.dumps(daten, ensure_ascii=False)}</script>
<script type="application/json" id="lp-basis">{json.dumps({'lernkarten': s.zu('lernkarten/'), 'ebooks': s.zu('ebooks/')})}</script>'''
    seite('lernplan/', 'Lernplan für die Anatomie-Prüfung erstellen', 'Kostenloser Lernplan-Generator: Prüfungsdatum, Themen und Lerntage wählen – Plan mit Wiederholungstagen, zum Abhaken, Ausdrucken und für den Kalender.',
          inhalt, skripte=('lernplan.js',), voller_titel=True)


def rechnerseite(seite, E, NACH_BAND, ICON, esc):
    def inhalt(s):
        b6, b7 = NACH_BAND[6], NACH_BAND[7]
        return f'''<section class="abschnitt eng"><div class="wrap">
<nav class="brotkrumen" aria-label="Brotkrumen"><ol><li><a href="{s.zu('')}">Start</a></li><li>Rechner</li></ol></nav>
<p class="oberzeile">Rechner · kostenlos</p><h1>Trainings- und Ernährungsrechner</h1>
<p class="einleitung">Drei Schätzformeln, die in Trainingslehre und Ernährung immer wieder vorkommen – mit Rechenweg, damit du sie auch in der Prüfung anwenden kannst.</p>
<p class="hinweisbox klein-hinweis">Die Ergebnisse sind <b>Schätzwerte für gesunde Erwachsene</b> und ersetzen keine ärztliche Untersuchung, Leistungsdiagnostik oder Ernährungsberatung.</p>

<div class="rechner-raster">
<section class="karte rechner" id="einer-rm" aria-labelledby="r1-titel">
<h2 id="r1-titel">{ICON['rechner']} Maximalkraft (1RM) schätzen</h2>
<p>Aus Gewicht und Wiederholungen bis zur Erschöpfung lässt sich das Einer-Wiederholungs-Maximum (1RM) schätzen – ohne Maximalversuch.</p>
<form class="t-felder" onsubmit="return false"><label>Gewicht (kg)<input type="number" id="rm-kg" min="1" max="500" step="0.5" value="60" inputmode="decimal"></label><label>Wiederholungen<input type="number" id="rm-wdh" min="1" max="12" value="8" inputmode="numeric"></label></form>
<div class="rechner-ergebnis" id="rm-ergebnis" aria-live="polite"></div>
<details><summary>Rechenweg</summary><div class="antwort"><p><b>Epley:</b> 1RM = Gewicht × (1 + Wiederholungen ÷ 30)<br><b>Brzycki:</b> 1RM = Gewicht × 36 ÷ (37 − Wiederholungen)</p><p>Beide Formeln sind bis etwa 10 Wiederholungen am genauesten; darüber weichen sie stärker ab. Der Rechner zeigt den Mittelwert und beide Einzelwerte.</p></div></details>
</section>

<section class="karte rechner" id="puls" aria-labelledby="r2-titel">
<h2 id="r2-titel">{ICON['rechner']} Trainingspuls (Karvonen)</h2>
<p>Die Karvonen-Formel berechnet Trainingsbereiche aus der Herzfrequenzreserve – also der Differenz zwischen maximaler Herzfrequenz und Ruhepuls.</p>
<form class="t-felder" onsubmit="return false"><label>Alter (Jahre)<input type="number" id="hf-alter" min="12" max="99" value="25" inputmode="numeric"></label><label>Ruhepuls (/min)<input type="number" id="hf-ruhe" min="30" max="120" value="60" inputmode="numeric"></label>
<label>HFmax, falls gemessen<input type="number" id="hf-max" min="120" max="230" placeholder="leer = Schätzung" inputmode="numeric"></label></form>
<div class="rechner-ergebnis" id="hf-ergebnis" aria-live="polite"></div>
<details><summary>Rechenweg</summary><div class="antwort"><p><b>Trainingspuls</b> = Ruhepuls + (HFmax − Ruhepuls) × Intensität</p><p>Ohne Messung wird die maximale Herzfrequenz mit der Faustformel <b>HFmax = 220 − Alter</b> geschätzt. Sie kann individuell um 10 bis 20 Schläge abweichen – ein gemessener Wert (Belastungstest) ist deutlich genauer.</p></div></details>
</section>

<section class="karte rechner" id="energie" aria-labelledby="r3-titel">
<h2 id="r3-titel">{ICON['rechner']} Energiebedarf schätzen</h2>
<p>Grundumsatz nach der Mifflin-St-Jeor-Formel, multipliziert mit dem PAL-Wert (Physical Activity Level) für den Alltag.</p>
<form class="t-felder" onsubmit="return false">
<label>Geschlecht<select id="en-g"><option value="w">weiblich</option><option value="m">männlich</option></select></label>
<label>Alter (Jahre)<input type="number" id="en-alter" min="15" max="99" value="25" inputmode="numeric"></label>
<label>Gewicht (kg)<input type="number" id="en-kg" min="30" max="250" step="0.5" value="65" inputmode="decimal"></label>
<label>Größe (cm)<input type="number" id="en-cm" min="120" max="230" value="170" inputmode="numeric"></label>
<label style="grid-column:1/-1">Alltag (PAL)<select id="en-pal">
<option value="1.4">überwiegend sitzend, kaum Freizeitbewegung (PAL 1,4)</option>
<option value="1.6" selected>sitzend, zeitweise gehend oder stehend (PAL 1,6)</option>
<option value="1.8">überwiegend gehend oder stehend (PAL 1,8)</option>
<option value="2.0">körperlich anstrengende Arbeit oder sehr viel Sport (PAL 2,0)</option></select></label></form>
<div class="rechner-ergebnis" id="en-ergebnis" aria-live="polite"></div>
<details><summary>Rechenweg</summary><div class="antwort"><p><b>Grundumsatz (Mifflin-St Jeor):</b> 10 × Gewicht (kg) + 6,25 × Größe (cm) − 5 × Alter (Jahre) + 5 (Männer) bzw. − 161 (Frauen).</p><p><b>Gesamtbedarf</b> ≈ Grundumsatz × PAL. Die PAL-Stufen sind gerundete Richtwerte; regelmäßiger Sport erhöht den Wert. Für Kinder, Schwangere, Stillende und bei Erkrankungen gelten andere Werte.</p></div></details>
</section>
</div>

<div class="raster zwei" style="margin-top:26px">
<a class="karte link ki-band-link" href="{s.zu('ebooks/' + b6['slug'] + '/')}" style="--bf:{b6['farbe']}"><img src="{s.zu('assets/bilder/' + b6['cover'])}" alt="" width="70" height="99" loading="lazy"><span><small>Band 6 · {b6['preis']}</small><b>{esc(b6['titel'])}</b><span>Belastungsnormative, Kraft, Ausdauer, Trainingsplanung – mit Diagrammen und Richtwerten.</span></span></a>
<a class="karte link ki-band-link" href="{s.zu('ebooks/' + b7['slug'] + '/')}" style="--bf:{b7['farbe']}"><img src="{s.zu('assets/bilder/' + b7['cover'])}" alt="" width="70" height="99" loading="lazy"><span><small>Band 7 · {b7['preis']}</small><b>{esc(b7['titel'])}</b><span>Energie und Nährstoffe, Körperzusammensetzung, Sporternährung – mit Referenzwerten.</span></span></a>
</div>
</div></section>'''
    seite('rechner/', 'Rechner: 1RM, Trainingspuls (Karvonen), Energiebedarf', 'Kostenlose Rechner mit Rechenweg: Maximalkraft (1RM) nach Epley und Brzycki, Trainingspuls nach Karvonen, Energiebedarf nach Mifflin-St Jeor und PAL.',
          inhalt, aktiv='rechner/', skripte=('rechner.js',), voller_titel=True)
