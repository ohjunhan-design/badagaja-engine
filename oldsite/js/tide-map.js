/* 전국 물때표 쪽(tide/)의 실제 지도 — 전국을 한 장에 보고, 확대하면 자세히 (2026-09-23 주인 지시)
   · 물때를 볼 수 있는 57권역을 핀으로 찍습니다.
   · 멀리서 보면 점(13 이상), 확대하면 권역 이름(12), 더 확대하면 이름 + 오늘 간조 시각(11 이하).
   · 핀을 누르면 아래 '오늘 물때' 칸이 그 권역으로 바뀝니다(권역 단추를 대신 눌러 줍니다).
   · 지도를 못 불러오면 그림 지도(.tm-fallback)가 그대로 남습니다. */
(function () {
  var box = document.getElementById('tideMap');
  var key = (window.BADAGAJA_MAP || {}).kakaoJsKey;
  if (!box || !key) return;

  /* ── 권역 목록 모으기 (전남 15 · 그 밖 35 · 제주 7) ── */
  var T = window.BADAGAJA_TIDE || {};
  var COORD = T.coords || {};
  var list = [];
  function add(slug, name, lat, lng) {
    if (!slug || !name) return;
    var c = COORD[slug];
    lat = lat || (c && c[0]); lng = lng || (c && c[1]);
    if (!lat || !lng) return;
    for (var i = 0; i < list.length; i++) if (list[i].slug === slug) return;
    list.push({ slug: slug, name: name, lat: lat, lng: lng });
  }
  var H = window.BADAGAJA_HOME;
  if (H && H.regions) H.regions.forEach(function (r) { add(r.slug, r.name, r.lat, r.lng); });
  var C = window.BADAGAJA_COAST || {};
  Object.keys(C).forEach(function (s) { add(s, C[s].name, C[s].lat, C[s].lng); });
  var J = window.BADAGAJA_JEJU;
  if (J && J.regions) J.regions.forEach(function (r) { add(r.slug, r.short || r.name, r.lat, r.lng); });
  // 이 쪽에는 제주 자료 파일이 실리지 않아, 권역 이름을 여기에 둡니다(js/home.js 의 JEJU 와 같은 목록)
  [['jejusi', '제주시내'], ['aewol', '애월·한림'], ['jocheon', '조천·구좌'], ['seongsan', '성산·표선'],
   ['seogwipo', '서귀포·중문'], ['daejeong', '대정·안덕'], ['chuja', '추자도']].forEach(function (x) { add(x[0], x[1]); });
  if (!list.length) return;

  /* ── 권역 고르기 — 아래 '오늘 물때' 칸의 단추를 대신 눌러 줍니다 ── */
  function pick(slug) {
    var rbox = document.getElementById('tsRegions');
    var gbox = document.getElementById('tsGroups');
    if (!rbox) return;
    var b = rbox.querySelector('[data-r="' + slug + '"]');
    if (!b && gbox) {                       // 다른 지역이면 지역 단추를 먼저 누릅니다
      var g = (window.BADAGAJA_COAST[slug] || {}).group ||
              (window.BADAGAJA_JEJU && (window.BADAGAJA_JEJU.regions || []).some(function (x) { return x.slug === slug; }) ? '제주' : '전남');
      var gb = gbox.querySelectorAll('button');
      for (var i = 0; i < gb.length; i++) {
        if (gb[i].textContent.replace(/\s/g, '') === String(g).replace(/\s/g, '')) { gb[i].click(); break; }
      }
      b = rbox.querySelector('[data-r="' + slug + '"]');
    }
    if (b) b.click();
    var t = document.getElementById('today');
    if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /* ── 간조 시각 — 확대했을 때만, 보이는 핀만 불러옵니다 ── */
  var lowCache = {};
  function lowTide(slug, done) {
    if (lowCache[slug] !== undefined) { done(lowCache[slug]); return; }
    lowCache[slug] = null;
    fetch('api/tide-cache.php?region=' + slug, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        var ev = d && d.days && d.days[0] && d.days[0].events;
        var low = null;
        (ev || []).forEach(function (e) { if (!low && e.type === '간조') low = e.time; });
        lowCache[slug] = low; done(low);
      })
      .catch(function () { lowCache[slug] = null; });
  }



  /* ── 지도 ── */
  function init() {
    var map = new kakao.maps.Map(box, { center: new kakao.maps.LatLng(35.55, 127.6), level: 13 });
    var pc = window.matchMedia('(min-width:1081px) and (hover:hover) and (pointer:fine)').matches;
    // 휴대폰에서도 두 손가락으로 확대됩니다. 다만 전국이 다 보이는 첫 크기에서는 지도를 끌 수 없게 두어
    // 한 손가락으로 쓸면 쪽이 그대로 스크롤되고, 확대한 뒤에는 지도를 끌 수 있습니다 (2026-09-23 주인 지시)
    map.setZoomable(true);
    map.setDraggable(pc);
    if (!pc) {
      kakao.maps.event.addListener(map, 'zoom_changed', function () {
        map.setDraggable(map.getLevel() < 13);
      });
    }
    map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
    box.classList.remove('tm-loading');
    var fb = document.querySelector('.tm-fallback');
    if (fb) fb.hidden = true;

    var pins = {};
    list.forEach(function (r) {
      var a = document.createElement('a');
      a.className = 'tm-pin';
      a.href = '#today';
      a.setAttribute('data-slug', r.slug);
      a.innerHTML = '<i class="tm-dot"></i><b>' + r.name + '</b><em></em>';
      a.addEventListener('click', function (e) { e.preventDefault(); pick(r.slug); });
      pins[r.slug] = a;
      // 점이 실제 자리에 오도록 왼쪽 끝을 기준으로 두고, CSS 에서 점 반지름만큼 당깁니다 (2026-09-23 밀림 고침)
      new kakao.maps.CustomOverlay({ position: new kakao.maps.LatLng(r.lat, r.lng), content: a, xAnchor: 0, yAnchor: .5, zIndex: 3 }).setMap(map);
    });

    function refresh() {
      var lv = map.getLevel();
      // 13 이상 권역 점만 · 12 권역 이름 · 11 이하 이름 + 오늘 간조 시각 (2026-09-23 주인 지정)
      var mode = lv >= 13 ? 'far' : (lv >= 12 ? 'mid' : 'near');
      box.setAttribute('data-zoom', mode);
      if (mode !== 'near') return;
      var b = map.getBounds();
      list.forEach(function (r) {
        if (!b.contain(new kakao.maps.LatLng(r.lat, r.lng))) return;
        lowTide(r.slug, function (t) {
          var el = pins[r.slug] && pins[r.slug].querySelector('em');
          if (el && t) el.textContent = '간조 ' + t;
        });
      });
    }
    // 처음에는 전국이 다 들어오게 맞춥니다 (제주·울릉까지)
    var bb = new kakao.maps.LatLngBounds();
    // 울릉도는 멀리 떨어져 있어 첫 화면 계산에서 뺍니다(핀은 그대로 있습니다)
    list.forEach(function (r) { if (r.slug !== 'ulleung') bb.extend(new kakao.maps.LatLng(r.lat, r.lng)); });
    function fit() { map.relayout(); map.setBounds(bb, 14, 14, 14, 14); }
    fit(); setTimeout(fit, 400);
    window.addEventListener('resize', function () { clearTimeout(fit.t); fit.t = setTimeout(fit, 250); });
    kakao.maps.event.addListener(map, 'idle', refresh);
    refresh();

    // 아래 칸에서 권역이 바뀌면 그 핀을 도드라지게
    function mark() {
      var on = document.querySelector('#tsRegions [aria-selected="true"]');
      var s = on && on.getAttribute('data-r');
      Object.keys(pins).forEach(function (k) { pins[k].classList.toggle('on', k === s); });
    }
    var rbox = document.getElementById('tsRegions');
    if (rbox) { rbox.addEventListener('click', function () { setTimeout(mark, 60); }); setTimeout(mark, 900); }
  }

  var started = false;
  function start() {
    if (started) return; started = true;
    var s = document.createElement('script');
    s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=' + encodeURIComponent(key);
    s.onload = function () { try { kakao.maps.load(init); } catch (e) { box.classList.add('tm-off'); } };
    s.onerror = function () { box.classList.add('tm-off'); };
    document.head.appendChild(s);
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); start(); } }, { rootMargin: '300px' });
    io.observe(box);
  } else start();
})();
