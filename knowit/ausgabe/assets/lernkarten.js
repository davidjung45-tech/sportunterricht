// Know it – Online-Lernkarten im Stil der Druckvorlagen.
// Vorderseite: Abbildung + Fragen. Umdrehen: nummerierte Antworten. Lernstand nur lokal im Browser.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var datenEl = $('#lk2-daten');
  if (!datenEl) return;
  var ALLE = JSON.parse(datenEl.textContent);
  var BASIS = JSON.parse($('#lk2-basis').textContent);
  var bereich = $('#lk2-bereich');
  var SPEICHER = 'ki-karten';
  var zustand = { band: String(ALLE[0].b), reihe: [], pos: 0, offen: false, umgedreht: false };

  function stand() { try { return JSON.parse(localStorage.getItem(SPEICHER)) || {}; } catch (e) { return {}; } }
  function merke(id, wert) { var s = stand(); s[id] = wert; try { localStorage.setItem(SPEICHER, JSON.stringify(s)); } catch (e) { /* privates Fenster */ } }
  function muskelUrl(slug) { return BASIS.muskeln.replace(/index\.html$/, '') + slug + '/' + (BASIS.vorschau ? 'index.html' : ''); }
  function nr2(n) { return (n < 10 ? '0' : '') + n; }

  function karten() { return ALLE.filter(function (k) { return String(k.b) === zustand.band; }); }
  function neueReihe(mischen) {
    var s = stand();
    var l = karten().filter(function (k) { return !zustand.offen || s[k.id] !== 'ja'; });
    if (mischen) for (var i = l.length - 1; i > 0; i--) { var j = Math.floor(Math.random() * (i + 1)); var t = l[i]; l[i] = l[j]; l[j] = t; }
    zustand.reihe = l; zustand.pos = 0;
  }

  function anzeigeStand() {
    var s = stand(), alle = karten(), ja = 0, nein = 0;
    alle.forEach(function (k) { if (s[k.id] === 'ja') ja++; else if (s[k.id] === 'nein') nein++; });
    var p = alle.length ? Math.round(ja / alle.length * 100) : 0;
    $('#lk2-stand').innerHTML = '<span class="lk2-balken" aria-hidden="true"><i style="width:' + p + '%"></i></span>' +
      '<b>' + ja + '</b> von ' + alle.length + ' gewusst' + (nein ? ' · <b>' + nein + '</b> üben' : '');
  }

  function karteHtml(k) {
    var b = BASIS.baende[k.b], farbe = b.f;
    var kopf = function (art) {
      return '<div class="lk2-kopf" style="background:' + farbe + '"><span>BAND ' + k.b + ' · KARTE ' + nr2(k.nr) + '</span><span>' + art + '</span></div>' +
        '<h2 class="lk2-titel">' + esc(k.t) + '</h2>' + (k.ut ? '<p class="lk2-unter">' + esc(k.ut) + '</p>' : '');
    };
    var vorn = '<div class="lk2-seite lk2-vorn" aria-hidden="' + (zustand.umgedreht ? 'true' : 'false') + '">' + kopf('FRAGEN') +
      '<div class="lk2-koerper' + (k.img ? '' : ' ohne-bild') + '">' + (k.img ? '<div class="lk2-bild"><img src="' + esc(k.img) + '" alt="Abbildung: ' + esc(k.t) + '" loading="lazy"></div>' : '') +
      '<ol class="lk2-fragen">' + k.q.map(function (q) { return '<li>' + esc(q) + '</li>'; }).join('') + '</ol></div>' +
      '<div class="lk2-fuss"><span>' + (k.img ? 'Benenne, was du erkennst.' : 'Nenne den Richtwert!') + '</span>' + (k.s ? '<span>Vollband S. ' + k.s + '</span>' : '<span>' + esc(b.k) + '</span>') + '</div></div>';
    var hinten = '<div class="lk2-seite lk2-hinten" aria-hidden="' + (zustand.umgedreht ? 'false' : 'true') + '">' + kopf('ANTWORTEN') +
      '<ol class="lk2-antworten" style="--bf:' + farbe + '">' + k.a.map(function (a, i) { return '<li><span class="lk2-frage-klein">' + esc(k.q[i]) + '</span><b>' + esc(a) + '</b></li>'; }).join('') + '</ol>' +
      (k.f ? '<details class="lk2-fakten"><summary>Mehr wissen</summary><p>' + esc(k.f) + '</p></details>' : '') +
      '<div class="lk2-fuss"><span>' + (k.s ? 'Erkläre die Antworten anhand von Band ' + k.b + ', Seite ' + k.s + '.' : 'Ausführlich in Band ' + k.b + '.') + '</span>' +
      '<span>' + (k.m ? '<a href="' + muskelUrl(k.m) + '">Im Lexikon</a> · ' : '') + '<a href="' + b.u + '">' + esc(b.t) + '</a></span></div></div>';
    return '<div class="lk2-karte' + (zustand.umgedreht ? ' umgedreht' : '') + '" style="--bf:' + farbe + '"><div class="lk2-innen">' + vorn + hinten + '</div></div>';
  }

  function zeigen(fokus) {
    anzeigeStand();
    var k = zustand.reihe[zustand.pos];
    if (!k) {
      bereich.innerHTML = '<div class="hinweisbox lk2-fertig"><h2>Geschafft!</h2><p>' + (zustand.offen ? 'Alle Karten dieses Bandes sind als „gewusst“ markiert.' : 'Keine Karten in dieser Auswahl.') + '</p>' +
        '<div class="knopfreihe"><button type="button" class="knopf primaer" data-aktion="alle">Alle Karten nochmal</button><button type="button" class="knopf" data-aktion="reset">Lernstand dieses Bandes löschen</button></div></div>';
      return;
    }
    var s = stand()[k.id];
    bereich.innerHTML = karteHtml(k) +
      '<div class="lk2-steuer">' +
      '<button type="button" class="knopf" data-aktion="zurueck"' + (zustand.pos ? '' : ' disabled') + ' aria-label="Vorige Karte">←</button>' +
      '<span class="lk2-zaehler">' + (zustand.pos + 1) + ' / ' + zustand.reihe.length + (s === 'ja' ? ' · <span class="ok">✓ gewusst</span>' : s === 'nein' ? ' · <span class="ueben">übe ich noch</span>' : '') + '</span>' +
      '<button type="button" class="knopf" data-aktion="weiter" aria-label="Nächste Karte">→</button></div>' +
      '<div class="lk2-aktion">' + (zustand.umgedreht
        ? '<button type="button" class="knopf gross lk2-ja" data-aktion="ja">✓ Gewusst</button><button type="button" class="knopf gross lk2-nein" data-aktion="nein">✗ Nochmal üben</button>'
        : '<button type="button" class="knopf primaer gross" data-aktion="umdrehen">Umdrehen</button>') + '</div>';
    if (fokus) { var f = $('[data-aktion="' + fokus + '"]', bereich) || $('[data-aktion]', bereich); if (f) f.focus({ preventScroll: true }); }
  }

  function umdrehen() { zustand.umgedreht = !zustand.umgedreht; zeigen(zustand.umgedreht ? 'ja' : 'umdrehen'); }
  function blaettern(d) { var n = zustand.pos + d; if (n < 0) return; zustand.pos = Math.min(n, zustand.reihe.length); zustand.umgedreht = false; zeigen(d > 0 ? 'umdrehen' : 'zurueck'); }
  function bewerten(w) { var k = zustand.reihe[zustand.pos]; if (k) merke(k.id, w); blaettern(1); }

  bereich.addEventListener('click', function (e) {
    var b = e.target.closest('[data-aktion]');
    if (!b) { if (e.target.closest('.lk2-karte') && !e.target.closest('a, summary, details')) umdrehen(); return; }
    var a = b.getAttribute('data-aktion');
    if (a === 'umdrehen') umdrehen();
    else if (a === 'weiter') blaettern(1);
    else if (a === 'zurueck') blaettern(-1);
    else if (a === 'ja' || a === 'nein') bewerten(a);
    else if (a === 'alle') { zustand.offen = false; $('#lk2-offen').checked = false; neueReihe(false); zeigen('umdrehen'); }
    else if (a === 'reset') { var s = stand(); karten().forEach(function (k) { delete s[k.id]; }); try { localStorage.setItem(SPEICHER, JSON.stringify(s)); } catch (x) { /* egal */ } neueReihe(false); zeigen('umdrehen'); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.target.closest && e.target.closest('input, select, textarea') || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === ' ' && !(e.target.closest && e.target.closest('button, a, summary'))) { e.preventDefault(); umdrehen(); }
    else if (e.key === 'ArrowRight') blaettern(1);
    else if (e.key === 'ArrowLeft') blaettern(-1);
    else if ((e.key === 'j' || e.key === 'J') && zustand.umgedreht) bewerten('ja');
    else if ((e.key === 'n' || e.key === 'N') && zustand.umgedreht) bewerten('nein');
  });

  function bandWaehlen(b) {
    zustand.band = String(b); zustand.umgedreht = false;
    $$('.lk2-baende button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-band') === zustand.band ? 'true' : 'false'); });
    neueReihe(false);
  }
  $$('.lk2-baende button').forEach(function (x) { x.addEventListener('click', function () { bandWaehlen(x.getAttribute('data-band')); zeigen(); }); });
  $('#lk2-offen').addEventListener('change', function () { zustand.offen = this.checked; zustand.umgedreht = false; neueReihe(false); zeigen(); });
  $('#lk2-mischen').addEventListener('click', function () { zustand.umgedreht = false; neueReihe(true); zeigen(); });

  // Direktlink: #muskel=iliopsoas (aus dem Lexikon) oder #band=2
  var h = location.hash, m = h.match(/muskel=([\w-]+)/), bd = h.match(/band=(\d)/);
  var start = m && ALLE.filter(function (k) { return k.m === m[1]; })[0];
  if (start) { bandWaehlen(start.b); zustand.pos = Math.max(0, zustand.reihe.indexOf(start)); }
  else if (bd && BASIS.baende[bd[1]]) bandWaehlen(bd[1]);
  else bandWaehlen(zustand.band);
  zeigen();
})();
