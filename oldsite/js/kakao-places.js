/* 카카오 장소 검색으로 순위 목록에 주소·전화·카카오맵 상세 링크 붙이기
 * - 지도용 JavaScript 키(point/map-config.js)와 카카오 지도 SDK services 라이브러리를 씀 (등록 도메인에서만 동작)
 * - 검색 결과는 저장하지 않고 화면에 보일 때만 조회
 * 사용: BadaKakaoEnrich(목록 ol, { prefix: '' | '../', center: [위도, 경도], label: {tel, detail} })
 *       목록의 li 에 data-q(검색어)·data-name(상호명) 이 있어야 함
 */
(function () {
  var ready = null;
  function script(src) {
    return new Promise(function (ok, no) { var s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = no; document.head.appendChild(s); });
  }
  function places(prefix) {
    if (ready) return ready;
    ready = (window.BADAGAJA_MAP ? Promise.resolve() : script(prefix + 'point/map-config.js')).then(function () {
      var key = (window.BADAGAJA_MAP || {}).kakaoJsKey;
      if (!key) throw 0;
      if (window.kakao && kakao.maps && kakao.maps.services) return;
      return script('https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&libraries=services&appkey=' + encodeURIComponent(key))
        .then(function () { return new Promise(function (ok) { kakao.maps.load(ok); }); });
    }).then(function () { return new kakao.maps.services.Places(); });
    return ready;
  }
  function norm(s) { return (s || '').replace(/[\s()\[\]·&.,\-]/g, '').toLowerCase(); }
  // 권역에 속하는 주소인지 (지번 주소 기준 — 읍·면·동이 늘 들어 있음)
  var AREA = {
    sinan: /신안군/, muan: /무안군/, mokpo: /목포시/, yeonggwang: /영광군/, hampyeong: /함평군/, jindo: /진도군/, haenam: /해남군/,
    wando: /완도군/, gangjin: /강진군/, jangheung: /장흥군/, boseong: /보성군/, goheung: /고흥군/, yeosu: /여수시/, suncheon: /순천시/, gwangyang: /광양시/,
    jejusi: /제주시\s+(?!애월읍|한림읍|한경면|조천읍|구좌읍|추자면|우도면)\S+동/, aewol: /애월읍|한림읍|한경면/, jocheon: /조천읍|구좌읍/,
    seongsan: /성산읍|표선면|남원읍|우도면/, seogwipo: /서귀포시\s+(?!성산읍|표선면|남원읍|대정읍|안덕면)\S+동/, daejeong: /대정읍|안덕면/, chuja: /추자면/
  };
  // 전국 확대 권역(충남 등)은 js/coast-data.js 의 시·군 이름으로 (2026-09-18)
  (function () { var C = window.BADAGAJA_COAST || {}; Object.keys(C).forEach(function (k) { if (!AREA[k] && C[k].sigungu && C[k].sigungu.length) AREA[k] = new RegExp(C[k].sigungu.join('|')); }); })();
  window.BadaInRegion = function (region, p) { var re = AREA[region]; if (!re) return true; return re.test(p.address_name || '') || re.test(p.road_address_name || ''); };
  // 이름이 맞는 음식점·카페 중 권역 안에 있는 곳. 이름은 맞는데 모두 권역 밖이면 'out'
  function pick(list, name, region) {
    var n = norm(name);
    var food = list.filter(function (p) { return p.category_group_code === 'FD6' || p.category_group_code === 'CE7'; });
    var same = food.filter(function (p) { var m = norm(p.place_name); return m.indexOf(n) > -1 || n.indexOf(m) > -1; });
    if (!same.length) return null;
    var inside = same.filter(function (p) { return window.BadaInRegion(region, p); });
    return inside[0] || 'out';
  }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  window.BadaKakaoEnrich = function (ol, opt) {
    opt = opt || {};
    var lab = opt.label || { tel: '전화', detail: '카카오맵 상세' };
    var SHOW = opt.show || 10;
    // 검사가 끝나면: 권역 밖(또는 제주에서 확인 못 한) 가게는 빼고 앞에서부터 SHOW곳만 번호를 다시 매겨 보여 줌
    function finish() {
      var n = 0;
      [].forEach.call(ol.querySelectorAll('li[data-q]'), function (li) {
        var bad = li.getAttribute('data-check') === 'out' || (opt.strict && li.getAttribute('data-check') !== 'ok');
        if (bad) { li.hidden = true; return; }
        n++; li.hidden = n > SHOW;
        var rk = li.querySelector('.rk'); if (rk) rk.textContent = String(n);
      });
      if (opt.onDone) opt.onDone(Math.min(n, SHOW));
    }
    function run() {
      places(opt.prefix || '').then(function (ps) {
        var lis = [].filter.call(ol.querySelectorAll('li[data-q]'), function (li) { return !li.getAttribute('data-done'); });
        var left = lis.length; if (!left) return finish();
        function done() { if (--left === 0) finish(); }
        lis.forEach(function (li) {
          li.setAttribute('data-done', '1');
          var o = { size: 5 };
          if (opt.center) { o.location = new kakao.maps.LatLng(opt.center[0], opt.center[1]); o.radius = 20000; }
          ps.keywordSearch(li.getAttribute('data-q'), function (res, st) {
            var p = st === kakao.maps.services.Status.OK ? pick(res, li.getAttribute('data-name'), opt.region) : null;
            if (!p) { li.setAttribute('data-check', 'none'); return done(); }
            if (p === 'out') { li.setAttribute('data-check', 'out'); return done(); }
            li.setAttribute('data-check', 'ok');
            var a = li.querySelector('a'); if (a && p.place_url) a.href = p.place_url;
            var info = el('div', 'tr-info');
            var addr = (p.road_address_name || p.address_name || '').replace(/^(전남광주통합특별시|광주전남통합특별시|전라남도|전남|제주특별자치도|제주도|제주)\s*/, '');
            if (addr) { var s = el('span', 'tr-addr', addr); if (opt.koLang) s.lang = 'ko'; info.appendChild(s); }
            if (p.phone) { var t = el('a', 'tr-tel', '📞 ' + p.phone); t.href = 'tel:' + p.phone.replace(/[^\d]/g, ''); info.appendChild(t); }
            if (p.place_url) { var d = el('a', 'tr-kakao', lab.detail + ' ↗'); d.href = p.place_url; d.target = '_blank'; d.rel = 'noopener'; info.appendChild(d); }
            if (window.BadaNaviButton && p.y && p.x) { var nv = window.BadaNaviButton(p.place_name, p.y, p.x, '🚗 내비'); if (nv) info.appendChild(nv); }
            li.appendChild(info);
            done();
          }, o);
        });
      }).catch(function () { finish(); });
    }
    // 화면에 보일 때만 조회하던 방식은 일부 휴대폰 화면에서 신호가 오지 않아, 순위가 그려지면 바로 조회한다 (한 페이지 최대 10건)
    ol._badaSeen = true; ol._badaRun = run;
    setTimeout(run, 300);
  };
})();
