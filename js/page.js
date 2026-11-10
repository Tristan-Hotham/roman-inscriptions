/* Where Romans wrote: Latin inscriptions (LIRE v2.1) in hexagons on a plain MapLibre base map (OpenFreeMap Positron), with a
 * 25-year time slider (aoristic counts), a filter by kind of inscription, soldiers' journeys from stated origin to the stone,
 * province outlines of about AD 117 (DARE), search by findspot, and popups with links to EDCS and EDH.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const TYPEL = ['epitaphs', 'votive inscriptions', 'honorific inscriptions', 'building inscriptions', 'milestones', 'other kinds'];
  const SEQ = ['#FBE9D6', '#F4C9A0', '#E89A63', '#D06A38', '#A9411F', '#6E2412'];
  const BRK_ALL = [1, 3, 10, 30, 100, 300];
  const BRK_BIN = [0.2, 0.6, 2, 6, 20, 60];
  const fmtYr = y => y < 0 ? `${-y} BC` : `AD ${y}`;
  let map = null, H = null, site = null, places = null, flows = null;
  let type = 'all', bin = null;          // bin null = all years
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  // ---- hexagon geometry (flat-topped, Web Mercator) ----
  const R0 = 6378137;
  const m2ll = (x, y) => [x / R0 * 180 / Math.PI, (2 * Math.atan(Math.exp(y / R0)) - Math.PI / 2) * 180 / Math.PI];
  function hexPoly(q, r, rad) {
    const cx = rad * 1.5 * q, cy = rad * Math.sqrt(3) * (r + q / 2), ring = [];
    for (let k = 0; k <= 6; k++) { const a = Math.PI / 3 * (k % 6); ring.push(m2ll(cx + rad * Math.cos(a), cy + rad * Math.sin(a))); }
    return [ring];
  }
  function value(h) {
    if (bin === null) return type === 'all' ? h[4].reduce((a, b) => a + b, 0) : h[4][+type];
    let v = 0; for (const [b, t, w] of h[5]) if (b === bin && (type === 'all' || t === +type)) v += w;
    return v;
  }
  function cls(v) { const B = bin === null ? BRK_ALL : BRK_BIN; let c = -1; for (let i = 0; i < B.length; i++) if (v >= B[i]) c = i; return c; }
  function hexData() {
    const feats = [];
    H.hex.forEach((h, i) => { const v = value(h), c = cls(v); if (c < 0) return; feats.push({ type: 'Feature', id: i, properties: { i, v, c }, geometry: { type: 'Polygon', coordinates: hexPoly(h[0], h[1], H.rad) } }); });
    return { type: 'FeatureCollection', features: feats };
  }
  function keyRows() {
    const B = bin === null ? BRK_ALL : BRK_BIN;
    const lab = bin === null ? ['1 to 2', '3 to 9', '10 to 29', '30 to 99', '100 to 299', '300 or more'] : ['0.2 to 0.5', '0.6 to 1.9', '2 to 5.9', '6 to 19', '20 to 59', '60 or more'];
    document.getElementById('keyTitle').textContent = bin === null ? 'Inscriptions per hexagon' : 'Expected inscriptions per hexagon in these 25 years';
    document.getElementById('keyRows').innerHTML = B.map((b, i) => `<div class="row"><span class="hx" style="background:${SEQ[i]}"></span>${lab[i]}</div>`).join('');
  }
  function refresh() {
    document.querySelectorAll('.chip[data-t]').forEach(x => x.setAttribute('aria-pressed', x.dataset.t === type));
    const yt = document.getElementById('yrTxt'), yn = document.getElementById('yrN');
    if (bin === null) { yt.textContent = 'All years'; yn.textContent = `${site.n.toLocaleString('en-GB')} inscriptions`; }
    else { const b0 = site.bins[bin]; yt.textContent = `${fmtYr(b0)} to ${fmtYr(b0 + 24)}`; yn.textContent = `about ${site.per_bin[bin].toLocaleString('en-GB')} (all kinds)`; }
    keyRows();
    if (map && map.getSource('hex')) map.getSource('hex').setData(hexData());
    const u = new URL(location.href); u.searchParams.set('t', type); u.searchParams.set('bin', bin === null ? 'all' : site.bins[bin]); history.replaceState(null, '', u);
  }
  document.querySelectorAll('.chip[data-t]').forEach(b => b.addEventListener('click', () => { type = b.dataset.t; refresh(); }));
  const yr = document.getElementById('yr');
  yr.addEventListener('input', () => { const v = +yr.value; bin = v >= site.bins.length ? null : v; refresh(); });
  let timer = null; const play = document.getElementById('play');
  play.addEventListener('click', () => {
    if (timer) { clearInterval(timer); timer = null; play.textContent = '▶'; play.setAttribute('aria-label', 'Play through time'); return; }
    play.textContent = '❚❚'; play.setAttribute('aria-label', 'Pause');
    bin = bin === null || bin >= site.bins.length - 1 ? 0 : bin + 1; yr.value = bin; refresh();
    timer = setInterval(() => { if (bin >= site.bins.length - 1) { clearInterval(timer); timer = null; play.textContent = '▶'; return; } bin++; yr.value = bin; refresh(); }, 1100);
  });
  const lp = document.getElementById('lp'), lb = document.getElementById('lyrBtn');
  // review fix: the open panel used to cover the Layers button (no way to close it); now it opens below the search and chips,
  // and has its own close button and Escape
  function setLp(o) {
    if (o) { const r = document.querySelector('.ov-top').getBoundingClientRect(), m = document.getElementById('mapWrap').getBoundingClientRect(); lp.style.top = Math.round(r.bottom - m.top + 6) + 'px'; }
    lp.classList.toggle('open', o); lb.setAttribute('aria-expanded', o);
  }
  lb.addEventListener('click', () => setLp(!lp.classList.contains('open')));
  document.getElementById('lpClose').addEventListener('click', () => { setLp(false); lb.focus(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && lp.classList.contains('open')) setLp(false); });
  function vis(ids, on) { ids.forEach(id => { if (map.getLayer(id)) map.setLayoutProperty(id, 'visibility', on ? 'visible' : 'none'); }); }

  // ---- popups ----
  const edcs = id => `http://db.edcs.eu/epigr/edcs_id.php?s_sprache=en&p_edcs_id=${encodeURIComponent(id)}`;
  const edh = id => `https://edh.ub.uni-heidelberg.de/edh/inschrift/${encodeURIComponent(id)}`;
  function popHex(h, lngLat) {
    const tot = h[4].reduce((a, b) => a + b, 0);
    const per = bin === null ? '' : `<tr><td>${fmtYr(site.bins[bin])} to ${fmtYr(site.bins[bin] + 24)}</td><td>about ${value(h).toFixed(1)}${type === 'all' ? '' : ' ' + TYPEL[+type]}</td></tr>`;
    const kinds = h[4].map((n, t) => n ? `${n.toLocaleString('en-GB')} ${TYPEL[t]}` : '').filter(Boolean).join(', ');
    const pl = h[6].map(p => `${esc(p[0])} (${p[1]})`).join('; ');
    const ex = h[8].map(e => e[0] ? `<a href="${edcs(e[0])}" target="_blank" rel="noopener">${esc(e[0])}</a>` : (e[1] ? `<a href="${edh(e[1])}" target="_blank" rel="noopener">${esc(e[1])}</a>` : '')).filter(Boolean).join(' ');
    const html = `<b class="t">${tot.toLocaleString('en-GB')} inscription${tot === 1 ? '' : 's'}</b><div>${esc(h[9])}${h[7].length ? ' · ' + h[7].map(esc).join(', ') : ''}</div>` +
      `<table>${per}<tr><td>Kinds</td><td>${kinds}</td></tr><tr><td>Findspots</td><td>${pl || 'not named'}</td></tr></table>` +
      `<div class="lk">Examples: ${ex}</div><p class="nt">A hexagon about 35 km across. Counts in a period are aoristic: each inscription is shared evenly over the years of its date range. Sources: EDCS and EDH via LIRE v2.1.</p>`;
    new maplibregl.Popup({ maxWidth: '330px' }).setLngLat(lngLat).setHTML(html).addTo(map);
  }
  function popFlow(p, lngLat) {
    const per = { early: 'dated before AD 101', late: 'dated AD 101 or later', span: 'date range spans AD 100' }[p.per];
    const html = `<b class="t">${esc(p.origin)} to ${esc(p.place || p.prov)}</b><div>${p.n} stone${p.n > 1 ? 's' : ''}, ${per}; ${Math.round(p.km).toLocaleString('en-GB')} km as the crow flies.</div>` +
      `<p class="nt">${p.prec === 'r' ? 'The stone names a people or region (e.g. natione Bessus), so the origin is a point for the region, not a town. ' : 'The stone names a home town (domo or tribe and town).'} Origins read from the text of military inscriptions and matched to the Digital Atlas of the Roman Empire.</p>`;
    new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(lngLat).setHTML(html).addTo(map);
  }

  // ---- search ----
  const q = document.getElementById('q'), sug = document.getElementById('sug');
  let hits = [], cur = -1;
  function show() { sug.innerHTML = hits.map((p, i) => `<li role="option" data-i="${i}" aria-selected="${i === cur}">${esc(p[0])} <span>${esc(p[1])} · ${p[4].toLocaleString('en-GB')}</span></li>`).join(''); sug.style.display = hits.length ? 'block' : 'none'; }
  function pick(p) {
    sug.style.display = 'none'; q.value = p[0];
    map.flyTo({ center: [p[2], p[3]], zoom: Math.max(map.getZoom(), 7.5) });
    map.once('moveend', () => {
      const pt = map.project([p[2], p[3]]); const f = map.queryRenderedFeatures(pt, { layers: ['hex'] })[0];
      if (f) popHex(H.hex[f.properties.i], { lng: p[2], lat: p[3] });
      else new maplibregl.Popup().setLngLat([p[2], p[3]]).setHTML(`<b class="t">${esc(p[0])}</b><div>${p[4]} inscriptions found here; none in the selected period or kind.</div>`).addTo(map);
    });
  }
  q.addEventListener('input', () => {
    const t = norm(q.value.trim()); cur = -1;
    if (t.length < 2 || !places) { hits = []; show(); return; }
    const a = [], b = [];
    for (const p of places) { const n = norm(p[0] + ' ' + p[1]); if (n.startsWith(t) || norm(p[1]).startsWith(t)) a.push(p); else if (n.includes(t)) b.push(p); if (a.length > 12) break; }
    hits = a.concat(b).slice(0, 12); show();
  });
  q.addEventListener('keydown', e => {
    if (e.key === 'ArrowDown') { cur = Math.min(cur + 1, hits.length - 1); show(); e.preventDefault(); }
    else if (e.key === 'ArrowUp') { cur = Math.max(cur - 1, 0); show(); e.preventDefault(); }
    else if (e.key === 'Enter' && hits.length) pick(hits[Math.max(cur, 0)]);
    else if (e.key === 'Escape') sug.style.display = 'none';
  });
  sug.addEventListener('click', e => { const li = e.target.closest('li'); if (li) pick(hits[+li.dataset.i]); });
  document.addEventListener('click', e => { if (!e.target.closest('.srch')) sug.style.display = 'none'; });
  document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => {
    e.preventDefault(); const [lon, lat, z] = a.dataset.go.split(',').map(Number);
    document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' });
    map.flyTo({ center: [lon, lat], zoom: z || 7 });
  }));

  function arc(a, b) {
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, vx = b[0] - a[0], vy = b[1] - a[1], c = [mx - vy * 0.18, my + vx * 0.18], out = [];
    for (let i = 0; i <= 20; i++) { const t = i / 20; out.push([(1 - t) * (1 - t) * a[0] + 2 * (1 - t) * t * c[0] + t * t * b[0], (1 - t) * (1 - t) * a[1] + 2 * (1 - t) * t * c[1] + t * t * b[1]]); }
    return out;
  }

  // ---- the map ----
  Promise.all(['data/site.json', 'data/hex.json'].map(u => fetch(u).then(r => r.json()))).then(([S, HX]) => {
    site = S; H = HX;
    const tq = qs.get('t'); if (['all', '0', '1', '2', '3', '4'].includes(tq)) type = tq;
    const bq = qs.get('bin'); if (bq && bq !== 'all' && site.bins.includes(+bq)) bin = site.bins.indexOf(+bq);
    yr.max = site.bins.length; yr.value = bin === null ? site.bins.length : bin;
    refresh();
    fetch('data/places.json').then(r => r.json()).then(P => { places = P.places; });
    if (!window.maplibregl) { document.getElementById('nojs').textContent = 'The map could not load (MapLibre GL JS missing).'; return; }
    map = new maplibregl.Map({ container: 'map', style: STYLE, bounds: small ? [[-9, 33], [36, 54]] : [[-10, 29], [40, 55]], fitBoundsOptions: { padding: small ? 6 : 30 }, maxZoom: 12, minZoom: 2.5, attributionControl: false });
    window.__map = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true, customAttribution: 'Inscriptions: LIRE v2.1 (EDCS, EDH), CC BY 4.0; provinces: DARE (Lund University)' }), 'bottom-right');
    map.on('load', () => {
      document.getElementById('nojs').remove();
      const at_ = document.querySelector('.maplibregl-ctrl-attrib'); if (at_ && small) at_.classList.remove('maplibregl-compact-show');
      const first = map.getStyle().layers.find(l => l.type === 'symbol');
      map.addSource('hex', { type: 'geojson', data: hexData() });
      map.addLayer({ id: 'hex', type: 'fill', source: 'hex', paint: { 'fill-color': ['match', ['get', 'c'], 0, SEQ[0], 1, SEQ[1], 2, SEQ[2], 3, SEQ[3], 4, SEQ[4], SEQ[5]], 'fill-opacity': 0.85, 'fill-outline-color': 'rgba(255,255,255,0.6)' } }, first && first.id);
      fetch('data/provinces.geojson').then(r => r.json()).then(P => {
        map.addSource('prov', { type: 'geojson', data: P });
        map.addLayer({ id: 'prov', type: 'line', source: 'prov', paint: { 'line-color': '#6E604E', 'line-width': ['interpolate', ['linear'], ['zoom'], 3, 0.6, 8, 1.6], 'line-opacity': 0.7, 'line-dasharray': [3, 2] } });
        const lab = P.features.map(f => { let b = [1e9, 1e9, -1e9, -1e9]; const walk = c => { if (typeof c[0] === 'number') { b = [Math.min(b[0], c[0]), Math.min(b[1], c[1]), Math.max(b[2], c[0]), Math.max(b[3], c[1])]; } else c.forEach(walk); }; walk(f.geometry.coordinates);
          return { type: 'Feature', properties: { name: f.properties.name }, geometry: { type: 'Point', coordinates: [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2] } }; });
        map.addSource('provl', { type: 'geojson', data: { type: 'FeatureCollection', features: lab } });
        map.addLayer({ id: 'provl', type: 'symbol', source: 'provl', minzoom: 4.2, layout: { 'text-field': ['get', 'name'], 'text-size': 11.5, 'text-font': ['Noto Sans Italic'], 'text-letter-spacing': 0.08 }, paint: { 'text-color': '#6E604E', 'text-halo-color': '#fff', 'text-halo-width': 1.4 } });
        vis(['prov', 'provl'], document.getElementById('lyP').checked);
      });
      fetch('data/flows.json').then(r => r.json()).then(Fl => {
        flows = Fl.flows;
        const lines = flows.map(f => ({ type: 'Feature', properties: { origin: f[0], prec: f[3], per: f[6], n: f[7], km: f[8], place: f[9], prov: f[10] }, geometry: { type: 'LineString', coordinates: arc([f[1], f[2]], [f[4], f[5]]) } }));
        const orig = {}; flows.forEach(f => { const k = f[0]; orig[k] = orig[k] || { n: 0, lon: f[1], lat: f[2] }; orig[k].n += f[7]; });
        map.addSource('flows', { type: 'geojson', data: { type: 'FeatureCollection', features: lines } });
        map.addLayer({ id: 'flows', type: 'line', source: 'flows', layout: { 'line-cap': 'round' }, paint: { 'line-color': ['match', ['get', 'per'], 'early', '#2F7FB8', 'late', '#B3202A', '#8C8C8C'], 'line-width': ['interpolate', ['linear'], ['get', 'n'], 1, 1.1, 10, 4], 'line-opacity': 0.55 } });
        map.addSource('orig', { type: 'geojson', data: { type: 'FeatureCollection', features: Object.entries(orig).map(([k, o]) => ({ type: 'Feature', properties: { name: k, n: o.n }, geometry: { type: 'Point', coordinates: [o.lon, o.lat] } })) } });
        map.addLayer({ id: 'orig', type: 'circle', source: 'orig', paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 3, 3.5, 9, 7], 'circle-color': '#fff', 'circle-stroke-color': '#1D2128', 'circle-stroke-width': 1.3 } });
        vis(['flows', 'orig'], document.getElementById('lyF').checked);
        document.getElementById('keyF').hidden = !document.getElementById('lyF').checked;
      });
      map.on('click', e => {
        const f = map.queryRenderedFeatures([[e.point.x - 3, e.point.y - 3], [e.point.x + 3, e.point.y + 3]], { layers: ['orig', 'flows', 'hex'].filter(l => map.getLayer(l) && map.getLayoutProperty(l, 'visibility') !== 'none') })[0];
        if (!f) return;
        if (f.layer.id === 'hex') popHex(H.hex[f.properties.i], e.lngLat);
        else if (f.layer.id === 'flows') popFlow(f.properties, e.lngLat);
        else if (f.layer.id === 'orig') { const n = f.properties.n; new maplibregl.Popup().setLngLat(f.geometry.coordinates).setHTML(`<b class="t">${esc(f.properties.name)}</b><div>Stated origin of ${n} soldier${n > 1 ? 's' : ''} on mapped stones.</div>`).addTo(map); }
      });
      ['hex', 'flows', 'orig'].forEach(l => { map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
      document.getElementById('lyH').addEventListener('change', e => { vis(['hex'], e.target.checked); document.getElementById('keyH').hidden = !e.target.checked; });
      document.getElementById('lyF').addEventListener('change', e => { vis(['flows', 'orig'], e.target.checked); document.getElementById('keyF').hidden = !e.target.checked; });
      document.getElementById('lyP').addEventListener('change', e => vis(['prov', 'provl'], e.target.checked));
      document.getElementById('lyL').addEventListener('change', e => { map.getStyle().layers.filter(l => l.type === 'symbol' && !['provl'].includes(l.id)).forEach(l => map.setLayoutProperty(l.id, 'visibility', e.target.checked ? 'visible' : 'none')); });
      document.getElementById('opa').addEventListener('input', e => map.setPaintProperty('hex', 'fill-opacity', +e.target.value));
      if (qs.get('flows') === '1') { document.getElementById('lyF').checked = true; document.getElementById('lyF').dispatchEvent(new Event('change')); }
    });
  });
})();
