// Sportunterricht – Werkzeuge für die Halle: Timer, Teams, Punkte, Zufall.
// Alles läuft im Browser. Namen und Punkte bleiben (nur auf Wunsch) im Speicher dieses Geräts.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var lies = function (k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } };
  var schreib = function (k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* privates Fenster */ } };
  var zufall = function (n) { // fairer Zufall 0..n-1
    if (window.crypto && crypto.getRandomValues) { var a = new Uint32Array(1); crypto.getRandomValues(a); return a[0] % n; }
    return Math.floor(Math.random() * n);
  };
  var mischen = function (l) { l = l.slice(); for (var i = l.length - 1; i > 0; i--) { var j = zufall(i + 1); var t = l[i]; l[i] = l[j]; l[j] = t; } return l; };
  var zahl = function (el, min, max, std) { var v = parseInt(el.value, 10); if (isNaN(v)) v = std; return Math.max(min, Math.min(max, v)); };

  // ================================================================ Reiter
  var tabs = $$('[role="tab"]');
  if (!tabs.length) return;
  document.documentElement.classList.add('reiter-an');
  function waehle(id, fokus) {
    tabs.forEach(function (t) {
      var an = t.getAttribute('aria-controls') === id;
      t.setAttribute('aria-selected', an ? 'true' : 'false');
      t.tabIndex = an ? 0 : -1;
      $('#' + t.getAttribute('aria-controls')).hidden = !an;
      if (an && fokus) t.focus();
    });
    try { history.replaceState(null, '', '#' + id); } catch (e) { /* egal */ }
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { waehle(t.getAttribute('aria-controls')); });
    t.addEventListener('keydown', function (e) {
      var n = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (e.key === 'Home') n = -i; else if (e.key === 'End') n = tabs.length - 1 - i;
      if (n == null) return;
      e.preventDefault();
      waehle(tabs[(i + n + tabs.length) % tabs.length].getAttribute('aria-controls'), true);
    });
  });
  var start = (location.hash || '').slice(1);
  waehle(tabs.some(function (t) { return t.getAttribute('aria-controls') === start; }) ? start : 'timer');

  // ================================================================ Ton
  var audio = null;
  function ton(freq, dauer, lautstaerke) {
    if (!$('#t-ton').checked) return;
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      if (audio.state === 'suspended') audio.resume();
      var o = audio.createOscillator(), g = audio.createGain(), t = audio.currentTime;
      o.type = 'square'; o.frequency.value = freq;
      g.gain.setValueAtTime(lautstaerke || 0.18, t);
      g.gain.exponentialRampToValueAtTime(0.0001, t + dauer);
      o.connect(g); g.connect(audio.destination);
      o.start(t); o.stop(t + dauer + 0.02);
    } catch (e) { /* kein Ton möglich */ }
  }
  var vibriere = function (m) { if (navigator.vibrate) navigator.vibrate(m); };

  // ================================================================ Timer
  var box = $('#t-box'), anzeige = $('#t-zeit'), phaseEl = $('#t-phase'), info = $('#t-info'), balken = $('#t-fortschritt');
  var startKnopf = $('#t-start');
  var ablauf = [], schritt = 0, ende = 0, rest = 0, laeuft = false, uhr = null, letzteSek = -1, sperre = null;

  function modus() { return $('input[name="modus"]:checked').value; }
  function fmt(s) { s = Math.max(0, Math.ceil(s)); var m = Math.floor(s / 60); return (m < 10 ? '0' : '') + m + ':' + (s % 60 < 10 ? '0' : '') + (s % 60); }

  function baueAblauf() {
    if (modus() === 'countdown') {
      var s = zahl($('#t-min'), 0, 99, 1) * 60 + zahl($('#t-sek'), 0, 59, 0);
      return [{ typ: 'arbeit', s: Math.max(1, s), text: 'Countdown', info: '' }];
    }
    var a = zahl($('#t-arbeit'), 5, 600, 40), p = zahl($('#t-pause'), 0, 600, 20), st = zahl($('#t-stationen'), 1, 30, 8),
      r = zahl($('#t-runden'), 1, 20, 1), rp = zahl($('#t-rundenpause'), 0, 900, 60);
    var l = [{ typ: 'pause', s: 5, text: 'Gleich geht’s los', info: 'Station 1' + (r > 1 ? ' · Runde 1' : '') }];
    for (var ri = 1; ri <= r; ri++) {
      for (var si = 1; si <= st; si++) {
        l.push({ typ: 'arbeit', s: a, text: 'Belastung', info: 'Station ' + si + ' von ' + st + (r > 1 ? ' · Runde ' + ri + ' von ' + r : '') });
        var letzte = si === st && ri === r;
        if (!letzte && si < st && p > 0) l.push({ typ: 'pause', s: p, text: 'Wechsel', info: 'Gleich: Station ' + (si + 1) });
        if (!letzte && si === st && (rp || p) > 0) l.push({ typ: 'pause', s: rp || p, text: 'Rundenpause', info: 'Gleich: Runde ' + (ri + 1) + ', Station 1' });
      }
    }
    return l;
  }
  function summe() {
    if (modus() !== 'intervall') return;
    var s = baueAblauf().slice(1).reduce(function (x, y) { return x + y.s; }, 0);
    $('#t-summe').textContent = 'Gesamtdauer: ' + fmt(s).replace(':', ' min ') + ' s';
  }
  function zeigeSchritt(sek) {
    var sch = ablauf[schritt];
    box.setAttribute('data-phase', sch ? sch.typ : 'fertig');
    phaseEl.textContent = sch ? sch.text : 'Fertig!';
    info.innerHTML = sch && sch.info ? esc(sch.info) : '&nbsp;';
    anzeige.textContent = fmt(sek);
    balken.style.width = sch ? (100 - (sek / sch.s) * 100) + '%' : '100%';
  }
  function tick() {
    var sek = (ende - performance.now()) / 1000;
    var ganz = Math.ceil(sek);
    if (ganz !== letzteSek) {
      letzteSek = ganz;
      if (ganz <= 3 && ganz >= 1) ton(880, 0.12);
    }
    if (sek <= 0) {
      schritt++;
      if (schritt >= ablauf.length) { fertig(); return; }
      var neu = ablauf[schritt];
      ton(neu.typ === 'arbeit' ? 1320 : 660, 0.45, 0.22);
      vibriere(neu.typ === 'arbeit' ? [200, 80, 200] : 300);
      ende = performance.now() + neu.s * 1000;
      sek = neu.s;
    }
    zeigeSchritt(sek);
  }
  async function wachHalten(an) {
    try {
      if (an && 'wakeLock' in navigator && !sperre) { sperre = await navigator.wakeLock.request('screen'); sperre.addEventListener('release', function () { sperre = null; }); }
      if (!an && sperre) { await sperre.release(); sperre = null; }
    } catch (e) { /* nicht unterstützt */ }
  }
  document.addEventListener('visibilitychange', function () { if (laeuft && document.visibilityState === 'visible') wachHalten(true); });

  function los() {
    if (!ablauf.length || schritt >= ablauf.length) { ablauf = baueAblauf(); schritt = 0; rest = ablauf[0].s; ton(1320, 0.3); }
    ende = performance.now() + rest * 1000;
    laeuft = true; letzteSek = -1;
    uhr = setInterval(tick, 100);
    startKnopf.textContent = 'Pause';
    $('#t-form').classList.add('gesperrt');
    $$('#t-form input, #t-form button').forEach(function (x) { x.disabled = true; });
    $('#t-ton').disabled = false;
    wachHalten(true);
    tick();
  }
  function halt() {
    clearInterval(uhr); laeuft = false;
    rest = Math.max(0, (ende - performance.now()) / 1000);
    startKnopf.textContent = 'Weiter';
    wachHalten(false);
  }
  function fertig() {
    clearInterval(uhr); laeuft = false; ablauf = []; schritt = 0;
    zeigeSchritt(0);
    ton(1320, 0.25); setTimeout(function () { ton(1320, 0.25); }, 320); setTimeout(function () { ton(1760, 0.6); }, 640);
    vibriere([300, 100, 300, 100, 600]);
    startKnopf.textContent = 'Nochmal';
    entsperren();
    wachHalten(false);
  }
  function entsperren() {
    $('#t-form').classList.remove('gesperrt');
    $$('#t-form input, #t-form button').forEach(function (x) { x.disabled = false; });
  }
  function zuruecksetzen() {
    clearInterval(uhr); laeuft = false; ablauf = []; schritt = 0;
    entsperren();
    var l = baueAblauf();
    box.setAttribute('data-phase', 'bereit');
    phaseEl.textContent = 'Bereit';
    info.innerHTML = modus() === 'intervall' ? esc((l.length - 1 > 0 ? l.filter(function (x) { return x.typ === 'arbeit'; }).length : 0) + ' Belastungsphasen') : '&nbsp;';
    anzeige.textContent = fmt(modus() === 'countdown' ? l[0].s : l[1].s);
    balken.style.width = '0%';
    startKnopf.textContent = 'Start';
    wachHalten(false);
    summe();
  }
  startKnopf.addEventListener('click', function () { if (laeuft) halt(); else los(); });
  $('#t-reset').addEventListener('click', zuruecksetzen);
  $('#t-vollbild').addEventListener('click', function () {
    if (document.fullscreenElement) document.exitFullscreen();
    else if (box.requestFullscreen) box.requestFullscreen().catch(function () { box.classList.toggle('gross-an'); });
    else box.classList.toggle('gross-an'); // iPhone: kein Vollbild für Elemente → große Ansicht
  });
  $$('input[name="modus"]').forEach(function (r) {
    r.addEventListener('change', function () {
      $('#t-countdown').hidden = modus() !== 'countdown';
      $('#t-intervall').hidden = modus() !== 'intervall';
      zuruecksetzen();
    });
  });
  $$('#t-countdown [data-sek]').forEach(function (b) {
    b.addEventListener('click', function () {
      var s = +b.getAttribute('data-sek');
      $('#t-min').value = Math.floor(s / 60); $('#t-sek').value = s % 60;
      zuruecksetzen();
    });
  });
  $$('#t-intervall [data-vorlage]').forEach(function (b) {
    b.addEventListener('click', function () {
      var v = b.getAttribute('data-vorlage').split(',');
      ['#t-arbeit', '#t-pause', '#t-stationen', '#t-runden', '#t-rundenpause'].forEach(function (s, i) { $(s).value = v[i]; });
      zuruecksetzen();
    });
  });
  $$('#t-form input[type="number"]').forEach(function (x) { x.addEventListener('input', function () { if (!laeuft) zuruecksetzen(); }); });
  document.addEventListener('keydown', function (e) {
    if (e.code === 'Space' && !$('#timer').hidden && !/INPUT|TEXTAREA|SELECT|BUTTON/.test(document.activeElement.tagName)) { e.preventDefault(); startKnopf.click(); }
  });
  zuruecksetzen();

  // ================================================================ Teams
  var FARBEN = [['Rot', '#d63b2a'], ['Blau', '#1f5bd8'], ['Gelb', '#e9b400'], ['Grün', '#1d8f55'], ['Orange', '#e8730c'], ['Lila', '#7a4fc9'], ['Weiß', '#f4f4f4'], ['Schwarz', '#222']];
  var namenFeld = $('#tm-namen');
  function namen() { return namenFeld.value.split('\n').map(function (n) { return n.trim(); }).filter(Boolean); }
  var gemerkt = lies('su-namen');
  if (Array.isArray(gemerkt) && gemerkt.length) { namenFeld.value = gemerkt.join('\n'); $('#tm-merken').checked = true; }
  function namenSpeichern() { schreib('su-namen', $('#tm-merken').checked ? namen() : null); }
  $('#tm-merken').addEventListener('change', namenSpeichern);
  namenFeld.addEventListener('input', function () { if ($('#tm-merken').checked) namenSpeichern(); });
  $('#tm-los').addEventListener('click', function () {
    var l = namen();
    if (!l.length) { var n = zahl($('#tm-anzahl'), 2, 80, 24); l = []; for (var i = 1; i <= n; i++) l.push('Nr. ' + i); }
    var k = Math.min(+$('#tm-teams').value, l.length);
    var teams = []; for (var t = 0; t < k; t++) teams.push([]);
    var farben = mischen(FARBEN.slice(0, Math.max(k, 4))).slice(0, k);
    mischen(l).forEach(function (n, i) { teams[i % k].push(n); });
    $('#tm-ergebnis').innerHTML = teams.map(function (tm, i) {
      return '<div class="team" style="--team:' + farben[i][1] + '"><h3>Team ' + farben[i][0] + ' <small>' + tm.length + '</small></h3><ul>' + tm.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul></div>';
    }).join('');
    $('#tm-los').innerHTML = $('#tm-los').innerHTML.replace('Teams bilden', 'Neu mischen');
  });

  // ================================================================ Punkte
  var TEAMFARBEN = ['#d63b2a', '#1f5bd8', '#e9b400', '#1d8f55'];
  var stand = lies('su-punkte') || { n: 2, t: [{ name: 'Team A', p: 0 }, { name: 'Team B', p: 0 }, { name: 'Team C', p: 0 }, { name: 'Team D', p: 0 }] };
  var tafel = $('#pk-tafel');
  $('#pk-anzahl').value = String(stand.n);
  function punkteZeigen() {
    tafel.style.setProperty('--spalten', stand.n);
    tafel.innerHTML = stand.t.slice(0, stand.n).map(function (t, i) {
      return '<div class="punkt-team" style="--team:' + TEAMFARBEN[i] + '"><input class="punkt-name" value="' + esc(t.name) + '" aria-label="Name von Team ' + (i + 1) + '" data-i="' + i + '" maxlength="24">' +
        '<p class="punkt-zahl" aria-live="polite" id="pk-' + i + '">' + t.p + '</p>' +
        '<button type="button" class="punkt-plus" data-i="' + i + '" data-d="1" aria-label="Plus ein Punkt für ' + esc(t.name) + '">+1</button>' +
        '<button type="button" class="punkt-minus" data-i="' + i + '" data-d="-1" aria-label="Minus ein Punkt für ' + esc(t.name) + '">−1</button></div>';
    }).join('');
  }
  tafel.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-d]');
    if (!b) return;
    var t = stand.t[+b.getAttribute('data-i')];
    t.p = Math.max(0, t.p + +b.getAttribute('data-d'));
    $('#pk-' + b.getAttribute('data-i')).textContent = t.p;
    if (+b.getAttribute('data-d') > 0) vibriere(30);
    schreib('su-punkte', stand);
  });
  tafel.addEventListener('input', function (e) {
    if (!e.target.classList.contains('punkt-name')) return;
    stand.t[+e.target.getAttribute('data-i')].name = e.target.value;
    schreib('su-punkte', stand);
  });
  $('#pk-anzahl').addEventListener('change', function () { stand.n = +this.value; schreib('su-punkte', stand); punkteZeigen(); });
  $('#pk-reset').addEventListener('click', function () { stand.t.forEach(function (t) { t.p = 0; }); schreib('su-punkte', stand); punkteZeigen(); });
  punkteZeigen();

  // ================================================================ Zufall
  var WUERFEL = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅'];
  function wirbeln(el, fertigText, rollen) {
    var n = 0;
    var t = setInterval(function () {
      el.textContent = rollen();
      if (++n >= 8) { clearInterval(t); el.textContent = fertigText; el.classList.remove('rollt'); }
    }, 55);
    el.classList.add('rollt');
  }
  $('#z-wuerfeln').addEventListener('click', function () {
    var w = zufall(6);
    wirbeln($('#z-wuerfel'), WUERFEL[w] + ' ' + (w + 1), function () { return WUERFEL[zufall(6)]; });
  });
  $('#z-muenze').addEventListener('click', function () {
    wirbeln($('#z-wuerfel'), zufall(2) ? 'Kopf' : 'Zahl', function () { return zufall(2) ? 'Kopf' : 'Zahl'; });
  });
  $('#z-ziehen').addEventListener('click', function () {
    var a = parseInt($('#z-von').value, 10), b = parseInt($('#z-bis').value, 10);
    if (isNaN(a) || isNaN(b)) { $('#z-zahl').textContent = 'Bitte von und bis eingeben'; return; }
    if (a > b) { var t = a; a = b; b = t; }
    var r = a + zufall(b - a + 1);
    wirbeln($('#z-zahl'), String(r), function () { return String(a + zufall(b - a + 1)); });
  });
  var topf = null;
  function topfNeu() {
    topf = mischen(namen());
    $('#z-rest').textContent = topf.length ? topf.length + ' Namen im Topf' : 'Trag zuerst bei „Teams“ Namen ein.';
  }
  $('#z-name-los').addEventListener('click', function () {
    if (!topf || (!topf.length && namen().length && $('#z-name').textContent === '–')) topfNeu();
    if (!topf.length) { $('#z-name').textContent = namen().length ? 'Alle gezogen!' : '–'; $('#z-rest').textContent = namen().length ? '„Neu starten“ legt alle Namen zurück in den Topf.' : 'Trag zuerst bei „Teams“ Namen ein.'; return; }
    var n = topf.pop();
    var alle = namen();
    wirbeln($('#z-name'), n, function () { return alle[zufall(alle.length)]; });
    $('#z-rest').textContent = topf.length ? 'Noch ' + topf.length + ' im Topf' : 'Das war der letzte Name.';
  });
  $('#z-name-neu').addEventListener('click', function () { topfNeu(); $('#z-name').textContent = '–'; });
})();
