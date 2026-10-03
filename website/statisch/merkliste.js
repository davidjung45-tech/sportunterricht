// Sportunterricht – Merkliste und Stationskarten (4 pro A4-Seite, mit QR-Code zum Video).
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var datenEl = $('#spiele-daten');
  if (!datenEl || !window.SU || !window.SU_KARTEN) return;
  var NACH_ID = {};
  JSON.parse(datenEl.textContent).forEach(function (g) { NACH_ID[g.i] = g; });
  var BASIS = JSON.parse($('#seiten-basis').textContent);
  var stufe = function (g) { return g.von === g.bis ? g.von + '. Schulstufe' : g.von + '.–' + g.bis + '. Schulstufe'; };
  var url = function (g) { return BASIS.spiele + g.s + '/' + (BASIS.vorschau ? 'index.html' : ''); };

  function zeige() {
    var ids = window.SU.merkLies().filter(function (i) { return NACH_ID[i]; });
    $('#merk-leer').hidden = ids.length > 0;
    $('#merk-inhalt').hidden = !ids.length;
    $('#merk-liste').innerHTML = ids.map(function (i) {
      var g = NACH_ID[i];
      return '<li><a href="' + url(g) + '"><span class="mini" style="background:' + g.f + '" aria-hidden="true">' + g.von + '–' + g.bis + '<small>Stufe</small></span><span><b>' + esc(g.n) + '</b><small>' + stufe(g) + ' · ' + esc(g.ph.join(', ')) + (g.d ? ' · ' + g.d[0] + '–' + g.d[1] + ' min' : '') + '</small></span></a>' +
        '<button type="button" class="merk-weg" data-weg="' + esc(i) + '" aria-label="„' + esc(g.n) + '“ von der Merkliste entfernen">✕</button></li>';
    }).join('');
    $('#karten-druck').innerHTML = window.SU_KARTEN.html(ids.map(function (i) { return NACH_ID[i]; }), BASIS.qr);
  }
  document.addEventListener('su-merkliste', zeige);
  $('#merk-liste').addEventListener('click', function (e) {
    var b = e.target.closest('[data-weg]');
    if (!b) return;
    var l = window.SU.merkLies(), i = l.indexOf(b.getAttribute('data-weg'));
    if (i >= 0) l.splice(i, 1);
    window.SU.merkSchreib(l);
    zeige();
    var naechster = $('#merk-liste [data-weg]') || $('#merk-leer a');
    if (naechster) naechster.focus();
  });
  $('#merk-drucken').addEventListener('click', function () { window.print(); });
  $('#merk-leeren').addEventListener('click', function () {
    if (window.confirm('Alle Spiele von der Merkliste entfernen?')) { window.SU.merkSchreib([]); zeige(); }
  });
  zeige();
})();
