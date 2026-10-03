// Sportunterricht – Stationskarten zum Drucken (4 pro A4-Seite, QR-Code zum Video). Genutzt von Merkliste und Planer.
(function () {
  'use strict';
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var MATERIAL = { ohne: 'Kein Material', standard: 'Standard-Hallenmaterial', tore: 'Tore, Körbe oder Netz', matten: 'Matten & Bänke', geraete: 'Turngeräte', schwimmbad: 'Schwimmbad' };
  var stufe = function (g) { return g.von === g.bis ? g.von + '. Schulstufe' : g.von + '.–' + g.bis + '. Schulstufe'; };

  function karte(g, nr, qrBasis) {
    return '<div class="station" style="--f:' + g.f + '"><div class="station-kopf"><span>Station ' + nr + '</span><span>' + stufe(g) + '</span></div>' +
      '<h2>' + esc(g.n) + '</h2><dl><div><dt>Material</dt><dd>' + esc(g.mt || MATERIAL[g.m] || '') + '</dd></div>' +
      (g.d ? '<div><dt>Spielzeit</dt><dd>' + g.d[0] + '–' + g.d[1] + ' min</dd></div>' : '') + (g.gr ? '<div><dt>Gruppe</dt><dd>' + esc(g.gr) + '</dd></div>' : '') + '</dl>' +
      (g.lz ? '<p><b>Ziel:</b> ' + esc(g.lz) + '</p>' : '') +
      '<div class="station-qr"><img src="' + qrBasis + g.i + '.svg" alt="QR-Code zum Video" width="110" height="110"><span>Video ansehen:<br><b>youtu.be/' + esc(g.i) + '</b></span></div></div>';
  }

  // spiele: Liste von Spiel-Objekten (aus #spiele-daten); liefert Druckseiten mit je 4 Karten
  window.SU_KARTEN = {
    html: function (spiele, qrBasis) {
      var k = spiele.map(function (g, i) { return karte(g, i + 1, qrBasis); });
      var seiten = '';
      for (var s = 0; s < k.length; s += 4) seiten += '<div class="druckseite">' + k.slice(s, s + 4).join('') + '</div>';
      return seiten;
    }
  };
})();
