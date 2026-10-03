// Sportunterricht – kleine Helfer für die Website. Kein Tracking, keine externen Skripte.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };

  // ---- Zwei-Klick-Video: YouTube wird erst nach dem Klick geladen.
  // Über das ganze Dokument verteilt, damit auch nachträglich eingefügte Videos (Spiel der Woche) funktionieren.
  document.addEventListener('click', function (e) {
    var knopf = e.target.closest ? e.target.closest('.video-start') : null;
    var box = knopf && knopf.closest('.video[data-video]');
    if (!box) return;
    // Eingebettete Videos funktionieren nicht in der claude.ai-Vorschau und nicht in einer lokal geöffneten Datei
    // (file://: YouTube verlangt eine Absender-Adresse, sonst „Fehler 153“) → dort direkt YouTube öffnen.
    if (window.SU_ARTIFACT || location.protocol === 'file:') {
      window.open('https://www.youtube.com/watch?v=' + box.getAttribute('data-video'), '_blank', 'noopener');
      return;
    }
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + box.getAttribute('data-video') + '?autoplay=1&rel=0&playsinline=1';
    f.title = knopf.getAttribute('aria-label') || 'Video';
    f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    box.innerHTML = '';
    box.appendChild(f);
    box.classList.add('laeuft');
    f.focus();
  });

  // ---- Menü schließen, wenn man daneben tippt oder Escape drückt
  var menue = $('.menue');
  if (menue) {
    document.addEventListener('click', function (e) { if (menue.open && !menue.contains(e.target)) menue.open = false; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && menue.open) { menue.open = false; $('summary', menue).focus(); } });
    $$('a', menue).forEach(function (a) { a.addEventListener('click', function () { menue.open = false; }); }); // Sprungmarken auf derselben Seite
    var sum = $('summary', menue);
    var beschriften = function () { sum.setAttribute('aria-label', menue.open ? 'Menü schließen' : 'Menü öffnen'); sum.setAttribute('aria-expanded', menue.open ? 'true' : 'false'); };
    menue.addEventListener('toggle', beschriften);
    beschriften();
  }

  // ---- Kauf-Dialog: Zusammenfassung vor dem Wechsel zu Digistore24 (ohne JavaScript führt der Link direkt dorthin)
  var dialog = $('#kauf-dialog');
  var kaufDaten = $('#kauf-daten');
  if (dialog && kaufDaten && typeof dialog.showModal === 'function') {
    var produkte = JSON.parse(kaufDaten.textContent);
    var ausloeser = null;
    $$('a[data-kauf]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        var d = produkte[a.getAttribute('data-kauf')];
        if (!d || e.metaKey || e.ctrlKey || e.shiftKey) return; // Neuer Tab: normal weiter
        e.preventDefault();
        ausloeser = a;
        $('#kauf-titel', dialog).textContent = d.t;
        $('#kauf-preis', dialog).textContent = d.p;
        $('#kauf-statt', dialog).textContent = d.s || '';
        $('#kauf-preis', dialog).parentNode.hidden = !d.p;
        $('#kauf-text', dialog).textContent = d.x;
        var c = $('#kauf-cover', dialog);
        c.hidden = !d.c;
        if (d.c) c.src = d.c;
        $('#kauf-weiter', dialog).href = d.u;
        var probe = $('#kauf-probe', dialog);
        probe.hidden = !d.l;
        if (d.l) probe.href = d.l;
        document.documentElement.classList.add('dialog-offen');
        dialog.showModal();
      });
    });
    dialog.addEventListener('close', function () {
      document.documentElement.classList.remove('dialog-offen');
      if (ausloeser) ausloeser.focus();
    });
    dialog.addEventListener('click', function (e) { if (e.target === dialog) dialog.close(); }); // Klick auf den Hintergrund
  }

  // ---- Merkliste: Herz-Knöpfe auf allen Seiten (gespeichert nur auf diesem Gerät)
  var MERK = 'su-merkliste';
  function merkLies() { try { var l = JSON.parse(localStorage.getItem(MERK)); return Array.isArray(l) ? l : []; } catch (e) { return []; } }
  function merkZaehler() {
    var z = $('.merk-zahl');
    if (!z) return;
    var n = merkLies().length;
    z.textContent = n; z.hidden = !n;
    var link = z.parentNode;
    var sr = $('.sr-only', link);
    if (sr) sr.textContent = n ? 'Merkliste (' + n + ' ' + (n === 1 ? 'Spiel' : 'Spiele') + ')' : 'Merkliste';
  }
  function merkSchreib(l) { try { localStorage.setItem(MERK, JSON.stringify(l)); } catch (e) { /* privates Fenster */ } merkZaehler(); }
  function merkStatus(root) {
    var l = merkLies();
    $$('[data-merk]', root).forEach(function (b) {
      var an = l.indexOf(b.getAttribute('data-merk')) >= 0;
      b.setAttribute('aria-pressed', an ? 'true' : 'false');
      var s = $('span', b);
      if (s) s.textContent = an ? 'Gemerkt' : 'Merken';
    });
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('[data-merk]') : null;
    if (!b) return;
    var id = b.getAttribute('data-merk'), l = merkLies(), i = l.indexOf(id);
    if (i >= 0) l.splice(i, 1); else l.unshift(id);
    merkSchreib(l);
    merkStatus(document);
    document.dispatchEvent(new CustomEvent('su-merkliste'));
  });
  window.addEventListener('storage', function (e) { if (e.key === MERK) { merkStatus(document); merkZaehler(); document.dispatchEvent(new CustomEvent('su-merkliste')); } });
  window.SU = { merkLies: merkLies, merkSchreib: merkSchreib, merkStatus: merkStatus };
  merkZaehler();

  // ---- Spiel der Woche: wechselt jeden Montag – im Browser berechnet, damit die Seite dafür nicht neu gebaut werden muss
  var woche = $('.woche');
  var wocheDaten = $('#woche-daten');
  if (woche && wocheDaten) {
    var wl = JSON.parse(wocheDaten.textContent);
    var jetzt = new Date();
    var heute = Date.UTC(jetzt.getFullYear(), jetzt.getMonth(), jetzt.getDate());
    var wochen = Math.floor((heute - Date.UTC(2024, 0, 1)) / 864e5 / 7); // gleiche Rechnung wie in bauen.py
    var g = wl[(wochen * 37) % wl.length];
    var d = new Date(heute); var tag = d.getUTCDay() || 7; d.setUTCDate(d.getUTCDate() + 4 - tag);
    var kw = Math.ceil(((d - Date.UTC(d.getUTCFullYear(), 0, 1)) / 864e5 + 1) / 7);
    $('.woche-kw', woche).textContent = 'KW ' + kw;
    if (g && $('.woche-name', woche).textContent !== g.n) {
      woche.style.setProperty('--wfarbe', g.f);
      var v = $('.video', woche);
      v.setAttribute('data-video', g.i); v.style.setProperty('--vfarbe', g.f);
      var vf = $('iframe', v);
      if (vf) { vf.src = 'https://www.youtube-nocookie.com/embed/' + g.i + '?rel=0&playsinline=1'; vf.title = 'Video: ' + g.n; }
      $('.woche-name', woche).textContent = g.n;
      $('.woche-st', woche).textContent = g.st;
      $('.woche-d', woche).textContent = g.d[0] + '–' + g.d[1] + ' min';
      $('.woche-p', woche).textContent = g.p.join(', ');
      $('.woche-lz', woche).textContent = g.lz;
      $('.woche-link', woche).href = woche.getAttribute('data-basis').replace(/index\.html$/, '') + g.s + '/' + (woche.getAttribute('data-vorschau') === '1' ? 'index.html' : '');
      var m = $('[data-merk]', woche);
      m.setAttribute('data-merk', g.i); m.setAttribute('aria-label', '„' + g.n + '“ merken');
    }
  }

  // ---- Spiele-Lexikon: Filter
  var liste = $('#liste');
  if (liste && $('#filter')) {
    var items = $$('li', liste);
    var SEITE = 60;
    var zeigen = SEITE;
    var f = { suche: $('#f-suche'), stufe: $('#f-stufe'), phase: $('#f-phase'), thema: $('#f-thema'), ohne: $('#f-ohne'), anl: $('#f-anl') };
    var treffer = $('#treffer'), mehr = $('#mehr'), leer = $('#leer');
    // Filter in der Adresse merken (teilbar, Zurück-Taste funktioniert)
    var q = new URLSearchParams(location.search);
    if (q.get('q')) f.suche.value = q.get('q');
    if (q.get('stufe')) f.stufe.value = q.get('stufe');
    if (q.get('teil')) f.phase.value = q.get('teil');
    if (q.get('thema')) f.thema.value = q.get('thema');
    if (q.get('ohne')) f.ohne.checked = true;
    if (q.get('anleitung')) f.anl.checked = true;
    var norm = function (t) { return t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss'); };
    function anwenden(zuruecksetzen) {
      if (zuruecksetzen) zeigen = SEITE;
      var worte = norm(f.suche.value.trim()).split(/\s+/).filter(Boolean);
      var st = parseInt(f.stufe.value, 10);
      var n = 0;
      items.forEach(function (li) {
        var d = li.dataset;
        var ok = (!st || (st >= +d.von && st <= +d.bis)) &&
          (!f.phase.value || d.phasen.indexOf(f.phase.value) >= 0) &&
          (!f.thema.value || (' ' + d.themen + ' ').indexOf(' ' + f.thema.value + ' ') >= 0) &&
          (!f.ohne.checked || d.ohne === '1') && (!f.anl.checked || d.anl === '1') &&
          worte.every(function (w) { return norm(d.suche).indexOf(w) >= 0; });
        if (ok) n++;
        li.hidden = !ok || n > zeigen;
      });
      treffer.textContent = n === 1 ? '1 Spiel' : n + ' Spiele';
      mehr.hidden = n <= zeigen;
      leer.hidden = n > 0;
      var p = new URLSearchParams();
      if (f.suche.value.trim()) p.set('q', f.suche.value.trim());
      if (f.stufe.value) p.set('stufe', f.stufe.value);
      if (f.phase.value) p.set('teil', f.phase.value);
      if (f.thema.value) p.set('thema', f.thema.value);
      if (f.ohne.checked) p.set('ohne', '1');
      if (f.anl.checked) p.set('anleitung', '1');
      var s = p.toString();
      try { history.replaceState(null, '', location.pathname + (s ? '?' + s : '')); } catch (e) { /* egal */ }
    }
    var timer;
    f.suche.addEventListener('input', function () { clearTimeout(timer); timer = setTimeout(function () { anwenden(true); }, 120); });
    ['stufe', 'phase', 'thema', 'ohne', 'anl'].forEach(function (k) { f[k].addEventListener('change', function () { anwenden(true); }); });
    mehr.addEventListener('click', function () { zeigen += SEITE; anwenden(false); });
    anwenden(true);
  }

  // ---- Startseite: Zufallsspiel
  var karte = $('#spielkarte');
  var datenEl = $('#zufall-daten');
  if (karte && datenEl) {
    var spiele = JSON.parse(datenEl.textContent);
    var basis = JSON.parse($('#zufall-basis').textContent);
    var bereich = [1, 4];
    var zuletzt = null;
    function spielUrl(s) { return basis.spiele.replace(/index\.html$/, '') + s + '/' + (basis.vorschau ? 'index.html' : ''); }
    function neu() {
      var passt = spiele.filter(function (s) { return s.v <= bereich[1] && s.b >= bereich[0] && s.n !== zuletzt; });
      if (!passt.length) return;
      var s = passt[Math.floor(Math.random() * passt.length)];
      zuletzt = s.n;
      karte.innerHTML = '<div class="chips"><span class="chip">' + esc(s.st) + ' Schulstufe</span>' + (s.d ? '<span class="chip">' + esc(s.d) + '</span>' : '') +
        '<span class="chip">' + esc(s.p.join(', ')) + '</span></div><h3>' + esc(s.n) + '</h3><p>' + esc(s.t) + '</p><p><b style="color:#fff">Material:</b> ' + esc(s.m) + '</p>' +
        '<div class="knopfreihe"><a class="knopf" href="' + spielUrl(s.s) + '">Zum Spiel mit Video</a></div>';
    }
    $$('.stufenwahl button').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('.stufenwahl button').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        bereich = b.getAttribute('data-stufe').split('-').map(Number);
        neu();
      });
    });
    $('#zufall-los').addEventListener('click', neu);
    neu();
  }

  // ---- Startseite: Welcher Band passt?
  var wEl = $('#waehler-daten');
  if (wEl) {
    var w = JSON.parse(wEl.textContent);
    var ziel = $('#waehler-ergebnis');
    $$('#waehler button[data-ziel]').forEach(function (b) {
      b.addEventListener('click', function () {
        $$('#waehler button[data-ziel]').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
        var d = w[b.getAttribute('data-ziel')];
        ziel.innerHTML = '<div class="empfehlung"><img src="' + d.c + '" alt="" width="88" height="124"><div><h3>' + esc(d.t) + '</h3><p>' + esc(d.x) + '</p>' +
          '<a class="knopf primaer klein" href="' + d.u + '">Ansehen · ' + esc(d.p) + '</a></div></div>';
        // Am Handy liegt das Ergebnis unter den Knöpfen → sichtbar machen
        var r = ziel.getBoundingClientRect();
        if (r.bottom > window.innerHeight || r.top < 0) ziel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      });
    });
  }
  merkStatus(document); // zuletzt: auch für das Spiel der Woche
})();
