/*
 * esterownik-card — karta schematu kotłowni dla integracji esterownik-ha
 * Nieoficjalny projekt, niezwiązany z producentem sterowników.
 * Wariant: Pello 3.5
 */
const EC_VERSION = '0.2.0';

const EC_DEFAULT_ENTITIES = {
  status: 'sensor.pello_status_pracy',
  tryb_pracy: 'sensor.pello_stan_trybu_pracy',
  zima_lato: 'select.pello_tryb_zima_lato',
  t_zewn: 'sensor.pello_temperatura_zewnetrzna',
  t_kotla: 'sensor.pello_temperatura_kotla',
  zad_kotla: 'number.pello_temperatura_zadana_kotla',
  t_powrotu: 'sensor.pello_temperatura_powrotu',
  t_spalin: 'sensor.pello_temperatura_spalin',
  t_podajnika: 'sensor.pello_temperatura_podajnika',
  t_cwu: 'sensor.pello_temperatura_cwu',
  zad_cwu: 'number.pello_temperatura_zadana_cwu',
  tryb_cwu: 'select.pello_tryb_cwu',
  t_za_zaworem: 'sensor.pello_temperatura_za_zaworem',
  zad_za_zaworem: 'number.pello_temperatura_zadana_za_zaworem_co1',
  poz_zaworu: 'sensor.pello_pozycja_zaworu_4d',
  stan_zaworu: 'sensor.pello_zawor_4d',
  t_wewn: 'sensor.pello_temperatura_wewnetrzna',
  zad_wewn: 'sensor.pello_temperatura_zadana_wewn_co1',
  wewn_komfortowa: 'number.pello_temperatura_wewn_komfortowa',
  wewn_normalna: 'number.pello_temperatura_wewn_normalna',
  wewn_niska: 'number.pello_temperatura_wewn_niska',
  poziom: 'sensor.pello_poziom_paliwa_w_zasobniku',
  kolejny_zasyp: 'sensor.pello_data_kolejnego_zasypu',
  czas_do_oproznienia: 'sensor.pello_czas_do_oproznienia_zasobnika',
  strumien: 'sensor.pello_strumien_paliwa',
  rozpalenia: 'sensor.pello_ilosc_rozpalen',
  plomien: 'sensor.pello_plomien',
  moc_dmuchawy: 'sensor.pello_aktualna_moc_dmuchawy',
  moc: 'sensor.pello_moc_obliczona',
  dmuchawa: 'binary_sensor.pello_dmuchawa',
  podajnik: 'binary_sensor.pello_podajnik',
  pompa_co: 'binary_sensor.pello_pompa_1',
  pompa_cwu: 'binary_sensor.pello_pompa_cwu',
  reg_pog_kociol: 'switch.pello_regulator_pogodowy_kociol',
  reg_pog_zawor: 'switch.pello_regulator_pogodowy_zawor_4d',
  kasuj_alarmy: 'button.pello_potwierdzenie_alarmow',
  cyrkulacja: null,
};
const EC_ALARM_PREFIX = 'binary_sensor.pello_alarm_';

const EC_PANELS = {
  kociol: {
    title: 'Kocioł',
    info: [['t_kotla', 'Temperatura kotła'], ['t_powrotu', 'Powrót'], ['moc', 'Moc'], ['plomien', 'Płomień']],
    ctrl: [['zad_kotla', 'Temperatura zadana kotła'], ['reg_pog_kociol', 'Regulator pogodowy (kocioł)']],
  },
  cwu: {
    title: 'Bojler CWU',
    info: [['t_cwu', 'Temperatura CWU']],
    ctrl: [['tryb_cwu', 'Tryb CWU'], ['zad_cwu', 'Temperatura zadana CWU']],
  },
  zawor: {
    title: 'Zawór 4D — obieg CO',
    info: [['t_za_zaworem', 'Temperatura za zaworem'], ['poz_zaworu', 'Pozycja zaworu'], ['stan_zaworu', 'Ruch zaworu']],
    ctrl: [['zad_za_zaworem', 'Temperatura zadana za zaworem'], ['reg_pog_zawor', 'Regulator pogodowy (zawór 4D)']],
  },
  pokoj: {
    title: 'Pokój',
    info: [['t_wewn', 'Temperatura wewnętrzna'], ['zad_wewn', 'Aktywna zadana']],
    ctrl: [['wewn_komfortowa', 'Komfortowa'], ['wewn_normalna', 'Normalna'], ['wewn_niska', 'Niska']],
  },
  tryb: {
    title: 'Tryb pracy',
    info: [['tryb_pracy', 'Stan trybu pracy'], ['t_zewn', 'Temperatura zewnętrzna']],
    ctrl: [['zima_lato', 'Zima / Lato']],
  },
  zasobnik: {
    title: 'Zasobnik pelletu',
    info: [['poziom', 'Poziom paliwa'], ['czas_do_oproznienia', 'Czas do opróżnienia'], ['kolejny_zasyp', 'Kolejny zasyp'], ['strumien', 'Strumień paliwa'], ['t_podajnika', 'Temperatura podajnika'], ['rozpalenia', 'Liczba rozpaleń']],
    ctrl: [],
  },
  cyrkulacja: {
    title: 'Cyrkulacja CWU',
    info: [],
    ctrl: [['cyrkulacja', 'Pompa cyrkulacji']],
  },
  alarmy: { title: 'Alarmy', info: [], ctrl: [] },
};

const EC_SET_INFO = { zad_kotla: [['t_kotla', 'Temperatura kotła']], zad_cwu: [['t_cwu', 'Temperatura CWU']], tryb_cwu: [['t_cwu', 'Temperatura CWU']], zad_za_zaworem: [['t_za_zaworem', 'Temperatura za zaworem']], reg_pog_zawor: [['t_zewn', 'Temperatura zewnętrzna']], reg_pog_kociol: [['t_zewn', 'Temperatura zewnętrzna']], zima_lato: [['t_zewn', 'Temperatura zewnętrzna']] };
function ecPanelDef(name) {
  if (!name) return null;
  if (!name.startsWith('set:')) return EC_PANELS[name];
  const k = name.slice(4);
  let label = k;
  for (const P of Object.values(EC_PANELS)) { const c = P.ctrl.find((x) => x[0] === k); if (c) { label = c[1]; break; } }
  return { title: label, info: EC_SET_INFO[k] || [], ctrl: [[k, label]] };
}
const ecDevCache = {};
function ecDeviceMap(hass, deviceId) {
  if (!ecDevCache[deviceId]) {
    ecDevCache[deviceId] = hass.callWS({ type: 'esterownik/card_entities', device_id: deviceId })
      .catch((e) => { delete ecDevCache[deviceId]; console.warn('esterownik-card:', e && e.message ? e.message : e); return null; });
  }
  return ecDevCache[deviceId];
}
function ecFindDevice(hass) {
  const ents = (hass && hass.entities) || {};
  for (const id of Object.keys(ents)) { const e = ents[id]; if (e && e.platform === 'esterownik' && e.device_id) return e.device_id; }
  return undefined;
}
const ecEsc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

class EsterownikBase extends HTMLElement {
  _initConfig(config) {
    if (!config) throw new Error('Brak konfiguracji');
    this._cfg = Object.assign({ motyw: 'auto', tylko_podglad: false, nazwa: 'Piec Pello' }, config);
    if (this._devFor !== this._cfg.device_id) { this._dev = null; this._devFor = null; }
    this._resolveEntities();
  }
  _resolveEntities() {
    const c = this._cfg;
    const base = c.device_id ? Object.assign({}, (this._dev && this._dev.entities) || {}) : Object.assign({}, EC_DEFAULT_ENTITIES);
    this._e = Object.assign(base, c.encje || {});
    if (c.cyrkulacja) this._e.cyrkulacja = c.cyrkulacja;
  }
  _ensureDevice() {
    const id = this._cfg && this._cfg.device_id;
    if (!id || !this._hass || this._devFor === id || this._devLoading === id) return;
    this._devLoading = id;
    ecDeviceMap(this._hass, id).then((dev) => {
      this._devLoading = null;
      if (!this._cfg || this._cfg.device_id !== id) return;
      this._dev = dev; this._devFor = id; this._devError = dev ? null : 'Nie udało się pobrać encji pieca z integracji eSterownik';
      this._resolveEntities();
      if (this._built) this._update();
    });
  }
  _st(k) {
    const id = this._e[k];
    if (!id || !this._hass) return undefined;
    return this._hass.states[id];
  }
  _ok(k) {
    const s = this._st(k);
    return s && s.state !== 'unavailable' && s.state !== 'unknown' ? s : undefined;
  }
  _on(k) { const s = this._ok(k); return !!s && s.state === 'on'; }
  _num(k) { const s = this._ok(k); if (!s) return NaN; return parseFloat(s.state); }
  _fmt(k) {
    const s = this._ok(k);
    if (!s) return '—';
    const a = s.attributes || {};
    const u = a.unit_of_measurement || '';
    if (a.device_class === 'timestamp') {
      const d = new Date(s.state);
      if (isNaN(d)) return s.state;
      return d.toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
    }
    const n = parseFloat(s.state);
    if (isNaN(n) || !/^-?[\d.]+$/.test(s.state)) return s.state;
    if (a.device_class === 'duration' && (u === 'min' || u === 'h' || u === 's')) {
      const tot = Math.round(u === 'h' ? n * 60 : u === 's' ? n / 60 : n);
      const h = Math.floor(tot / 60), m = tot % 60;
      return h > 0 ? `${h} h ${m} min` : `${m} min`;
    }
    let dec = 0;
    const dom = (this._e[k] || '').split('.')[0];
    if (dom === 'number' || dom === 'input_number') dec = (a.step || 1) < 1 ? 1 : 0;
    else if (u === '°C') dec = 1;
    else if (u === 'kg/h' || u === 'kW') dec = 1;
    const txt = n.toLocaleString('pl-PL', { minimumFractionDigits: dec, maximumFractionDigits: dec });
    if (!u) return txt;
    return u === '%' ? `${txt} %` : `${txt} ${u}`;
  }
  _alarms() {
    if (!this._hass) return [];
    const out = [];
    for (const id of Object.keys(this._hass.states)) {
      if (this._dev && this._dev.alarms && !this._cfg.alarm_prefix) { if (!this._dev.alarms.includes(id)) continue; }
      else if (!id.startsWith(this._cfg.alarm_prefix || EC_ALARM_PREFIX)) continue;
      const s = this._hass.states[id];
      if (s.state === 'on') {
        const n = (s.attributes.friendly_name || id).replace(/^.*?Alarm\s*/i, '');
        out.push(n);
      }
    }
    return out;
  }
  _themeClass() {
    const m = this._cfg.motyw;
    return m === 'jasny' || m === 'ciemny' ? m : 'auto';
  }
}

const EC_CSS = `
:host{display:block}
ha-card{display:block;position:relative;overflow:hidden;
  --ec-bg:var(--ha-card-background,var(--card-background-color,#fff));
  --ec-fg:var(--primary-text-color,#1a1a1a);
  --ec-muted:var(--secondary-text-color,#555);
  --ec-line:var(--divider-color,#c8c8c8);
  --ec-red:#e0262b;--ec-blue:#2a9be0;--ec-boiler:#1f6fb8;--ec-door:#1d2a3a;--ec-chimney:#7a7a7a;
  --ec-hopper:#e8e2d6;--ec-pellet:#b98b4f;--ec-on:#2ea44f;--ec-off:#d0312d;
  background:var(--ec-bg);color:var(--ec-fg);font-family:var(--ha-font-family-body,Roboto,system-ui,sans-serif)}
ha-card.jasny{--ec-bg:#ffffff;--ec-fg:#1a1a1a;--ec-muted:#555555;--ec-line:#c8c8c8}
ha-card.ciemny{--ec-bg:#1c1c1c;--ec-fg:#e8e8e8;--ec-muted:#a8a8a8;--ec-line:#4a4a4a;--ec-door:#0f151c;--ec-hopper:#3a3630;--ec-red:#e5484d;--ec-blue:#3aa0e6;--ec-boiler:#2563a6}
.hdr{display:flex;align-items:center;gap:10px;padding:14px 16px 0;flex-wrap:wrap}
.name{font-size:17px;font-weight:500}
.chip{padding:3px 10px;border-radius:999px;font-size:12px;font-weight:700;letter-spacing:.04em;background:var(--ec-line);color:var(--ec-fg)}
.chip.GRZANIE{background:#fde3cf;color:#8a3a06}.chip.ROZPALANIE{background:#fdf0c4;color:#6b5200}
.chip.WYGASZANIE,.chip.CZYSZCZENIE{background:#e6e6e6;color:#3d3d3d}
.ro{font-size:11px;color:var(--ec-muted);margin-left:auto}
.alarm{display:none;margin:10px 16px 0;padding:8px 12px;border-radius:8px;border:1px solid #c0392b;background:#fdecea;color:#8e1b12;font-size:13px;cursor:pointer;width:calc(100% - 32px);text-align:left;font:inherit;box-sizing:border-box}
.alarm.show{display:block}
svg{display:block;width:100%;height:auto;max-height:var(--ec-max-h,calc(100vh - 160px));margin:0 auto}
.more{cursor:pointer}.more:hover rect,.more:focus-visible rect{stroke:#2a9be0;stroke-width:2}.more:hover circle{stroke-width:4}
.iv{border:none;background:transparent;color:var(--ec-fg);font:inherit;font-size:13px;padding:0;text-align:right;cursor:pointer}.iv:hover{color:#2a9be0}
svg text{fill:var(--ec-fg);font-size:13px;font-family:inherit}
.box rect{fill:var(--ec-bg);stroke:var(--ec-line);stroke-width:1}
.box text{text-anchor:middle}
.small text,.small{font-size:11px}
.pipe{fill:none;stroke-width:6;stroke-linecap:round;stroke-linejoin:round}
.flow{fill:none;stroke:#fff;stroke-opacity:.6;stroke-width:3;stroke-dasharray:6 14;opacity:0;animation:ecfl 1s linear infinite}
@keyframes ecfl{to{stroke-dashoffset:-20}}
svg.on-co .flow.co,svg.on-cwu .flow.cwu,svg.on-main .flow.main,svg.on-circ .flow.circ{opacity:1}
.fan{transform-box:fill-box;transform-origin:center}
svg.spin .fan{animation:ecsp 1s linear infinite}
@keyframes ecsp{to{transform:rotate(360deg)}}
.flame{transform-box:fill-box;transform-origin:50% 100%;animation:ecfk .6s ease-in-out infinite;display:none}
svg.burn .flame{display:inline}
@keyframes ecfk{50%{transform:scaleY(.86)}}
.tap{cursor:pointer;outline:none}
.tap:hover .hl,.tap:focus-visible .hl{stroke:#2a9be0;stroke-width:2.5}
.circ-grp{display:none}svg.has-circ .circ-grp{display:inline}
.dot-lbl{font-size:10px;font-weight:700}
.dlg-wrap{display:none;position:absolute;inset:0;background:rgba(0,0,0,.45);align-items:center;justify-content:center;z-index:5}
.dlg-wrap.show{display:flex}
.dlg{background:var(--ec-bg);color:var(--ec-fg);border-radius:14px;padding:18px;width:min(380px,calc(100% - 32px));max-height:calc(100% - 32px);overflow:auto;box-shadow:0 8px 30px rgba(0,0,0,.35);display:flex;flex-direction:column;gap:14px;box-sizing:border-box}
.dlg h3{margin:0;font-size:18px;font-weight:500;flex-grow:1}
.dlg .top{display:flex;align-items:center}
.dlg button{font:inherit;cursor:pointer}
.x{width:40px;height:40px;border:none;border-radius:50%;background:transparent;color:var(--ec-muted);font-size:20px}
.inf{display:grid;grid-template-columns:1fr auto;gap:4px 12px;font-size:13px}
.inf span:nth-child(odd){color:var(--ec-muted)}
.lbl{font-size:12px;color:var(--ec-muted);letter-spacing:.04em;margin-bottom:6px}
.seg{display:flex;flex-wrap:wrap;gap:6px}
.seg button{min-height:40px;padding:0 12px;border-radius:10px;border:1px solid var(--ec-line);background:transparent;color:var(--ec-fg)}
.seg button.sel{border-color:#2a9be0;background:rgba(42,155,224,.18);font-weight:500}
.step{display:flex;align-items:center;gap:12px}
.step button{width:44px;height:44px;border-radius:50%;border:1px solid var(--ec-line);background:transparent;color:var(--ec-fg);font-size:20px}
.step .v{flex-grow:1;text-align:center;font-size:26px;font-weight:700}
.dlg button:disabled{opacity:.45;cursor:not-allowed}
.sum{padding:8px 12px;border-radius:10px;background:rgba(243,213,138,.2);border:1px solid #b08a2e;font-size:13px}
.note{padding:8px 12px;border-radius:10px;background:rgba(42,155,224,.12);border:1px solid rgba(42,155,224,.5);font-size:13px}
.err{padding:8px 12px;border-radius:10px;background:#fdecea;color:#8e1b12;font-size:13px}
.acts{display:flex;gap:10px}
.acts button{flex:1;min-height:44px;border-radius:10px;border:1px solid var(--ec-line);background:transparent;color:var(--ec-fg)}
.acts button.pri{background:#2a7fc0;border-color:#2a7fc0;color:#fff;font-weight:500}
.alist{margin:0;padding-left:18px;font-size:14px}
`;

function ecBox(id, x, y, w, h = 24, cls = '') {
  return `<g class="box more ${cls}" data-more="${id}" tabindex="0" role="button" aria-label="Historia"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="3"/><text id="v-${id}" x="${x + w / 2}" y="${y + h / 2 + 4.5}">—</text></g>`;
}
function ecSetBox(id, panel, x, y, w, h = 24) {
  return `<g class="box tap" data-panel="${panel}" tabindex="0" role="button" aria-label="Nastawa"><rect class="hl" x="${x}" y="${y}" width="${w}" height="${h}" rx="3"/><text id="v-${id}" x="${x + w / 2}" y="${y + h / 2 + 4.5}">—</text></g>`;
}
function ecPipe(d, color, grp) {
  return `<path class="pipe" d="${d}" stroke="var(--ec-${color})"/><path class="flow ${grp}" d="${d}"/>`;
}
function ecDot(id, x, y, anchor = 'start') {
  const tx = anchor === 'start' ? x + 7 : x - 7;
  return `<circle id="d-${id}" cx="${x}" cy="${y}" r="4" fill="var(--ec-off)"/><text id="l-${id}" class="dot-lbl" x="${tx}" y="${y + 3.5}" text-anchor="${anchor}">OFF</text>`;
}
function ecPump(x, y, dir) {
  const tri = dir === 'up' ? `M${x} ${y - 7}L${x + 7} ${y + 5}H${x - 7}Z` : `M${x} ${y + 7}L${x + 7} ${y - 5}H${x - 7}Z`;
  return `<circle cx="${x}" cy="${y}" r="12" fill="var(--ec-bg)" stroke="var(--ec-fg)" stroke-width="2"/><path d="${tri}" fill="var(--ec-fg)"/>`;
}

const EC_SVG = (() => {
  const fins = [];
  for (let i = 0; i < 8; i++) fins.push(`<rect x="${602 + i * 15}" y="408" width="11" height="96" rx="2" fill="url(#ecgrad)"/>`);
  const zig = (x0, y, n) => { let d = `M${x0} ${y}`; for (let i = 0; i < n; i++) d += ` l4 ${i % 2 ? 8 : -8}`; return d; };
  return `
<svg viewBox="0 0 800 525" role="img" aria-label="Schemat kotłowni">
<defs><linearGradient id="ecgrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e0262b"/><stop offset=".55" stop-color="#f6c9c9"/><stop offset=".8" stop-color="#bfe3f7"/><stop offset="1" stop-color="#7cc4f2"/></linearGradient>
<clipPath id="echop"><rect x="172" y="332" width="60" height="96"/></clipPath></defs>

${ecPipe('M440 330H470V225H790', 'red', 'main')}
${ecPipe('M790 240H490V500H440', 'blue', 'main')}
${ecPipe('M600 225V55H620', 'red', 'cwu')}
${ecPipe('M620 108H585V240', 'blue', 'cwu')}
${ecPipe('M565 225V278', 'red', 'co')}
${ecPipe('M545 240V278', 'blue', 'co')}
${ecPipe('M565 302V420H602', 'red', 'co')}
${ecPipe('M602 496H545V302', 'blue', 'co')}
${ecPipe('M730 48H775V104H752', 'red', 'circ')}

<g class="tap" data-panel="tryb" tabindex="0" role="button" aria-label="Tryb pracy">
  <g class="box"><rect class="hl" x="150" y="10" width="140" height="30" rx="3"/><text id="v-tryb_pracy" x="220" y="30">—</text></g>
  <g class="box" data-panel="set:zima_lato"><rect class="hl" x="150" y="46" width="140" height="30" rx="3"/><text id="v-zima_lato" x="220" y="66">—</text></g>
</g>
<g fill="none" stroke="var(--ec-fg)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" transform="translate(160 92)">
  <circle cx="44" cy="18" r="8"/><path d="M44 3v4M44 29v4M29 18h4M55 18h4M33.5 7.5l2.8 2.8M54.5 7.5l-2.8 2.8M54.5 28.5l-2.8-2.8"/>
  <path d="M14 52h30a10 10 0 0 0 0-20 13 13 0 0 0-25-3A11 11 0 0 0 14 52z" fill="var(--ec-bg)"/>
</g>
${ecBox('t_zewn', 162, 150, 72)}

${ecBox('kolejny_zasyp', 10, 280, 130)}
${ecBox('poziom', 10, 310, 70)}
${ecBox('strumien', 10, 360, 90)}
${ecBox('rozpalenia', 10, 440, 70)}
${ecBox('status', 10, 475, 130)}
${ecBox('czas_do_oproznienia', 220, 280, 92)}

<g class="tap" data-panel="zasobnik" tabindex="0" role="button" aria-label="Zasobnik pelletu">
  <rect x="172" y="332" width="60" height="96" fill="var(--ec-hopper)"/>
  <rect id="hop-lvl" x="172" y="380" width="60" height="48" fill="var(--ec-pellet)" clip-path="url(#echop)"/>
  <rect class="hl" x="170" y="330" width="64" height="100" fill="none" stroke="var(--ec-boiler)" stroke-width="3"/>
  <rect x="174" y="430" width="5" height="62" fill="var(--ec-boiler)"/><rect x="225" y="430" width="5" height="62" fill="var(--ec-boiler)"/>
</g>
<g transform="rotate(-38 268 372)"><rect x="232" y="364" width="76" height="16" rx="3" fill="var(--ec-boiler)"/><path d="${zig(238, 376, 16)}" fill="none" stroke="#fff" stroke-width="1.6"/></g>
<path d="M300 338C330 350 330 420 318 450" fill="none" stroke="var(--ec-line)" stroke-width="9" stroke-linecap="round"/>
${ecDot('podajnik', 262, 326)}
${ecBox('t_podajnika', 238, 418, 62)}
<rect x="282" y="450" width="58" height="18" rx="9" fill="var(--ec-boiler)"/><path d="${zig(290, 463, 11)}" fill="none" stroke="#fff" stroke-width="1.6"/>
<g transform="translate(318 496)"><circle r="15" fill="var(--ec-boiler)"/>
  <g class="fan"><circle r="2.2" fill="#fff"/><path d="M0-2C-1-7 .5-11 3-11c1.6 0 2 1.8.6 3.2zM2 0c5-1 9 .5 9 3 0 1.6-1.8 2-3.2.6zM0 2c1 5-.5 9-3 9-1.6 0-2-1.8-.6-3.2zM-2 0c-5 1-9-.5-9-3 0-1.6 1.8-2 3.2-.6z" fill="#fff"/></g></g>
${ecBox('moc_dmuchawy', 232, 484, 60)}
<circle id="d-dmuchawa" cx="222" cy="496" r="4" fill="var(--ec-off)"/>

<polygon points="364,202 416,202 390,180" fill="var(--ec-chimney)"/>
<rect x="378" y="202" width="24" height="90" fill="var(--ec-chimney)"/>
${ecBox('t_spalin', 352, 230, 76)}

<g class="tap" data-panel="kociol" tabindex="0" role="button" aria-label="Kocioł">
  <rect class="hl" x="340" y="290" width="100" height="225" fill="var(--ec-boiler)" stroke="var(--ec-boiler)"/>
  <g class="box" data-panel="set:zad_kotla"><rect class="hl" x="346" y="298" width="88" height="24" rx="3"/><text id="v-zad_kotla" x="390" y="314.5">—</text></g>
  <text data-panel="set:reg_pog_kociol" id="v-reg_kociol" x="390" y="336" text-anchor="middle" style="fill:#e6f0fa;font-size:10px">—</text>
  <rect x="352" y="342" width="76" height="40" fill="var(--ec-door)"/>
  <rect x="352" y="388" width="76" height="62" fill="var(--ec-door)"/>
  <rect x="352" y="456" width="76" height="50" fill="var(--ec-door)"/>
  <g class="flame"><path d="M390 400c6 8 14 13 14 25a14 14 0 0 1-28 0c0-5 2.4-9 5.6-12 .5 4.5 2.7 7 5.8 8-1-5.5 0-13 2.6-21z" fill="#f07a2a"/><path d="M390 422c3 4 6 6.5 6 11a6 6 0 0 1-12 0c0-2.4 1.2-4.2 2.7-5.4.3 1.8 1.2 2.7 2.4 3-.6-3 0-6 .9-8.6z" fill="#ffd36b"/></g>
  <g class="box"><rect x="362" y="470" width="56" height="22" rx="3"/><text id="v-plomien" x="390" y="485">—</text></g>
</g>
${ecBox('t_kotla', 450, 340, 76)}
${ecBox('t_powrotu', 452, 466, 76)}

<g class="tap" data-panel="cwu" tabindex="0" role="button" aria-label="Bojler CWU">
  <rect class="hl" x="620" y="35" width="110" height="80" fill="url(#ecgrad)" stroke="none"/>
  <g class="box" data-panel="set:tryb_cwu"><rect class="hl" x="630" y="44" width="90" height="22" rx="3"/><text id="v-tryb_cwu" x="675" y="59">—</text></g>
  <g class="box more" data-more="t_cwu"><rect x="640" y="74" width="70" height="22" rx="3"/><text id="v-t_cwu" x="675" y="89">—</text></g>
</g>
${ecSetBox('zad_cwu', 'set:zad_cwu', 630, 122, 92)}
${ecPump(600, 118, 'up')}
${ecDot('pompa_cwu', 588, 94, 'end')}
<g transform="translate(736 96)"><rect width="16" height="16" rx="2" fill="var(--ec-bg)" stroke="var(--ec-fg)" stroke-width="1.6"/><path d="M3 5h7a3 3 0 0 1 3 3v3" fill="none" stroke="var(--ec-fg)" stroke-width="1.6"/><circle cx="13" cy="13.5" r="1" fill="var(--ec-fg)"/></g>
<g class="circ-grp tap" data-panel="cyrkulacja" tabindex="0" role="button" aria-label="Pompa cyrkulacji">${ecPump(775, 76, 'down')}<circle class="hl" cx="775" cy="76" r="14" fill="none" stroke="transparent"/>${ecDot('cyrkulacja', 760, 128)}</g>

<g class="tap" data-panel="zawor" tabindex="0" role="button" aria-label="Zawór 4D">
  <circle class="hl" cx="555" cy="290" r="17" fill="var(--ec-bg)" stroke="transparent"/>
  <path d="M555 290 543 280v20zM555 290l12-10v20zM555 290l-10-12h20zM555 290l-10 12h20z" fill="var(--ec-bg)" stroke="var(--ec-fg)" stroke-width="1.8" stroke-linejoin="round"/>
</g>
${ecBox('poz_zaworu', 590, 252, 70)}
${ecBox('t_za_zaworem', 590, 280, 70)}
${ecSetBox('zad_za_zaworem', 'set:zad_za_zaworem', 666, 252, 92)}
${ecSetBox('reg_zawor', 'set:reg_pog_zawor', 666, 280, 120)}
${ecPump(565, 352, 'down')}
${ecDot('pompa_co', 582, 338)}

<g class="tap" data-panel="pokoj" tabindex="0" role="button" aria-label="Pokój">
  <rect class="hl" x="600" y="406" width="122" height="100" fill="transparent" stroke="transparent"/>
  ${fins.join('')}
  <g class="more" data-more="t_wewn"><circle cx="640" cy="462" r="28" fill="#fff" stroke="#e0262b" stroke-width="2.5"/>
  <text id="v-t_wewn" x="640" y="468" text-anchor="middle" style="fill:#e0262b;font-size:15px">—</text></g>
</g>
${ecSetBox('zad_wewn', 'pokoj', 690, 380, 92)}
</svg>`;
})();

class EsterownikPelloCard extends EsterownikBase {
  static getStubConfig(hass) { const d = ecFindDevice(hass); return d ? { device_id: d } : { tylko_podglad: false }; }
  static async getConfigElement() { await ecEnsureForm(); return document.createElement('esterownik-pello-card-editor'); }
  setConfig(config) {
    this._initConfig(config);
    this._built = false;
    if (this._hass) { this._build(); this._update(); }
  }
  set hass(h) {
    this._hass = h;
    if (!this._cfg) return;
    this._ensureDevice();
    if (!this._built) this._build();
    this._update();
    if (this._panel) this._renderDialog();
  }
  get hass() { return this._hass; }
  getCardSize() { return 10; }
  getGridOptions() { return { columns: 'full', min_columns: 12, rows: 'auto' }; }

  _build() {
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    const ro = this._cfg.tylko_podglad ? '<span class="ro">tryb podglądu</span>' : '';
    this.shadowRoot.innerHTML = `<style>${EC_CSS}</style>
<ha-card class="${this._themeClass()}" style="${this._cfg.max_wysokosc ? '--ec-max-h:' + ecEsc(this._cfg.max_wysokosc) : ''}">
  <div class="hdr"><span class="name">${ecEsc(this._cfg.nazwa)}</span><span class="chip" id="chip">—</span>${ro}</div>
  <button class="alarm" id="alarm"></button>
  ${EC_SVG}
  <div class="dlg-wrap" id="wrap"><div class="dlg" id="dlg" role="dialog" aria-modal="true"></div></div>
</ha-card>`;
    const root = this.shadowRoot;
    this._svg = root.querySelector('svg');
    const open = (ev) => {
      const m = ev.target.closest('[data-more]');
      if (m) { this._moreInfo(m.dataset.more); return; }
      const t = ev.target.closest('[data-panel]');
      if (t) this._open(t.dataset.panel);
    };
    this._svg.addEventListener('click', open);
    this._svg.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(ev); } });
    root.getElementById('alarm').addEventListener('click', () => this._open('alarmy'));
    root.getElementById('wrap').addEventListener('click', (ev) => { if (ev.target.id === 'wrap') this._close(); });
    this._built = true;
  }

  _moreInfo(k) {
    const id = this._e[k]; if (!id) return;
    this.dispatchEvent(new CustomEvent('hass-more-info', { detail: { entityId: id }, bubbles: true, composed: true }));
  }
  _set(id, txt) { const el = this.shadowRoot.getElementById(id); if (el && el.textContent !== txt) el.textContent = txt; }
  _dot(id, on) {
    const d = this.shadowRoot.getElementById('d-' + id); if (d) d.setAttribute('fill', on ? 'var(--ec-on)' : 'var(--ec-off)');
    this._set('l-' + id, on ? 'ON' : 'OFF');
  }

  _update() {
    if (!this._built || !this._hass) return;
    const boxes = ['tryb_pracy', 'zima_lato', 't_zewn', 'kolejny_zasyp', 'poziom', 'strumien', 'rozpalenia', 'status', 'czas_do_oproznienia',
      't_podajnika', 'moc_dmuchawy', 't_spalin', 'plomien', 't_kotla', 't_powrotu', 'tryb_cwu', 't_cwu', 'poz_zaworu', 't_za_zaworem', 't_wewn'];
    for (const k of boxes) this._set('v-' + k, this._fmt(k));
    this._set('v-zad_kotla', 'zad. ' + this._fmt('zad_kotla'));
    this._set('v-zad_wewn', 'zad. ' + this._fmt('zad_wewn'));
    this._set('v-zad_cwu', 'zad. ' + this._fmt('zad_cwu'));
    this._set('v-zad_za_zaworem', 'zad. ' + this._fmt('zad_za_zaworem'));
    const reg = (k) => (this._ok(k) ? (this._on(k) ? 'wł.' : 'wył.') : '—');
    this._set('v-reg_kociol', 'pogodowy: ' + reg('reg_pog_kociol'));
    this._set('v-reg_zawor', 'pogodowy: ' + reg('reg_pog_zawor'));

    const p = this._num('poziom');
    const lvl = this.shadowRoot.getElementById('hop-lvl');
    if (lvl) { const h = isNaN(p) ? 0 : Math.max(0, Math.min(100, p)) * 0.96; lvl.setAttribute('y', String(428 - h)); lvl.setAttribute('height', String(h)); }

    const co = this._on('pompa_co'), cwu = this._on('pompa_cwu'), circ = this._on('cyrkulacja');
    this._dot('podajnik', this._on('podajnik'));
    this._dot('pompa_co', co);
    this._dot('pompa_cwu', cwu);
    this._dot('cyrkulacja', circ);
    const dm = this._on('dmuchawa');
    const dd = this.shadowRoot.getElementById('d-dmuchawa'); if (dd) dd.setAttribute('fill', dm ? 'var(--ec-on)' : 'var(--ec-off)');

    const st = this._ok('status') ? this._st('status').state : '';
    const burn = (st === 'GRZANIE' || st === 'ROZPALANIE') || (this._num('plomien') > 0);
    const cl = this._svg.classList;
    cl.toggle('on-co', co); cl.toggle('on-cwu', cwu); cl.toggle('on-main', co || cwu);
    cl.toggle('on-circ', circ); cl.toggle('has-circ', !!this._e.cyrkulacja);
    cl.toggle('spin', dm); cl.toggle('burn', burn);

    const chip = this.shadowRoot.getElementById('chip');
    chip.textContent = st || '—';
    chip.className = 'chip ' + st;
    const al = this._alarms();
    const ab = this.shadowRoot.getElementById('alarm');
    ab.classList.toggle('show', al.length > 0);
    const at = al.length ? `⚠ Alarm: ${al.join(' · ')} — szczegóły ›` : '';
    if (ab.textContent !== at) ab.textContent = at;
  }

  /* ---------- okna sterowania ---------- */
  _open(panel) {
    this._panel = panel; this._pending = {}; this._msg = null; this._busy = false;
    this.shadowRoot.getElementById('wrap').classList.add('show');
    this._renderDialog();
  }
  _close() {
    this._panel = null;
    this.shadowRoot.getElementById('wrap').classList.remove('show');
  }
  _cur(k) {
    const s = this._ok(k); if (!s) return undefined;
    const dom = this._e[k].split('.')[0];
    if (dom === 'number' || dom === 'input_number') return parseFloat(s.state);
    return s.state;
  }
  _renderDialog() {
    const P = ecPanelDef(this._panel); if (!P) return;
    const ro = !!this._cfg.tylko_podglad;
    let html = `<div class="top"><h3>${ecEsc(P.title)}</h3><button class="x" data-act="close" aria-label="Zamknij">✕</button></div>`;
    if (P.info.length) {
      html += '<div class="inf">' + P.info.filter(([k]) => this._e[k]).map(([k, l]) => `<span>${ecEsc(l)}</span><button class="iv" data-act="more" data-k="${k}" title="Historia">${ecEsc(this._fmt(k))} ›</button>`).join('') + '</div>';
    }
    if (this._panel === 'alarmy') {
      const al = this._alarms();
      html += al.length ? `<ul class="alist">${al.map((a) => `<li>${ecEsc(a)}</li>`).join('')}</ul>` : '<div>Brak aktywnych alarmów.</div>';
    }
    for (const [k, label] of P.ctrl) {
      const id = this._e[k]; if (!id) continue;
      const s = this._ok(k);
      if (!s) { html += `<div><div class="lbl">${ecEsc(label.toUpperCase())}</div><div>niedostępne</div></div>`; continue; }
      const dom = id.split('.')[0];
      const val = k in this._pending ? this._pending[k] : this._cur(k);
      if (dom === 'number' || dom === 'input_number') {
        const a = s.attributes; const step = a.step || 1;
        const dec = step < 1 ? 1 : 0;
        html += `<div><div class="lbl">${ecEsc(label.toUpperCase())}</div><div class="step">
          <button data-act="dec" data-k="${k}" aria-label="Obniż" ${ro || val <= a.min ? 'disabled' : ''}>−</button>
          <div class="v">${Number(val).toLocaleString('pl-PL', { minimumFractionDigits: dec, maximumFractionDigits: dec })} ${ecEsc(a.unit_of_measurement || '')}</div>
          <button data-act="inc" data-k="${k}" aria-label="Podnieś" ${ro || val >= a.max ? 'disabled' : ''}>+</button></div></div>`;
      } else if (dom === 'select' || dom === 'input_select') {
        html += `<div><div class="lbl">${ecEsc(label.toUpperCase())}</div><div class="seg">` +
          (s.attributes.options || []).map((o) => `<button data-act="opt" data-k="${k}" data-v="${ecEsc(o)}" class="${o === val ? 'sel' : ''}" ${ro ? 'disabled' : ''}>${ecEsc(o)}</button>`).join('') + '</div></div>';
      } else if (dom === 'switch' || dom === 'input_boolean' || dom === 'fan' || dom === 'light') {
        html += `<div><div class="lbl">${ecEsc(label.toUpperCase())}</div><div class="seg">
          <button data-act="opt" data-k="${k}" data-v="on" class="${val === 'on' ? 'sel' : ''}" ${ro ? 'disabled' : ''}>Włączony</button>
          <button data-act="opt" data-k="${k}" data-v="off" class="${val === 'off' ? 'sel' : ''}" ${ro ? 'disabled' : ''}>Wyłączony</button></div></div>`;
      } else {
        html += `<div><div class="lbl">${ecEsc(label.toUpperCase())}</div><div>${ecEsc(this._fmt(k))}</div></div>`;
      }
    }
    const changes = Object.keys(this._pending).filter((k) => this._pending[k] !== this._cur(k));
    const isAlarm = this._panel === 'alarmy' && this._alarms().length > 0 && this._e.kasuj_alarmy;
    if (ro && (P.ctrl.length || isAlarm)) html += '<div class="note">Tryb podglądu: zmiany z karty są wyłączone (tylko_podglad: true).</div>';
    if (changes.length) {
      html += '<div class="sum">Do sterownika trafi: ' + changes.map((k) => {
        const lab = (P.ctrl.find((c) => c[0] === k) || [k, k])[1];
        const fmt = (v) => (v === 'on' ? 'wł.' : v === 'off' ? 'wył.' : String(v).replace('.', ','));
        return `${ecEsc(lab)}: ${ecEsc(fmt(this._cur(k)))} → <b>${ecEsc(fmt(this._pending[k]))}</b>`;
      }).join('; ') + '</div>';
    }
    if (this._msg) html += `<div class="${this._msg.err ? 'err' : 'note'}">${ecEsc(this._msg.text)}</div>`;
    if (isAlarm) {
      html += `<div class="acts"><button data-act="close">Zamknij</button><button class="pri" data-act="ack" ${ro || this._busy ? 'disabled' : ''}>Kasuj alarmy</button></div>`;
    } else if (P.ctrl.length) {
      html += `<div class="acts"><button data-act="close">Anuluj</button><button class="pri" data-act="save" ${ro || !changes.length || this._busy ? 'disabled' : ''}>Zapisz w piecu</button></div>`;
    }
    const dlg = this.shadowRoot.getElementById('dlg');
    dlg.innerHTML = html;
    dlg.onclick = (ev) => this._dlgClick(ev);
  }
  _dlgClick(ev) {
    const b = ev.target.closest('button'); if (!b || b.disabled) return;
    const act = b.dataset.act, k = b.dataset.k;
    if (act === 'close') return this._close();
    if (act === 'more') { this._close(); return this._moreInfo(k); }
    if (act === 'inc' || act === 'dec') {
      const s = this._ok(k); const a = s.attributes; const step = a.step || 1;
      const cur = k in this._pending ? this._pending[k] : this._cur(k);
      let v = Math.round((cur + (act === 'inc' ? step : -step)) / step) * step;
      v = Math.min(a.max, Math.max(a.min, parseFloat(v.toFixed(3))));
      this._pending[k] = v; this._msg = null;
    } else if (act === 'opt') {
      this._pending[k] = b.dataset.v; this._msg = null;
    } else if (act === 'save') {
      return this._save();
    } else if (act === 'ack') {
      return this._ack();
    }
    this._renderDialog();
  }
  async _save() {
    if (this._cfg.tylko_podglad) return;
    const ks = Object.keys(this._pending).filter((k) => this._pending[k] !== this._cur(k));
    this._busy = true; this._renderDialog();
    try {
      for (const k of ks) {
        const id = this._e[k]; const dom = id.split('.')[0]; const v = this._pending[k];
        if (dom === 'number' || dom === 'input_number') await this._hass.callService(dom, 'set_value', { entity_id: id, value: v });
        else if (dom === 'select' || dom === 'input_select') await this._hass.callService(dom, 'select_option', { entity_id: id, option: v });
        else await this._hass.callService(dom === 'input_boolean' ? 'input_boolean' : 'homeassistant', v === 'on' ? 'turn_on' : 'turn_off', { entity_id: id });
      }
      this._pending = {}; this._msg = { text: 'Zapisano. Wartości odświeżą się po kolejnym odczycie ze sterownika.' };
    } catch (e) {
      this._msg = { err: true, text: 'Błąd zapisu: ' + (e && e.message ? e.message : e) };
    }
    this._busy = false; this._renderDialog();
  }
  async _ack() {
    if (this._cfg.tylko_podglad) return;
    this._busy = true; this._renderDialog();
    try {
      await this._hass.callService('button', 'press', { entity_id: this._e.kasuj_alarmy });
      this._msg = { text: 'Wysłano kasowanie alarmów.' };
    } catch (e) { this._msg = { err: true, text: 'Błąd: ' + (e && e.message ? e.message : e) }; }
    this._busy = false; this._renderDialog();
  }
}

/* ---------- mała karta ---------- */
const EC_MINI_CSS = `
:host{display:block}
ha-card{display:block;position:relative;
  --ec-bg:var(--ha-card-background,var(--card-background-color,#fff));--ec-fg:var(--primary-text-color,#1a1a1a);--ec-muted:var(--secondary-text-color,#555);--ec-line:var(--divider-color,#c8c8c8);
  background:var(--ec-bg);color:var(--ec-fg);font-family:var(--ha-font-family-body,Roboto,system-ui,sans-serif)}
ha-card.jasny{--ec-bg:#fff;--ec-fg:#1a1a1a;--ec-muted:#555;--ec-line:#c8c8c8}
ha-card.ciemny{--ec-bg:#1c1c1c;--ec-fg:#e8e8e8;--ec-muted:#a8a8a8;--ec-line:#4a4a4a}
.row{display:flex;align-items:center;gap:14px;padding:14px 16px;width:100%;border:none;background:transparent;color:inherit;font:inherit;text-align:left;cursor:pointer;box-sizing:border-box}
.ic{position:relative;width:46px;height:46px;flex-shrink:0;border-radius:50%;background:var(--ec-line);display:flex;align-items:center;justify-content:center}
.ic.burn{background:#fde3cf}
.ad{position:absolute;top:0;right:0;width:12px;height:12px;border-radius:50%;background:#e74c3c;border:2px solid var(--ec-bg);display:none}
.ad.show{display:block}
.mid{flex-grow:1;min-width:0;display:flex;flex-direction:column;gap:6px}
.t1{display:flex;gap:8px;align-items:baseline;flex-wrap:wrap}
.n{font-size:15px;font-weight:500}.s{font-size:12px;font-weight:700;letter-spacing:.04em;color:#c25a12}
.t2{display:flex;gap:14px;font-size:13px;color:var(--ec-muted);flex-wrap:wrap}.t2 b{color:var(--ec-fg);font-weight:500}
.pel{display:flex;flex-direction:column;align-items:flex-end;gap:5px;width:84px;flex-shrink:0;font-size:12px;color:var(--ec-muted)}
.bar{width:84px;height:7px;border-radius:4px;background:var(--ec-line);overflow:hidden}.bar i{display:block;height:7px;background:#b98b4f}
.ov{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:999;align-items:center;justify-content:center;padding:12px;box-sizing:border-box}
.ov.show{display:flex}.ov .in{width:min(860px,100%);max-height:100%;overflow:auto;border-radius:16px}
`;
class EsterownikPelloMiniCard extends EsterownikBase {
  static getStubConfig(hass) { const d = ecFindDevice(hass); return d ? { device_id: d } : {}; }
  static async getConfigElement() { await ecEnsureForm(); return document.createElement('esterownik-pello-card-editor'); }
  setConfig(config) { this._initConfig(config); this._built = false; if (this._hass) { this._build(); this._update(); } }
  set hass(h) { this._hass = h; if (!this._cfg) return; this._ensureDevice(); if (!this._built) this._build(); this._update(); if (this._big) this._big.hass = h; }
  getCardSize() { return 2; }
  getGridOptions() { return { columns: 12, min_columns: 6, rows: 2 }; }
  _build() {
    if (!this.shadowRoot) this.attachShadow({ mode: 'open' });
    this.shadowRoot.innerHTML = `<style>${EC_MINI_CSS}</style>
<ha-card class="${this._themeClass()}"><button class="row" id="row" aria-label="Otwórz schemat pieca">
  <span class="ic" id="ic"><svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c3.4 4.6 7 7.4 7 12a7 7 0 0 1-14 0c0-2.4 1.2-4.4 2.8-6 .2 2.4 1.4 3.8 3 4.2C10.4 9.4 10.8 5.6 12 2z" fill="#f07a2a"/></svg><span class="ad" id="ad"></span></span>
  <span class="mid"><span class="t1"><span class="n">${ecEsc(this._cfg.nazwa)}</span><span class="s" id="st">—</span><span style="font-size:12px;color:var(--ec-muted)" id="moc"></span></span>
  <span class="t2"><span>Kocioł <b id="tk">—</b></span><span>CWU <b id="tc">—</b></span><span>Pokój <b id="tw">—</b></span></span></span>
  <span class="pel"><span>Pellet <b id="pp" style="color:var(--ec-fg)">—</b></span><span class="bar"><i id="pb" style="width:0"></i></span><span id="pt">—</span></span>
</button><div class="ov" id="ov"><div class="in" id="in"></div></div></ha-card>`;
    this.shadowRoot.getElementById('row').addEventListener('click', () => this._openBig());
    this.shadowRoot.getElementById('ov').addEventListener('click', (e) => { if (e.target.id === 'ov') this._closeBig(); });
    this._built = true;
  }
  _openBig() {
    if (!this._big) {
      this._big = document.createElement('esterownik-pello-card');
      this._big.setConfig(this._cfg);
      this.shadowRoot.getElementById('in').appendChild(this._big);
    }
    this._big.hass = this._hass;
    this.shadowRoot.getElementById('ov').classList.add('show');
  }
  _closeBig() { this.shadowRoot.getElementById('ov').classList.remove('show'); }
  _update() {
    if (!this._built || !this._hass) return;
    const r = this.shadowRoot; const set = (id, t) => { const e = r.getElementById(id); if (e.textContent !== t) e.textContent = t; };
    const st = this._ok('status') ? this._st('status').state : '—';
    set('st', st);
    set('moc', this._num('moc') > 0 ? '· ' + this._fmt('moc') : '');
    set('tk', this._fmt('t_kotla')); set('tc', this._fmt('t_cwu')); set('tw', this._fmt('t_wewn'));
    set('pp', this._fmt('poziom')); set('pt', this._fmt('czas_do_oproznienia'));
    const p = this._num('poziom'); r.getElementById('pb').style.width = (isNaN(p) ? 0 : p) + '%';
    r.getElementById('ic').classList.toggle('burn', st === 'GRZANIE' || st === 'ROZPALANIE');
    r.getElementById('ad').classList.toggle('show', this._alarms().length > 0);
  }
}


/* ---------- edytor wizualny ---------- */
const EC_SEL = {
  sensor: { entity: { domain: 'sensor' } },
  temp: { entity: { domain: ['sensor', 'input_number'] } },
  number: { entity: { domain: ['number', 'input_number'] } },
  select: { entity: { domain: ['select', 'input_select'] } },
  out: { entity: { domain: ['binary_sensor', 'switch', 'input_boolean'] } },
  sw: { entity: { domain: ['switch', 'input_boolean'] } },
  btn: { entity: { domain: ['button', 'input_button', 'script'] } },
  circ: { entity: { domain: ['switch', 'binary_sensor', 'input_boolean', 'fan', 'light'] } },
};
const EC_LABELS = {
  device_id: 'Piec (urządzenie eSterownik) — wypełnia encje automatycznie', nazwa: 'Nazwa na karcie', motyw: 'Motyw', tylko_podglad: 'Tylko podgląd (bez zapisu do pieca)', max_wysokosc: 'Maksymalna wysokość schematu (np. 600px)',
  alarm_prefix: 'Prefiks encji alarmów', status: 'Status pracy', tryb_pracy: 'Tryb pracy (Automatyczny/Ręczny)', zima_lato: 'Tryb Zima / Lato', t_zewn: 'Temperatura zewnętrzna', kasuj_alarmy: 'Przycisk kasowania alarmów',
  t_kotla: 'Temperatura kotła', zad_kotla: 'Zadana kotła', t_powrotu: 'Temperatura powrotu', t_spalin: 'Temperatura spalin', reg_pog_kociol: 'Regulator pogodowy kotła', moc: 'Moc palnika', plomien: 'Płomień',
  poziom: 'Poziom paliwa', czas_do_oproznienia: 'Czas do opróżnienia zasobnika', kolejny_zasyp: 'Data kolejnego zasypu', strumien: 'Strumień paliwa (kg/h)', rozpalenia: 'Liczba rozpaleń', t_podajnika: 'Temperatura podajnika', podajnik: 'Podajnik (praca)', dmuchawa: 'Dmuchawa (praca)', moc_dmuchawy: 'Moc dmuchawy',
  t_cwu: 'Temperatura CWU', zad_cwu: 'Zadana CWU', tryb_cwu: 'Tryb CWU', pompa_cwu: 'Pompa CWU', cyrkulacja: 'Pompa cyrkulacji (opcjonalnie)',
  t_za_zaworem: 'Temperatura za zaworem', zad_za_zaworem: 'Zadana za zaworem', poz_zaworu: 'Pozycja zaworu 4D', stan_zaworu: 'Ruch zaworu 4D', reg_pog_zawor: 'Regulator pogodowy zaworu', pompa_co: 'Pompa CO',
  t_wewn: 'Temperatura w pokoju', zad_wewn: 'Aktywna zadana pokoju', wewn_komfortowa: 'Nastawa komfortowa', wewn_normalna: 'Nastawa normalna', wewn_niska: 'Nastawa niska',
};
const ecF = (name, sel) => ({ name, selector: EC_SEL[sel] });
const EC_SCHEMA = [
  { type: 'expandable', name: '', flatten: true, title: 'Ogólne', icon: 'mdi:cog', expanded: true, schema: [
    { name: 'device_id', selector: { device: { integration: 'esterownik' } } },
    { name: 'nazwa', selector: { text: {} } },
    { name: 'motyw', selector: { select: { mode: 'dropdown', options: [{ value: 'auto', label: 'Auto (motyw HA)' }, { value: 'jasny', label: 'Jasny' }, { value: 'ciemny', label: 'Ciemny' }] } } },
    { name: 'tylko_podglad', selector: { boolean: {} } },
    { name: 'max_wysokosc', selector: { text: {} } },
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Status i tryb', icon: 'mdi:information-outline', schema: [
    ecF('status', 'sensor'), ecF('tryb_pracy', 'sensor'), ecF('zima_lato', 'select'), ecF('t_zewn', 'temp'), ecF('kasuj_alarmy', 'btn'),
    { name: 'alarm_prefix', selector: { text: {} } },
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Kocioł', icon: 'mdi:fire', schema: [
    ecF('t_kotla', 'temp'), ecF('zad_kotla', 'number'), ecF('t_powrotu', 'temp'), ecF('t_spalin', 'temp'), ecF('reg_pog_kociol', 'sw'), ecF('moc', 'sensor'), ecF('plomien', 'sensor'),
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Zasobnik, podajnik, dmuchawa', icon: 'mdi:barrel', schema: [
    ecF('poziom', 'sensor'), ecF('czas_do_oproznienia', 'sensor'), ecF('kolejny_zasyp', 'sensor'), ecF('strumien', 'sensor'), ecF('rozpalenia', 'sensor'),
    ecF('t_podajnika', 'temp'), ecF('podajnik', 'out'), ecF('dmuchawa', 'out'), ecF('moc_dmuchawy', 'sensor'),
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Ciepła woda (CWU)', icon: 'mdi:water-boiler', schema: [
    ecF('t_cwu', 'temp'), ecF('zad_cwu', 'number'), ecF('tryb_cwu', 'select'), ecF('pompa_cwu', 'out'), ecF('cyrkulacja', 'circ'),
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Zawór 4D i obieg CO', icon: 'mdi:valve', schema: [
    ecF('t_za_zaworem', 'temp'), ecF('zad_za_zaworem', 'number'), ecF('poz_zaworu', 'sensor'), ecF('stan_zaworu', 'sensor'), ecF('reg_pog_zawor', 'sw'), ecF('pompa_co', 'out'),
  ] },
  { type: 'expandable', name: '', flatten: true, title: 'Pokój', icon: 'mdi:home-thermometer', schema: [
    ecF('t_wewn', 'temp'), ecF('zad_wewn', 'temp'), ecF('wewn_komfortowa', 'number'), ecF('wewn_normalna', 'number'), ecF('wewn_niska', 'number'),
  ] },
];
const EC_GENERAL_KEYS = ['device_id', 'nazwa', 'motyw', 'tylko_podglad', 'max_wysokosc', 'alarm_prefix'];

async function ecEnsureForm() {
  if (customElements.get('ha-form') && customElements.get('ha-entity-picker')) return;
  try {
    const helpers = await window.loadCardHelpers();
    const c = await helpers.createCardElement({ type: 'tile', entity: 'sun.sun' });
    if (c && c.constructor && c.constructor.getConfigElement) await c.constructor.getConfigElement();
  } catch (e) { /* ignore */ }
  try { await Promise.race([customElements.whenDefined('ha-form'), new Promise((r) => setTimeout(r, 3000))]); } catch (e) { /* ignore */ }
}

class EsterownikPelloCardEditor extends HTMLElement {
  setConfig(config) { this._cfg = Object.assign({}, config); this._loadDevice(); this._render(); }
  set hass(h) { const first = !this._hass; this._hass = h; if (first) this._loadDevice(); if (this._form) this._form.hass = h; else this._render(); }
  _base() {
    if (this._cfg && this._cfg.device_id) return Object.assign({}, (this._dev && this._devFor === this._cfg.device_id && this._dev.entities) || {});
    return Object.assign({}, EC_DEFAULT_ENTITIES);
  }
  _loadDevice() {
    const id = this._cfg && this._cfg.device_id;
    if (!id || !this._hass || this._devFor === id) return;
    ecDeviceMap(this._hass, id).then((dev) => {
      if (!this._cfg || this._cfg.device_id !== id) return;
      this._dev = dev || { entities: {} }; this._devFor = id; this._render();
    });
  }
  connectedCallback() { ecEnsureForm().then(() => this._render()); }
  _data() {
    const c = this._cfg || {};
    const e = Object.assign(this._base(), c.encje || {});
    if (c.cyrkulacja) e.cyrkulacja = c.cyrkulacja;
    const d = { device_id: c.device_id || undefined, nazwa: c.nazwa || 'Piec Pello', motyw: c.motyw || 'auto', tylko_podglad: !!c.tylko_podglad, max_wysokosc: c.max_wysokosc || '', alarm_prefix: c.alarm_prefix || EC_ALARM_PREFIX };
    for (const k of Object.keys(EC_DEFAULT_ENTITIES)) if (e[k]) d[k] = e[k];
    return d;
  }
  _render() {
    if (!this._hass || !this._cfg || !customElements.get('ha-form')) {
      if (!this._hint) { this._hint = document.createElement('div'); this._hint.style.padding = '8px 0'; this._hint.textContent = 'Ładowanie edytora…'; this.appendChild(this._hint); }
      return;
    }
    if (this._hint) { this._hint.remove(); this._hint = null; }
    if (!this._form) {
      this._form = document.createElement('ha-form');
      this._form.computeLabel = (s) => EC_LABELS[s.name] || s.title || s.name;
      this._form.addEventListener('value-changed', (ev) => this._changed(ev.detail.value));
      this.appendChild(this._form);
    }
    this._form.hass = this._hass;
    this._form.schema = EC_SCHEMA;
    this._form.data = this._data();
  }
  _changed(v) {
    const cfg = Object.assign({}, this._cfg);
    delete cfg.cyrkulacja;
    for (const k of EC_GENERAL_KEYS) {
      const val = v[k];
      if (val === undefined || val === '' || val === null) delete cfg[k]; else cfg[k] = val;
    }
    if (cfg.motyw === 'auto') delete cfg.motyw;
    if (cfg.alarm_prefix === EC_ALARM_PREFIX) delete cfg.alarm_prefix;
    if (!cfg.tylko_podglad) cfg.tylko_podglad = false;
    const devChanged = (v.device_id || undefined) !== (this._cfg.device_id || undefined);
    if (devChanged) {
      // Nowy piec: encje bierzemy z niego, zostają tylko dodatki spoza integracji.
      this._cfg = cfg;
      const keep = {};
      if (v.cyrkulacja) keep.cyrkulacja = v.cyrkulacja;
      if (Object.keys(keep).length) cfg.encje = keep; else delete cfg.encje;
      this._loadDevice();
      this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: cfg }, bubbles: true, composed: true }));
      return;
    }
    const base = this._base();
    const encje = {};
    for (const k of Object.keys(EC_DEFAULT_ENTITIES)) {
      const val = v[k] || '';
      const def = base[k] || '';
      if (val !== def) encje[k] = val;
    }
    if (Object.keys(encje).length) cfg.encje = encje; else delete cfg.encje;
    this._cfg = cfg;
    this.dispatchEvent(new CustomEvent('config-changed', { detail: { config: cfg }, bubbles: true, composed: true }));
  }
}
if (!customElements.get('esterownik-pello-card-editor')) customElements.define('esterownik-pello-card-editor', EsterownikPelloCardEditor);

if (!customElements.get('esterownik-pello-card')) customElements.define('esterownik-pello-card', EsterownikPelloCard);
if (!customElements.get('esterownik-pello-mini-card')) customElements.define('esterownik-pello-mini-card', EsterownikPelloMiniCard);
window.customCards = window.customCards || [];
if (!window.customCards.find((c) => c.type === 'esterownik-pello-card')) {
  window.customCards.push(
    { type: 'esterownik-pello-card', name: 'Esterownik — Pello (schemat)', description: 'Schemat kotłowni Pello 3.5 z podglądem i sterowaniem', preview: false },
    { type: 'esterownik-pello-mini-card', name: 'Esterownik — Pello (status)', description: 'Kompaktowy status pieca Pello', preview: false },
  );
}
console.info(`%c ESTEROWNIK-CARD %c ${EC_VERSION} `, 'background:#1f6fb8;color:#fff', 'background:#e0262b;color:#fff');
