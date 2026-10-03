// Know it – Lernkarten: Karteikarten nach dem Karteikasten-Prinzip (5 Fächer) und Quiz.
// Inhalte = Steckbriefe aus dem Muskel-Lexikon. Lernstand nur lokal im Browser (localStorage).
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var datenEl = $('#lk-daten');
  if (!datenEl) return;
  var ALLE = JSON.parse(datenEl.textContent);
  var BASIS = JSON.parse($('#lk-basis').textContent);
  var bereich = $('#lk-bereich');
  var SPEICHER = 'ki-lernstand';
  var FELD = { i: 'Innervation', a: 'Ansatz', u: 'Ursprung' };
  var zustand = { band: '', kapitel: '', modus: 'karten', feld: 'i' };
  var aktuell = null, zuletzt = null, punkte = { r: 0, n: 0 };

  function stand() { try { return JSON.parse(localStorage.getItem(SPEICHER)) || {}; } catch (e) { return {}; } }
  function speichern(s) { try { localStorage.setItem(SPEICHER, JSON.stringify(s)); } catch (e) { /* privates Fenster */ } }
  function fach(slug) { return stand()[slug] || 0; } // 0 = neu, 1–5 = Fach im Karteikasten
  function setzeFach(slug, f) { var s = stand(); s[slug] = Math.max(1, Math.min(5, f)); speichern(s); }
  function url(m) { return BASIS.muskeln.replace(/index\.html$/, '') + m.s + '/' + (BASIS.vorschau ? 'index.html' : ''); }
  function auswahl() {
    return ALLE.filter(function (m) { return (!zustand.band || String(m.b) === zustand.band) && (!zustand.kapitel || m.ki === zustand.kapitel); });
  }
  function zufall(l) { return l[Math.floor(Math.random() * l.length)]; }
  function mischen(l) { l = l.slice(); for (var i = l.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = l[i]; l[i] = l[j]; l[j] = t; } return l; }

  // Nächste Karte: bevorzugt niedrige Fächer (Neues und Unsicheres öfter), nie zweimal hintereinander dieselbe
  function naechste() {
    var pool = auswahl();
    if (pool.length > 1) pool = pool.filter(function (m) { return m.s !== zuletzt; });
    var gewichte = pool.map(function (m) { return [6, 5, 4, 2, 1, 0.5][fach(m.s)]; });
    var summe = gewichte.reduce(function (a, b) { return a + b; }, 0), r = Math.random() * summe;
    for (var i = 0; i < pool.length; i++) { r -= gewichte[i]; if (r <= 0) return pool[i]; }
    return pool[pool.length - 1];
  }

  function fortschritt() {
    var pool = auswahl(), neu = 0, lernen = 0, sicher = 0;
    pool.forEach(function (m) { var f = fach(m.s); if (!f) neu++; else if (f >= 4) sicher++; else lernen++; });
    var p = pool.length ? Math.round(sicher / pool.length * 100) : 0;
    $('#lk-fortschritt').innerHTML = '<div class="lk-balken" aria-hidden="true"><i style="width:' + p + '%"></i></div>' +
      '<p><b>' + sicher + '</b> sicher · <b>' + lernen + '</b> im Lernen · <b>' + neu + '</b> neu <span class="klein">(' + pool.length + ' Muskeln in dieser Auswahl)</span>' +
      (zustand.modus === 'quiz' && punkte.n ? ' · Quiz: <b>' + punkte.r + '/' + punkte.n + '</b> richtig' : '') + '</p>';
  }
  function kopf(m) {
    return '<p class="oberzeile">' + esc(m.k) + ' · Fach ' + (fach(m.s) || 'neu') + '</p><h2 id="lk-titel" tabindex="-1">' + esc(m.n) + '</h2><p class="lk-deutsch">' + esc(m.d) + '</p>';
  }
  function antwortHtml(m) {
    return '<dl class="lk-antwort"><div><dt>Ursprung</dt><dd>' + esc(m.u) + '</dd></div><div><dt>Ansatz</dt><dd>' + esc(m.a) + '</dd></div><div><dt>Innervation</dt><dd>' + esc(m.i) + '</dd></div>' +
      '<div><dt>Funktion</dt><dd><ul>' + m.f.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></dd></div></dl>' +
      '<p class="klein"><a href="' + url(m) + '">Zeichnung und Video zum ' + esc(m.n) + '</a> · Merkhilfe und Prüfungsfalle im <a href="' + BASIS.baende[m.b].u + '">E-Book „' + esc(BASIS.baende[m.b].t) + '“</a></p>';
  }

  function karte(m) {
    aktuell = m; zuletzt = m.s;
    bereich.innerHTML = '<div class="lk-karte">' + kopf(m) + '<p class="lk-frage">Ursprung, Ansatz, Innervation, Funktion – weißt du es? Sag es laut oder schreib es auf, dann deck auf.</p>' +
      '<div class="knopfreihe"><button type="button" class="knopf primaer gross" id="lk-auf">Aufdecken</button><button type="button" class="knopf" id="lk-weiter">Überspringen</button></div></div>';
    fortschritt();
  }
  function aufdecken() {
    var m = aktuell;
    bereich.innerHTML = '<div class="lk-karte offen">' + kopf(m) + antwortHtml(m) +
      '<div class="knopfreihe lk-bewertung"><button type="button" class="knopf lk-ja gross" id="lk-ja">✓ Gewusst</button><button type="button" class="knopf lk-nein gross" id="lk-nein">✗ Nochmal üben</button></div></div>';
    $('#lk-ja').focus();
  }

  function quiz() {
    var m = naechste();
    if (!m) { bereich.innerHTML = '<p class="hinweisbox">In dieser Auswahl gibt es keine Muskeln.</p>'; return; }
    aktuell = m; zuletzt = m.s;
    var f = zustand.feld, richtig = m[f];
    // falsche Antworten bevorzugt aus derselben Körperregion – dann sind sie plausibel
    var kandidaten = mischen(ALLE.filter(function (x) { return x.b === m.b && x[f] && x[f] !== richtig; }));
    if (kandidaten.length < 3) kandidaten = kandidaten.concat(mischen(ALLE.filter(function (x) { return x.b !== m.b && x[f] !== richtig; })));
    var falsch = [];
    kandidaten.forEach(function (x) { if (falsch.length < 3 && falsch.indexOf(x[f]) < 0) falsch.push(x[f]); });
    var optionen = mischen([richtig].concat(falsch));
    bereich.innerHTML = '<div class="lk-karte">' + kopf(m) + '<p class="lk-frage">Welche <b>' + FELD[f] + '</b> hat der ' + esc(m.n) + '?</p>' +
      '<div class="lk-optionen" role="group" aria-label="Antwortmöglichkeiten">' + optionen.map(function (o, i) { return '<button type="button" class="lk-option" data-richtig="' + (o === richtig ? 1 : 0) + '"><span>' + 'ABCD'[i] + '</span>' + esc(o) + '</button>'; }).join('') + '</div>' +
      '<div id="lk-rueck" aria-live="polite"></div></div>';
    fortschritt();
  }
  function beantworten(knopf) {
    var ok = knopf.getAttribute('data-richtig') === '1';
    $$('.lk-option', bereich).forEach(function (b) { b.disabled = true; if (b.getAttribute('data-richtig') === '1') b.classList.add('richtig'); });
    if (!ok) knopf.classList.add('falsch');
    punkte.n++; if (ok) punkte.r++;
    setzeFach(aktuell.s, ok ? fach(aktuell.s) + 1 : 1);
    $('#lk-rueck').innerHTML = '<p class="lk-ergebnis ' + (ok ? 'gut' : 'schlecht') + '">' + (ok ? '✓ Richtig!' : '✗ Leider nicht – die richtige Antwort ist markiert.') + '</p>' + antwortHtml(aktuell) +
      '<div class="knopfreihe"><button type="button" class="knopf primaer gross" id="lk-naechste">Nächste Frage</button></div>';
    fortschritt();
    $('#lk-naechste').focus();
  }

  function start() {
    var pool = auswahl();
    if (!pool.length) { bereich.innerHTML = '<p class="hinweisbox">In dieser Auswahl gibt es keine Muskeln.</p>'; fortschritt(); return; }
    if (zustand.modus === 'quiz') quiz(); else karte(naechste());
  }

  // ---------------------------------------------------------------- Steuerung
  function kapitelListe() {
    var sel = $('#lk-kapitel'), gesehen = {};
    sel.innerHTML = '<option value="">alle Kapitel</option>';
    ALLE.forEach(function (m) {
      if ((zustand.band && String(m.b) !== zustand.band) || gesehen[m.ki]) return;
      gesehen[m.ki] = 1;
      var o = document.createElement('option'); o.value = m.ki; o.textContent = m.k; sel.appendChild(o);
    });
    sel.value = zustand.kapitel && gesehen[zustand.kapitel] ? zustand.kapitel : '';
    zustand.kapitel = sel.value;
  }
  $$('.ki-bandwahl button').forEach(function (b) {
    b.addEventListener('click', function () {
      zustand.band = b.getAttribute('data-band');
      $$('.ki-bandwahl button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      kapitelListe(); start();
    });
  });
  $('#lk-kapitel').addEventListener('change', function () { zustand.kapitel = this.value; start(); });
  $$('.lk-modus button').forEach(function (b) {
    b.addEventListener('click', function () {
      zustand.modus = b.getAttribute('data-modus');
      $$('.lk-modus button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      $('#lk-quizfeld-label').hidden = zustand.modus !== 'quiz';
      punkte = { r: 0, n: 0 };
      start();
    });
  });
  $('#lk-quizfeld').addEventListener('change', function () { zustand.feld = this.value; start(); });
  $('#lk-reset').addEventListener('click', function () {
    if (!window.confirm('Lernstand für die aktuelle Auswahl zurücksetzen?')) return;
    var s = stand();
    auswahl().forEach(function (m) { delete s[m.s]; });
    speichern(s); punkte = { r: 0, n: 0 }; start();
  });
  bereich.addEventListener('click', function (e) {
    var b = e.target.closest('button');
    if (!b) return;
    if (b.id === 'lk-auf') aufdecken();
    else if (b.id === 'lk-weiter') { karte(naechste()); $('#lk-auf').focus(); }
    else if (b.id === 'lk-ja' || b.id === 'lk-nein') { setzeFach(aktuell.s, b.id === 'lk-ja' ? fach(aktuell.s) + 1 : 1); karte(naechste()); $('#lk-auf').focus(); }
    else if (b.classList.contains('lk-option')) beantworten(b);
    else if (b.id === 'lk-naechste') { quiz(); var o = $('.lk-option', bereich); if (o) o.focus(); }
  });

  // Direkt mit einem Muskel starten (Link „Diesen Muskel abfragen“ im Lexikon)
  var m = location.hash.match(/muskel=([\w-]+)/);
  var start1 = m && ALLE.filter(function (x) { return x.s === m[1]; })[0];
  if (start1) {
    zustand.band = String(start1.b);
    $$('.ki-bandwahl button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-band') === zustand.band ? 'true' : 'false'); });
  }
  kapitelListe();
  if (start1) { zustand.kapitel = start1.ki; $('#lk-kapitel').value = start1.ki; karte(start1); } else start();
})();
