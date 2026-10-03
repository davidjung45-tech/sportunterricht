// Sportunterricht – Bewegte Pause: ein Spiel ganz ohne Material, mit Video und Timer.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var form = $('#pause-form');
  var datenEl = $('#spiele-daten');
  if (!form || !datenEl) return;
  var DATEN = JSON.parse(datenEl.textContent);
  var BASIS = JSON.parse($('#seiten-basis').textContent);
  var ziel = $('#pause-ergebnis');
  var VIEL_PLATZ = ['fangen', 'turnen', 'leichtathletik', 'parkour']; // brauchen Raum zum Laufen oder Geräte
  var zuletzt = null, uhr = null, ende = 0, rest = 0, sperre = null, audio = null;

  var stufe = function (g) { return g.von === g.bis ? g.von + '. Schulstufe' : g.von + '.–' + g.bis + '. Schulstufe'; };
  var url = function (g) { return BASIS.spiele + g.s + '/' + (BASIS.vorschau ? 'index.html' : ''); };
  var fmt = function (s) { s = Math.max(0, Math.ceil(s)); return Math.floor(s / 60) + ':' + (s % 60 < 10 ? '0' : '') + (s % 60); };
  function minuten() { return +(form.querySelector('input[name="pa-min"]:checked') || { value: 5 }).value; }

  function auswahl() {
    var b = $('#pa-stufe').value.split('-').map(Number), eng = $('#pa-eng').checked;
    return DATEN.filter(function (g) {
      if (g.bis < b[0] || g.von > b[1]) return false;
      if (eng && g.th.some(function (t) { return VIEL_PLATZ.indexOf(t) >= 0; })) return false;
      return true;
    });
  }
  function ziehe() {
    var l = auswahl();
    if (l.length > 1) l = l.filter(function (g) { return g.i !== zuletzt; });
    return l.length ? l[Math.floor(Math.random() * l.length)] : null;
  }

  function zeige(g) {
    stopp();
    if (!g) {
      ziel.innerHTML = '<p class="hinweisbox">Für diese Auswahl gibt es kein passendes Spiel. Tipp: „wenig Platz“ abwählen oder „alle“ Altersstufen nehmen.</p>';
      ziel.hidden = false;
      return;
    }
    zuletzt = g.i;
    rest = minuten() * 60;
    ziel.innerHTML = '<div class="pause-karte" style="--f:' + g.f + '">' +
      '<div class="pause-video"><div class="video kompakt" data-video="' + esc(g.i) + '" style="--vfarbe:' + g.f + '"><button type="button" class="video-start" aria-label="Video „' + esc(g.n) + '“ abspielen">' +
      '<span class="play"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 4.8v14.4c0 .8.9 1.3 1.6.8l11-7.2a1 1 0 000-1.6l-11-7.2C7.9 3.5 7 4 7 4.8z"/></svg></span><b>Video ansehen</b><small>Lädt von YouTube</small></button></div>' +
      '<p class="video-alt"><a href="https://www.youtube.com/watch?v=' + esc(g.i) + '" target="_blank" rel="noopener">Video lädt nicht? Direkt auf YouTube ansehen<span class="sr-only"> (neues Fenster)</span></a></p></div>' +
      '<div class="pause-text"><p class="oberzeile">Deine Bewegte Pause</p><h2 id="pause-titel" tabindex="-1">' + esc(g.n) + '</h2>' +
      '<div class="chips"><span class="chip">' + stufe(g) + '</span><span class="chip">kein Material</span>' + (g.gr ? '<span class="chip">' + esc(g.gr) + '</span>' : '') + '</div>' +
      (g.lz ? '<p><b>Ziel:</b> ' + esc(g.lz) + '</p>' : '') + (g.tx ? '<p class="block-text">' + esc(g.tx) + '</p>' : '') +
      '<div class="pause-uhr" id="pa-uhr" role="timer" aria-live="off">' + fmt(rest) + '</div>' +
      '<div class="knopfreihe"><button type="button" class="knopf pro gross" id="pa-start">▶ ' + minuten() + ' Minuten starten</button><button type="button" class="knopf" id="pa-anders">⇄ Anderes Spiel</button>' +
      '<button type="button" class="merken klein" data-merk="' + esc(g.i) + '" aria-pressed="false" aria-label="„' + esc(g.n) + '“ merken"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.3-9.2C1.4 8 3.4 4.5 7 4.5c2 0 3.6 1.1 5 3 1.4-1.9 3-3 5-3 3.6 0 5.6 3.5 4.3 6.8-1.8 4.6-9.3 9.2-9.3 9.2z"/></svg><span>Merken</span></button>' +
      (g.a ? '<a class="knopf klein" href="' + url(g) + '">Zum Spiel</a>' : '') + '</div></div></div>';
    ziel.hidden = false;
    if (window.SU) window.SU.merkStatus(ziel);
  }

  function ton(freq, dauer) {
    try {
      audio = audio || new (window.AudioContext || window.webkitAudioContext)();
      var o = audio.createOscillator(), v = audio.createGain(), t = audio.currentTime;
      o.type = 'square'; o.frequency.value = freq;
      v.gain.setValueAtTime(0.18, t); v.gain.exponentialRampToValueAtTime(0.0001, t + dauer);
      o.connect(v); v.connect(audio.destination); o.start(t); o.stop(t + dauer + 0.02);
    } catch (e) { /* kein Ton */ }
  }
  async function wach(an) {
    try {
      if (an && 'wakeLock' in navigator && !sperre) sperre = await navigator.wakeLock.request('screen');
      if (!an && sperre) { await sperre.release(); sperre = null; }
    } catch (e) { /* nicht unterstützt */ }
  }
  function stopp() { clearInterval(uhr); uhr = null; wach(false); }
  function tick() {
    var s = (ende - performance.now()) / 1000;
    $('#pa-uhr').textContent = fmt(s);
    if (s <= 0) {
      stopp();
      $('#pa-uhr').textContent = 'Geschafft!';
      $('#pa-start').textContent = '↻ Nochmal';
      rest = minuten() * 60;
      ton(1320, 0.3); setTimeout(function () { ton(1760, 0.6); }, 350);
      if (navigator.vibrate) navigator.vibrate([300, 100, 500]);
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    zeige(ziehe());
    var h = $('#pause-titel');
    if (h) { ziel.scrollIntoView({ behavior: 'smooth', block: 'start' }); h.focus({ preventScroll: true }); }
  });
  ziel.addEventListener('click', function (e) {
    var k = e.target.closest('button');
    if (!k) return;
    if (k.id === 'pa-anders') { zeige(ziehe()); $('#pa-anders').focus(); }
    if (k.id === 'pa-start') {
      if (uhr) { stopp(); rest = Math.max(0, (ende - performance.now()) / 1000); k.textContent = '▶ Weiter'; return; }
      if (rest <= 0) rest = minuten() * 60;
      ende = performance.now() + rest * 1000;
      uhr = setInterval(tick, 200);
      k.textContent = '❚❚ Pause';
      ton(1320, 0.25);
      wach(true);
      tick();
    }
  });
  form.addEventListener('change', function (e) {
    if (e.target.name === 'pa-min' && !uhr && $('#pa-uhr')) { rest = minuten() * 60; $('#pa-uhr').textContent = fmt(rest); $('#pa-start').textContent = '▶ ' + minuten() + ' Minuten starten'; }
  });
})();
