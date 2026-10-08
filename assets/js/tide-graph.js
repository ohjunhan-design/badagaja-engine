/* 물높이 그래프 (국립해양조사원 조석예보 시계열, api/marine.php?kind=series)
 * BADAGAJA_TIDEGRAPH.mount(box, region, { dark: true|false, coords: [lat,lng] })
 *
 * ★ 2026-10-02 — **디자인을 지피티 시안대로 다시 짰습니다.**
 *   주인 지시 「디자인부분은 너가 항상 의뢰를 해서 지피티의 사진이
 *   오면 그걸 사용하면됨」. 받은 파일 `tide-graph-design.html` 의
 *   짜임·색·치수를 그대로 옮기고, **곡선 계산과 「지금」 시각
 *   계산은 건드리지 않았습니다**(지피티 지시).
 *
 *   시안이 바꾼 것
 *     · 머리 — 눈썹「오늘의 바다」+ 제목 + 오른쪽에 관측소
 *     · 간·만조 — 알약 네 개, 시각을 굵게
 *     · 그래프 — 크림색 상자(.tg-plot) 안에, **격자선 없이**
 *     · 「지금」 — 주황 알약 배지
 *     · 꼬리 — 출처 / 주의 두 덩이 + 색 범례 한 줄
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

  // 다시 그릴 때 **먼저 지웁니다** — 그래프·범례·알약 셋이 한 벌입니다
  function 지우기(box) {
    ['.tg-plot', '.tg-note'].forEach(function (c) {
      var e = box.querySelector(c); if (e) { e.remove(); }
    });
    var w = box.querySelector('.tg-when'); if (w) { w.innerHTML = ''; }
  }

  function draw(box, d, opt) {
    지우기(box);
    /* ★ compact — 좁은 칸(포인트 상세 패널)용 표시 모드 (2026-10-08)
       계산은 그대로이고 **보여 주는 방식만** 다릅니다. */
    var compact = (opt.mode === 'compact');
    var 역 = box.querySelector('.tg-station');
    if (역) { 역.textContent = (d.station || '') + ' 관측소 기준'; }

    var pts = 고르게(d.points.map(function (p) { return [toMin(p[0]), p[1]]; }));
    var vals = pts.map(function (p) { return p[1]; });
    var vmin = Math.min.apply(null, vals), vmax = Math.max.apply(null, vals);
    var pad = Math.max(10, (vmax - vmin) * 0.12);
    vmin -= pad; vmax += pad;
    // 동해안처럼 조차가 작은 곳은 세로를 자료 범위에 딱 맞추면 1cm 차이가
    // 크게 벌어져 톱니로 보입니다. 최소 폭을 60cm 로 두어 잔잔한
    // 오르내림이 과장되지 않게 합니다. (2026-09-23)
    var MINSPAN = 60;
    if (vmax - vmin < MINSPAN) {
      var mid = (vmax + vmin) / 2;
      vmin = mid - MINSPAN / 2; vmax = mid + MINSPAN / 2;
    }

    // 만조·간조: 물때표와 같은 고·저조 예보 시각이 있으면 그것을,
    // 없으면 곡선에서 찾은 값
    var marks = (opt.events && opt.events.length) ? opt.events.map(function (ev) {
      var m = toMin(ev.time), a = pts[0], b = pts[pts.length - 1];
      for (var j = 1; j < pts.length; j++) { if (pts[j][0] >= m) { a = pts[j - 1]; b = pts[j]; break; } }
      var v = a[0] === b[0] ? a[1] : a[1] + (b[1] - a[1]) * (m - a[0]) / (b[0] - a[0]);
      return { t: ev.time, v: v, type: ev.type === '만조' ? 'high' : 'low' };
    }) : extrema(d.points).map(function (e) { return { t: e.t, v: e.v, type: e.type }; });

    // ★ 간·만조 시각은 **곡선 밖 알약 줄**입니다 (지피티 시안)
    //   그래프 안에는 곡선 + 작은 점 + 「지금」 세로선만 둡니다.
    //   그래야 화면이 좁아져도 글자가 점을 덮지 않습니다.
    //
    // ★ 2026-10-02 — **권역 쪽에서는 이 줄을 끕니다** (지피티 검수)
    //   권역 쪽에는 바로 옆에 「오늘 물때」 요약이 있어 **똑같은 네
    //   시각이 두 번** 나왔습니다. 모바일에서는 세로로 쌓여 바로
    //   위아래로 붙습니다.
    //   지피티 — 「요약칸에 시각을 남기고 그래프 머리의 알약은
    //     제거합니다. 요약칸은 그래프가 실패해도 남아 정보
    //     안정성이 더 높습니다. 다만 점의 색 의미가 사라지지
    //     않도록 그래프 아래에 아주 작은 범례만 남깁니다」
    /* compact 에서는 알약 줄이 아예 없습니다 — 바로 위 패널에
       같은 네 시각이 수위까지 붙어 있습니다 (지피티 검수) */
    var 알약보임 = !compact && box.getAttribute('data-events') !== 'off';
    var when = box.querySelector('.tg-when');
    if (when && 알약보임) {
      marks.forEach(function (e) {
        var one = el('span', 'tg-w ' + e.type);
        one.appendChild(el('i', 'tg-w-k', e.type === 'high' ? '만조' : '간조'));
        one.appendChild(el('b', 'tg-w-t', e.t));
        when.appendChild(one);
      });
    }

    // ── 그래프 바탕을 먼저 넣고 **실제 폭을 잽니다**
    //
    //   ★ 왜 재는가 (2026-10-02)
    //     시안은 viewBox 720×168 에 글자 12px 입니다. 그런데 이 그림을
    //     360px 화면에 넣으면 **안의 글자도 절반(6px)** 이 됩니다 —
    //     밖에서 햇빛 아래 못 읽습니다. 전에는 차림표에서 글자만
    //     17~20px 로 키웠는데, 그러면 점·선과 비례가 깨졌습니다.
    //
    //     그래서 **치수 전체에 같은 배율(k)** 을 곱합니다.
    //     그러면 어느 폭에서든 화면에 보이는 크기가 **시안 그대로**
    //     입니다 — 글자 12px, 알약 42×22, 높이 168px.
    var wrap = el('div', 'tg-plot');
    var svg = s('svg', { role: 'img', 'aria-label': (d.station || '') + ' 시간별 물높이 그래프' });
    wrap.appendChild(svg);
    box.insertBefore(wrap, box.querySelector('.tg-foot'));
    var 실폭 = svg.getBoundingClientRect().width || 720;
    var k = Math.max(1, 720 / 실폭);

    /* ★ **좁은 칸을 위한 compact 모드** (2026-10-08 지피티 검수)
     *
     *   포인트 상세 패널(폭 346px)에 그대로 넣었더니 그래프가
     *   **376px** 로 커졌습니다. 까닭은 계산이 틀려서가 아니라
     *   **720px 폭용 UI 를 346px 칸에 그대로 넣었기** 때문입니다.
     *     720 논리폭 → 346px 화면에 축소 → 글씨도 반토막
     *     → k=2.08 로 모든 것을 다시 키움 → 높이 376px
     *
     *   지피티 — 「max-height 로 자르지도 말고, 기존 k 를 없애지도
     *     마세요. 정답은 공식 compact 표시 모드를 하나 추가하는
     *     것입니다. 손댈 것은 데이터나 계산이 아니라 그래프의
     *     표현 레이어뿐입니다」
     *
     *   compact 는 **논리 폭을 실제 폭과 맞춥니다.**
     *     346 논리폭 → 346px 화면 → 글씨 12px 그대로 → 높이 120px
     *
     *   ★ mode 를 안 주면 **지금까지와 한 글자도 다르지 않습니다.**
     *     홈·물때 쪽 그래프는 한 픽셀도 바뀌면 안 됩니다.
     */
    var W, H, L, R, T, B;
    if (compact) {
      W = Math.max(280, Math.round(실폭));
      H = 120;
      k = 1;
      L = 10; R = 8; T = 12; B = 22;
    } else {
      W = 720;
      H = 168 * k; L = 16 * k; R = 12 * k; T = 28 * k; B = 26 * k;
    }
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H.toFixed(1));

    var X = function (m) { return L + m / 1440 * (W - L - R); };
    var Y = function (v) { return T + (1 - (v - vmin) / (vmax - vmin)) * (H - T - B); };

    var gid = 'tg' + Math.random().toString(36).slice(2, 7);
    var defs = s('defs', {}), grad = s('linearGradient', { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 });
    // 시안 — #7CB4AD 0.44 → 0.025
    grad.appendChild(s('stop', { offset: '0%', 'stop-color': opt.dark ? '#6FA8A0' : '#7CB4AD', 'stop-opacity': opt.dark ? '.55' : '.44' }));
    grad.appendChild(s('stop', { offset: '100%', 'stop-color': opt.dark ? '#6FA8A0' : '#7CB4AD', 'stop-opacity': '.025' }));
    defs.appendChild(grad); svg.appendChild(defs);

    // ★ **밤 시간 음영은 두지 않습니다** (2026-10-02 지피티 검수)
    //   「야간 음영은 제거하십시오. 첫 화면에서 꼭 필요한 정보가
    //     아니고 지금의 깨끗한 그래프를 흐립니다」
    //   해뜸·해짐은 쪽의 다른 자리에서 숫자로 밝힙니다.

    // 곡선 — 점을 직선으로 이으면 10분마다 꺾여 톱니처럼 보입니다.
    // 조석은 본래 매끄러운 곡선이라 부드럽게 잇습니다
    var line = (function () {
      var xy = pts.map(function (p) { return [X(p[0]), Y(p[1])]; });
      if (xy.length < 3) {
        return xy.map(function (q, i) { return (i ? 'L' : 'M') + q[0].toFixed(1) + ' ' + q[1].toFixed(1); }).join(' ');
      }
      var dd = 'M' + xy[0][0].toFixed(1) + ' ' + xy[0][1].toFixed(1);
      for (var i = 0; i < xy.length - 1; i++) {
        var p0 = xy[i > 0 ? i - 1 : 0], p1 = xy[i], p2 = xy[i + 1], p3 = xy[i + 2 < xy.length ? i + 2 : i + 1];
        var 당김 = 0.2;   // 크면 물결이 심해집니다
        var c1x = p1[0] + (p2[0] - p0[0]) * 당김, c1y = p1[1] + (p2[1] - p0[1]) * 당김;
        var c2x = p2[0] - (p3[0] - p1[0]) * 당김, c2y = p2[1] - (p3[1] - p1[1]) * 당김;
        dd += ' C' + c1x.toFixed(1) + ' ' + c1y.toFixed(1) + ' ' + c2x.toFixed(1) + ' ' + c2y.toFixed(1)
            + ' ' + p2[0].toFixed(1) + ' ' + p2[1].toFixed(1);
      }
      return dd;
    })();
    svg.appendChild(s('path', {
      d: line + ' L' + X(pts[pts.length - 1][0]).toFixed(1) + ' ' + (H - B).toFixed(1)
         + ' L' + X(pts[0][0]).toFixed(1) + ' ' + (H - B).toFixed(1) + ' Z',
      fill: 'url(#' + gid + ')' }));
    // ★ **fill='none' 을 속성으로 박습니다** (2026-09-29 주인 지적)
    //
    //   SVG <path> 는 fill 기본값이 **검정**입니다.
    //   스타일시트(tidegraph.css)가 .tg-line{fill:none} 을 주지만,
    //   **CSS 가 실리기 전 찰나**에는 곡선 안쪽이 통째로 검게 보입니다.
    //   주인이 그 순간을 보고 「뭐가 잘못되었어」 하셨습니다.
    svg.appendChild(s('path', { d: line, class: 'tg-line', fill: 'none',
                                'stroke-width': (2.8 * k).toFixed(1) }));

    // 만조·간조 점 — **글자 없이 점만** (시안)
    marks.forEach(function (e) {
      svg.appendChild(s('circle', {
        cx: X(toMin(e.t)).toFixed(1), cy: Y(e.v).toFixed(1),
        r: (5 * k).toFixed(1), class: 'tg-dot ' + e.type,
        'stroke-width': (2 * k).toFixed(1) }));
    });

    // 시각 눈금 — **글자만**, 격자선 없이 (시안)
    //   손님이 알고 싶은 것은 「언제 물이 빠지나」이지
    //   「6시가 어디쯤인가」가 아닙니다. 0·12·24시 셋만 둡니다.
    [0, 12, 24].forEach(function (h) {
      var tx = s('text', { x: X(h * 60).toFixed(1), y: (H - 6 * k).toFixed(1),
                           'text-anchor': h === 0 ? 'start' : h === 24 ? 'end' : 'middle',
                           class: 'tg-axis', 'font-size': (12 * k).toFixed(1) });
      tx.textContent = h + '시'; svg.appendChild(tx);
    });

    // 지금 — 세로 점선 + **주황 알약 배지** (시안)
    if (opt.today) {
      var nm = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
      var m = nm.getHours() * 60 + nm.getMinutes();
      var xn = X(m);
      svg.appendChild(s('line', {
        x1: xn.toFixed(1), y1: T.toFixed(1), x2: xn.toFixed(1), y2: (H - B).toFixed(1),
        class: 'tg-now', 'stroke-width': (1.5 * k).toFixed(1),
        'stroke-dasharray': (4 * k).toFixed(1) + ' ' + (5 * k).toFixed(1) }));
      /* ★ compact 에서는 **알약 없이 선만** 둡니다 (지피티 검수)
           「상세 패널에는 이미 『다음 간조까지 4시간 31분』이라는
             훨씬 가치 있는 정보가 있습니다. 그래프 안의 지금 검은
             알약까지 넣으면 좁은 폭에서 복잡하기만 합니다.
             글자 없는 얇은 세로선 정도는 허용합니다」 */
      if (!compact) {
        var bw = 42 * k, bh = 22 * k;
        // 배지가 양 끝에서 잘리지 않게 안으로 당깁니다
        var bx = Math.min(W - bw - 2, Math.max(2, xn - bw / 2));
        svg.appendChild(s('rect', { x: bx.toFixed(1), y: k.toFixed(1),
                                    width: bw.toFixed(1), height: bh.toFixed(1),
                                    rx: (11 * k).toFixed(1), class: 'tg-nowbadge' }));
        var tn = s('text', { x: (bx + bw / 2).toFixed(1), y: (16 * k).toFixed(1),
                             'text-anchor': 'middle', class: 'tg-nowlbl',
                             'font-size': (12 * k).toFixed(1) });
        tn.textContent = '지금'; svg.appendChild(tn);
      }
    }

    // 눌러서 보기
    var hv = s('g', { class: 'tg-hover', style: 'display:none' });
    var hl = s('line', { y1: T.toFixed(1), y2: (H - B).toFixed(1), class: 'tg-hline',
                         'stroke-width': k.toFixed(2) });
    var hc = s('circle', { r: (5 * k).toFixed(1), class: 'tg-hdot',
                           'stroke-width': (2.5 * k).toFixed(1) });
    hv.appendChild(hl); hv.appendChild(hc); svg.appendChild(hv);
    var tip = el('div', 'tg-tip'); tip.hidden = true;
    function move(ev) {
      var r = svg.getBoundingClientRect();
      var cx = ((ev.touches ? ev.touches[0].clientX : ev.clientX) - r.left) / r.width * W;
      var mm = Math.max(0, Math.min(1440, (cx - L) / (W - L - R) * 1440)), best = pts[0];
      pts.forEach(function (p) { if (Math.abs(p[0] - mm) < Math.abs(best[0] - mm)) best = p; });
      var x = X(best[0]), y = Y(best[1]);
      hv.style.display = ''; hl.setAttribute('x1', x); hl.setAttribute('x2', x);
      hc.setAttribute('cx', x); hc.setAttribute('cy', y);
      tip.hidden = false; tip.textContent = fmt(best[0]) + ' · ' + Math.round(best[1]) + 'cm';
      tip.style.left = (x / W * 100) + '%';
    }
    svg.addEventListener('pointermove', move); svg.addEventListener('pointerdown', move);
    svg.addEventListener('touchmove', function (e) { move(e); }, { passive: true });
    svg.addEventListener('pointerleave', function () { hv.style.display = 'none'; tip.hidden = true; });
    wrap.appendChild(tip);

    // 꼬리 (시안)
    //   알약을 켠 쪽  — 출처 / 주의 두 덩이 + 아래에 글 범례
    //   알약을 끈 쪽  — **점 범례**(● 간조 ● 만조) + 출처
    //     시각을 되풀이하지 않고 **색이 무엇을 뜻하는지만** 남깁니다
    var foot = box.querySelector('.tg-foot');
    foot.textContent = '';
    /* ★ compact 에서는 **꼬리도 범례도 두지 않습니다** (지피티 검수)
         좁은 칸에서 「간조만조」가 붙어 나오고, 출처와 주의 두
         문장도 붙어 나왔습니다. 위 패널에 이미 ▼간조·▲만조 네
         칸이 있어 범례가 중복입니다.
         ★ 출처를 **없애는 것이 아닙니다** — 쪽의 출처 자리에
           한 번만 있으면 됩니다. 346px 그래프 바로 밑에 둘
           까닭이 없습니다. */
    if (compact) { return; }
    if (!알약보임) {
      var 범 = el('div', 'tg-legend');
      [['low', '간조'], ['high', '만조']].forEach(function (x) {
        var 한 = el('span', null);
        한.appendChild(el('i', 'tg-dotlbl tg-dotlbl--' + x[0]));
        한.appendChild(document.createTextNode(x[1]));
        범.appendChild(한);
      });
      foot.appendChild(범);
    }
    foot.appendChild(el('span', null, '자료: ' + d.source + ' · 10분 간격 예측'));
    foot.appendChild(el('span', null, '실제 방문 지점의 물때와 다를 수 있습니다.'));
    if (알약보임) {
      // 색 범례 — 점과 알약의 색이 무엇을 뜻하는지 한 줄로 (시안)
      box.appendChild(el('p', 'tg-note', '간조는 녹색, 만조는 주황색으로 표시합니다.'));
    }
  }

  function mount(box, region, opt) {
    opt = opt || {};
    // ★ **api 주소를 받습니다** (2026-09-29 주인 지적 「롬링 물때표가 안나와」)
    //   전에는 'api/marine.php' 로 **고정**되어 있었습니다.
    //   묶음 쪽은 주소가 **폴더**라(/chungnam/)
    //   /chungnam/api/marine.php 로 가 **404** 였습니다.
    //   그 404 가 「물높이 예보를 불러오지 못했어요」로 보였습니다.
    var API = opt.api || 'api/';
    box.innerHTML = '';
    box.classList.add('tide-graph'); if (opt.dark) box.classList.add('dark');
    // ★ 머리 — 눈썹 + 제목 + 오른쪽 관측소 (지피티 시안)
    //   ★ **날짜 단추는 두지 않습니다** (2026-09-30 주인 지시)
    //     「날자별 버튼도 지워버려 이건 필요없어
    //       오늘 시간별 물높이 이렇게 통일하자」
    //     먼 날은 「물때표 2주 전체 보기」가 맡습니다 — 몫이 나뉩니다.
    //   ★ **compact 에서는 머리를 만들지 않습니다** (2026-10-08 지피티)
    //     포인트 상세 패널에는 이미 「오늘 물때 · ○○ 관측소 기준」이
    //     있는데, 머리가 「오늘의 바다 / 시간별 물높이 / ○○ 관측소
    //     기준」을 또 적어 **같은 말이 두 번** 나왔습니다.
    //     mode 를 안 주면 지금까지와 똑같습니다.
    var compact = (opt.mode === 'compact');
    if (compact) { box.classList.add('tg-compact'); }
    if (!compact) {
      var head = el('div', 'tg-head');
      var 왼 = el('div', 'tg-head-l');
      왼.appendChild(el('div', 'tg-eyebrow', '오늘의 바다'));
      왼.appendChild(el('h2', 'tg-title', '시간별 물높이'));
      head.appendChild(왼);
      head.appendChild(el('div', 'tg-station', ''));
      box.appendChild(head);
      // 간·만조 알약 줄 — draw 가 채웁니다
      box.appendChild(el('div', 'tg-when'));
    }
    box.appendChild(el('p', 'tg-foot', '물높이 예보를 불러오는 중…'));
    var T = window.BADAGAJA_TIDE, cache = {}, tidePromise = null;
    var 알린적있나 = false;
    function load(day) {
      var dt = new Date(); dt.setDate(dt.getDate() + day);
      var sun = (T && opt.coords) ? T.sunTimes(dt, opt.coords[0], opt.coords[1]) : null;
      /* ★ **받은 자료를 밖에도 알립니다** (2026-10-08 바깥 검수 지시)
           「물때 그래프는 새 계산 로직을 만들지 말고 기존 메인
             compact 그래프 renderer/data 를 재사용할 것」
         포인트 상세 패널이 「▲ 만조 04:12 312cm」 요약과 「다음
         간조까지」를 적어야 하는데, 그 자료는 여기서 이미 받고
         있습니다. 또 받으면 **두 곳에서 따로 셈하게 됩니다.**
         그래서 그리는 쪽은 그대로 두고 **알림만** 보냅니다.
         못 받았으면 null 을 보내 「추정 금지」가 지켜지게 합니다. */
      var 알리기 = function (d, ev) {
        if (typeof opt.받으면 === 'function') {
          try { opt.받으면(d, ev, day); } catch (e) {}
        }
      };
      var 물때알리기 = function (전체) {
        if (알린적있나) { return; }      // 날짜를 바꿀 때마다 또 보내지 않습니다
        알린적있나 = true;
        if (typeof opt.물때받으면 === 'function') {
          try { opt.물때받으면(전체); } catch (e) {}
        }
      };
      var go = function (d, ev) {
        if (!d || !d.ok) {
          box.querySelector('.tg-foot').textContent = '물높이 예보를 불러오지 못했어요.';
          지우기(box); 알리기(null, null); return;
        }
        draw(box, d, { dark: opt.dark, sun: sun, today: day === 0, events: ev,
                       mode: opt.mode });
        알리기(d, ev);
      };
      if (cache[day]) return go(cache[day].d, cache[day].ev);
      if (!tidePromise) tidePromise = fetch(API + 'tide-cache.php?region=' + region).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; });
      Promise.all([
        fetch(API + 'marine.php?kind=series&region=' + region + '&day=' + day).then(function (r) { if (!r.ok) throw 0; return r.json(); }),
        tidePromise
      ]).then(function (a) {
        var ev = a[1] && a[1].days && a[1].days[day] ? a[1].days[day].events : null;
        /* ★ 물때표 **전체**(14일치)도 한 번 알립니다 — 오늘 것이
             다 지난 밤에는 **내일 첫 물때**를 가리켜야 하는데,
             그 자료가 여기 이미 들어 있습니다. */
        물때알리기(a[1]);
        cache[day] = { d: a[0], ev: ev }; go(a[0], ev);
      }).catch(function () { 물때알리기(null); go(null); });
    }
    load(0);
    return { load: load };
  }
  window.BADAGAJA_TIDEGRAPH = { mount: mount };
})();
