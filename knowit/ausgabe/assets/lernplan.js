// Know it – Lernplan bis zur Prüfung: verteilt die Kapitel der gewählten Bände auf die Lerntage,
// hält Wiederholungstage frei. Abhaken (lokal gespeichert), Drucken, Kalender-Datei (.ics).
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var form = $('#lp-form');
  if (!form) return;
  var DATEN = JSON.parse($('#lp-daten').textContent);
  var BASIS = JSON.parse($('#lp-basis').textContent);
  var SPEICHER = 'ki-lernplan';
  var TAGE = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  var plan = null;

  var iso = function (d) { return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); };
  var lies = function () { try { return JSON.parse(localStorage.getItem(SPEICHER)) || null; } catch (e) { return null; } };
  var schreib = function (x) { try { localStorage.setItem(SPEICHER, JSON.stringify(x)); } catch (e) { /* privat */ } };
  function anzeige(d) { return TAGE[d.getDay()] + ', ' + d.getDate() + '. ' + d.toLocaleDateString('de-AT', { month: 'short' }); }

  function einstellungen() {
    return {
      datum: $('#lp-datum').value, wdh: +$('#lp-wdh').value,
      tage: $$('input[name="lp-tag"]:checked').map(function (x) { return +x.value; }), // 0 = Mo … 6 = So
      baende: $$('input[name="lp-band"]:checked').map(function (x) { return +x.value; })
    };
  }
  function setze(e) {
    $('#lp-datum').value = e.datum; $('#lp-wdh').value = String(e.wdh);
    $$('input[name="lp-tag"]').forEach(function (x) { x.checked = e.tage.indexOf(+x.value) >= 0; });
    $$('input[name="lp-band"]').forEach(function (x) { x.checked = e.baende.indexOf(+x.value) >= 0; });
  }

  function erstellen(e) {
    var pruefung = new Date(e.datum + 'T00:00:00'), heute = new Date(); heute.setHours(0, 0, 0, 0);
    if (isNaN(pruefung) || pruefung <= heute) return { fehler: 'Bitte ein Prüfungsdatum in der Zukunft wählen.' };
    if (!e.baende.length) return { fehler: 'Bitte mindestens ein Thema auswählen.' };
    if (!e.tage.length) return { fehler: 'Bitte mindestens einen Lerntag pro Woche auswählen.' };
    var tage = [];
    for (var d = new Date(heute); d < pruefung; d.setDate(d.getDate() + 1)) {
      if (e.tage.indexOf((d.getDay() + 6) % 7) >= 0) tage.push(new Date(d));
    }
    var wdh = Math.min(e.wdh, Math.max(0, tage.length - 1));
    var lern = tage.slice(0, tage.length - wdh), wiederholen = tage.slice(tage.length - wdh);
    if (!lern.length) return { fehler: 'Bis zur Prüfung bleiben zu wenige Lerntage. Wähle mehr Wochentage oder weniger Wiederholungstage.' };
    var themen = [];
    DATEN.forEach(function (b) { if (e.baende.indexOf(b.b) >= 0) b.k.forEach(function (k) { themen.push({ b: b.b, t: b.t, f: b.f, k: k }); }); });
    var tageListe = lern.map(function (d) { return { d: iso(d), anz: anzeige(d), themen: [] }; });
    // gleichmäßig verteilen: Thema i an Tag ⌊i · Tage / Themen⌋
    themen.forEach(function (th, i) { tageListe[Math.floor(i * lern.length / themen.length)].themen.push(th); });
    wiederholen.forEach(function (d) { tageListe.push({ d: iso(d), anz: anzeige(d), wdh: true, themen: [] }); });
    return { e: e, tage: tageListe, pruefung: anzeige(pruefung), proTag: (themen.length / lern.length) };
  }

  function zeigen() {
    var z = $('#lp-ergebnis');
    $('#lp-bereich').hidden = false;
    if (plan.fehler) { z.innerHTML = '<p class="hinweisbox">' + esc(plan.fehler) + '</p>'; return; }
    var erledigt = (lies() || {}).erledigt || {};
    var zeilen = plan.tage.map(function (t) {
      var inhalt = t.wdh ? '<b>Wiederholung</b> – alle Themen noch einmal durchgehen, <a href="' + BASIS.lernkarten + '">Lernkarten-Quiz</a> machen, offene Fragen klären'
        : t.themen.length ? t.themen.map(function (th) { return '<span class="lp-thema" style="--f:' + th.f + '"><small>Band ' + th.b + '</small> ' + esc(th.k) + (th.b <= 3 ? ' <a href="' + BASIS.lernkarten + '" class="lp-lk">abfragen</a>' : '') + '</span>'; }).join('')
          : '<span class="lp-frei">Puffer – Vorheriges wiederholen</span>';
      return '<li class="lp-tag' + (t.wdh ? ' wdh' : '') + (erledigt[t.d] ? ' fertig' : '') + '"><label><input type="checkbox" data-tag="' + t.d + '"' + (erledigt[t.d] ? ' checked' : '') + '><span class="lp-datum">' + t.anz + '</span></label><div>' + inhalt + '</div></li>';
    }).join('');
    var fertig = plan.tage.filter(function (t) { return erledigt[t.d]; }).length;
    z.innerHTML = '<div class="planer-kopf"><div><p class="oberzeile">Dein Lernplan</p><h2 id="lp-titel" tabindex="-1">Prüfung am ' + plan.pruefung + '</h2>' +
      '<p class="planer-sub">' + plan.tage.length + ' Lerntage · etwa ' + (Math.round(plan.proTag * 10) / 10).toLocaleString('de-AT') + ' Kapitel pro Tag · ' + fertig + ' erledigt</p></div>' +
      '<div class="knopfreihe"><button type="button" class="knopf primaer" id="lp-drucken">Drucken</button><button type="button" class="knopf" id="lp-ics">In den Kalender (.ics)</button></div></div>' +
      (plan.proTag > 3 ? '<p class="hinweisbox">Das sind viele Kapitel pro Tag. Wenn möglich: früher anfangen, mehr Lerntage wählen oder Schwerpunkte setzen.</p>' : '') +
      '<ol class="lp-liste">' + zeilen + '</ol><p class="klein">Abgehakte Tage bleiben auf diesem Gerät gespeichert.</p>';
    $('#lp-druck').innerHTML = '<div class="sb"><h1>Lernplan – Prüfung am ' + plan.pruefung + '</h1><table class="sb-verlauf"><thead><tr><th>✓</th><th>Tag</th><th>Thema</th></tr></thead><tbody>' +
      plan.tage.map(function (t) { return '<tr><td>☐</td><td>' + t.anz + '</td><td>' + (t.wdh ? 'Wiederholung' : t.themen.length ? t.themen.map(function (th) { return 'Band ' + th.b + ': ' + esc(th.k); }).join('<br>') : 'Puffer') + '</td></tr>'; }).join('') +
      '</tbody></table><p class="sb-fuss">Erstellt mit dem Lernplan von Know it – Anatomie und Training</p></div>';
  }

  function ics() {
    var z = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Know it//Lernplan//DE', 'CALSCALE:GREGORIAN'];
    var stempel = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
    var text = function (s) { return s.replace(/\\/g, '\\\\').replace(/;/g, '\;').replace(/,/g, '\\,').replace(/\n/g, '\\n'); };
    plan.tage.forEach(function (t, i) {
      var d = t.d.replace(/-/g, ''), n = new Date(t.d + 'T00:00:00'); n.setDate(n.getDate() + 1);
      var titel = t.wdh ? 'Lernen: Wiederholung' : t.themen.length ? 'Lernen: ' + t.themen.map(function (th) { return th.k.replace(/^\d+ · /, ''); }).join(', ') : 'Lernen: Puffer';
      z.push('BEGIN:VEVENT', 'UID:lernplan-' + d + '-' + i + '@knowit', 'DTSTAMP:' + stempel, 'DTSTART;VALUE=DATE:' + d, 'DTEND;VALUE=DATE:' + iso(n).replace(/-/g, ''),
        'SUMMARY:' + text(titel.slice(0, 120)), 'DESCRIPTION:' + text(t.themen.map(function (th) { return 'Band ' + th.b + ' – ' + th.t + ': ' + th.k; }).join('\n') || 'Alle Themen wiederholen'), 'END:VEVENT');
    });
    z.push('END:VCALENDAR');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([z.join('\r\n') + '\r\n'], { type: 'text/calendar' }));
    a.download = 'Lernplan.ics';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
  }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var e = einstellungen();
    plan = erstellen(e);
    var alt = lies() || {};
    schreib({ e: e, erledigt: alt.e && JSON.stringify(alt.e) === JSON.stringify(e) ? alt.erledigt : {} });
    zeigen();
    $('#lp-bereich').scrollIntoView({ behavior: 'smooth', block: 'start' });
    var h = $('#lp-titel'); if (h) h.focus({ preventScroll: true });
  });
  $('#lp-ergebnis').addEventListener('change', function (ev) {
    var c = ev.target.closest('input[data-tag]');
    if (!c) return;
    var s = lies() || { e: einstellungen(), erledigt: {} };
    s.erledigt = s.erledigt || {};
    if (c.checked) s.erledigt[c.getAttribute('data-tag')] = 1; else delete s.erledigt[c.getAttribute('data-tag')];
    schreib(s);
    c.closest('.lp-tag').classList.toggle('fertig', c.checked);
  });
  $('#lp-ergebnis').addEventListener('click', function (ev) {
    if (ev.target.id === 'lp-drucken') window.print();
    if (ev.target.id === 'lp-ics') ics();
  });

  // Start: gespeicherten Plan wiederherstellen, sonst Prüfung in 4 Wochen vorschlagen
  var gespeichert = lies();
  if (gespeichert && gespeichert.e && new Date(gespeichert.e.datum + 'T00:00:00') > new Date()) {
    setze(gespeichert.e); plan = erstellen(gespeichert.e); zeigen();
  } else {
    var d = new Date(); d.setDate(d.getDate() + 28); $('#lp-datum').value = iso(d);
  }
  $('#lp-datum').min = iso(new Date(Date.now() + 864e5));
})();
