// Sportunterricht – Raumplaner: Geräte maßstabsgetreu in die Halle ziehen.
// Einheit überall: Zentimeter. Der Plan bleibt nur auf diesem Gerät (localStorage) oder steckt im geteilten Link.
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (t) { return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var svg = $('#rp-svg');
  if (!svg) return;
  var NS = 'http://www.w3.org/2000/svg';
  var RAND = 160; // Platz rund um die Halle (für Maße und zum Hinausziehen)
  var SPEICHER = 'su-raumplan';
  var SCHRIFT = 'Arial, Helvetica, sans-serif';

  // Typische Gerätemaße (Länge × Breite in cm) – Richtwerte, keine Normangaben
  var T = {
    langbank: { n: 'Langbank', w: 300, h: 30, f: '#b9853f' },
    weichboden: { n: 'Weichboden', w: 300, h: 200, f: '#2f63c4' },
    matte: { n: 'Turnmatte', w: 200, h: 100, f: '#5b9be3' },
    kasten: { n: 'Kasten', w: 160, h: 50, f: '#c49152' },
    bock: { n: 'Bock', w: 60, h: 40, f: '#9b6a35' },
    sprungbrett: { n: 'Sprungbrett', w: 120, h: 60, f: '#d8b06a' },
    minitramp: { n: 'Minitrampolin', w: 110, h: 110, f: '#2b2b2b', form: 'tramp' },
    reck: { n: 'Reck', w: 240, h: 24, f: '#7a7a7a', form: 'stange' },
    barren: { n: 'Barren', w: 350, h: 60, f: '#8a6a45', form: 'barren' },
    ringe: { n: 'Ringpaar', w: 70, h: 30, f: '#6f6f6f', form: 'ringe' },
    sprossenwand: { n: 'Sprossenwand', w: 100, h: 24, f: '#a07b4f', form: 'sprossen' },
    tor: { n: 'Tor', w: 300, h: 100, f: '#d63b2a', form: 'tor' },
    korb: { n: 'Basketballkorb', w: 180, h: 60, f: '#e8730c', form: 'korb' },
    netz: { n: 'Netz', w: 900, h: 14, f: '#444444', form: 'netz' },
    huetchen: { n: 'Hütchen', w: 36, h: 36, f: '#f28c28', form: 'kegel' },
    reifen: { n: 'Reifen', w: 80, h: 80, f: '#d9407f', form: 'ring' },
    ball: { n: 'Ball', w: 30, h: 30, f: '#e9b400', form: 'kreis' },
    station: { n: 'Station', w: 90, h: 90, f: '#13211b', form: 'station', ohneListe: true },
    person: { n: 'Schüler:in', w: 50, h: 50, f: '#1f5bd8', form: 'person', ohneListe: true },
    lehrkraft: { n: 'Lehrkraft', w: 56, h: 56, f: '#c8402a', form: 'lehrkraft', ohneListe: true },
    pfeil: { n: 'Laufweg', w: 300, h: 40, f: '#13211b', form: 'pfeil', ohneListe: true },
    text: { n: 'Notiz', w: 260, h: 60, f: '#13211b', form: 'text', ohneListe: true }
  };
  var GRUPPEN = [['Turnen', ['langbank', 'weichboden', 'matte', 'kasten', 'bock', 'sprungbrett', 'minitramp', 'reck', 'barren', 'ringe', 'sprossenwand']],
    ['Spiel', ['tor', 'korb', 'netz', 'huetchen', 'reifen', 'ball']], ['Planung', ['station', 'person', 'lehrkraft', 'pfeil', 'text']]];

  var plan = { l: 2700, b: 1500, linien: true, raster: false, dinge: [], titel: '', notizen: '', nr: 1 };
  var auswahl = null, verlauf = [], ziehen = null;

  // ---------------------------------------------------------------- Zeichnen
  function el(name, attr, kinder) {
    var e = document.createElementNS(NS, name);
    for (var k in attr) e.setAttribute(k, attr[k]);
    (kinder || []).forEach(function (c) { e.appendChild(c); });
    return e;
  }
  function schrift(text, groesse, farbe, extra) {
    var t = el('text', Object.assign({ x: 0, y: 0, 'text-anchor': 'middle', 'dominant-baseline': 'central', 'font-family': SCHRIFT, 'font-weight': 700, 'font-size': groesse, fill: farbe }, extra || {}));
    t.textContent = text;
    return t;
  }
  // Form eines Geräts, Mittelpunkt bei 0/0
  function form(d) {
    var t = T[d.t], w = t.w, h = t.h, f = t.f, g = el('g');
    var r = function (x, y, ww, hh, fill, extra) { return el('rect', Object.assign({ x: x, y: y, width: ww, height: hh, fill: fill }, extra || {})); };
    switch (t.form) {
      case 'tramp': g.appendChild(el('circle', { r: w / 2, fill: '#d9d9d9', stroke: f, 'stroke-width': 10 })); g.appendChild(el('circle', { r: w / 2 - 18, fill: f })); break;
      case 'stange': g.appendChild(r(-w / 2, -3, w, 6, f)); g.appendChild(r(-w / 2, -h / 2, 10, h, '#555')); g.appendChild(r(w / 2 - 10, -h / 2, 10, h, '#555')); break;
      case 'barren': g.appendChild(r(-w / 2, -h / 2, w, 7, f, { rx: 3 })); g.appendChild(r(-w / 2, h / 2 - 7, w, 7, f, { rx: 3 })); g.appendChild(r(-w / 2 + 40, -h / 2, 12, h, '#555')); g.appendChild(r(w / 2 - 52, -h / 2, 12, h, '#555')); break;
      case 'ringe': g.appendChild(el('circle', { cx: -w / 4, r: 13, fill: 'none', stroke: f, 'stroke-width': 6 })); g.appendChild(el('circle', { cx: w / 4, r: 13, fill: 'none', stroke: f, 'stroke-width': 6 })); break;
      case 'sprossen': g.appendChild(r(-w / 2, -h / 2, w, h, '#e9d8bf', { stroke: f, 'stroke-width': 4 })); for (var i = 1; i < 8; i++) g.appendChild(r(-w / 2 + i * w / 8 - 2, -h / 2, 4, h, f)); break;
      case 'tor': g.appendChild(el('path', { d: 'M' + (-w / 2) + ' ' + (h / 2) + 'V' + (-h / 2) + 'H' + (w / 2) + 'V' + (h / 2), fill: 'rgba(214,59,42,.12)', stroke: f, 'stroke-width': 10, 'stroke-linejoin': 'round' })); break;
      case 'korb': g.appendChild(r(-w / 2, -h / 2, w, 10, f)); g.appendChild(el('circle', { cy: 8, r: 23, fill: 'none', stroke: f, 'stroke-width': 6 })); break;
      case 'netz': g.appendChild(el('line', { x1: -w / 2, x2: w / 2, y1: 0, y2: 0, stroke: f, 'stroke-width': 6, 'stroke-dasharray': '22 10' })); g.appendChild(el('circle', { cx: -w / 2, r: 8, fill: f })); g.appendChild(el('circle', { cx: w / 2, r: 8, fill: f })); break;
      case 'kegel': g.appendChild(el('circle', { r: w / 2, fill: f })); g.appendChild(el('circle', { r: w / 5, fill: '#fff' })); break;
      case 'ring': g.appendChild(el('circle', { r: w / 2 - 4, fill: 'none', stroke: f, 'stroke-width': 8 })); break;
      case 'kreis': g.appendChild(el('circle', { r: w / 2, fill: f, stroke: '#8a6a00', 'stroke-width': 3 })); break;
      case 'station': g.appendChild(el('circle', { r: w / 2, fill: f })); g.appendChild(schrift(d.n || '?', 50, '#fff')); break;
      case 'person': g.appendChild(el('circle', { r: w / 2, fill: f, stroke: '#fff', 'stroke-width': 5 })); break;
      case 'lehrkraft': g.appendChild(el('circle', { r: w / 2, fill: f, stroke: '#fff', 'stroke-width': 5 })); g.appendChild(schrift('L', 34, '#fff')); break;
      case 'pfeil': g.appendChild(el('path', { d: 'M' + (-w / 2) + ' 0H' + (w / 2 - 40) + 'M' + (w / 2 - 50) + ' -24L' + (w / 2) + ' 0L' + (w / 2 - 50) + ' 24', fill: 'none', stroke: f, 'stroke-width': 10, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' })); break;
      case 'text': g.appendChild(r(-w / 2, -h / 2, w, h, 'rgba(255,255,255,.9)', { rx: 10, stroke: f, 'stroke-width': 3 })); g.appendChild(schrift(d.n || 'Notiz', 34, f)); break;
      default:
        g.appendChild(r(-w / 2, -h / 2, w, h, f, { rx: Math.min(10, h / 4), stroke: 'rgba(0,0,0,.25)', 'stroke-width': 2 }));
        if (w >= 150 && h >= 30) g.appendChild(schrift(t.n, Math.min(36, h * 0.62), '#fff'));
    }
    return g;
  }
  function trans(d) { return 'translate(' + d.x + ' ' + d.y + ') rotate(' + d.r + ')'; }
  function beschrift(d) { return T[d.t].n + (d.t === 'station' ? ' ' + d.n : d.t === 'text' ? ': ' + d.n : '') + (d.r ? ', gedreht um ' + d.r + ' Grad' : ''); }

  function zeichneHalle() {
    var L = plan.l, B = plan.b;
    svg.setAttribute('viewBox', (-RAND) + ' ' + (-RAND) + ' ' + (L + 2 * RAND) + ' ' + (B + 2 * RAND));
    svg.innerHTML = '';
    var h = el('g', { id: 'rp-halle' });
    h.appendChild(el('rect', { x: -RAND, y: -RAND, width: L + 2 * RAND, height: B + 2 * RAND, fill: '#e3e7e4' }));
    h.appendChild(el('rect', { x: 0, y: 0, width: L, height: B, fill: '#f3e3c3', stroke: '#6b5a3a', 'stroke-width': 8 }));
    if (plan.raster) for (var x = 100; x < L; x += 100) h.appendChild(el('line', { x1: x, x2: x, y1: 0, y2: B, stroke: 'rgba(0,0,0,.09)', 'stroke-width': 2 }));
    if (plan.raster) for (var y = 100; y < B; y += 100) h.appendChild(el('line', { x1: 0, x2: L, y1: y, y2: y, stroke: 'rgba(0,0,0,.09)', 'stroke-width': 2 }));
    if (plan.linien) {
      h.appendChild(el('line', { x1: L / 2, x2: L / 2, y1: 0, y2: B, stroke: '#ffffff', 'stroke-width': 6 }));
      h.appendChild(el('circle', { cx: L / 2, cy: B / 2, r: Math.min(180, B / 5), fill: 'none', stroke: '#ffffff', 'stroke-width': 6 }));
      h.appendChild(el('rect', { x: 60, y: 60, width: L - 120, height: B - 120, fill: 'none', stroke: '#ffffff', 'stroke-width': 6 }));
    }
    // Maße an den Rändern und Maßstab
    var mL = schrift((L / 100).toLocaleString('de-AT') + ' m', 60, '#3f5048'); mL.setAttribute('transform', 'translate(' + L / 2 + ' ' + (-RAND / 2) + ')');
    var mB = schrift((B / 100).toLocaleString('de-AT') + ' m', 60, '#3f5048'); mB.setAttribute('transform', 'translate(' + (-RAND / 2) + ' ' + B / 2 + ') rotate(-90)');
    h.appendChild(mL); h.appendChild(mB);
    var sk = el('g', { transform: 'translate(' + (L - 500) + ' ' + (B + RAND / 2) + ')' });
    sk.appendChild(el('path', { d: 'M0 -12V12M0 0H500M500 -12V12', stroke: '#3f5048', 'stroke-width': 6, fill: 'none' }));
    var st = schrift('5 m', 46, '#3f5048'); st.setAttribute('transform', 'translate(250 -40)'); sk.appendChild(st);
    h.appendChild(sk);
    svg.appendChild(h);
    svg.appendChild(el('g', { id: 'rp-dinge' }));
    zeichneDinge();
  }
  function zeichneDinge() {
    var g = $('#rp-dinge', svg);
    g.innerHTML = '';
    plan.dinge.forEach(function (d) {
      var t = T[d.t];
      var e = el('g', { class: 'rp-ding' + (d === auswahl ? ' gewaehlt' : ''), 'data-id': d.id, transform: trans(d), tabindex: 0, role: 'button', 'aria-label': beschrift(d) });
      if (d === auswahl) e.appendChild(el('rect', { class: 'rp-rahmen', x: -t.w / 2 - 14, y: -t.h / 2 - 14, width: t.w + 28, height: t.h + 28, rx: 12, fill: 'none', stroke: '#1f5bd8', 'stroke-width': 6, 'stroke-dasharray': '18 10' }));
      // unsichtbare, etwas größere Greiffläche – kleine Teile lassen sich so auch mit dem Finger fassen
      e.appendChild(el('rect', { x: -Math.max(t.w, 70) / 2, y: -Math.max(t.h, 70) / 2, width: Math.max(t.w, 70), height: Math.max(t.h, 70), fill: 'transparent' }));
      e.appendChild(form(d));
      g.appendChild(e);
    });
    liste();
    leiste();
  }

  // ---------------------------------------------------------------- Zustand
  function speichern() { try { localStorage.setItem(SPEICHER, JSON.stringify(plan)); } catch (e) { /* privat */ } }
  function merke() { verlauf.push(JSON.stringify(plan)); if (verlauf.length > 60) verlauf.shift(); $('#rp-zurueck').disabled = false; }
  function zurueck() {
    if (!verlauf.length) return;
    plan = JSON.parse(verlauf.pop());
    auswahl = null;
    $('#rp-zurueck').disabled = !verlauf.length;
    formular(); zeichneHalle(); speichern();
    meldung('Rückgängig gemacht.');
  }
  function meldung(t) { var m = $('#rp-meldung'); m.textContent = t; m.hidden = false; clearTimeout(meldung.t); meldung.t = setTimeout(function () { m.hidden = true; }, 3500); }
  function finde(id) { return plan.dinge.filter(function (d) { return d.id === id; })[0]; }
  var raster = function (v) { return Math.round(v / 10) * 10; };
  function klemme(d) { d.x = Math.max(0, Math.min(plan.l, raster(d.x))); d.y = Math.max(0, Math.min(plan.b, raster(d.y))); }

  function neu(typ, x, y) {
    merke();
    var d = { id: 'd' + Date.now().toString(36) + Math.floor(Math.random() * 1e4), t: typ, x: x, y: y, r: 0 };
    if (typ === 'station') { d.n = String(plan.dinge.filter(function (z) { return z.t === 'station'; }).length + 1); }
    if (typ === 'text') { var txt = window.prompt('Text für die Notiz:', 'Start'); if (txt === null) { verlauf.pop(); return null; } d.n = txt.slice(0, 30) || 'Notiz'; }
    klemme(d);
    plan.dinge.push(d);
    auswahl = d;
    zeichneDinge(); speichern();
    return d;
  }
  function freierPlatz() { // neue Teile nicht exakt übereinander legen
    var n = plan.dinge.length % 12;
    return { x: plan.l / 2 + (n % 4 - 1.5) * 120, y: plan.b / 2 + (Math.floor(n / 4) - 1) * 120 };
  }
  function waehle(d, fokus) {
    auswahl = d || null;
    zeichneDinge();
    if (d && fokus) { var e = $('.rp-ding[data-id="' + d.id + '"]', svg); if (e) e.focus({ preventScroll: true }); } // Leiste bleibt im Blick
  }
  function aktion(a) {
    var d = auswahl;
    if (!d) return;
    if (a === 'drehen') { merke(); d.r = (d.r + 45) % 360; }
    if (a === 'kopie') { merke(); var k = Object.assign({}, d, { id: d.id + 'k' + Math.floor(Math.random() * 1e4), x: d.x + 60, y: d.y + 60 }); if (k.t === 'station') k.n = String(plan.dinge.filter(function (z) { return z.t === 'station'; }).length + 1); klemme(k); plan.dinge.push(k); auswahl = k; }
    if (a === 'text') { var t = window.prompt(d.t === 'station' ? 'Nummer oder Name der Station:' : 'Text der Notiz:', d.n || ''); if (t === null) return; merke(); d.n = t.slice(0, d.t === 'station' ? 4 : 30) || d.n; }
    if (a === 'loeschen') { merke(); plan.dinge.splice(plan.dinge.indexOf(d), 1); auswahl = null; meldung(T[d.t].n + ' entfernt. „Rückgängig“ holt es zurück.'); }
    zeichneDinge(); speichern();
    if (auswahl) waehle(auswahl, true);
  }

  // ---------------------------------------------------------------- Leiste, Auswahl, Liste
  function symbol(typ) {
    var t = T[typ], gr = Math.max(t.w, t.h, 60) + 30;
    var s = el('svg', { viewBox: (-gr / 2) + ' ' + (-gr / 2) + ' ' + gr + ' ' + gr, 'aria-hidden': 'true', focusable: 'false' });
    var f = form({ t: typ, n: typ === 'station' ? '1' : typ === 'text' ? 'Aa' : '' });
    s.appendChild(f);
    return s;
  }
  function baueLeiste() {
    var l = $('#rp-leiste');
    GRUPPEN.forEach(function (gr) {
      var h = document.createElement('span'); h.className = 'rp-gruppe'; h.textContent = gr[0]; l.appendChild(h);
      gr[1].forEach(function (typ) {
        var b = document.createElement('button');
        b.type = 'button'; b.className = 'rp-teil'; b.setAttribute('data-typ', typ);
        b.setAttribute('aria-label', T[typ].n + ' hinzufügen');
        b.appendChild(symbol(typ));
        var s = document.createElement('span'); s.textContent = T[typ].n; b.appendChild(s);
        l.appendChild(b);
      });
    });
  }
  function leiste() {
    var box = $('#rp-auswahl');
    box.hidden = !auswahl;
    if (!auswahl) return;
    $('#rp-auswahl-name').textContent = beschrift(auswahl);
    var tk = $('#rp-text-knopf');
    tk.hidden = auswahl.t !== 'station' && auswahl.t !== 'text';
    tk.textContent = auswahl.t === 'station' ? '✎ Nummer' : '✎ Text';
  }
  function liste() {
    var z = {}, stationen = 0;
    plan.dinge.forEach(function (d) { if (d.t === 'station') stationen++; if (!T[d.t].ohneListe) z[d.t] = (z[d.t] || 0) + 1; });
    var reihen = Object.keys(T).filter(function (k) { return z[k]; }).map(function (k) { return '<li><b>' + z[k] + ' ×</b> ' + esc(T[k].n) + '</li>'; });
    if (stationen) reihen.push('<li><b>' + stationen + '</b> ' + (stationen === 1 ? 'Station' : 'Stationen') + '</li>');
    $('#rp-liste').innerHTML = reihen.length ? reihen.join('') : '<li class="leer">Noch keine Geräte in der Halle.</li>';
  }

  // ---------------------------------------------------------------- Zeiger (Maus, Finger, Stift)
  function punkt(e) {
    var p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY;
    return p.matrixTransform(svg.getScreenCTM().inverse());
  }
  function draussen(d) { return d.x < -60 || d.y < -60 || d.x > plan.l + 60 || d.y > plan.b + 60; }

  svg.addEventListener('pointerdown', function (e) {
    var g = e.target.closest('.rp-ding');
    if (!g) { if (auswahl) waehle(null); return; }
    var d = finde(g.getAttribute('data-id'));
    if (!d) return;
    e.preventDefault();
    if (auswahl !== d) waehle(d);
    var p = punkt(e);
    ziehen = { d: d, dx: p.x - d.x, dy: p.y - d.y, vorher: JSON.stringify(plan), bewegt: false, id: e.pointerId };
    svg.setPointerCapture(e.pointerId);
  });
  svg.addEventListener('pointermove', function (e) {
    if (!ziehen || e.pointerId !== ziehen.id) return;
    var p = punkt(e), d = ziehen.d;
    d.x = raster(p.x - ziehen.dx); d.y = raster(p.y - ziehen.dy);
    ziehen.bewegt = true;
    var g = $('.rp-ding[data-id="' + d.id + '"]', svg);
    if (g) { g.setAttribute('transform', trans(d)); g.classList.toggle('weg', draussen(d)); }
  });
  function loslassen(e) {
    if (!ziehen || e.pointerId !== ziehen.id) return;
    var z = ziehen; ziehen = null;
    if (!z.bewegt) return;
    verlauf.push(z.vorher); $('#rp-zurueck').disabled = false;
    if (draussen(z.d)) { plan.dinge.splice(plan.dinge.indexOf(z.d), 1); auswahl = null; meldung(T[z.d.t].n + ' entfernt. „Rückgängig“ holt es zurück.'); }
    else klemme(z.d);
    zeichneDinge(); speichern();
  }
  svg.addEventListener('pointerup', loslassen);
  svg.addEventListener('pointercancel', loslassen);

  // Aus der Leiste in die Halle ziehen – oder einfach antippen
  var geist = null, leisteZug = null, letzterZug = 0;
  $('#rp-leiste').addEventListener('pointerdown', function (e) {
    var b = e.target.closest('.rp-teil');
    if (!b || e.button > 0) return;
    leisteZug = { typ: b.getAttribute('data-typ'), x0: e.clientX, y0: e.clientY, id: e.pointerId, aktiv: false, b: b };
  });
  window.addEventListener('pointermove', function (e) {
    if (!leisteZug || e.pointerId !== leisteZug.id) return;
    var dx = e.clientX - leisteZug.x0, dy = e.clientY - leisteZug.y0;
    if (!leisteZug.aktiv) {
      // Finger: waagrecht wischen scrollt die Leiste, senkrecht ziehen holt das Gerät heraus
      var genug = Math.abs(dx) + Math.abs(dy) > 8;
      if (!genug) return;
      if (e.pointerType === 'touch' && Math.abs(dx) > Math.abs(dy)) { leisteZug = null; return; }
      leisteZug.aktiv = true;
      geist = document.createElement('div');
      geist.className = 'rp-geist';
      geist.appendChild(symbol(leisteZug.typ));
      document.body.appendChild(geist);
    }
    e.preventDefault();
    geist.style.transform = 'translate(' + (e.clientX - 32) + 'px,' + (e.clientY - 32) + 'px)';
  }, { passive: false });
  window.addEventListener('pointerup', function (e) {
    if (!leisteZug || e.pointerId !== leisteZug.id) return;
    var z = leisteZug; leisteZug = null;
    if (geist) { geist.remove(); geist = null; }
    if (!z.aktiv) return; // war ein Antippen → „click“ fügt hinzu
    letzterZug = Date.now(); // der folgende „click“ gehört zum Ziehen, nicht zum Antippen
    var r = svg.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) return;
    var p = punkt(e);
    var d = neu(z.typ, p.x, p.y);
    if (d) meldung(T[d.t].n + ' hinzugefügt.');
  });
  $('#rp-leiste').addEventListener('click', function (e) {
    var b = e.target.closest('.rp-teil');
    if (!b) return;
    if (Date.now() - letzterZug < 400) return;
    var p = freierPlatz();
    var d = neu(b.getAttribute('data-typ'), p.x, p.y);
    if (d) { waehle(d, true); meldung(T[d.t].n + ' in die Hallenmitte gelegt – jetzt verschieben.'); }
  });

  // ---------------------------------------------------------------- Tastatur
  svg.addEventListener('focusin', function (e) {
    var g = e.target.closest('.rp-ding');
    if (g && (!auswahl || auswahl.id !== g.getAttribute('data-id'))) { auswahl = finde(g.getAttribute('data-id')); leiste(); $$('.rp-ding', svg).forEach(function (x) { x.classList.toggle('gewaehlt', x === g); }); }
  });
  svg.addEventListener('keydown', function (e) {
    if (!auswahl) return;
    var schritt = e.shiftKey ? 50 : 10, d = auswahl;
    var bew = { ArrowLeft: [-schritt, 0], ArrowRight: [schritt, 0], ArrowUp: [0, -schritt], ArrowDown: [0, schritt] }[e.key];
    if (bew) { e.preventDefault(); merke(); d.x += bew[0]; d.y += bew[1]; klemme(d); zeichneDinge(); speichern(); waehle(d, true); return; }
    if (e.key === 'r' || e.key === 'R') { e.preventDefault(); merke(); d.r = (d.r + (e.shiftKey ? 345 : 15)) % 360; zeichneDinge(); speichern(); waehle(d, true); }
    if (e.key === 'Delete' || e.key === 'Backspace') { e.preventDefault(); aktion('loeschen'); svg.focus(); }
    if (e.key === 'd' || e.key === 'D') { e.preventDefault(); aktion('kopie'); }
    if (e.key === 'Escape') { waehle(null); }
  });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) { e.preventDefault(); zurueck(); }
  });
  $('#rp-auswahl').addEventListener('click', function (e) { var b = e.target.closest('[data-aktion]'); if (b) aktion(b.getAttribute('data-aktion')); });

  // ---------------------------------------------------------------- Halle, Vorlagen
  function formular() {
    var wert = plan.l + 'x' + plan.b;
    var sel = $('#rp-halle');
    sel.value = $$('option', sel).some(function (o) { return o.value === wert; }) ? wert : 'eigene';
    $('#rp-eigen').hidden = sel.value !== 'eigene';
    $('#rp-l').value = plan.l / 100; $('#rp-b').value = plan.b / 100;
    $('#rp-linien').checked = plan.linien; $('#rp-raster').checked = plan.raster;
    $('#rp-titel').value = plan.titel || ''; $('#rp-notizen').value = plan.notizen || '';
  }
  function halle(l, b) {
    merke();
    plan.l = l; plan.b = b;
    plan.dinge.forEach(klemme);
    zeichneHalle(); speichern();
  }
  $('#rp-halle').addEventListener('change', function () {
    $('#rp-eigen').hidden = this.value !== 'eigene';
    if (this.value === 'eigene') { $('#rp-l').focus(); return; }
    var m = this.value.split('x').map(Number); halle(m[0], m[1]);
  });
  ['#rp-l', '#rp-b'].forEach(function (s) {
    $(s).addEventListener('change', function () {
      var l = Math.round(Math.max(4, Math.min(80, +$('#rp-l').value || 27)) * 100), b = Math.round(Math.max(3, Math.min(60, +$('#rp-b').value || 15)) * 100);
      halle(l, b);
    });
  });
  $('#rp-linien').addEventListener('change', function () { plan.linien = this.checked; zeichneHalle(); speichern(); });
  $('#rp-raster').addEventListener('change', function () { plan.raster = this.checked; zeichneHalle(); speichern(); });
  $('#rp-titel').addEventListener('input', function () { plan.titel = this.value; speichern(); });
  $('#rp-notizen').addEventListener('input', function () { plan.notizen = this.value; speichern(); });

  function vorlage(name) {
    var L = plan.l, B = plan.b, l = [];
    var add = function (t, x, y, r, n) { l.push({ id: 'v' + l.length + Date.now().toString(36), t: t, x: Math.round(x), y: Math.round(y), r: r || 0, n: n }); };
    if (name === 'zirkel') {
      var geraet = ['langbank', 'matte', 'kasten', 'reifen', 'huetchen', 'sprungbrett', 'matte', 'ball'];
      for (var i = 0; i < 8; i++) {
        var oben = i < 4, sp = i % 4;
        var x = L * (0.14 + sp * 0.24), y = oben ? B * 0.24 : B * 0.76;
        if (!oben) x = L - x;
        add('station', x, y + (oben ? -B * 0.12 : B * 0.12), 0, String(i + 1));
        add(geraet[i], x, y);
      }
      add('pfeil', L / 2, B / 2 - 90, 0); add('pfeil', L / 2, B / 2 + 90, 180); add('lehrkraft', L / 2, B / 2);
    } else if (name === 'geraete') {
      add('station', L * 0.1, B * 0.12, 0, '1'); add('sprungbrett', L * 0.12, B * 0.3); add('kasten', L * 0.12 + 150, B * 0.3); add('weichboden', L * 0.12 + 360, B * 0.3);
      add('station', L * 0.62, B * 0.12, 0, '2'); add('barren', L * 0.7, B * 0.25); add('matte', L * 0.7, B * 0.25 - 80); add('matte', L * 0.7, B * 0.25 + 80);
      add('station', L * 0.08, B * 0.66, 0, '3'); add('langbank', L * 0.16, B * 0.75); add('langbank', L * 0.16 + 320, B * 0.75, 45); add('langbank', L * 0.16 + 600, B * 0.75 + 110);
      add('station', L * 0.6, B * 0.6, 0, '4'); add('minitramp', L * 0.66, B * 0.78); add('weichboden', L * 0.66 + 270, B * 0.78);
      add('station', L * 0.88, B * 0.48, 0, '5'); add('reck', L * 0.9, B * 0.62, 90); add('matte', L * 0.9 - 100, B * 0.62, 90);
      add('lehrkraft', L / 2, B / 2);
    } else if (name === 'spiel') {
      for (var k = 0; k * 300 < B; k++) add('langbank', L / 2, 150 + k * 300, 90);
      add('tor', 60, B / 2, 90); add('tor', L / 2 - 60, B / 2, 270); add('tor', L / 2 + 60, B / 2, 90); add('tor', L - 60, B / 2, 270);
      add('ball', L / 4, B / 2); add('ball', L * 3 / 4, B / 2); add('lehrkraft', L / 2, B - 90);
    }
    l.forEach(klemme);
    return l;
  }
  $('#rp-vorlage').addEventListener('change', function () {
    var v = this.value; this.value = '';
    if (!v) return;
    if (plan.dinge.length && !window.confirm('Die Vorlage ersetzt deinen aktuellen Plan. Fortfahren? (Rückgängig ist danach möglich.)')) return;
    merke();
    plan.dinge = vorlage(v); auswahl = null;
    zeichneDinge(); speichern();
    meldung(v === 'leer' ? 'Halle geleert.' : 'Vorlage geladen – passe sie an deine Halle an.');
  });
  $('#rp-neu').addEventListener('click', function () {
    if (!plan.dinge.length) return;
    if (!window.confirm('Alle Geräte aus der Halle entfernen?')) return;
    merke(); plan.dinge = []; auswahl = null; zeichneDinge(); speichern(); meldung('Halle geleert. „Rückgängig“ holt alles zurück.');
  });
  $('#rp-zurueck').addEventListener('click', zurueck);

  // ---------------------------------------------------------------- Drucken, Bild, Link
  function druckkopf() { $('#rp-druck-titel').textContent = plan.titel || 'Raumplan'; $('#rp-druck-notizen').textContent = plan.notizen || ''; }
  window.addEventListener('beforeprint', druckkopf); // auch für Strg+P
  $('#rp-drucken').addEventListener('click', function () { waehle(null); druckkopf(); window.print(); });
  $('#rp-bild').addEventListener('click', function () {
    var alt = auswahl; waehle(null);
    var kopie = svg.cloneNode(true);
    var vb = svg.viewBox.baseVal, breite = 2400, hoehe = Math.round(breite * vb.height / vb.width);
    kopie.setAttribute('width', breite); kopie.setAttribute('height', hoehe);
    $$('[tabindex]', kopie).forEach(function (x) { x.removeAttribute('tabindex'); });
    if (plan.titel) { var t = schrift(plan.titel, 64, '#13211b', { 'text-anchor': 'start' }); t.setAttribute('transform', 'translate(0 ' + (-RAND / 2) + ')'); kopie.appendChild(t); }
    var daten = new XMLSerializer().serializeToString(kopie);
    var img = new Image();
    img.onload = function () {
      var c = document.createElement('canvas'); c.width = breite; c.height = hoehe;
      var ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, breite, hoehe); ctx.drawImage(img, 0, 0, breite, hoehe);
      c.toBlob(function (blob) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = (plan.titel || 'Raumplan').replace(/[^\wäöüÄÖÜß -]+/g, '').trim().replace(/\s+/g, '-') + '.png';
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
        meldung('Bild gespeichert – du findest es in deinen Downloads.');
      }, 'image/png');
    };
    img.onerror = function () { meldung('Das Bild konnte nicht erstellt werden. Tipp: „Drucken“ und als PDF speichern.'); };
    img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(daten);
    if (alt) waehle(alt);
  });
  function kodieren() {
    var kurz = { h: [plan.l, plan.b], li: plan.linien ? 1 : 0, ti: plan.titel || '', d: plan.dinge.map(function (d) { return [d.t, d.x, d.y, d.r].concat(d.n ? [d.n] : []); }) };
    var bytes = new TextEncoder().encode(JSON.stringify(kurz)), s = '';
    bytes.forEach(function (b) { s += String.fromCharCode(b); });
    return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
  }
  function dekodieren(text) {
    var s = atob(text.replace(/-/g, '+').replace(/_/g, '/'));
    var bytes = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) bytes[i] = s.charCodeAt(i);
    var k = JSON.parse(new TextDecoder().decode(bytes));
    var p = { l: Math.max(400, Math.min(8000, +k.h[0])), b: Math.max(300, Math.min(6000, +k.h[1])), linien: !!k.li, raster: false, titel: String(k.ti || '').slice(0, 80), notizen: '', dinge: [] };
    (k.d || []).slice(0, 400).forEach(function (x, i) {
      if (!T[x[0]]) return;
      var d = { id: 'l' + i, t: x[0], x: +x[1] || 0, y: +x[2] || 0, r: (+x[3] || 0) % 360 };
      if (x[4] != null) d.n = String(x[4]).slice(0, 30);
      p.dinge.push(d);
    });
    return p;
  }
  $('#rp-link').addEventListener('click', function () {
    var url = location.href.split('#')[0] + '#plan=' + kodieren();
    var ok = function () { meldung('Link kopiert – wer ihn öffnet, sieht genau diesen Plan.'); };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(url).then(ok, function () { window.prompt('Link zum Kopieren:', url); });
    else window.prompt('Link zum Kopieren:', url);
  });

  // ---------------------------------------------------------------- Start
  baueLeiste();
  var geladen = false;
  var m = location.hash.match(/plan=([\w-]+)/);
  if (m) { try { plan = dekodieren(m[1]); geladen = true; } catch (e) { /* kaputter Link → gespeicherter Plan */ } }
  if (!geladen) { try { var s = JSON.parse(localStorage.getItem(SPEICHER)); if (s && s.dinge) plan = Object.assign(plan, s); } catch (e) { /* nichts gespeichert */ } }
  plan.dinge = plan.dinge.filter(function (d) { return T[d.t]; });
  formular();
  zeichneHalle();
  if (geladen) { speichern(); meldung('Geteilter Plan geladen.'); }
})();
