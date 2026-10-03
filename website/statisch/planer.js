// Sportunterricht – Stundenplaner. Läuft komplett im Browser, nichts wird gespeichert oder gesendet.
// Die Stunde steht in der Adresse (#…) – dadurch lässt sie sich teilen und als Lesezeichen speichern.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };

  var form = $('#planer-form');
  var datenEl = $('#spiele-daten');
  if (!form || !datenEl) return;
  var DATEN = JSON.parse(datenEl.textContent);
  var BASIS = JSON.parse($('#seiten-basis').textContent);
  var NACH_ID = {};
  DATEN.forEach(function (g) { NACH_ID[g.i] = g; });
  var POOL = DATEN.filter(function (g) { return g.a && g.d; }); // nur Spiele mit ausgearbeiteter Anleitung und Spielzeit
  var bereich = $('#planer-bereich');
  var ziel = $('#planer-ergebnis');
  var druck = $('#stundenbild');

  var PHASE = {
    E: { name: 'Einstieg', farbe: '#8a6200' },
    A: { name: 'Aufwärmen', farbe: '#c8402a' },
    H: { name: 'Hauptteil', farbe: '#1f5bd8' },
    S: { name: 'Abschluss', farbe: '#167a4b' },
    R: { name: 'Ausklang', farbe: '#0f6d7a' },
    P: { name: 'Puffer', farbe: '#56645d' }
  };
  var PHASE_NAME = { A: 'Aufwärmen', H: 'Hauptteil', S: 'Abschluss' };
  var FEST = {
    E: { titel: 'Begrüßung und Stundenziel', text: 'Kurz begrüßen, Ziel der Stunde nennen, Organisation klären: Aufstellung, Material, Sicherheitsregeln.' },
    R: { titel: 'Ausklang und Reflexion', text: 'Was hat gut geklappt? Was nehmen wir mit? Gemeinsam aufräumen und verabschieden.' },
    P: { titel: 'Puffer für Übergänge', text: 'Zeit für Erklären, Gruppenwechsel, Trinkpause sowie Auf- und Abbau – erfahrungsgemäß wird sie gebraucht.' }
  };

  var plan = null; // { e: Einstellungen, bloecke: [{p, id?, d}] }

  function spielUrl(g) { return BASIS.spiele + g.s + '/' + (BASIS.vorschau ? 'index.html' : ''); }
  function buchUrl(slug) { return BASIS.ebooks + slug + '/' + (BASIS.vorschau ? 'index.html' : ''); }

  // ---------------------------------------------------------------- Einstellungen
  function leseForm() {
    return {
      stufe: +$('#p-stufe').value,
      dauer: +$('#p-dauer').value,
      thema: $('#p-thema').value,
      mat: $$('input[name="mat"]:checked', form).map(function (x) { return x.value; }),
      ohne: $('#p-ohne').checked
    };
  }
  function setzeForm(e) {
    $('#p-stufe').value = e.stufe;
    $('#p-dauer').value = e.dauer;
    $('#p-thema').value = e.thema || '';
    $$('input[name="mat"]', form).forEach(function (x) { x.checked = e.mat.indexOf(x.value) >= 0; });
    $('#p-ohne').checked = !!e.ohne;
  }
  function passt(g, e) {
    var w = e.weit || 0; // Ausweichen um höchstens zwei Schulstufen, wenn es zu wenige Spiele gibt
    if (e.stufe < g.von - w || e.stufe > g.bis + w) return false;
    if (e.ohne) return g.m === 'ohne';
    return g.m === 'ohne' || g.m === 'standard' || e.mat.indexOf(g.m) >= 0;
  }
  function kandidaten(e, phase, ausser) {
    return POOL.filter(function (g) { return passt(g, e) && g.ph.indexOf(PHASE_NAME[phase]) >= 0 && ausser.indexOf(g.i) < 0; });
  }
  // Zufall mit Gewicht: Schwerpunkt-Thema zählt stark, Beliebtheit leicht
  function ziehe(liste, e) {
    if (!liste.length) return null;
    var gew = liste.map(function (g) { return 1 + (e.thema && g.th.indexOf(e.thema) >= 0 ? 6 : 0) + Math.min(g.au, 150000) / 150000; });
    var summe = gew.reduce(function (a, b) { return a + b; }, 0);
    var r = Math.random() * summe;
    for (var i = 0; i < liste.length; i++) { r -= gew[i]; if (r <= 0) return liste[i]; }
    return liste[liste.length - 1];
  }
  var klemme = function (x, a, b) { return Math.max(a, Math.min(b, x)); };

  // ---------------------------------------------------------------- Planen
  function fest(e) {
    var D = e.dauer;
    return { E: D >= 90 ? 5 : 3, R: D >= 90 ? 7 : 5 };
  }

  // Kleinster Abstand (0–2 Stufen), bei dem es genug Spiele gibt – streng nach Schulstufe, wo immer möglich
  function weite(e) {
    for (var w = 0; w <= 2; w++) {
      var x = { stufe: e.stufe, mat: e.mat, ohne: e.ohne, weit: w };
      if (kandidaten(x, 'A', []).length >= 1 && kandidaten(x, 'H', []).length >= (e.dauer >= 90 ? 3 : 2)) return w;
    }
    return 2;
  }

  function plane(e) {
    e.weit = weite(e);
    var D = e.dauer, f = fest(e), benutzt = [], bloecke = [];
    var rest = D - f.E - f.R;
    // Aufwärmen: ca. ein Fünftel der Stunde
    var aufZiel = Math.round(D * (D >= 90 ? 0.17 : 0.2));
    var aufAnzahl = D >= 90 ? 2 : 1;
    var auf = [];
    for (var i = 0; i < aufAnzahl; i++) {
      var g = ziehe(kandidaten(e, 'A', benutzt), e);
      if (!g) break;
      benutzt.push(g.i);
      auf.push({ p: 'A', id: g.i, d: klemme(Math.round(aufZiel / aufAnzahl), g.d[0], g.d[1]) });
    }
    auf.forEach(function (b) { rest -= b.d; });
    // Abschlussspiel (nur wenn es passende gibt)
    var abschluss = null;
    var gs = ziehe(kandidaten(e, 'S', benutzt), e);
    if (gs && rest - gs.d[0] >= 15) {
      benutzt.push(gs.i);
      abschluss = { p: 'S', id: gs.i, d: klemme(gs.d[0], gs.d[0], Math.min(gs.d[1], 10)) };
      rest -= abschluss.d;
    }
    // Hauptteil: so viele Spiele, dass jedes mindestens seine Mindestzeit bekommt
    var haupt = [];
    var anzahl = klemme(Math.round(rest / 16), 1, 4);
    for (var j = 0; j < anzahl; j++) {
      var kand = kandidaten(e, 'H', benutzt).filter(function (x) { return x.d[0] <= rest; });
      var h = ziehe(kand, e);
      if (!h) break;
      benutzt.push(h.i);
      haupt.push({ p: 'H', id: h.i, d: h.d[0] });
    }
    // Mindestzeiten passen nicht in den Rest → letztes Spiel weglassen
    var summe = function (l) { return l.reduce(function (a, b) { return a + b.d; }, 0); };
    while (haupt.length > 1 && summe(haupt) > rest) haupt.pop();
    // Übrige Zeit bis zur Höchstzeit verteilen
    var frei = rest - summe(haupt);
    var lauf = true;
    while (frei > 0 && lauf) {
      lauf = false;
      haupt.forEach(function (b) { if (frei > 0 && b.d < NACH_ID[b.id].d[1]) { b.d++; frei--; lauf = true; } });
    }
    bloecke.push({ p: 'E', d: f.E });
    bloecke = bloecke.concat(auf, haupt);
    if (abschluss) bloecke.push(abschluss);
    bloecke.push({ p: 'R', d: f.R });
    plan = { e: e, bloecke: bloecke };
    puffer();
  }

  // Puffer-Block so setzen, dass die Summe genau der Stundendauer entspricht
  function puffer() {
    var b = plan.bloecke.filter(function (x) { return x.p !== 'P'; });
    var summe = b.reduce(function (a, x) { return a + x.d; }, 0);
    var frei = plan.e.dauer - summe;
    if (frei > 0) {
      var r = b.findIndex(function (x) { return x.p === 'R'; });
      if (frei <= 2) b[r].d += frei;
      else b.splice(r, 0, { p: 'P', d: frei });
    }
    plan.bloecke = b;
  }

  function tausche(index) {
    var b = plan.bloecke[index];
    var benutzt = plan.bloecke.filter(function (x) { return x.id; }).map(function (x) { return x.id; });
    var spielraum = b.d + (plan.bloecke.filter(function (x) { return x.p === 'P'; })[0] || { d: 0 }).d;
    var kand = kandidaten(plan.e, b.p, benutzt).filter(function (g) { return g.d[0] <= spielraum; });
    var g = ziehe(kand, plan.e);
    if (!g) { meldung('Für diesen Stundenteil gibt es mit deinen Einstellungen kein weiteres passendes Spiel.'); return; }
    b.id = g.i;
    b.d = klemme(b.d, g.d[0], g.d[1]);
    // Zeit, die das neue Spiel mehr braucht, kommt aus dem Puffer; Überschuss geht in den Puffer
    var ohneP = plan.bloecke.filter(function (x) { return x.p !== 'P'; }).reduce(function (a, x) { return a + x.d; }, 0);
    if (ohneP > plan.e.dauer) b.d -= ohneP - plan.e.dauer;
    puffer();
    zeige(index);
  }

  // ---------------------------------------------------------------- Adresse (#…)
  function speichern() {
    var e = plan.e;
    var p = new URLSearchParams();
    p.set('stufe', e.stufe); p.set('dauer', e.dauer);
    if (e.thema) p.set('thema', e.thema);
    p.set('mat', e.mat.join('.') || '-');
    if (e.ohne) p.set('ohne', '1');
    p.set('plan', plan.bloecke.filter(function (x) { return x.id; }).map(function (x) { return x.p + '~' + x.id + '~' + x.d; }).join('.')); // „.“ kommt in Video-IDs nie vor
    try { history.replaceState(null, '', '#' + p.toString()); } catch (err) { /* egal */ }
  }
  function laden() {
    if (!location.hash || location.hash.length < 5) return false;
    var p = new URLSearchParams(location.hash.slice(1));
    if (!p.get('plan')) return false;
    var e = { stufe: klemme(+p.get('stufe') || 5, 1, 13), dauer: [45, 50, 90, 100].indexOf(+p.get('dauer')) >= 0 ? +p.get('dauer') : 50,
      thema: p.get('thema') || '', mat: (p.get('mat') || '').split('.').filter(function (x) { return x && x !== '-'; }), ohne: p.get('ohne') === '1' };
    var f = fest(e);
    var spiele = p.get('plan').split('.').map(function (t) {
      var x = t.split('~');
      return { p: x[0], id: x[1], d: +x[2] };
    }).filter(function (b) { return NACH_ID[b.id] && PHASE_NAME[b.p] && b.d > 0 && b.d <= 60; });
    if (!spiele.length) return false;
    var bl = [{ p: 'E', d: f.E }].concat(spiele.filter(function (b) { return b.p !== 'S'; }), spiele.filter(function (b) { return b.p === 'S'; }), [{ p: 'R', d: f.R }]);
    e.weit = weite(e);
    plan = { e: e, bloecke: bl };
    var summe = bl.reduce(function (a, x) { return a + x.d; }, 0);
    if (summe > e.dauer) return false; // manipulierte Adresse
    puffer();
    setzeForm(e);
    return true;
  }

  // ---------------------------------------------------------------- Anzeige
  function zeitText(von, bis) { return von + '–' + bis + '′'; }
  function meldung(t) {
    var m = $('#planer-meldung');
    if (m) { m.textContent = t; m.hidden = false; clearTimeout(meldung.t); meldung.t = setTimeout(function () { m.hidden = true; }, 4000); }
  }

  function zeige(fokusIndex) {
    var e = plan.e;
    var thema = e.thema ? $('#p-thema option[value="' + e.thema + '"]').textContent : 'gemischt';
    var t = 0;
    var balken = '', liste = '';
    plan.bloecke.forEach(function (b, i) {
      var von = t; t += b.d;
      var ph = PHASE[b.p];
      balken += '<span style="flex:' + b.d + ';background:' + ph.farbe + '" title="' + esc(ph.name + ' ' + zeitText(von, t)) + '"><b>' + b.d + '′</b></span>';
      if (!b.id) {
        var fx = FEST[b.p];
        liste += '<li class="block fest" style="--ph:' + ph.farbe + '"><div class="block-zeit">' + zeitText(von, t) + '<small>' + b.d + ' min</small></div><div class="block-inhalt">' +
          '<p class="block-phase">' + ph.name + '</p><h3>' + fx.titel + '</h3><p>' + fx.text + '</p></div></li>';
        return;
      }
      var g = NACH_ID[b.id];
      var chips = '<span class="chip">Spielzeit laut Buch ' + g.d[0] + '–' + g.d[1] + ' min</span>' + (g.gr ? '<span class="chip">' + esc(g.gr) + '</span>' : '') + '<span class="chip">' + esc(g.mt) + '</span>';
      var band = g.b && BASIS.baende[g.b] ? '<a class="knopf klein" href="' + buchUrl(g.b) + '">Anleitung: Band ' + BASIS.baende[g.b].n + '</a>' : '';
      liste += '<li class="block" style="--ph:' + ph.farbe + '" data-index="' + i + '"><div class="block-zeit">' + zeitText(von, t) + '<small>' + b.d + ' min</small></div><div class="block-inhalt">' +
        '<p class="block-phase">' + ph.name + '</p><h3><a href="' + spielUrl(g) + '">' + esc(g.n) + '</a></h3><div class="chips">' + chips + '</div>' +
        (g.lz ? '<p><b>Lernziel:</b> ' + esc(g.lz) + '</p>' : '') + (g.tx ? '<p class="block-text">' + esc(g.tx) + '</p>' : '') +
        '<div class="knopfreihe"><button type="button" class="knopf klein blau" data-video="' + g.i + '" data-titel="' + esc(g.n) + '">▶ Video</button>' +
        '<button type="button" class="knopf klein" data-tausch="' + i + '">⇄ Anderes Spiel</button>' +
        '<button type="button" class="merken klein" data-merk="' + g.i + '" aria-pressed="false" aria-label="„' + esc(g.n) + '“ merken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 7 4.5c2 0 3.6 1.1 5 3 1.4-1.9 3-3 5-3 3.6 0 5.6 3.5 4.3 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/></svg><span>Merken</span></button>' +
        band + '</div></div></li>';
    });
    var anzahl = plan.bloecke.filter(function (b) { return b.id; }).length;
    ziel.innerHTML = '<div class="planer-kopf"><div><p class="oberzeile">Deine Stunde</p><h2 id="planer-titel" tabindex="-1">' + e.stufe + '. Schulstufe · ' + e.dauer + ' Minuten</h2>' +
      '<p class="planer-sub">Schwerpunkt: ' + esc(thema) + ' · ' + anzahl + ' Spiele · Material: ' + (e.ohne ? 'ganz ohne' : 'Standard' + (e.mat.length ? ', ' + e.mat.map(function (m) { return { matten: 'Matten & Bänke', tore: 'Tore/Körbe', geraete: 'Turngeräte' }[m]; }).join(', ') : '')) + '</p></div>' +
      '<div class="knopfreihe"><button type="button" class="knopf pro" id="p-neu">↻ Neu würfeln</button><button type="button" class="knopf primaer" id="p-drucken">Stundenbild drucken</button>' +
      '<button type="button" class="knopf" id="p-karten">Stationskarten drucken</button><button type="button" class="knopf" id="p-alle-merken">♥ Alle merken</button><button type="button" class="knopf" id="p-link">Link kopieren</button></div></div>' +
      '<p class="planer-meldung" id="planer-meldung" role="status" hidden></p>' +
      (e.weit ? '<p class="hinweisbox">Für die ' + e.stufe + '. Schulstufe gibt es in der Sammlung nur wenige passende Spiele. Der Planer hat deshalb auch Spiele einbezogen, die bis zu ' + e.weit + (e.weit === 1 ? ' Schulstufe' : ' Schulstufen') + ' daneben liegen – passe Regeln und Tempo an deine Klasse an.</p>' : '') +
      '<div class="zeitleiste" aria-hidden="true">' + balken + '</div>' +
      '<ol class="stunde">' + liste + '</ol>' +
      (anzahl < 2 ? '<p class="hinweisbox">Mit diesen Einstellungen gibt es nur wenige passende Spiele. Tipp: Material dazunehmen, „nur ohne Material“ abwählen oder den Schwerpunkt auf „gemischt“ stellen.</p>' : '') +
      '<p class="klein">Die Zeiten beruhen auf den Spielzeiten aus der Praxis-Reihe und ergeben zusammen genau ' + e.dauer + ' Minuten. Passe sie an deine Klasse an – du kennst sie am besten.</p>';
    bereich.hidden = false;
    stundenbild();
    speichern();
    if (window.SU && window.SU.merkStatus) window.SU.merkStatus(ziel);
    if (typeof fokusIndex === 'number') {
      var k = $('[data-tausch="' + fokusIndex + '"]', ziel);
      if (k) k.focus();
    }
  }

  // ---------------------------------------------------------------- Stundenbild (nur im Druck sichtbar)
  function stundenbild() {
    var e = plan.e, t = 0, zeilen = '', ziele = [];
    plan.bloecke.forEach(function (b) {
      var von = t; t += b.d;
      var ph = PHASE[b.p];
      if (!b.id) {
        zeilen += '<tr><td>' + zeitText(von, t) + '</td><td>' + ph.name + '</td><td><b>' + FEST[b.p].titel + '</b><br>' + FEST[b.p].text + '</td><td></td><td></td></tr>';
        return;
      }
      var g = NACH_ID[b.id];
      if (g.lz) ziele.push(g.lz);
      zeilen += '<tr><td>' + zeitText(von, t) + '</td><td>' + ph.name + '</td><td><b>' + esc(g.n) + '</b>' + (g.tx ? '<br>' + esc(g.tx) : '') + '<br><small>Video: youtu.be/' + esc(g.i) + '</small></td>' +
        '<td>' + esc(g.gr || '') + (g.gr ? '<br>' : '') + 'Material: ' + esc(g.mt) + '</td><td>' + esc(g.lz || '') + '</td></tr>';
    });
    var thema = e.thema ? $('#p-thema option[value="' + e.thema + '"]').textContent : '';
    druck.innerHTML = '<div class="sb"><h1>Stundenbild Bewegung und Sport</h1>' +
      '<table class="sb-kopf"><tr><td>Schule / Klasse:</td><td>Datum:</td></tr><tr><td>Lehrkraft:</td><td>Schulstufe: <b>' + e.stufe + '.</b> · Dauer: <b>' + e.dauer + ' min</b></td></tr>' +
      '<tr><td colspan="2">Thema / Schwerpunkt: ' + esc(thema) + '</td></tr></table>' +
      '<h2>Lernziele</h2><ul>' + ziele.map(function (z) { return '<li>' + esc(z) + '</li>'; }).join('') + '</ul>' +
      '<h2>Verlaufsplanung</h2><table class="sb-verlauf"><thead><tr><th>Zeit</th><th>Phase</th><th>Inhalt</th><th>Organisation &amp; Material</th><th>Lernziel</th></tr></thead><tbody>' + zeilen + '</tbody></table>' +
      '<h2>Sicherheit, Differenzierung, Notizen</h2><div class="sb-linien"></div><h2>Reflexion nach der Stunde</h2><div class="sb-linien kurz"></div>' +
      '<p class="sb-fuss">Erstellt mit dem Stundenplaner von Sportunterricht · Ansagetexte, Varianten und Sicherheitshinweise zu allen Spielen in der Praxis-Reihe</p></div>';
  }

  // ---------------------------------------------------------------- Video-Dialog
  var vDialog = null;
  function video(id, titel) {
    if (BASIS.artifact || location.protocol === 'file:') { window.open('https://www.youtube.com/watch?v=' + id, '_blank', 'noopener'); return; }
    if (!vDialog) {
      vDialog = document.createElement('dialog');
      vDialog.className = 'dialog dialog-video';
      vDialog.setAttribute('aria-labelledby', 'v-titel');
      vDialog.innerHTML = '<form method="dialog" class="dialog-zu"><button type="submit" aria-label="Video schließen"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></form>' +
        '<h2 id="v-titel"></h2><div class="video laeuft"></div><p class="video-alt"><a target="_blank" rel="noopener">Video lädt nicht? Direkt auf YouTube ansehen</a></p>';
      document.body.appendChild(vDialog);
      vDialog.addEventListener('close', function () { $('.video', vDialog).innerHTML = ''; document.documentElement.classList.remove('dialog-offen'); });
      vDialog.addEventListener('click', function (ev) { if (ev.target === vDialog) vDialog.close(); });
    }
    $('#v-titel', vDialog).textContent = titel;
    $('.video-alt a', vDialog).href = 'https://www.youtube.com/watch?v=' + id;
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0&playsinline=1';
    f.title = 'Video: ' + titel;
    f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    $('.video', vDialog).appendChild(f);
    document.documentElement.classList.add('dialog-offen');
    vDialog.showModal();
  }

  // ---------------------------------------------------------------- Ereignisse
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    plane(leseForm());
    zeige();
    var h = $('#planer-titel');
    bereich.scrollIntoView({ behavior: 'smooth', block: 'start' });
    if (h) h.focus({ preventScroll: true });
  });
  $('#p-ohne').addEventListener('change', function () {
    $$('input[name="mat"]', form).forEach(function (x) { x.disabled = $('#p-ohne').checked; });
  });
  ziel.addEventListener('click', function (ev) {
    var k = ev.target.closest('button');
    if (!k) return;
    if (k.hasAttribute('data-tausch')) tausche(+k.getAttribute('data-tausch'));
    else if (k.hasAttribute('data-video')) video(k.getAttribute('data-video'), k.getAttribute('data-titel'));
    else if (k.id === 'p-neu') { plane(plan.e); zeige(); $('#p-neu').focus(); }
    else if (k.id === 'p-drucken') { document.documentElement.classList.remove('druck-karten'); window.print(); }
    else if (k.id === 'p-karten') {
      var spiele = plan.bloecke.filter(function (b) { return b.id; }).map(function (b) { return NACH_ID[b.id]; });
      if (window.SU_KARTEN) $('#karten-druck').innerHTML = window.SU_KARTEN.html(spiele, BASIS.qr);
      document.documentElement.classList.add('druck-karten');
      window.print();
    }
    else if (k.id === 'p-alle-merken' && window.SU) {
      var l = window.SU.merkLies(), neu = 0;
      plan.bloecke.forEach(function (b) { if (b.id && l.indexOf(b.id) < 0) { l.push(b.id); neu++; } });
      window.SU.merkSchreib(l);
      window.SU.merkStatus(document);
      meldung(neu ? neu + (neu === 1 ? ' Spiel' : ' Spiele') + ' auf die Merkliste gelegt.' : 'Alle Spiele dieser Stunde sind schon auf deiner Merkliste.');
    }
    else if (k.id === 'p-link') {
      var fertig = function () { meldung('Link kopiert – du kannst ihn jetzt teilen.'); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(location.href).then(fertig, function () { window.prompt('Link zum Kopieren:', location.href); });
      else window.prompt('Link zum Kopieren:', location.href);
    }
  });

  window.addEventListener('afterprint', function () { document.documentElement.classList.remove('druck-karten'); });
  if (laden()) zeige();
})();
