/* 지역 페이지 추가 정보 (공공데이터)
 * ① 근처 숙소: 한국관광공사 숙박 + 포인트 좌표로 가까운 순 (api/tour.php)
 * ② 티맵 목적지 인기 순위: 한국관광공사 관광빅데이터(TMAP 제공) (api/places.php)
 * ③ 축제 실제 일정: 한국관광공사 행사정보 (api/tour.php?kind=festival)
 */
(function () {
  var REGION = document.body.getAttribute('data-region');
  if (!REGION) return;
  var GEO = (window.BADAGAJA_POINTS_GEO || {})[REGION] || [];
  // 제주 권역: 해루질·낚시 포인트 대신 페이지에 적은 바닷가 명소 좌표를 기준점으로 씀 ([이름,'a',위도,경도])
  var JEJU = ['jejusi', 'aewol', 'jocheon', 'seongsan', 'seogwipo', 'daejeong', 'chuja'];
  var IS_JEJU = JEJU.indexOf(REGION) > -1;
  // 전국 확대 권역(충남 등) — js/coast-data.js (2026-09-18)
  var COASTS = window.BADAGAJA_COAST || {};
  var IS_COAST = !!COASTS[REGION];
  if (!GEO.length && window.BADAGAJA_ANCHORS) GEO = window.BADAGAJA_ANCHORS;
  var NAME = { sinan: '신안', muan: '무안', mokpo: '목포', yeonggwang: '영광', hampyeong: '함평', jindo: '진도', haenam: '해남', wando: '완도', gangjin: '강진', jangheung: '장흥', boseong: '보성', goheung: '고흥', yeosu: '여수', suncheon: '순천', gwangyang: '광양',
    jejusi: '제주시', aewol: '애월', jocheon: '조천', seongsan: '성산', seogwipo: '서귀포', daejeong: '대정', chuja: '추자도' }[REGION] || (IS_COAST ? COASTS[REGION].name : '');

  // 주소 앞 시·도 떼기 — 전남·제주만 떼고 '충청남도 태안군…'은 그대로 나오던 것 (2026-09-24)
  var PROV_RE = /^[가-힣]+(?:특별자치도|특별자치시|통합특별시|광역시|특별시|도)\s+/;
  function noProv(s) { return (s || '').replace(PROV_RE, ''); }
  var PROVINCE = IS_JEJU ? '제주특별자치도' : IS_COAST ? (COASTS[REGION].province || '') : '전라남도';
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function km(a, b, c, d) { var r = Math.PI / 180, x = Math.sin((c - a) * r / 2), y = Math.sin((d - b) * r / 2); var h = x * x + Math.cos(a * r) * Math.cos(c * r) * y * y; return 12742 * Math.asin(Math.sqrt(h)); }
  function distText(k) { return k < 1 ? Math.round(k * 100) * 10 + 'm' : (Math.round(k * 10) / 10) + 'km'; }
  function kakaoSearch(q) { return 'https://map.kakao.com/link/search/' + encodeURIComponent(q); }

  /* ---------- 설명 팝업 (관광지·축제 카드 공통) ----------
   * 카드를 누르면 전체 설명을 작은 창으로 보여주고, 지도·전화는 창 안의 버튼으로 연다 */
  var INFO = {};   // 설명 캐시: 콘텐츠 id → 개요
  function getInfo(id) {
    if (INFO[id] != null) return Promise.resolve(INFO[id]);
    return fetch('api/tour.php?kind=spotinfo&ids=' + id).then(function (r) { return r.json(); })
      .then(function (d) { INFO[id] = (d && d.items && d.items[id]) || ''; return INFO[id]; });
  }
  var pop, popLast;
  function closeInfo() {
    if (!pop) return;
    pop.hidden = true; document.body.classList.remove('ip-open');
    if (popLast && popLast.focus) popLast.focus();
  }
  function openInfo(o) {
    popLast = document.activeElement;
    if (!pop) {
      pop = el('div', 'ip-overlay'); pop.hidden = true;
      pop.addEventListener('click', function (e) { if (e.target === pop) closeInfo(); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && pop && !pop.hidden) closeInfo(); });
      document.body.appendChild(pop);
    }
    pop.innerHTML = '';
    var box = el('div', 'ip-box'); box.setAttribute('role', 'dialog'); box.setAttribute('aria-modal', 'true'); box.setAttribute('aria-label', o.title);
    var x = el('button', 'ip-close', '×'); x.type = 'button'; x.setAttribute('aria-label', '닫기'); x.addEventListener('click', closeInfo);
    box.appendChild(x);
    if (o.img) {
      var ph = el('div', 'ip-photo'); var im = el('img'); im.src = o.img; im.alt = o.title;
      im.addEventListener('error', function () { ph.parentNode && ph.parentNode.removeChild(ph); });   // 사진이 없어졌으면 칸을 비운다
      ph.appendChild(im); box.appendChild(ph);
    }
    var body = el('div', 'ip-body');
    if (o.kicker) body.appendChild(el('div', 'ip-kicker', o.kicker));
    body.appendChild(el('h3', 'ip-title serif', o.title));
    (o.lines || []).forEach(function (t) { if (t) body.appendChild(el('div', 'ip-line', t)); });
    var desc = el('p', 'ip-desc', o.text != null ? (o.text || '등록된 설명이 없습니다.') : '설명을 불러오는 중입니다…');
    body.appendChild(desc);
    var act = el('div', 'ip-actions');
    (o.actions || []).forEach(function (a) { var b = el('a', 'ip-btn' + (a.main ? ' main' : ''), a.label); b.href = a.href; if (!/^tel:/.test(a.href)) { b.target = '_blank'; b.rel = 'noopener'; } act.appendChild(b); });
    body.appendChild(act);
    if (o.source) body.appendChild(el('p', 'ip-src', o.source));
    box.appendChild(body); pop.appendChild(box);
    pop.hidden = false; document.body.classList.add('ip-open');
    x.focus();
    if (o.text == null && o.id) getInfo(o.id).then(function (t) { if (desc.isConnected) desc.textContent = t || '등록된 설명이 없습니다.'; }).catch(function () { desc.textContent = '설명을 불러오지 못했습니다.'; });
  }
  function asButton(node, fn) {
    node.setAttribute('role', 'button'); node.tabIndex = 0;
    node.addEventListener('click', fn);
    node.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } });
  }
  function naverSearch(q) { return 'https://map.naver.com/p/search/' + encodeURIComponent(q); }

  /* ---------- ① 근처 숙소 ---------- */
  /* 숙소 칸 광고(트립닷컴) — 첫 숙소 묶음 맨 끝에 숙소 카드 모양으로. 광고가 꺼져 있으면 광고 스크립트조차 안 받음.
     카드가 한 줄(4칸)을 꽉 채우면 마지막 숙소 하나를 빼고 그 자리에 둡니다 (2026-09-22 주인) · 설정은 data/ads.json 'region-stay' */
  function adsLoad(cb) {
    if (window.BadagajaAds) return cb();
    var v = ((document.querySelector('script[src*="region-extra.js"]') || {}).src || '').split('?v=')[1] || '';
    function js(src, ok) { var s = document.createElement('script'); s.src = src + (v ? '?v=' + v : ''); s.onload = ok; document.head.appendChild(s); }
    js('js/ads-data.js', function () {
      if (!window.BADAGAJA_ADS || !window.BADAGAJA_ADS.enabled) return;
      js('js/ads.js', cb);
    });
  }
  function stayAd(row) {
    if (!row) return;
    adsLoad(function () {
      if (!window.BadagajaAds.willShow('region-stay')) return;
      var cards = row.querySelectorAll('.stay-card');
      if (cards.length && cards.length % 4 === 0) {
        var real = row.querySelectorAll('.stay-card.real');
        if (real.length) real[real.length - 1].remove();
      }
      var box = el('aside', 'ad-slot'); box.setAttribute('data-ad-slot', 'region-stay'); box.hidden = true;
      row.appendChild(box);
      window.BadagajaAds.mount(box);
    });
  }

  (function stays() {
    var groups = document.querySelectorAll('#stay [data-stay]');
    if (!groups.length) return;
    var icon = document.getElementById('stayIcon');
    fetch('api/tour.php?kind=stay&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var items = (d && d.ok && d.items) || [];
      var used = {};
      [].forEach.call(groups, function (g) {
        var kind = g.getAttribute('data-stay'), row = g.querySelector('.stay-row'), loading = row.querySelector('.stay-loading');
        var pts = GEO.filter(function (p) { return p[1] === kind; });
        var cand = items.map(function (s) {
          var best = null, bk = 1e9;
          pts.forEach(function (p) { var k = km(s.lat, s.lng, p[2], p[3]); if (k < bk) { bk = k; best = p; } });
          return { s: s, p: best, k: bk };
        }).filter(function (x) { return x.p && x.k <= 20; }).sort(function (a, b) { return a.k - b.k; });
        var fresh = cand.filter(function (x) { return !used[x.s.id]; });
        var max = kind === 'a' ? 6 : 3;   // 제주는 숙소 묶음이 하나라 6곳까지
        var list = (fresh.length ? fresh : cand).slice(0, max);   // 숙소가 적은 권역은 다른 그룹과 겹쳐도 보여줌
        if (loading) loading.remove();
        var ad = row.querySelector('.ad-slot');
        list.forEach(function (x) {
          used[x.s.id] = 1;
          var card = el('div', 'stay-card real'), th = el('div', 'thumb');
          if (x.s.img) {
            var im = el('img'); im.src = x.s.img; im.alt = x.s.name; im.loading = 'lazy';
            // 관광공사 쪽 사진 주소는 같은 사진이라도 _image2_1 / _image3_1 두 가지가 있고
            // 한쪽만 없어진 경우가 있습니다. 한 번은 다른 쪽으로 바꿔 보고, 그래도 안 되면 기본 그림으로 (2026-09-20)
            im.addEventListener('error', function () {
              var s = im.getAttribute('src') || '', alt2 = '';
              if (s.indexOf('_image3_1') > -1) alt2 = s.replace('_image3_1', '_image2_1');
              else if (s.indexOf('_image2_1') > -1) alt2 = s.replace('_image2_1', '_image3_1');
              if (alt2 && !im.dataset.retried) { im.dataset.retried = '1'; im.src = alt2; return; }
              if (im.parentNode) im.parentNode.removeChild(im);
              if (icon) th.insertBefore(icon.content.cloneNode(true), th.firstChild);
            });
            th.appendChild(im);
          }
          else if (icon) th.appendChild(icon.content.cloneNode(true));
          th.appendChild(el('span', 'distance', x.p[0] + '에서 ' + distText(x.k)));
          card.appendChild(th);
          var b = el('div', 'body');
          b.appendChild(el('h3', null, x.s.name));
          b.appendChild(el('div', 'meta', x.s.type + ' · ' + noProv(x.s.addr)));
          var links = el('div', 'stay-links');
          if (x.s.tel) { var t = el('a', null, '📞 전화'); t.href = 'tel:' + x.s.tel.split(/[,\s]/)[0]; links.appendChild(t); }
          var m = el('a', null, '📍 카카오맵'); m.href = kakaoSearch(x.s.name); m.target = '_blank'; m.rel = 'noopener'; links.appendChild(m);
          if (window.BadaNaviButton) { var nv = window.BadaNaviButton(x.s.name, x.s.lat, x.s.lng, '🚗 길안내'); if (nv) links.appendChild(nv); }
          b.appendChild(links); card.appendChild(b);
          row.insertBefore(card, ad);
        });
        if (list.length < max) {
          var more = el('a', 'stay-card stay-more');
          var q = NAME + ' ' + (kind === 'g' ? '펜션' : kind === 'a' ? '숙소' : '낚시 민박');
          more.href = kakaoSearch(q); more.target = '_blank'; more.rel = 'noopener';
          var mb = el('div', 'body');
          mb.appendChild(el('h3', null, list.length ? '근처 숙소 더 찾기' : '등록된 숙소가 적은 권역이에요'));
          mb.appendChild(el('div', 'meta', '카카오맵에서 "' + q + '" 검색 결과 보기 →'));
          more.appendChild(mb); row.insertBefore(more, ad);
        }
      });
      stayAd(groups[0].querySelector('.stay-row'));
    }).catch(function () {
      [].forEach.call(document.querySelectorAll('#stay .stay-loading'), function (p) { p.textContent = '숙소 정보를 불러오지 못했어요. 잠시 후 다시 확인해 주세요.'; });
    });
  })();

  /* ---------- ② 티맵 목적지 인기 순위 ---------- */
  var SELF = (document.currentScript && document.currentScript.src) || '';
  (function tmap() {
    var box = document.getElementById('tmapRank');
    if (!box) return;
    // 카카오 장소 검색(주소·전화·상세 링크) 도우미 — 순위가 그려진 뒤 불러온다
    var center = GEO.length ? [GEO.reduce(function (s, p) { return s + p[2]; }, 0) / GEO.length, GEO.reduce(function (s, p) { return s + p[3]; }, 0) / GEO.length] : null;
    function enrich(list) {
      function go() { if (window.BadaKakaoEnrich) { if (!list._badaRun) window.BadaKakaoEnrich(list, { prefix: '', center: IS_JEJU ? center : null, region: REGION, strict: true, onDone: function (n) { if (!n) box.hidden = true; } }); else if (list._badaSeen) list._badaRun(); } }
      if (window.BadaKakaoEnrich) return go();
      var s = document.createElement('script'); s.src = SELF.replace(/region-extra\.js/, 'kakao-places.js') || 'js/kakao-places.js'; s.onload = go; document.head.appendChild(s);
    }
    // 제주는 시군구가 둘뿐이라 권역 명소를 기준으로 모은 places-jeju.php 를 쓴다
    fetch((IS_JEJU ? 'api/places-jeju.php' : 'api/places.php') + '?region=' + REGION + '&type=food&limit=40').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      // 서버가 모르는 권역(제주 등)은 보성 자료를 돌려주므로, 권역이 다르면 표시하지 않는다
      if (!d || !d.ok || !d.items || !d.items.length || d.region !== REGION) return;
      var cafe = d.items.filter(function (x) { return /카페|찻집/.test(x.group || x.category); });
      var food = d.items.filter(function (x) { return !/카페|찻집/.test(x.group || x.category); });
      box.innerHTML = '';
      var head = el('div', 'tr-head');
      var h = el('h3', 'serif', '🚗 요즘 많이 찾아가는 곳'); head.appendChild(h);
      head.appendChild(el('p', null, d.mode === 'related'
        ? '이 권역 명소(' + (d.basis || []).slice(0, 3).join('·') + ' 등)를 티맵으로 찾아간 사람들이 함께 많이 찾은 곳입니다 (' + (d.baseLabel || '') + ' 기준). 맛 평가가 아닌 방문 동선 순위예요.'
        : '티맵 내비게이션 목적지 검색을 바탕으로 한 인기 순위입니다 (' + (d.baseLabel || '') + ' 기준). 맛 평가가 아닌 방문 수요 순위예요.'));
      box.appendChild(head);
      var tabs = el('div', 'tr-tabs'), list = el('ol', 'tr-list');
      function render(arr) {
        list.innerHTML = '';
        // 후보 20곳을 그려 두고, 카카오 주소 검사(권역 밖 제외) 뒤 앞에서 10곳만 보인다
        arr.slice(0, 20).forEach(function (x, i) {
          var q = (IS_JEJU ? '제주' : NAME) + ' ' + x.name + (x.branch ? ' ' + x.branch : '');
          var li = el('li'), a = el('a'); a.href = kakaoSearch(q); a.target = '_blank'; a.rel = 'noopener';
          li.setAttribute('data-q', q); li.setAttribute('data-name', x.name); if (i >= 10) li.hidden = true;
          a.appendChild(el('b', 'rk', String(i + 1)));
          var nm = el('span', 'nm', x.name + (x.branch ? ' ' + x.branch : '')); a.appendChild(nm);
          a.appendChild(el('span', 'ct', x.category || ''));
          if (x.area && x.area.indexOf(NAME) < 0 && !IS_JEJU) a.appendChild(el('span', 'ar', x.area));
          li.appendChild(a); list.appendChild(li);
        });
        enrich(list);
      }
      [['식당', food], ['카페', cafe]].forEach(function (t, i) {
        if (!t[1].length) return;
        var b = el('button', i === 0 ? 'on' : '', t[0] + ' TOP ' + Math.min(10, t[1].length)); b.type = 'button';
        b.addEventListener('click', function () { [].forEach.call(tabs.children, function (x) { x.classList.toggle('on', x === b); }); render(t[1]); });
        tabs.appendChild(b);
      });
      box.appendChild(tabs); box.appendChild(list);
      box.appendChild(el('p', 'tr-src', '출처: ' + (d.source || '한국관광공사 관광빅데이터(TMAP Mobility 제공)') + ' · 주소·전화: 카카오 장소 검색 · 영업 여부는 방문 전 확인하세요'));
      render(food.length ? food : cafe);
      box.hidden = false;
    }).catch(function () {});
  })();

  /* ---------- 권역 네비게이터 (헤더 아래 한 줄, 헤더와 함께 상단 고정) ---------- */
  (function regionNav() {
    var C = window.BADAGAJA_REGION_COUNTS, header = document.querySelector('body > header');
    if (!C || !header || document.querySelector('.region-nav')) return;
    var nav = el('nav', 'region-nav'); nav.setAttribute('aria-label', '권역 이동');
    var inner = el('div', 'rn-inner');
    inner.appendChild(el('span', 'rn-label', '권역 이동'));
    var list = el('div', 'rn-list'), current = null;
    // 제주 권역에서는 제주 7곳을, 전남 권역에서는 전남 15곳을 보여주고 끝에 다른 지역으로 가는 칸을 둔다
    // 첫 화면이 전국(57곳)으로 바뀌어 '전남여행'·'제주여행' 대신 '전국 바다' 한 칸만 둔다 (2026-09-20)
    var JN = { jejusi: '제주시내', aewol: '애월·한림', jocheon: '조천·구좌', seongsan: '성산·표선', seogwipo: '서귀포·중문', daejeong: '대정·안덕', chuja: '추자도' };
    function cross(text, href, tip) { var x = el('a', 'rn-cross', text); x.href = href; x.setAttribute('data-tip', tip); list.appendChild(x); }
    if (IS_COAST) {
      var grp = COASTS[REGION].group;
      inner.firstChild.textContent = grp + ' 권역';
      Object.keys(COASTS).filter(function (k) { return COASTS[k].group === grp; }).forEach(function (slug) {
        var a = el('a', slug === REGION ? 'on' : '', COASTS[slug].name); a.href = slug + '.html';
        if (slug === REGION) { a.setAttribute('aria-current', 'page'); current = a; }
        list.appendChild(a);
      });
      cross('전국 바다 →', './', '전국 57개 권역 · 서해에서 동해, 제주까지');
      tips();
    } else if (IS_JEJU) {
      inner.firstChild.textContent = '제주 권역';
      JEJU.forEach(function (slug) {
        var a = el('a', slug === REGION ? 'on' : '', JN[slug]); a.href = slug + '.html';
        if (slug === REGION) { a.setAttribute('aria-current', 'page'); current = a; }
        list.appendChild(a);
      });
      cross('전국 바다 →', './', '전국 57개 권역 · 서해에서 동해, 제주까지');
      tips();
    } else {
      Object.keys(C).sort(function (a, b) { return C[a][0] - C[b][0]; }).forEach(function (slug) {
        var v = C[slug], a = el('a', slug === REGION ? 'on' : '', v[1]);
        a.href = slug + '.html';
        a.setAttribute('data-tip', '포인트 ' + (v[2] + v[3]) + '곳 · 낚시 ' + v[2] + ' · 해루질 ' + v[3]);
        if (slug === REGION) { a.setAttribute('aria-current', 'page'); current = a; }
        list.appendChild(a);
      });
      cross('전국 바다 →', './', '전국 57개 권역 · 서해에서 동해, 제주까지');
    }
    // 전국 확대·제주 권역 말풍선(포인트 수) — 전남만 BADAGAJA_REGION_COUNTS 로 달려 있었습니다 (2026-09-24)
    function tips() {
      fetch('data/coast-points-index.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (ix) {
        [].forEach.call(list.querySelectorAll('a[href$=".html"]'), function (a) {
          var v = ix[a.getAttribute('href').replace(/\.html$/, '')]; if (!v) return;
          var f = (v.fishing && v.fishing.n) || 0, g = (v.gleaning && v.gleaning.n) || 0;
          a.setAttribute('data-tip', '포인트 ' + (f + g) + '곳 · 낚시 ' + f + ' · 해루질 ' + g);
        });
      }).catch(function () {});
    }
    inner.appendChild(list); nav.appendChild(inner);
    header.appendChild(nav);   // 헤더 안에 넣어 스크롤해도 함께 상단 고정
    if (current) {   // 현재 권역이 보이도록 가로 스크롤 위치 맞춤 (페이지 스크롤은 건드리지 않음)
      var left = current.offsetLeft - (list.clientWidth - current.offsetWidth) / 2;
      list.scrollLeft = Math.max(0, left);
    }
  })();

  /* ---------- 해안가 관광지: 한국관광공사 관광지 중 포인트와 가까운 4곳 ---------- */
  (function coastSpots() {
    var grid = document.getElementById('spotGrid');
    if (!grid || !GEO.length || IS_JEJU || IS_COAST) return;   // 제주는 직접 확인한 바닷가 명소 카드를 그대로 둔다
    fetch('api/tour.php?kind=spot&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var items = (d && d.ok && d.items) || [];
      var list = items.map(function (s) {
        var best = null, bk = 1e9;
        GEO.forEach(function (p) { var k = km(s.lat, s.lng, p[2], p[3]); if (k < bk) { bk = k; best = p; } });
        return { s: s, p: best, k: bk };
      }).filter(function (x) { return x.p && x.k <= 15; })
        .sort(function (a, b) { return (a.k - (a.s.img ? 1.5 : 0)) - (b.k - (b.s.img ? 1.5 : 0)); })   // 사진 있는 곳을 조금 우선
        .slice(0, 4);
      if (list.length < 4) return;   // 가까운 관광지가 부족하면 기존 카드 유지
      grid.innerHTML = '';
      list.forEach(function (x) {
        var c = el('div', 'spot-card real');
        var addr = noProv(x.s.addr), meta = x.s.kind + ' · ' + x.p[0] + '에서 ' + distText(x.k);
        (function (x, addr, meta) {
          asButton(c, function () {
            openInfo({ id: x.s.id, text: INFO[x.s.id], img: x.s.img, kicker: meta, title: x.s.name, lines: [addr],
              actions: [{ label: '카카오맵에서 위치 보기', href: kakaoSearch(x.s.name), main: true }, { label: '네이버 지도', href: naverSearch(x.s.name) }],
              source: '설명·사진: 한국관광공사 국문 관광정보(공공누리 제3유형) · 운영 시간·요금은 방문 전 확인하세요' });
          });
        })(x, addr, meta);
        if (x.s.img) {
          var ph = el('div', 'spot-photo'); var im = el('img'); im.src = x.s.img; im.alt = x.s.name; im.loading = 'lazy';
          im.addEventListener('error', function () {          // 관광공사 쪽 사진이 없어진 경우 (예: 404)
            ph.classList.add('noimg'); ph.innerHTML = '';
            ph.appendChild(el('span', null, x.s.name + ' 사진 준비 중'));
          });
          ph.appendChild(im); c.appendChild(ph);
        }
        c.appendChild(el('div', 'spot-kind', meta));
        c.appendChild(el('h3', null, x.s.name));
        c.appendChild(el('div', 'spot-addr', addr));
        var desc = el('p', 'spot-desc'); desc.dataset.id = x.s.id; c.appendChild(desc);
        c.appendChild(el('span', 'spot-more', '설명 자세히 보기 ›'));
        grid.appendChild(c);
      });
      var note = document.getElementById('spotNote');
      if (note) note.textContent = '관광지 정보: 한국관광공사 국문 관광정보 · ' + (IS_JEJU ? '바닷가 명소' : '포인트') + '에서 가까운 순 · 사진: 한국관광공사(공공누리 제3유형) · 카드를 누르면 전체 설명과 지도 링크를 볼 수 있습니다';
      fetch('api/tour.php?kind=spotinfo&ids=' + list.map(function (x) { return x.s.id; }).join(',')).then(function (r) { return r.json(); }).then(function (info) {
        [].forEach.call(grid.querySelectorAll('.spot-desc'), function (p) {
          var t = info && info.items ? (info.items[p.dataset.id] || '') : '';
          INFO[p.dataset.id] = t;
          if (t.length > 90) t = t.slice(0, 88).replace(/\s+\S*$/, '') + '…';
          p.textContent = t;
        });
      }).catch(function () {});
    }).catch(function () {});
  })();

  /* ---------- 직접 정리한 바닷가 명소 카드도 눌러서 크게 보기 ----------
   * 전남은 위 coastSpots() 가 관광공사 자료로 카드를 바꾸면서 팝업을 달아 줍니다.
   * 제주·전국 확대 권역은 직접 확인한 카드를 그대로 두느라 팝업이 없었습니다(2026-09-19).
   * 전남도 관광공사 자료를 못 받으면 적어 둔 카드가 그대로 남으므로, 그때도 팝업이 열리게 다 같이 달아 둡니다.
   * (coastSpots() 가 성공하면 카드를 통째로 바꾸며 자기 팝업을 답니다 — 겹치지 않습니다)
   * 카드 안에 사진 출처 링크가 있는 제주 쪽은 그 링크 클릭은 그대로 살려 둡니다. */
  (function curatedSpots() {
    var grid = document.getElementById('spotGrid');
    if (!grid) return;
    [].forEach.call(grid.querySelectorAll('.spot-card'), function (c) {
      if (c.getAttribute('role') === 'button') return;
      var pick = function (sel) { var e = c.querySelector(sel); return e ? e.textContent.trim() : ''; };
      var title = pick('h3'); if (!title) return;
      var im = c.querySelector('.spot-photo img'), cap = c.querySelector('.spot-photo figcaption');
      var kind = pick('.spot-kind'), addr = pick('.spot-addr'), desc = pick('.spot-desc');
      if (!c.querySelector('.spot-more')) c.appendChild(el('span', 'spot-more', '크게 보기 ›'));
      var open = function () {
        openInfo({
          text: desc, img: im ? (im.currentSrc || im.src) : '', kicker: kind, title: title, lines: [addr],
          actions: [{ label: '카카오맵에서 위치 보기', href: kakaoSearch(title), main: true },
                    { label: '네이버 지도', href: naverSearch(title) }],
          source: cap ? cap.textContent.trim() : ''
        });
      };
      c.setAttribute('role', 'button'); c.tabIndex = 0;
      c.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('a')) return; open(); });
      c.addEventListener('keydown', function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
    });
  })();

  /* ---------- 포인트 배너 버튼 문구 ---------- */
  [].forEach.call(document.querySelectorAll('a.sinan-banner .btn-more'), function (m) { m.textContent = '🗺️ 지도에서 포인트 보기 →'; });

  /* ---------- 시간별 물높이 그래프 (물때표 아래) ---------- */
  (function tideGraph() {
    var strip = document.getElementById('tideStrip');
    if (!strip || !window.BADAGAJA_TIDEGRAPH) return;
    var box = document.createElement('div');
    strip.parentNode.insertBefore(box, strip.nextSibling);
    var T = window.BADAGAJA_TIDE;
    window.BADAGAJA_TIDEGRAPH.mount(box, REGION, { coords: T && T.coords ? T.coords[REGION] : null });
  })();



  /* ---------- 제철 어종 카드에 금어기·금지체장 표시 (data/fishery-rules.json) ---------- */
  (function catchRule() {
    var cards = document.querySelectorAll('#catch .catch-card');
    if (!cards.length) return;
    var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
    var M = kst.getMonth() + 1, D = kst.getDate();
    function norm(s) { return (s || '').replace(/\(.*?\)/g, '').replace(/[\s·]/g, ''); }
    // 이 권역의 도 — 낙지·참문어처럼 시·도가 금어기를 따로 정한 어종은 그 도 기간(banBy)으로 판단 (2026-09-22)
    var CO = window.BADAGAJA_COAST || {};
    var GRP = CO[REGION] ? CO[REGION].group : (IS_JEJU ? '제주' : '전남');
    function banOf(s) { return (s.banBy && s.banBy[GRP]) || s.ban; }
    function mmdd(b) { return b[0] + '월 ' + b[1] + '일 ~ ' + b[2] + '월 ' + b[3] + '일'; }
    function banTextOf(s) { return (s.banBy && s.banBy[GRP]) ? s.banBy[GRP].map(mmdd).join(', ') + ' (' + GRP + ')' : s.banText; }
    function inBan(s) {
      if (!s.ban || s.byNotice) return false;
      return banOf(s).some(function (b) {
        var a = b[0] * 100 + b[1], z = b[2] * 100 + b[3], t = M * 100 + D;
        return a <= z ? (t >= a && t <= z) : (t >= a || t <= z);
      });
    }
    fetch('data/fishery-rules.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var by = {};
      d.species.forEach(function (s) {
        by[norm(s.n)] = s;
        if (s.alias) s.alias.split(/[,·]/).forEach(function (a) { by[norm(a)] = s; });
      });
      [].forEach.call(cards, function (card) {
        var h = card.querySelector('h3'); if (!h) return;
        var key = norm(h.textContent), rule = by[key];
        if (!rule) {                                  // 이름이 조금 다른 경우 앞부분으로 한 번 더
          for (var k in by) { if (k.length >= 2 && (key.indexOf(k) === 0 || k.indexOf(key) === 0)) { rule = by[k]; break; } }
        }
        if (!rule) return;
        var box = el('a', 'cc-rule'); box.href = 'rule.html#find';
        if (inBan(rule)) {
          box.classList.add('now');
          box.appendChild(el('b', null, '지금 금어기'));
          box.appendChild(el('span', null, banTextOf(rule)));
        } else if (rule.byNotice) {
          box.appendChild(el('b', null, '금어기 있음'));
          box.appendChild(el('span', null, rule.banText));
        } else if (rule.banText) {
          box.appendChild(el('b', null, '금어기'));
          box.appendChild(el('span', null, banTextOf(rule)));
        }
        if (rule.size) box.appendChild(el('span', 'cc-size', '잡을 수 없는 크기 ' + rule.size));
        if (box.children.length) card.insertBefore(box, card.querySelector('.cc-more'));  // 안내 링크는 항상 맨 아래
      });
    }).catch(function () { });

    /* 같은 카드에 "잡는 법" 안내 페이지 링크 붙이기 (data/species-index.json) */
    fetch('data/species-index.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var by = {};
      (d.species || []).forEach(function (s) {
        by[norm(s.n)] = s;
        (s.alias || []).forEach(function (a) { if (a) by[norm(a)] = s; });
      });
      [].forEach.call(cards, function (card) {
        var h = card.querySelector('h3'); if (!h || card.querySelector('.cc-more')) return;
        var key = norm(h.textContent), sp = by[key];
        if (!sp) { for (var k in by) { if (k.length >= 2 && (key.indexOf(k) === 0 || k.indexOf(key) === 0)) { sp = by[k]; break; } } }
        if (!sp) return;
        var a = el('a', 'cc-more', sp.n + ' ' + (sp.sec === 'catch' ? '잡는 법' : '낚는 법') + ' 보기 →');
        a.href = sp.sec + '/' + sp.slug + '.html';
        card.appendChild(a);
      });
    }).catch(function () { });
  })();

  /* ---------- 간조 알림 캘린더(.ics) — 물때표 아래 버튼. 휴대폰 캘린더에 2주치 간조와 미리 알림을 넣어줌 ---------- */
  (function tideIcs() {
    var note = document.querySelector('#tide .tide-note');
    if (!note || !NAME) return;
    var box = el('div', 'ics-box');
    var btn = el('button', 'ics-btn', '📅 간조 알림 캘린더 내려받기');
    btn.type = 'button';
    var msg = el('span', 'ics-msg', '휴대폰·PC 캘린더에 앞으로 2주치 간조 시각이 들어가고, 1시간 전과 20분 전에 알림이 옵니다.');
    box.appendChild(btn); box.appendChild(msg);
    note.parentNode.insertBefore(box, note.nextSibling);

    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function utcStamp(y, mo, d, hh, mm) {           // 한국 시간 → UTC (KST는 -9시간)
      var t = Date.UTC(y, mo - 1, d, hh - 9, mm, 0);
      var x = new Date(t);
      return x.getUTCFullYear() + pad(x.getUTCMonth() + 1) + pad(x.getUTCDate()) + 'T' + pad(x.getUTCHours()) + pad(x.getUTCMinutes()) + '00Z';
    }
    function esc(s) { return String(s).replace(/([,;\\])/g, '\\$1').replace(/\n/g, '\\n'); }
    btn.addEventListener('click', function () {
      btn.disabled = true; msg.textContent = '물때를 불러오는 중입니다…';
      fetch('api/tide-cache.php?region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
        var days = (d && d.days) || [];
        if (!days.length) throw 0;
        var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
        var year = kst.getFullYear(), prevMonth = 0, n = 0;
        var L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//badagaja.com//tide//KO', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
                 'X-WR-CALNAME:' + NAME + ' 간조 알림 (바다가자닷컴)', 'X-WR-TIMEZONE:Asia/Seoul'];
        days.forEach(function (day) {
          var md = (day.date || '').split('/'), mo = parseInt(md[0], 10), dd = parseInt(md[1], 10);
          if (!mo || !dd) return;
          if (prevMonth && mo < prevMonth) year++;      // 12월 → 1월
          prevMonth = mo;
          (day.events || []).forEach(function (ev) {
            if (ev.type !== '간조') return;
            var hm = (ev.time || '').split(':'), hh = parseInt(hm[0], 10), mm = parseInt(hm[1], 10);
            if (isNaN(hh) || isNaN(mm)) return;
            n++;
            var start = utcStamp(year, mo, dd, hh, mm), end = utcStamp(year, mo, dd, hh, mm + 40);
            // 물때 번호는 화면과 같은 계산(음력 기준)으로 — 조석 자료의 muldae 는 셈법이 달라 쓰지 않습니다
            var T = window.BADAGAJA_TIDE;
            var mul = T && T.calcMuldae ? T.calcMuldae(new Date(year, mo - 1, dd)) + '물' : '';
            L.push('BEGIN:VEVENT',
              'UID:badagaja-' + REGION + '-' + start + '@badagaja.com',
              'DTSTAMP:' + start,
              'DTSTART:' + start,
              'DTEND:' + end,
              'SUMMARY:' + esc('간조 · ' + NAME + (mul ? ' (' + mul + ')' : '')),
              'DESCRIPTION:' + esc('간조 ' + ev.time + (ev.level != null ? ' · 조위 ' + ev.level + 'cm' : '') + (mul ? ' · ' + mul : '') +
                '\n물이 들어오기 시작하는 시각을 꼭 확인하고, 정해진 시간 전에 나오세요.\n물때·포인트: https://badagaja.com/' + REGION + '.html#tide'),
              'LOCATION:' + esc(NAME),
              'BEGIN:VALARM', 'TRIGGER:-PT60M', 'ACTION:DISPLAY', 'DESCRIPTION:' + esc('1시간 뒤 ' + NAME + ' 간조입니다'), 'END:VALARM',
              'BEGIN:VALARM', 'TRIGGER:-PT20M', 'ACTION:DISPLAY', 'DESCRIPTION:' + esc('20분 뒤 ' + NAME + ' 간조입니다'), 'END:VALARM',
              'END:VEVENT');
          });
        });
        L.push('END:VCALENDAR');
        var blob = new Blob([L.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
        var a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = 'badagaja-' + REGION + '-tide.ics';
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 2000);
        msg.textContent = '간조 ' + n + '건을 내려받았습니다. 캘린더 앱에서 파일을 열면 일정이 추가됩니다.';
        btn.disabled = false;
      }).catch(function () { msg.textContent = '물때를 불러오지 못했습니다. 잠시 후 다시 눌러 주세요.'; btn.disabled = false; });
    });
  })();

  /* ---------- 축제 월별 카드: 테마 색 + 벡터 그림 ---------- */
  (function festTheme() {
    var cells = document.querySelectorAll('#festival .fest-month');
    if (!cells.length) return;
    var ICON = {
      flower: '<circle cx="12" cy="6.5" r="3"/><circle cx="17.5" cy="10.5" r="3"/><circle cx="15.5" cy="17" r="3"/><circle cx="8.5" cy="17" r="3"/><circle cx="6.5" cy="10.5" r="3"/><circle cx="12" cy="12.5" r="1.8"/>',
      seafood: '<path d="M2.5 12c3-4.2 8.2-5.2 12.3-3 1.8 1 3 2 4.2 3-1.2 1-2.4 2-4.2 3-4.1 2.2-9.3 1.2-12.3-3z"/><path d="M19 12l3-3.2v6.4z"/><circle cx="7.5" cy="11.2" r=".9"/><path d="M11 9.5c.8 1.6.8 3.4 0 5"/>',
      food: '<path d="M3 11.5h18a9 9 0 0 1-18 0z"/><path d="M8 8c0-2 2-2.2 2-4.5M12.5 8c0-2 2-2.2 2-4.5"/><path d="M2 20.5h20"/>',
      light: '<path d="M12 2.5v4M12 17.5v4M2.5 12h4M17.5 12h4M5.3 5.3l2.9 2.9M15.8 15.8l2.9 2.9M5.3 18.7l2.9-2.9M15.8 8.2l2.9-2.9"/><circle cx="12" cy="12" r="1.6"/>',
      music: '<path d="M9 18V6.5l11-2.5v11.5"/><circle cx="6.5" cy="18" r="2.5"/><circle cx="17.5" cy="15.5" r="2.5"/><path d="M9 10l11-2.5"/>',
      history: '<path d="M2.5 16.5h19l-2.5 4h-14z"/><path d="M12 3v13.5"/><path d="M12 4.5l6.5 8.5H12z"/><path d="M12 7l-5 6h5"/>',
      sea: '<path d="M2 14.5c2.5-2 5-2 7.5 0s5 2 7.5 0 5-2 5-2"/><path d="M2 19.5c2.5-2 5-2 7.5 0s5 2 7.5 0 5-2 5-2"/><circle cx="16.5" cy="6.5" r="3.2"/>',
      eco: '<path d="M4.5 19.5c0-9 6-14.5 15-14.5 0 9-5.5 15-14.5 15"/><path d="M4.5 19.5l9.5-9.5"/><path d="M9 15h4M11.5 12.5v-3"/>',
      spring: '<path d="M12 21v-8"/><path d="M12 13c-4 0-6-3-6-6 3 0 6 2 6 6zM12 13c4 0 6-3 6-6-3 0-6 2-6 6z"/>',
      summer: '<circle cx="12" cy="9" r="3.5"/><path d="M2 17c2.5-2 5-2 7.5 0s5 2 7.5 0 5-2 5-2"/>',
      autumn: '<path d="M12 21V11"/><path d="M12 3l2.5 4 4-1-1.5 4 3 2.5-4.5 1L12 17l-3.5-3.5-4.5-1 3-2.5-1.5-4 4 1z"/>',
      winter: '<path d="M12 2.5v19M3.8 7.2l16.4 9.6M3.8 16.8l16.4-9.6"/><path d="M9.5 4.5L12 7l2.5-2.5M9.5 19.5L12 17l2.5 2.5"/>'
    };
    var RULES = [
      ['history', /대첩|거북선|이순신|장보고|역사|의병|유배|다산|청해진/, '역사'],
      ['light', /불꽃|드론|야경|해맞이|일출|노을|빛|라이트|해넘이|별|달빛/, '빛·야경'],
      ['music', /피아노|음악|공연|예술|영화|재즈|콘서트|판소리|국악|문화/, '공연'],
      ['flower', /꽃|튤립|수국|동백|매화|벚|진달래|상사화|꽃무릇|유채|국화|연꽃|철쭉|나비/, '꽃'],
      ['eco', /갯벌|생태|정원|습지|함초|갈대|숲|녹차밭|철새|순천만/, '생태'],
      ['seafood', /홍어|병어|전어|낙지|굴|전복|꼬막|갯장어|하모|수산|해산물|새조개|키조개|장어|주꾸미|꽃게|조기|굴비|김|미역|매생이|재첩|벚굴|멸치|삼치|민어|숭어|대하|문어|젓갈|해조/, '해산물'],
      ['food', /유자|녹차|국밥|먹거리|음식|맛|떡|한우|딸기|무화과|고구마|쌀|술|막걸리|차\b|토마토|양파|마늘|배추/, '먹거리'],
      ['sea', /해수욕|바다|섬|요트|카누|수영|파도|항구|포구|크루즈|물놀이|해변/, '바다']
    ];
    function season(m) { return (m >= 3 && m <= 5) ? 'spring' : (m >= 6 && m <= 8) ? 'summer' : (m >= 9 && m <= 11) ? 'autumn' : 'winter'; }
    function svg(name) { return '<svg class="fm-art" viewBox="0 0 24 24" aria-hidden="true">' + ICON[name] + '</svg>'; }
    [].forEach.call(cells, function (c) {
      var m = parseInt((c.querySelector('.fm-num') || {}).textContent, 10) || 0;
      if (!c.classList.contains('active')) { var s = season(m); c.classList.add('s-' + s); c.insertAdjacentHTML('beforeend', svg(s)); return; }
      var txt = ((c.querySelector('.fm-name') || {}).textContent || '') + ' ' + ((c.querySelector('.fm-desc') || {}).textContent || '');
      var hit = null;
      for (var i = 0; i < RULES.length; i++) { if (RULES[i][1].test(txt)) { hit = RULES[i]; break; } }
      if (!hit) hit = ['sea', null, '축제'];
      c.classList.add('t-' + hit[0]);
      c.insertAdjacentHTML('beforeend', svg(hit[0]));
      var num = c.querySelector('.fm-num'); if (num) num.insertAdjacentHTML('beforeend', '<span class="fm-tag">' + hit[2] + '</span>');
    });
  })();

  /* ---------- ③ 축제 실제 일정 ---------- */
  (function fest() {
    var box = document.getElementById('festReal');
    if (!box) return;
    fetch('api/tour.php?kind=festival&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var items = (d && d.ok && d.items) || [];
      var today = new Date(); today.setHours(0, 0, 0, 0);
      items = items.filter(function (x) { return new Date(x.end + 'T00:00:00') >= today; });
      if (!items.length) return;
      box.appendChild(el('h3', 'serif', '📅 다가오는 축제 · 실제 일정'));
      var row = el('div', 'fr-row');
      items.slice(0, 6).forEach(function (x) {
        var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00');
        var card = el('div', 'fr-card');
        var dateText = (s.getMonth() + 1) + '.' + s.getDate() + ' ~ ' + (e.getMonth() + 1) + '.' + e.getDate();
        var addr = x.addr ? noProv(x.addr) : '';
        (function (x, s, e, addr) {
          asButton(card, function () {
            var dd2 = Math.round((s - today) / 86400000);
            var acts = [{ label: '카카오맵에서 위치 보기', href: kakaoSearch(x.name), main: true }, { label: '네이버에서 검색', href: 'https://search.naver.com/search.naver?query=' + encodeURIComponent(x.name) }];
            if (x.tel) acts.push({ label: '전화 ' + x.tel.split(/[,\s]/)[0], href: 'tel:' + x.tel.split(/[,\s]/)[0].replace(/[^\d]/g, '') });
            openInfo({ id: x.id, img: x.img, kicker: dd2 <= 0 ? '진행 중인 축제' : '축제 · D-' + dd2, title: x.name,
              lines: ['📅 ' + s.getFullYear() + '. ' + (s.getMonth() + 1) + '. ' + s.getDate() + ' ~ ' + (e.getMonth() + 1) + '. ' + e.getDate(), addr ? '📍 ' + addr : ''],
              actions: acts, source: '설명·사진: 한국관광공사 행사정보(공공누리 제3유형) · 일정·프로그램은 주최 측 공지를 꼭 확인하세요' });
          });
        })(x, s, e, addr);
        if (x.img) { var im = el('img'); im.src = x.img; im.alt = x.name; im.loading = 'lazy'; card.appendChild(im); }
        var b = el('div', 'fr-body');
        var dd = Math.round((s - today) / 86400000);
        b.appendChild(el('span', 'fr-badge' + (dd <= 0 ? ' now' : ''), dd <= 0 ? '진행 중' : 'D-' + dd));
        b.appendChild(el('b', null, x.name));
        b.appendChild(el('span', 'fr-date', dateText));
        if (addr) b.appendChild(el('span', 'fr-addr', addr));
        b.appendChild(el('span', 'fr-more', '설명 보기 ›'));
        card.appendChild(b); row.appendChild(card);
      });
      box.appendChild(row);
      // 검색엔진용 축제 일정 데이터 (실제 일정이 검색 결과에 함께 보이도록)
      try {
        var ev = items.slice(0, 10).map(function (x) {
          return {
            '@type': 'Event', name: x.name,
            startDate: x.start, endDate: x.end,
            eventStatus: 'https://schema.org/EventScheduled',
            eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
            location: { '@type': 'Place', name: NAME, address: { '@type': 'PostalAddress', addressCountry: 'KR', addressRegion: ((x.addr || '').match(PROV_RE) || [PROVINCE])[0].trim(), streetAddress: noProv(x.addr) } },
            image: x.img || undefined,
            url: 'https://badagaja.com/' + REGION + '.html#festival',
            organizer: { '@type': 'Organization', name: NAME + ' 지역 행사 주최' }
          };
        });
        var s = document.createElement('script');
        s.type = 'application/ld+json';
        s.textContent = JSON.stringify({ '@context': 'https://schema.org', '@graph': ev });
        document.head.appendChild(s);
      } catch (e) { }      box.appendChild(el('p', 'fr-src', '일정: 한국관광공사 행사정보 · 사진: 한국관광공사(공공누리 제3유형) · 카드를 누르면 축제 설명을 볼 수 있습니다'));
      box.hidden = false;
    }).catch(function () {});
  })();
})();
