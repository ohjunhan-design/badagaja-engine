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

  // ── 잔떨림을 고릅니다 (2026-09-29 주인 지시 — 「좀더 부드럽게」)
  //
  //   10분 간격 예측값은 cm 단위로 반올림되어 **계단이 집니다.**
  //   곡선으로 이어도 그 계단을 그대로 따라가 톱니처럼 보입니다.
  //
  //   재 보니 이랬습니다.
  //       곡선 조각 143개 · 평균 꺾임 2.74도 · 가장 꺾인 곳 9.2도
  //   조석은 본래 매끄러우니 이 꺾임은 **자료의 잡음**입니다.
  //
  //   두 가지를 합니다.
  //     ① 이웃 평균으로 값을 고릅니다 (1-2-1 저울)
  //     ② 20분 간격으로 솎습니다 — 조석은 느리게 변해 넉넉합니다
  //
  //   ★ 만조·간조 **시각과 높이는 따로 표시**하므로
  //     (해양조사원 고·저조 예보) 정확도가 떨어지지 않습니다.
  //     솎는 것은 **선을 그리는 점**뿐입니다.
  function 고르게(점들) {
    if (!점들 || 점들.length < 5) { return 점들 || []; }
    // ① 이웃 평균 — 양 끝은 그대로 둡니다
    var 고른것 = 점들.map(function (p, i) {
      if (i === 0 || i === 점들.length - 1) { return [p[0], p[1]]; }
      var a = 점들[i - 1][1], b = p[1], c = 점들[i + 1][1];
      return [p[0], (a + 2 * b + c) / 4];
    });
    // ② 솎기 — 20분마다. 마지막 점은 반드시 남깁니다
    var 사이 = 20;
    var 난것 = [];
    for (var i = 0; i < 고른것.length; i++) {
      if (i === 0 || i === 고른것.length - 1
          || 고른것[i][0] - 난것[난것.length - 1][0] >= 사이) {
        난것.push(고른것[i]);
      }
    }
    return 난것;
  }

  function draw(box, d, opt) {
    box.querySelector('.tg-plot') && box.querySelector('.tg-plot').remove();
    // ★ 2026-10-01 — 아래 여백(B)을 늘렸습니다.
    //   시각 눈금과 「지금」을 **같은 줄**에 두면 서로 안 부딪칩니다.
    //   왼쪽(L)은 `cm` 글자를 뺀 만큼 줄였습니다.
    var W = 720, H = 196, L = 16, R = 12, T = 22, B = 34;
    var pts = 고르게(d.points.map(function (p) { return [toMin(p[0]), p[1]]; }));
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
      var rise = toMin(opt.sun.rise), set = toMin(opt.sun.set), night = opt.dark ? 'rgba(0,0,0,.26)' : 'rgba(47,93,87,.09)';
      svg.appendChild(s('rect', { x: X(0), y: T, width: X(rise) - X(0), height: H - T - B, fill: night }));
      svg.appendChild(s('rect', { x: X(set), y: T, width: X(1440) - X(set), height: H - T - B, fill: night }));
    }
    // ★ **가로 눈금선** — 높이를 눈으로 가늘하게 합니다 (2026-10-01)
    //   전에는 세로선만 있어 곱선이 허공에 떠 있는 듯했습니다.
    [0.25, 0.5, 0.75].forEach(function (r) {
      var yy = T + r * (H - T - B);
      svg.appendChild(s('line', { x1: L, y1: yy, x2: W - R, y2: yy,
                                  class: 'tg-grid tg-grid--h' }));
    });
    // 격자
    [0, 6, 12, 18, 24].forEach(function (h) {
      var x = X(h * 60);
      svg.appendChild(s('line', { x1: x, y1: T, x2: x, y2: H - B, class: 'tg-grid' }));
      // ★ 눈금 글씨를 **맨 아래로** 내립니다 — 간조 라벨과 안 부딪치게
      var tx = s('text', { x: x, y: H - 8, 'text-anchor': h === 0 ? 'start' : h === 24 ? 'end' : 'middle', class: 'tg-axis' }); tx.textContent = h + '시'; svg.appendChild(tx);
    });
    // ★ 왼쪽 위 `cm` 을 **비웠습니다** (2026-10-01 주인 지시)
    //   「모든 물때에서 cm 지워」. 무엇을 재는지는 라벨과
    //   꼬리글에서 이미 압니다. 글자 하나가 덬그러니 떠 있었습니다.
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
    // ★ **fill='none' 을 속성으로 박습니다** (2026-09-29 주인 지적)
    //
    //   SVG <path> 는 fill 기본값이 **검정**입니다.
    //   스타일시트(tidegraph.css)가 .tg-line{fill:none} 을 주지만,
    //   **CSS 가 실리기 전 찰나**에는 곡선 안쪽이 통째로 검게 보입니다.
    //   주인이 그 순간을 보고 「뭐가 잘못되었어」 하셨습니다.
    //
    //   그리는 쪽에서 속성으로 박으면 **CSS 를 기다리지 않습니다.**
    //   보이는 것을 스타일시트에만 맡기지 않습니다.
    svg.appendChild(s('path', { d: line, class: 'tg-line',
                                fill: 'none' }));
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
      svg.appendChild(s('circle', { cx: x, cy: y, r: 4.5, class: 'tg-dot ' + e.type }));
      // ★ 간조 라벨을 점에 **더 가깝게** 붙입니다 (17 → 14)
      //   아래 눈금(「12시」)과 부딪혀 갑니다.
      var lb = s('text', { x: Math.min(W - 42, Math.max(L + 24, x)), y: e.type === 'high' ? y - 10 : y + 14, 'text-anchor': 'middle', class: 'tg-lbl ' + e.type });
      lb.textContent = (e.type === 'high' ? '만조 ' : '간조 ') + e.t;
      svg.appendChild(lb);
    });
    // 지금
    if (opt.today) {
      var nm = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000), m = nm.getHours() * 60 + nm.getMinutes();
      // ★ 「지금」을 **아래 눈금 줄로** 내렸습니다 (2026-10-01)
      //   전에는 위 끝에 있어 「만조 13:45」 라벨과 **겹쳤습니다.**
      //   시각 눈금과 같은 줄에 두면 서로 안 부딪칩니다.
      var xn = X(m); svg.appendChild(s('line', { x1: xn, y1: T, x2: xn, y2: H - B, class: 'tg-now' }));
      var tn = s('text', { x: Math.min(W - 24, Math.max(L + 18, xn)), y: H - 8, 'text-anchor': 'middle', class: 'tg-nowlbl' }); tn.textContent = '지금'; svg.appendChild(tn);
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
    // ★ **api 주소를 받습니다** (2026-09-29 주인 지적 「롬링 물때표가 안나와」)
    //   전에는 'api/marine.php' 로 **고정**되어 있었습니다.
    //   권역 쪽(/gochang.html)에서는 맞지만,
    //   묶음 쪽은 주소가 **폴더**라(/chungnam/)
    //   /chungnam/api/marine.php 로 가 **404** 였습니다.
    //   그 404 가 「물높이 예보를 불러오지 못했어요」로 보였습니다.
    //   이제 쪽을 만드는 쪽에서 상대 주소를 주고,
    //   안 주면 예전처럼 'api/' 를 씁니다.
    var API = opt.api || 'api/';
    box.innerHTML = '';
    box.classList.add('tide-graph'); if (opt.dark) box.classList.add('dark');
    // ★ **날짜 단추를 뺐습니다** (2026-09-30 주인 지시)
    //   「날자별 버튼도 지워버려 이건 필요없어
    //     오늘 시간별 물높이 이렇게 통일하자」
    //
    //   이 그래프가 있는 자리는 **오늘 나갈지 정하는 자리**입니다.
    //   이레치를 넘기는 단추가 일곱 개나 붙어 눈이 먼저 그리로 갔습니다.
    //   먼 날은 「물때표 2주 전체 보기」가 맡습니다 — 몫이 나뉩니다.
    var head = el('div', 'tg-head');
    head.appendChild(el('b', null, '🌊 오늘 시간별 물높이'));
    box.appendChild(head);
    var tabs = null;
    box.appendChild(el('p', 'tg-foot', '물높이 예보를 불러오는 중…'));
    var T = window.BADAGAJA_TIDE, cache = {}, tidePromise = null;
    function load(day) {
      if (tabs) {
        [].forEach.call(tabs.children, function (b, i) {
          b.classList.toggle('on', i === day); });
      }
      var dt = new Date(); dt.setDate(dt.getDate() + day);
      var sun = (T && opt.coords) ? T.sunTimes(dt, opt.coords[0], opt.coords[1]) : null;
      var go = function (d, ev) {
        if (!d || !d.ok) { box.querySelector('.tg-foot').textContent = '물높이 예보를 불러오지 못했어요.'; var p = box.querySelector('.tg-plot'); if (p) p.remove(); return; }
        draw(box, d, { dark: opt.dark, sun: sun, today: day === 0, events: ev });
      };
      if (cache[day]) return go(cache[day].d, cache[day].ev);
      if (!tidePromise) tidePromise = fetch(API + 'tide-cache.php?region=' + region).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
      Promise.all([
        fetch(API + 'marine.php?kind=series&region=' + region + '&day=' + day).then(function (r) { if (!r.ok) throw 0; return r.json(); }),
        tidePromise
      ]).then(function (a) {
        var ev = a[1] && a[1].days && a[1].days[day] ? a[1].days[day].events : null;
        cache[day] = { d: a[0], ev: ev }; go(a[0], ev);
      }).catch(function () { go(null); });
    }
    load(0);
    return { load: load };
  }
  window.BADAGAJA_TIDEGRAPH = { mount: mount };
})();
