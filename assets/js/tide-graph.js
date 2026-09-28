/* 물높이 그래프 (국립해양조사원 조석예보 시계열, api/marine.php?kind=series)
 * BADAGAJA_TIDEGRAPH.mount(box, region, { dark: true|false, coords: [lat,lng] })
 */
(function () {
  var NS = 'http://www.w3.org/2000/svg';
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function s(tag, attrs) { var e = document.createElementNS(NS, tag); for (var k in attrs) e.setAttribute(k, attrs[k]); return e; }
  function toMin(hm) { var p = hm.split(':'); return +p[0] * 60 + +p[1]; }
  function fmt(m) { m = Math.round(m); return ('0' + Math.floor(m / 60)).slice(-2) + ':' + ('0' + (m % 60)).slice(-2); }

  function extrema(pts) {
    var out = [], w = 6;   // 앞뒤 1시간 안에서 가장 높거나 낮은 지점
    for (var i = 0; i < pts.length; i++) {
      var v = pts[i][1], hi = true, lo = true;
      for (var j = Math.max(0, i - w); j <= Math.min(pts.length - 1, i + w); j++) {
        if (j === i) continue;
        if (pts[j][1] > v || (pts[j][1] === v && j < i)) hi = false;
        if (pts[j][1] < v || (pts[j][1] === v && j < i)) lo = false;
      }
      if ((hi || lo) && i > 0 && i < pts.length - 1) out.push({ i: i, t: pts[i][0], v: v, type: hi ? 'high' : 'low' });
    }
    return out;
  }

  function draw(box, d, opt) {
    box.querySelector('.tg-plot') && box.querySelector('.tg-plot').remove();
    var W = 720, H = 190, L = 34, R = 10, T = 26, B = 24;
    var pts = d.points.map(function (p) { return [toMin(p[0]), p[1]]; });
    var vals = pts.map(function (p) { return p[1]; });
    var vmin = Math.min.apply(null, vals), vmax = Math.max.apply(null, vals), pad = Math.max(10, (vmax - vmin) * 0.12);
    vmin -= pad; vmax += pad;
    // 동해안처럼 조차가 작은 곳은 세로를 자료 범위에 딱 맞추면 1cm 차이가 크게 벌어져 톱니로 보입니다.
    // 최소 폭을 60cm 로 두어 잔잔한 오르내림이 과장되지 않게 합니다. (2026-09-23)
    var MINSPAN = 60;
    if (vmax - vmin < MINSPAN) {
      var mid = (vmax + vmin) / 2;
      vmin = mid - MINSPAN / 2; vmax = mid + MINSPAN / 2;
    }
    var X = function (m) { return L + m / 1440 * (W - L - R); }, Y = function (v) { return T + (1 - (v - vmin) / (vmax - vmin)) * (H - T - B); };
    var wrap = el('div', 'tg-plot'), svg = s('svg', { viewBox: '0 0 ' + W + ' ' + H, role: 'img', 'aria-label': d.station + ' 시간별 물높이 그래프' });
    var gid = 'tg' + Math.random().toString(36).slice(2, 7);
    var defs = s('defs', {}), grad = s('linearGradient', { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 });
    grad.appendChild(s('stop', { offset: '0%', 'stop-color': opt.dark ? '#6FA8A0' : '#2E8A8A', 'stop-opacity': opt.dark ? '.55' : '.35' }));
    grad.appendChild(s('stop', { offset: '100%', 'stop-color': opt.dark ? '#6FA8A0' : '#2E8A8A', 'stop-opacity': '0' }));
    defs.appendChild(grad); svg.appendChild(defs);
    // 밤 시간 음영
    if (opt.sun) {
      var rise = toMin(opt.sun.rise), set = toMin(opt.sun.set), night = opt.dark ? 'rgba(0,0,0,.22)' : 'rgba(38,51,46,.06)';
      svg.appendChild(s('rect', { x: X(0), y: T, width: X(rise) - X(0), height: H - T - B, fill: night }));
      svg.appendChild(s('rect', { x: X(set), y: T, width: X(1440) - X(set), height: H - T - B, fill: night }));
    }
    // 격자
    [0, 6, 12, 18, 24].forEach(function (h) {
      var x = X(h * 60);
      svg.appendChild(s('line', { x1: x, y1: T, x2: x, y2: H - B, class: 'tg-grid' }));
      var tx = s('text', { x: x, y: H - 6, 'text-anchor': h === 0 ? 'start' : h === 24 ? 'end' : 'middle', class: 'tg-axis' }); tx.textContent = h + '시'; svg.appendChild(tx);
    });
    var ty = s('text', { x: 2, y: T - 10, class: 'tg-axis' }); ty.textContent = 'cm'; svg.appendChild(ty);
    // 곡선
    // 점을 직선으로 이으면 10분마다 꺾여 톱니처럼 보입니다. 조석은 본래 매끄러운 곡선이라 부드럽게 잇습니다
    var line = (function () {
      var xy = pts.map(function (p) { return [X(p[0]), Y(p[1])]; });
      if (xy.length < 3) {
        return xy.map(function (q, i) { return (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1); }).join(' ');
      }
      var d = 'M' + xy[0][0].toFixed(1) + ' ' + xy[0][1].toFixed(1);
      for (var i = 0; i < xy.length - 1; i++) {
        var p0 = xy[i > 0 ? i - 1 : 0], p1 = xy[i], p2 = xy[i + 1], p3 = xy[i + 2 < xy.length ? i + 2 : i + 1];
        var k = 0.2;   // 당기는 정도 — 크면 물결이 심해집니다
        var c1x = p1[0] + (p2[0] - p0[0]) * k, c1y = p1[1] + (p2[1] - p0[1]) * k;
        var c2x = p2[0] - (p3[0] - p1[0]) * k, c2y = p2[1] - (p3[1] - p1[1]) * k;
        d += ' C' + c1x.toFixed(1) + ' ' + c1y.toFixed(1) + ' ' + c2x.toFixed(1) + ' ' + c2y.toFixed(1)
           + ' ' + p2[0].toFixed(1) + ' ' + p2[1].toFixed(1);
      }
      return d;
    })();
    svg.appendChild(s('path', { d: line + ' L' + X(pts[pts.length - 1][0]) + ' ' + (H - B) + ' L' + X(pts[0][0]) + ' ' + (H - B) + ' Z', fill: 'url(#' + gid + ')' }));
    svg.appendChild(s('path', { d: line, class: 'tg-line' }));
    // 만조·간조 표시: 물때표와 같은 고·저조 예보 시각이 있으면 그것을, 없으면 곡선에서 찾은 값
    var marks = (opt.events && opt.events.length) ? opt.events.map(function (ev) {
      var m = toMin(ev.time), a = pts[0], b = pts[pts.length - 1];
      for (var k = 1; k < pts.length; k++) { if (pts[k][0] >= m) { a = pts[k - 1]; b = pts[k]; break; } }
      var v = a[0] === b[0] ? a[1] : a[1] + (b[1] - a[1]) * (m - a[0]) / (b[0] - a[0]);
      return { t: ev.time, v: ev.level != null ? Math.max(Math.min(ev.level, vmax), vmin) : v, vy: v, type: ev.type === '만조' ? 'high' : 'low' };
    }) : extrema(d.points).map(function (e) { e.vy = e.v; return e; });
    marks.forEach(function (e) {
      e.v = e.vy;
      var x = X(toMin(e.t)), y = Y(e.v);
      svg.appendChild(s('circle', { cx: x, cy: y, r: 4, class: 'tg-dot ' + e.type }));
      var lb = s('text', { x: Math.min(W - 40, Math.max(L + 20, x)), y: e.type === 'high' ? y - 9 : y + 17, 'text-anchor': 'middle', class: 'tg-lbl ' + e.type });
      lb.textContent = (e.type === 'high' ? '만조 ' : '간조 ') + e.t;
      svg.appendChild(lb);
    });
    // 지금
    if (opt.today) {
      var nm = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000), m = nm.getHours() * 60 + nm.getMinutes();
      var xn = X(m); svg.appendChild(s('line', { x1: xn, y1: T - 4, x2: xn, y2: H - B, class: 'tg-now' }));
      var tn = s('text', { x: Math.min(W - 20, xn + 4), y: T - 8, class: 'tg-nowlbl' }); tn.textContent = '지금'; svg.appendChild(tn);
    }
    // 눌러서 보기
    var hv = s('g', { class: 'tg-hover', style: 'display:none' }), hl = s('line', { y1: T, y2: H - B, class: 'tg-hline' }), hc = s('circle', { r: 5, class: 'tg-hdot' });
    hv.appendChild(hl); hv.appendChild(hc); svg.appendChild(hv);
    var tip = el('div', 'tg-tip'); tip.hidden = true;
    function move(ev) {
      var r = svg.getBoundingClientRect(), cx = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left) / r.width * W;
      var m = Math.max(0, Math.min(1440, (cx - L) / (W - L - R) * 1440)), best = pts[0];
      pts.forEach(function (p) { if (Math.abs(p[0] - m) < Math.abs(best[0] - m)) best = p; });
      var x = X(best[0]), y = Y(best[1]);
      hv.style.display = ''; hl.setAttribute('x1', x); hl.setAttribute('x2', x); hc.setAttribute('cx', x); hc.setAttribute('cy', y);
      tip.hidden = false; tip.textContent = fmt(best[0]) + ' · ' + best[1] + 'cm';
      tip.style.left = (x / W * 100) + '%';
    }
    svg.addEventListener('pointermove', move); svg.addEventListener('pointerdown', move);
    svg.addEventListener('touchmove', function (e) { move(e); }, { passive: true });
    svg.addEventListener('pointerleave', function () { hv.style.display = 'none'; tip.hidden = true; });
    wrap.appendChild(svg); wrap.appendChild(tip);
    box.insertBefore(wrap, box.querySelector('.tg-foot'));
    box.querySelector('.tg-foot').textContent = '관측소: ' + d.station + ' · 10분 간격 예측 물높이 · ' + d.source;
  }

  function mount(box, region, opt) {
    opt = opt || {};
    box.innerHTML = '';
    box.classList.add('tide-graph'); if (opt.dark) box.classList.add('dark');
    var head = el('div', 'tg-head'); head.appendChild(el('b', null, '🌊 시간별 물높이'));
    var tabs = el('div', 'tg-tabs'); head.appendChild(tabs); box.appendChild(head);
    box.appendChild(el('p', 'tg-foot', '물높이 예보를 불러오는 중…'));
    var T = window.BADAGAJA_TIDE, cache = {}, tidePromise = null;
    function load(day) {
      [].forEach.call(tabs.children, function (b, i) { b.classList.toggle('on', i === day); });
      var dt = new Date(); dt.setDate(dt.getDate() + day);
      var sun = (T && opt.coords) ? T.sunTimes(dt, opt.coords[0], opt.coords[1]) : null;
      var go = function (d, ev) {
        if (!d || !d.ok) { box.querySelector('.tg-foot').textContent = '물높이 예보를 불러오지 못했어요.'; var p = box.querySelector('.tg-plot'); if (p) p.remove(); return; }
        draw(box, d, { dark: opt.dark, sun: sun, today: day === 0, events: ev });
      };
      if (cache[day]) return go(cache[day].d, cache[day].ev);
      if (!tidePromise) tidePromise = fetch('api/tide-cache.php?region=' + region).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
      Promise.all([
        fetch('api/marine.php?kind=series&region=' + region + '&day=' + day).then(function (r) { if (!r.ok) throw 0; return r.json(); }),
        tidePromise
      ]).then(function (a) {
        var ev = a[1] && a[1].days && a[1].days[day] ? a[1].days[day].events : null;
        cache[day] = { d: a[0], ev: ev }; go(a[0], ev);
      }).catch(function () { go(null); });
    }
    ['오늘', '내일', '모레'].forEach(function (n, i) { var b = el('button', i === 0 ? 'on' : '', n); b.type = 'button'; b.addEventListener('click', function () { load(i); }); tabs.appendChild(b); });
    load(0);
    return { load: load };
  }
  window.BADAGAJA_TIDEGRAPH = { mount: mount };
})();
