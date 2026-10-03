// Know it – Rechner: 1RM (Epley, Brzycki), Trainingspuls (Karvonen), Energiebedarf (Mifflin-St Jeor × PAL).
// Nichts wird gespeichert oder gesendet.
(function () {
  'use strict';
  var $ = function (s) { return document.querySelector(s); };
  if (!$('#rm-kg')) return;
  var zahl = function (id) { var v = parseFloat(String($(id).value).replace(',', '.')); return isNaN(v) ? null : v; };
  var de = function (x, n) { return x.toLocaleString('de-AT', { minimumFractionDigits: n || 0, maximumFractionDigits: n || 0 }); };
  var feld = function (titel, wert, extra) { return '<div class="r-wert"><span>' + titel + '</span><b>' + wert + '</b>' + (extra ? '<small>' + extra + '</small>' : '') + '</div>'; };
  var fehler = function (t) { return '<p class="r-fehler">' + t + '</p>'; };

  function einerRM() {
    var kg = zahl('#rm-kg'), w = zahl('#rm-wdh'), z = $('#rm-ergebnis');
    if (!kg || !w || kg <= 0 || w < 1 || w > 12) { z.innerHTML = fehler('Bitte Gewicht und 1 bis 12 Wiederholungen eingeben.'); return; }
    var epley = w === 1 ? kg : kg * (1 + w / 30), brzycki = kg * 36 / (37 - w), mittel = (epley + brzycki) / 2;
    var prozente = [90, 80, 70, 60].map(function (p) { return '<li><b>' + p + ' %</b> ≈ ' + de(Math.round(mittel * p / 100 / 2.5) * 2.5, 1) + ' kg</li>'; }).join('');
    z.innerHTML = '<div class="r-haupt">' + feld('Geschätztes 1RM', de(mittel, 1) + ' kg', 'Epley ' + de(epley, 1) + ' kg · Brzycki ' + de(brzycki, 1) + ' kg') + '</div>' +
      '<p class="klein">Prozent vom 1RM (auf 2,5 kg gerundet):</p><ul class="r-liste">' + prozente + '</ul>';
  }
  function puls() {
    var alter = zahl('#hf-alter'), ruhe = zahl('#hf-ruhe'), max = zahl('#hf-max'), z = $('#hf-ergebnis');
    if (!alter || !ruhe || alter < 12 || alter > 99 || ruhe < 30 || ruhe > 120) { z.innerHTML = fehler('Bitte Alter (12–99) und Ruhepuls (30–120) eingeben.'); return; }
    var geschaetzt = !max;
    if (geschaetzt) max = 220 - alter;
    if (max <= ruhe + 20) { z.innerHTML = fehler('Die maximale Herzfrequenz muss deutlich über dem Ruhepuls liegen.'); return; }
    var reserve = max - ruhe;
    var zeilen = [50, 60, 70, 80, 90].map(function (p) { return '<li><b>' + p + ' %</b> der Reserve: ' + Math.round(ruhe + reserve * p / 100) + '/min</li>'; }).join('');
    z.innerHTML = '<div class="r-haupt">' + feld('HFmax', Math.round(max) + '/min', geschaetzt ? 'geschätzt mit 220 − Alter' : 'gemessen') + feld('Herzfrequenzreserve', Math.round(reserve) + '/min') + '</div><ul class="r-liste">' + zeilen + '</ul>';
  }
  function energie() {
    var g = $('#en-g').value, alter = zahl('#en-alter'), kg = zahl('#en-kg'), cm = zahl('#en-cm'), pal = parseFloat($('#en-pal').value), z = $('#en-ergebnis');
    if (!alter || !kg || !cm || alter < 15 || kg < 30 || cm < 120) { z.innerHTML = fehler('Bitte Alter (ab 15), Gewicht und Größe eingeben.'); return; }
    var gu = 10 * kg + 6.25 * cm - 5 * alter + (g === 'm' ? 5 : -161);
    z.innerHTML = '<div class="r-haupt">' + feld('Grundumsatz', de(Math.round(gu / 10) * 10) + ' kcal/Tag', 'Mifflin-St Jeor') + feld('Gesamtbedarf', de(Math.round(gu * pal / 10) * 10) + ' kcal/Tag', '× PAL ' + de(pal, 1)) + '</div>' +
      '<p class="klein">Das sind etwa ' + de(Math.round(gu * pal * 4.184 / 100) / 10, 1) + ' MJ pro Tag (1 kcal = 4,184 kJ).</p>';
  }
  [['#einer-rm', einerRM], ['#puls', puls], ['#energie', energie]].forEach(function (x) {
    var box = $(x[0]);
    box.addEventListener('input', x[1]);
    box.addEventListener('change', x[1]);
    x[1]();
  });
})();
