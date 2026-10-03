// Know it – Muskel-Lexikon: Suche (auch ?q= aus der Startseite) und Filter nach Körperregion.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var feld = $('#m-suche');
  var liste = $('#m-liste');
  if (!feld || !liste) return;
  var norm = function (t) { return (t || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss'); };
  var items = $$('li[data-suche]', liste).map(function (li) { return { li: li, t: norm(li.getAttribute('data-suche')), i: norm(li.getAttribute('data-innerv')), b: li.getAttribute('data-band') }; });
  var band = '', nerv = ''; // nerv gesetzt = nur in der Innervation suchen (Nerven-Schnellwahl)
  function anwenden() {
    var worte = norm(feld.value.trim()).split(/\s+/).filter(Boolean);
    var n = 0;
    items.forEach(function (x) {
      var ok = (!band || x.b === band) && (nerv ? x.i.indexOf(norm(nerv)) >= 0 : worte.every(function (w) { return x.t.indexOf(w) >= 0; }));
      x.li.hidden = !ok;
      if (ok) n++;
    });
    // leere Kapitel und Bände ausblenden
    $$('.m-gruppe', liste).forEach(function (g) { g.hidden = !$$('li[data-suche]:not([hidden])', g).length; });
    $$('.m-band', liste).forEach(function (b) { b.hidden = !$$('li[data-suche]:not([hidden])', b).length; });
    $('#m-treffer').textContent = (n === 1 ? '1 Muskel' : n + ' Muskeln') + (nerv ? (n === 1 ? ' wird' : ' werden') + ' vom ' + nerv + ' innerviert' : '');
    $$('[data-nerv]').forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-nerv') === nerv ? 'true' : 'false'); });
    $('#m-leer').hidden = n > 0;
    var p = new URLSearchParams();
    if (feld.value.trim()) p.set('q', feld.value.trim());
    if (band) p.set('region', band);
    try { history.replaceState(null, '', location.pathname + (p.toString() ? '?' + p : '') + location.hash); } catch (e) { /* egal */ }
  }
  var q = new URLSearchParams(location.search);
  if (q.get('q')) feld.value = q.get('q');
  if (q.get('region')) band = q.get('region');
  $$('.ki-bandwahl button').forEach(function (b) {
    b.setAttribute('aria-pressed', b.getAttribute('data-band') === band ? 'true' : 'false');
    b.addEventListener('click', function () {
      band = b.getAttribute('data-band');
      $$('.ki-bandwahl button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      anwenden();
    });
  });
  // Nerven-Schnellwahl: füllt die Suche, zeigt alle Regionen
  $$('[data-nerv]').forEach(function (b) {
    b.addEventListener('click', function () {
      nerv = nerv === b.getAttribute('data-nerv') ? '' : b.getAttribute('data-nerv');
      feld.value = '';
      band = '';
      $$('.ki-bandwahl button').forEach(function (x) { x.setAttribute('aria-pressed', x.getAttribute('data-band') === '' ? 'true' : 'false'); });
      anwenden();
      $('#m-treffer').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
  var t;
  feld.addEventListener('input', function () { nerv = ''; clearTimeout(t); t = setTimeout(anwenden, 100); });
  if (q.get('q') || q.get('region')) anwenden();
})();
