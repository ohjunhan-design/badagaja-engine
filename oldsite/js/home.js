/* 바다가자닷컴 메인페이지
 * ① 사진 슬라이드 + 통합 검색  ② 오늘의 바다  ③ 권역 지도 + 사진 카드
 * ④ 이달의 제철·축제  ⑤ 동행별 추천 코스
 * 데이터: js/home-data.js (build-home-data.ps1로 생성), 물때 계산: js/app.js의 BADAGAJA_TIDE
 */
(function () {
  var D = window.BADAGAJA_HOME;
  if (!D) return;
  var T = window.BADAGAJA_TIDE || null;
  var R = {}; D.regions.forEach(function (r) { R[r.slug] = r; });
  var ORDER = D.regions.slice().sort(function (a, b) { return a.no - b.no; });
  // 제주 7권역 (2026-09-17 확장) — 오늘의 바다·검색·이달의 바다·추천 코스에 함께 보여 준다
  var JEJU = [
    { slug: 'jejusi', name: '제주시내', tag: '공항 가까운 도심 바다 용두암 이호테우' },
    { slug: 'aewol', name: '애월·한림', tag: '협재 금능 해변 노을 해안도로 한림항' },
    { slug: 'jocheon', name: '조천·구좌', tag: '함덕 월정리 세화 해변 해녀' },
    { slug: 'seongsan', name: '성산·표선', tag: '성산일출봉 섭지코지 우도 표선' },
    { slug: 'seogwipo', name: '서귀포·중문', tag: '정방폭포 쇠소깍 주상절리 은갈치' },
    { slug: 'daejeong', name: '대정·안덕', tag: '산방산 송악산 모슬포 방어 가파도 마라도' },
    { slug: 'chuja', name: '추자도', tag: '갯바위 낚시 돌돔 감성돔 참굴비' }
  ];
  JEJU.forEach(function (r, i) { r.jeju = true; r.no = i + 1; R[r.slug] = r; });
  // 첫 화면은 두 갈래: 전남여행(index.html, data-site 없음) · 제주여행(jeju.html, data-site="jeju")
  // 제주여행 화면은 js/jeju-data.js(build-jeju.ps1 가 만듦)의 제철·축제·코스만 쓴다
  var SITE_JEJU = document.body.getAttribute('data-site') === 'jeju';
  // 전국 첫 화면(index.html, data-site="all") — 전남 15·제주 7·확대 권역 35를 묶음별로 다 보여 준다 (2026-09-20)
  var SITE_ALL = document.body.getAttribute('data-site') === 'all';
  // 입구에서 넘어온 검색어(guide/?q=…)를 검색창에 넣고 바로 실행합니다 (2026-09-21)
  try {
    var _q = new URLSearchParams(location.search).get('q');
    if (_q) setTimeout(function () {
      var box = document.getElementById('hSearch');
      if (box) { box.value = _q; box.dispatchEvent(new Event('input', { bubbles: true })); box.focus(); }
    }, 60);
  } catch (e) {}
  var GROUP_ORDER = ['제주', '부산·울산', '강원', '전남', '경남', '충남', '경북', '인천·경기', '전북'];
  var GROUP_COLOR = { '충남': '#3B7EA1', '전북': '#5A8F5A', '경남': '#2F5873', '부산·울산': '#4A6FA5', '경북': '#4A4F7A', '강원': '#3C6E71', '인천·경기': '#6B7FA3' };
  var COASTS = Object.keys(window.BADAGAJA_COAST || {}).map(function (s, i) {
    var c = window.BADAGAJA_COAST[s];
    return { slug: s, name: c.name, tag: c.group + ' ' + c.name, color: GROUP_COLOR[c.group] || '#2F5D57', lat: c.lat, lng: c.lng, fishing: 0, gleaning: 0, photo: '', coast: true, group: c.group, no: 100 + i };
  });
  // 오늘의 바다에서 고른 권역 — 이달의 축제 칸이 이 권역 것을 먼저 보여 준다 (2026-09-20)
  var TODAY_SLUG = null, onRegion = [];
  var JD = window.BADAGAJA_JEJU;
  if (JD) (JD.regions || []).forEach(function (x) { var r = R[x.slug]; if (r) { r.no = x.no; r.color = x.color; } });
  if (SITE_JEJU) {
    D.catch = (JD && JD.catch) || []; D.festivals = (JD && JD.festivals) || []; D.courses = (JD && JD.courses) || []; D.points = [];
    ORDER = JEJU.slice();
  }
  if (SITE_ALL) {
    D.regions.forEach(function (r) { r.group = '전남'; }); JEJU.forEach(function (r) { r.group = '제주'; });
    COASTS.forEach(function (r) { R[r.slug] = r; });
    // 제주·전국 확대 권역의 제철·축제·코스를 합칩니다 — home-data.js 는 전남뿐이라 '전국' 제목에 전남 내용만 나왔습니다 (2026-09-24)
    var NA = window.BADAGAJA_NATION;
    if (NA) ['catch', 'festivals', 'courses'].forEach(function (k) { D[k] = (D[k] || []).concat((NA[k] || []).filter(function (x) { return R[x.r]; })); });
    // 전국 첫 화면 슬라이드에 쓸 대표 사진 (권역 히어로)
    var PHOTO = { seongsan: 'img/jeju/photo/home-hero.jpg?v=951142953', busaneast: 'img/coast/busaneast-hero.jpg?v=2390918060', gangneung: 'img/coast/gangneung-hero.jpg?v=1162090535', tongyeong: 'img/coast/tongyeong-hero.jpg?v=2175099577', taean: 'img/coast/taean-hero.jpg?v=3125325243', pohang: 'img/coast/pohang-hero.jpg?v=1113267983', ganghwa: 'img/coast/ganghwa-hero.jpg?v=1780335185', gunsan: 'img/coast/gunsan-hero.jpg?v=4230525424', sokcho: 'img/coast/sokcho-hero.jpg?v=2457212343', namhae: 'img/coast/namhae-hero.jpg?v=3926067475' };
    Object.keys(PHOTO).forEach(function (k) { if (R[k]) R[k].photo = PHOTO[k]; });
    var all = JEJU.concat(COASTS).concat(ORDER);
    ORDER = [];
    GROUP_ORDER.forEach(function (g) { all.filter(function (r) { return r.group === g; }).forEach(function (r) { ORDER.push(r); }); });
  }
  function rname(slug) { var r = R[slug]; return r ? (r.jeju && !SITE_JEJU ? '제주 ' : '') + r.name : ''; }

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function norm(s) { return (s || '').replace(/\(.*?\)/g, '').replace(/[\s·\-]/g, '').toLowerCase(); }
  function kst() { var d = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000); return d; }
  var NOW = kst();
  var DAY = ['일', '월', '화', '수', '목', '금', '토'];

  /* 대상 목록(해루질·낚시 안내 페이지) — 검색과 "이달에 잡을 수 있는 것"이 함께 쓴다 */
  var SPI = [], SPI_P = null;
  function loadSpecies() {
    if (!SPI_P) {
      SPI_P = fetch('data/species-index.json').then(function (r) { if (!r.ok) throw 0; return r.json(); })
        .then(function (d) { SPI = d.species || []; return SPI; });
    }
    return SPI_P;
  }
  function monthLabel(ms) {                       // [4,5,6,7] → "4~7월", 겨울에 걸치면 "9월~다음 해 2월"
    if (!ms || !ms.length) return '';
    if (ms.length >= 12) return '연중';
    var has = {}; ms.forEach(function (m) { has[m] = 1; });
    var starts = ms.filter(function (m) { return !has[m === 1 ? 12 : m - 1]; });
    if (starts.length === 1 && ms.length >= 3) {
      var a = starts[0];
      var z = ms.filter(function (m) { return !has[m === 12 ? 1 : m + 1]; })[0];
      return z < a ? a + '월~다음 해 ' + z + '월' : a + '~' + z + '월';
    }
    return ms.join('·') + '월';
  }

  /* ---------- ① 사진 슬라이드 ---------- */
  (function slides() {
    var box = $('hSlides'), cap = $('hCaption');
    if (!box) return;
    // 전체 화면 배경은 해상도가 충분하고 워터마크·인물 사진이 없는 사진만 사용
    var HERO = SITE_ALL
      ? ['taean', 'seongsan', 'gangneung', 'namhae', 'boseong', 'tongyeong', 'busaneast', 'pohang', 'ganghwa', 'jindo', 'gunsan', 'sokcho']   // 전국 첫 화면: 만리포 일몰로 시작해 제주·동해·서해·남해 골고루
      : ['boseong', 'jindo', 'sinan', 'goheung', 'muan', 'haenam', 'gwangyang', 'hampyeong', 'mokpo', 'suncheon', 'yeonggwang'];
    var list = HERO.map(function (s) { return R[s]; }).filter(Boolean);
    var nodes = [box.firstElementChild], cur = 0;
    for (var i = 1; i < list.length; i++) { var s = el('div', 'h-slide'); box.appendChild(s); nodes.push(s); }
    function load(i) { var n = nodes[i]; if (!n.style.backgroundImage) n.style.backgroundImage = "url('" + list[i].photo + "')"; }
    function show(i) {
      load(i); load((i + 1) % list.length);
      nodes[cur].classList.remove('on'); nodes[i].classList.add('on'); cur = i;
      if (cap) { cap.textContent = rname(list[i].slug) || list[i].name; cap.href = list[i].slug + '.html'; }
    }
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var timer = setInterval(function () { if (!document.hidden) show((cur + 1) % list.length); }, 6500);
    window.addEventListener('load', function () { load(1); });
  })();

  /* ---------- ① 첫 화면 숫자 (자료에서 바로 세어 넣는다) ---------- */
  (function stats() {
    var p = $('statPoints'), c = $('statCatch'), f = $('statFest');
    if (p) {
      var jn = D.regions.reduce(function (s, r) { return s + (r.fishing || 0) + (r.gleaning || 0); }, 0);
      p.textContent = jn;
      // 전국 확대 권역(충남~수도권)의 포인트는 data/coast-points-index.json 에 권역별 n 으로 있다 — 전국 첫 화면에서만 더한다 (2026-09-20)
      if (SITE_ALL) fetch('data/coast-points-index.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (ix) {
        var add = 0;
        Object.keys(ix).forEach(function (k) { var v = ix[k] || {}; Object.keys(v).forEach(function (t) { add += (v[t] && v[t].n) || 0; }); });
        if (add) p.textContent = (jn + add).toLocaleString('ko-KR');
      }).catch(function () { });
    }
    if (c) {
      var names = {};
      (D.catch || []).forEach(function (x) { names[x.n] = 1; });
      c.textContent = Object.keys(names).length;
    }
    if (f) f.textContent = (D.festivals || []).length;
  })();

  /* ---------- ① 통합 검색 ---------- */
  (function search() {
    var input = $('hSearch'), out = $('hResults');
    if (!input) return;
    loadSpecies().catch(function () { });          // 검색에서 "잡는 법" 결과를 쓰려면 미리 받아둔다

    // 포인트 목록(1,000곳 넘음)은 첫 화면을 여는 데는 쓰이지 않고 검색할 때만 필요합니다.
    // 같이 받으면 자료가 130KB 넘게 무거워져, 검색창을 처음 건드릴 때 받아 옵니다 (2026-09-20)
    var ptsLoading = null;
    function loadPoints() {
      if (window.BADAGAJA_HOME_POINTS) { D.points = window.BADAGAJA_HOME_POINTS; return Promise.resolve(); }
      if (ptsLoading) return ptsLoading;
      ptsLoading = new Promise(function (ok) {
        var s = document.createElement('script');
        // 같은 쪽의 home-data.js 가 쓰는 판 번호를 그대로 따라갑니다(캐시가 엇갈리지 않게)
        var ref = document.querySelector('script[src*="home-data.js"]');
        var ver = ref && ref.src.indexOf('?v=') > -1 ? ref.src.split('?v=')[1] : '';
        s.src = 'js/home-points.js' + (ver ? '?v=' + ver : '');
        s.onload = function () { D.points = window.BADAGAJA_HOME_POINTS || []; ok(); };
        s.onerror = function () { ok(); };       // 못 받아도 나머지 검색은 그대로 됩니다
        document.head.appendChild(s);
      });
      return ptsLoading;
    }
    input.addEventListener('focus', function () { loadPoints().then(function () { if (input.value.trim()) run(); }); }, { once: true });
    // 안내 문구가 휴대폰 화면에서는 잘리므로, 좁을 때만 짧은 문구로 바꾼다
    (function placeholder() {
      var full = input.getAttribute('placeholder'), brief = '축제·낚시·해루질·포인트 검색';
      function fit() { input.setAttribute('placeholder', window.innerWidth < 620 ? brief : full); }
      fit();
      window.addEventListener('resize', fit);
    })();
    var KIND = { f: '낚시', g: '해루질' };
    var species = {};
    D.catch.forEach(function (c) {
      var k = norm(c.n); if (!species[k]) species[k] = { n: c.n.replace(/\(.*?\)/g, '').trim(), regions: [] };
      if (species[k].regions.indexOf(c.r) < 0) species[k].regions.push(c.r);
    });
    // 말로 쓴 검색을 알아듣기 위한 낱말 해석 — 달(9월·이달·이번 주)과 갈래(해루질·낚시·축제…) (2026-09-23)
    var MONTH_WORD = { '이달': 0, '이번달': 0, '이번주': 0, '지금': 0, '오늘': 0, '내일': 0, '주말': 0, '다음달': 1, '담달': 1 };
    function monthOfToken(t) {
      var m = t.match(/^(1[0-2]|[1-9])월$/);
      if (m) return +m[1];
      var HAN = { '일월': 1, '이월': 2, '삼월': 3, '사월': 4, '오월': 5, '유월': 6, '칠월': 7, '팔월': 8, '구월': 9, '시월': 10, '십일월': 11, '십이월': 12 };
      if (HAN[t]) return HAN[t];
      if (t in MONTH_WORD) { var d = new Date(NOW.getFullYear(), NOW.getMonth() + MONTH_WORD[t], 1); return d.getMonth() + 1; }
      return null;
    }
    var KIND_WORD = {
      '해루질': 'catch', '갯벌': 'catch', '조개': 'catch', '캐기': 'catch', '채취': 'catch',
      '낚시': 'fish', '갯바위': 'fish', '방파제': 'fish', '루어': 'fish', '찌낚시': 'fish',
      '축제': 'fest', '먹거리': 'eat', '맛집': 'eat', '먹을거리': 'eat', '먹을': 'eat',
      '코스': 'course', '여행': 'course', '일정': 'course',
      '명소': 'spot', '관광': 'spot', '볼거리': 'spot', '가볼만한곳': 'spot', '구경': 'spot',
      '포인트': 'point', '자리': 'point', '물때': 'tide', '물때표': 'tide', '간조': 'tide', '만조': 'tide'
    };
    // 난이도·동행 말 — 자료에 있는 값으로만 거릅니다 (2026-09-23 검색 2단계)
    var EASY_WORD = ['초보', '처음', '쉬운', '쉬워', '쉽게', '입문', '왕초보', '초급'];
    var WITH_WORD = { '아이': '아이', '아이와': '아이', '애들': '아이', '가족': '가족', '가족과': '가족',
                      '연인': '연인', '커플': '연인', '부모님': '부모님', '어머니': '부모님', '아버지': '부모님',
                      '혼자': '혼자', '나홀로': '혼자', '친구': '친구', '친구와': '친구' };
    var travel = null, tvLoading = null;
    function loadTravel() {
      if (window.BADAGAJA_TRAVEL_DATA) { travel = window.BADAGAJA_TRAVEL_DATA; return Promise.resolve(); }
      if (tvLoading) return tvLoading;
      tvLoading = new Promise(function (ok) {
        var sc = document.createElement('script');
        var ref = document.querySelector('script[src*="home-data.js"]');
        var ver = ref && ref.src.indexOf('?v=') > -1 ? ref.src.split('?v=')[1] : '';
        sc.src = 'js/travel-data.js' + (ver ? '?v=' + ver : '');
        sc.onload = function () { travel = window.BADAGAJA_TRAVEL_DATA || null; ok(); };
        sc.onerror = function () { ok(); };      // 못 받아도 나머지 검색은 그대로 됩니다
        document.head.appendChild(sc);
      });
      return tvLoading;
    }
    var sel = -1;
    function regionOfToken(t) {
      for (var i = 0; i < ORDER.length; i++) {
        var r = ORDER[i];
        if (t === r.name || t === r.name + '군' || t === r.name + '시' || (r.jeju && r.name.split('·').indexOf(t) > -1)) return r.slug;
        if (r.coast && (t === r.name.replace(/\s/g, '') || t === r.group || t === r.group + '여행' || r.name.split(/[\s·]/).indexOf(t) > -1)) return r.slug;   // 확대 권역: '포항'·'부산'·'강원'
      }
      return null;
    }
    function run() {
      var q = input.value.trim()
        .replace(/이번\s*주/g, '이번주').replace(/이번\s*달/g, '이번달')
        .replace(/다음\s*달/g, '다음달').replace(/잡을\s*수\s*있는/g, '');   // 띄어 쓴 말도 알아듣게 (2026-09-23)
      out.innerHTML = ''; sel = -1;
      if (!q) { out.hidden = true; input.setAttribute('aria-expanded', 'false'); return; }
      var toks = q.split(/\s+/), rFilter = null, rest = [], mFilter = null, kFilter = null;
      var eFilter = false, wFilter = null;      // 난이도 '쉬움' · 동행 (2026-09-23 검색 2단계)
      toks.forEach(function (t) {
        var s = regionOfToken(t);
        if (s) { rFilter = s; return; }
        var m = monthOfToken(t);
        if (m) { mFilter = m; return; }
        var k = KIND_WORD[norm(t)];
        if (k) { kFilter = k; return; }
        if (EASY_WORD.indexOf(norm(t)) > -1) { eFilter = true; return; }
        var w = WITH_WORD[norm(t)];
        if (w) { wFilter = w; if (!kFilter) kFilter = 'course'; return; }
        rest.push(norm(t));
      });
      var groups = [];
      // 권역
      var regs = ORDER.filter(function (r) { return (rFilter === r.slug && !rest.length) || rest.some(function (t) { return norm(r.name + r.tag).indexOf(t) > -1; }); });
      var jregs = rest.length && !SITE_JEJU ? JEJU.filter(function (r) { return rest.some(function (t) { return norm('제주' + r.name + r.tag).indexOf(t) > -1; }); }) : [];
      var regItems = regs.slice(0, 4).map(function (r) { return { href: r.slug + '.html', tag: '권역', text: r.name, meta: r.jeju ? '물때·낚시·인생사진' : '포인트 ' + (r.fishing + r.gleaning) + '곳' }; })
        .concat(jregs.slice(0, 4).map(function (r) { return { href: r.slug + '.html', tag: '제주', text: '제주 ' + r.name, meta: '물때·낚시·관광' }; }));
      if (regItems.length) groups.push(['권역', regItems.slice(0, 6)]);
      // 제철 어종
      if (rest.length) {
        var sp = Object.keys(species).map(function (k) { return species[k]; }).filter(function (s) {
          return rest.every(function (t) { return norm(s.n).indexOf(t) > -1; }) && (!rFilter || s.regions.indexOf(rFilter) > -1);
        });
        if (sp.length) groups.push(['제철 어종·패류', sp.slice(0, 4).map(function (s) {
          var rs = rFilter ? [rFilter] : s.regions;
          return { href: rs[0] + '.html#catch', tag: '제철', text: s.n, meta: rs.map(function (x) { return rname(x); }).slice(0, 4).join('·') + (rs.length > 4 ? ' 외' : '') };
        })]);
      }
      // 잡는 법 안내(해루질·낚시 대상 페이지)
      if ((rest.length || kFilter === 'catch' || kFilter === 'fish' || (mFilter && !kFilter)) && SPI.length && ['fest', 'eat', 'course', 'tide'].indexOf(kFilter) < 0) {
        var gs = SPI.filter(function (s) {
          var hay = norm(s.n + (s.alias || []).join('') + (s.sec === 'catch' ? '해루질잡는법채취' : '낚시낚는법채비'));
          if (kFilter === 'catch' && s.sec !== 'catch') return false;          // '해루질'이라고 썼으면 해루질만 (2026-09-23)
          if (kFilter === 'fish' && s.sec !== 'fish') return false;
          if (mFilter && (s.months || []).length && s.months.indexOf(mFilter) < 0) return false;   // 달 자료가 있을 때만 거릅니다 (2026-09-23)
          if (rFilter && (s.regions || []).length && s.regions.indexOf(rFilter) < 0) return false;
          if (eFilter && s.level && s.level.indexOf('쉬') < 0) return false;   // '초보' 라고 썼으면 쉬운 것만
          return rest.every(function (t) { return hay.indexOf(t) > -1; });
        });
        if (gs.length) groups.push(['잡는 법 안내', gs.slice(0, 4).map(function (s) {
          return {
            href: s.sec + '/' + s.slug + '.html', tag: s.sec === 'catch' ? '해루질' : '낚시', cls: s.sec === 'catch' ? 'g' : 'f',
            text: s.n + (s.sec === 'catch' ? ' 잡는 법' : ' 낚는 법'),
            meta: (monthLabel(s.months) ? monthLabel(s.months) + ' · ' : '') + '난이도 ' + s.level
          };
        })]);
      }
      // 축제
      var MON = ['', '1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
      var fests = (D.festivals || []).filter(function (x) {
        if (rFilter && x.r !== rFilter) return false;
        if (mFilter && x.m !== mFilter) return false;                          // '9월 축제' (2026-09-23)
        if (kFilter && kFilter !== 'fest') return false;
        if (!rest.length) return !!(rFilter || mFilter || kFilter === 'fest');
        var hay = norm(x.n + (x.d || '') + '축제');
        return rest.every(function (t) { return hay.indexOf(t) > -1; });
      });
      if (fests.length) {
        var nowM = NOW.getMonth() + 1;
        fests.sort(function (a, b) { return ((a.m - nowM + 12) % 12) - ((b.m - nowM + 12) % 12); });
        groups.push(['축제 ' + fests.length + '개', fests.slice(0, 5).map(function (x) {
          return { href: x.r + '.html#festival', tag: MON[x.m] || '축제', cls: 'fest', text: x.n, meta: rname(x.r) + (x.d ? ' · ' + x.d.split('·')[0].trim() : '') };
        })]);
      }      // 포인트
      var pts = (D.points || []).filter(function (p) {   // 포인트 자료를 아직 못 받았을 때 검색이 멈추던 것 (2026-09-23)
        if (rFilter && p.r !== rFilter) return false;
        if (kFilter === 'catch' && p.k !== 'g') return false;                  // 해루질만 (2026-09-23)
        if (kFilter === 'fish' && p.k !== 'f') return false;
        if (kFilter && ['catch', 'fish', 'point'].indexOf(kFilter) < 0) return false;
        if (!rest.length) return !!(rFilter || kFilter);
        var hay = norm(p.n + p.t + KIND[p.k]);
        return rest.every(function (t) { return hay.indexOf(t) > -1; });
      });
      // 맛집·명소·코스 — js/travel-data.js (검색을 쓸 때만 늦게 받습니다, 2026-09-23)
      if (travel && travel.regions) {
        var want = { eat: '맛집 · 먹거리', spot: '바닷가 명소', course: '동행별 코스' };
        Object.keys(want).forEach(function (kind) {
          if (kFilter && kFilter !== kind) return;
          if (!kFilter && !rest.length && !rFilter) return;
          var rows = [];
          travel.regions.forEach(function (r) {
            if (rFilter && r.slug !== rFilter) return;
            var list = kind === 'eat' ? r.eat : kind === 'spot' ? r.spots : r.courses;
            (list || []).forEach(function (x) {
              if (kind === 'course' && wFilter && (x.theme || '').indexOf(wFilter) < 0) return;
              var nm = x.name || x.title || '';
              var hay = norm(nm + (x.desc || '') + (x.addr || '') + (x.theme || '') + (x.when || ''));
              if (rest.length && !rest.every(function (t) { return hay.indexOf(t) > -1; })) return;
              rows.push({ r: r, x: x, nm: nm });
            });
          });
          if (!rows.length) return;
          groups.push([want[kind] + ' ' + rows.length + '개', rows.slice(0, 5).map(function (o) {
            var meta = rname(o.r.slug);
            if (kind === 'eat' && o.x.when) meta += ' · ' + o.x.when;
            else if (kind === 'spot' && o.x.addr) meta += ' · ' + o.x.addr;
            else if (kind === 'course' && o.x.theme) meta += ' · ' + o.x.theme;
            return { href: 'travel/', tag: kind === 'eat' ? '맛집' : kind === 'spot' ? '명소' : '코스',
                     cls: 'fest', text: o.nm, meta: meta };
          })]);
        });
      }
      if (pts.length) groups.push(['포인트 ' + pts.length + '곳', pts.slice(0, 8).map(function (p) {
        return { href: 'point/' + p.p + '#point-' + p.i, tag: KIND[p.k], cls: p.k, text: p.n, meta: R[p.r].name + ' · ' + p.t };
      })]);
      if (!groups.length) { out.appendChild(el('div', 'empty', '"' + q + '"에 맞는 결과가 없어요. 지역명(예: 여수)이나 어종(예: 낙지)으로 찾아보세요.')); }
      groups.forEach(function (g) {
        out.appendChild(el('div', 'grp', g[0]));
        g[1].forEach(function (it) {
          var a = el('a'); a.href = it.href; a.setAttribute('role', 'option');
          a.appendChild(el('span', 'tag' + (it.cls ? ' ' + it.cls : ''), it.tag));
          a.appendChild(el('span', null, it.text));
          a.appendChild(el('span', 'meta', it.meta));
          out.appendChild(a);
        });
      });
      out.hidden = false; input.setAttribute('aria-expanded', 'true');
    }
    function move(d) {
      var links = out.querySelectorAll('a'); if (!links.length) return;
      if (sel > -1) links[sel].classList.remove('on');
      sel = (sel + d + links.length) % links.length; links[sel].classList.add('on'); links[sel].scrollIntoView({ block: 'nearest' });
    }
    input.addEventListener('input', function () {
      run();
      if (!(D.points || []).length) loadPoints().then(run);
      if (!travel) loadTravel().then(run);
    });
    input.addEventListener('focus', function () { if (input.value.trim()) run(); });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
      else if (e.key === 'Enter') { var links = out.querySelectorAll('a'); var t = links[sel > -1 ? sel : 0]; if (t) location.href = t.href; }
      else if (e.key === 'Escape') { out.hidden = true; }
    });
    document.addEventListener('click', function (e) { if (!e.target.closest('.h-search')) out.hidden = true; });
    [].forEach.call(document.querySelectorAll('.h-quick button'), function (b) {
      b.addEventListener('click', function () { input.value = b.getAttribute('data-q'); input.focus(); run(); });
    });
  })();


  /* ---------- 이달에 잡을 수 있는 것 (data/species-index.json) ---------- */
  (function species() {
    var grid = $('spGrid'), tabs = $('spTabs');
    if (!grid) return;
    var M = NOW.getMonth() + 1, DAY = NOW.getDate(), sec = 'all', LIST = [];
    function inBan(s) {
      if (!s.ban || !s.ban.length || s.byNotice) return false;
      return s.ban.some(function (b) {
        var a = b[0] * 100 + b[1], z = b[2] * 100 + b[3], t = M * 100 + DAY;
        return a <= z ? (t >= a && t <= z) : (t >= a || t <= z);
      });
    }
    function draw() {
      var list = LIST.filter(function (s) { return s.months.indexOf(M) > -1 && (sec === 'all' || s.sec === sec); });
      list.sort(function (a, b) { return (inBan(a) ? 1 : 0) - (inBan(b) ? 1 : 0) || a.n.localeCompare(b.n, 'ko'); });
      grid.innerHTML = '';
      if (!list.length) { grid.appendChild(el('p', 'sp-loading', '이 달에 정리된 대상이 없습니다.')); return; }
      list.forEach(function (s) {
        var a = el('a', 'sp-card' + (inBan(s) ? ' banned' : ''));
        a.href = s.sec + '/' + s.slug + '.html';
        var head = el('div', 'sp-top');
        head.appendChild(el('b', null, s.n));
        head.appendChild(el('span', 'sp-tag ' + s.sec, s.sec === 'catch' ? '해루질' : '낚시'));
        a.appendChild(head);
        a.appendChild(el('p', null, s.one));
        var meta = el('div', 'sp-meta');
        meta.appendChild(el('span', null, '난이도 ' + s.level));
        if (s.regions && s.regions.length) meta.appendChild(el('span', null, R[s.regions[0]] ? s.regions.length + '개 시·군' : ''));
        if (s.size) meta.appendChild(el('span', null, s.size + ' 금지'));
        a.appendChild(meta);
        if (inBan(s)) a.appendChild(el('span', 'sp-ban', '지금 금어기 · ' + s.banText));
        else if (s.byNotice) a.appendChild(el('span', 'sp-ban notice', '금어기 있음 · 고시 확인'));
        grid.appendChild(a);
      });
      fold(list.length);
      var t = $('spTitle'); if (t) t.textContent = M + '월에 잡을 수 있는 것';
    }
    /* 처음에는 조금만 보여 주고 나머지는 펼쳐서 본다 (2026-09-22 주인: 너무 많다 → 5개 안팎)
       휴대폰(한 줄에 1~2개)은 5개, PC(한 줄에 3~4개)는 딱 한 줄 — 5개로 하면 둘째 줄에 하나만 남기 때문 */
    function showCount() {
      var cols = getComputedStyle(grid).gridTemplateColumns.split(' ').filter(Boolean).length || 1;
      return cols >= 3 ? cols : 5;
    }
    var SHOW = 5, lastCols = 0;
    window.addEventListener('resize', function () {
      var c = getComputedStyle(grid).gridTemplateColumns.split(' ').filter(Boolean).length;
      if (lastCols && c !== lastCols && LIST.length) draw();
    });
    function fold(total) {
      lastCols = getComputedStyle(grid).gridTemplateColumns.split(' ').filter(Boolean).length;
      SHOW = showCount();
      [].forEach.call(grid.querySelectorAll('.sp-card'), function (c, i) { c.classList.toggle('sp-extra', i >= SHOW); });
      var row = $('spFold');
      if (!row) { row = el('div', 'sp-fold'); row.id = 'spFold'; grid.parentNode.insertBefore(row, grid.nextSibling); }
      row.innerHTML = '';
      grid.classList.remove('expanded');
      if (total <= SHOW) { row.hidden = true; return; }
      row.hidden = false;
      var b = el('button', 'sp-foldbtn', (total - SHOW) + '개 더 보기 ▾');
      b.type = 'button';
      b.addEventListener('click', function () {
        var open = grid.classList.toggle('expanded');
        b.textContent = open ? '접기 ▴' : (total - SHOW) + '개 더 보기 ▾';
        if (!open) grid.scrollIntoView({ block: 'start', behavior: 'smooth' });
      });
      row.appendChild(b);
    }
    loadSpecies().then(function (list) {
      LIST = list;
      draw();
      [].forEach.call(tabs.querySelectorAll('button'), function (b) {
        b.addEventListener('click', function () {
          sec = b.getAttribute('data-sec');
          [].forEach.call(tabs.children, function (x) { x.classList.toggle('on', x === b); });
          draw();
        });
      });
    }).catch(function () { grid.innerHTML = ''; grid.appendChild(el('p', 'sp-loading', '목록을 불러오지 못했습니다.')); });
  })();

  /* ---------- ② 오늘의 바다 ---------- */
  (function today() {
    var box = $('tsRegions');
    if (!box || !T) return;
    var KEY = SITE_JEJU ? 'bdg-today-jeju' : (SITE_ALL ? 'bdg-today-all' : 'bdg-today-region');
    var slug = store(KEY);
    if (!R[slug] || (!SITE_ALL && !!R[slug].jeju !== SITE_JEJU)) slug = SITE_JEJU ? 'seongsan' : (SITE_ALL ? 'jejusi' : 'yeosu');
    var reqId = 0;
    ORDER.forEach(function (r) {
      var b = el('button', null, r.name); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.r = r.slug; if (r.group) b.dataset.g = r.group;
      b.addEventListener('click', function () { select(r.slug, true); });
      box.appendChild(b);
    });
    // 전국 첫 화면: 묶음 칩(제주·부산울산·…)으로 권역 버튼을 걸러 보여 준다
    var gbox = $('tsGroups'), curGroup = null;
    function showGroup(g) {
      curGroup = g;
      [].forEach.call(box.querySelectorAll('button'), function (b) { b.hidden = !!g && b.dataset.g !== g; });
      if (gbox) [].forEach.call(gbox.querySelectorAll('button'), function (b) { b.setAttribute('aria-selected', b.dataset.g === g ? 'true' : 'false'); });
    }
    if (SITE_ALL && gbox) {
      GROUP_ORDER.forEach(function (g) {
        var b = el('button', null, g); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.g = g;
        b.addEventListener('click', function () { showGroup(g); var first = ORDER.filter(function (r) { return r.group === g; })[0]; if (first && R[slug].group !== g) select(first.slug, true); });
        gbox.appendChild(b);
      });
    }
    // 전에 고른 권역은 맨 앞으로 — 다시 왔을 때 내 바다가 먼저 보이게
    if (store(KEY)) { var mine = box.querySelector('[data-r="' + slug + '"]'); if (mine) box.insertBefore(mine, box.firstChild); }
    function toMin(hm) { var p = hm.split(':'); return +p[0] * 60 + +p[1]; }
    function select(s, user) {
      slug = s; if (user) store(KEY, s);
      if (SITE_ALL && gbox && R[s].group !== curGroup) showGroup(R[s].group);
      TODAY_SLUG = s; onRegion.forEach(function (fn) { try { fn(); } catch (e) { } });
      var saved = store(KEY);
      [].forEach.call(box.querySelectorAll('button'), function (b) {
        b.setAttribute('aria-selected', b.dataset.r === s ? 'true' : 'false');
        b.classList.toggle('mine', b.dataset.r === saved);
      });
      if (user) { var on = box.querySelector('[aria-selected="true"]'); on && on.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' }); }
      var r = R[s], d = new Date(NOW.getFullYear(), NOW.getMonth(), NOW.getDate());
      var m = T.calcMuldae(d), inten = T.calcIntensity(m), lab = T.tideLabel(inten);
      var c = T.coords[s] || [r.lat, r.lng], sun = T.sunTimes(d, c[0], c[1]);
      $('tsTitle').textContent = '오늘 ' + rname(s) + ' 바다는';
      $('tsDate').textContent = (d.getMonth() + 1) + '월 ' + d.getDate() + '일 (' + DAY[d.getDay()] + ') 기준';
      $('tsMuldae').textContent = m + '물';
      $('tsMuldaeName').textContent = lab.text;
      $('tsGauge').style.width = inten + '%';
      $('tsRise').textContent = sun ? sun.rise : '–'; $('tsSet').textContent = sun ? sun.set : '–';
      $('tsMore').href = s + '.html#tide'; $('tsMore').textContent = r.name + ' 물때표 2주 전체 보기 →';
      var state = { inten: inten, sun: sun, lows: null, wave: null, jeju: !!r.jeju };
      verdict(state);
      week(d, !!r.jeju);
      if ($('tsNext')) $('tsNext').hidden = true;
      $('tsTides').innerHTML = '<li class="muted">불러오는 중</li>'; $('tsTideSrc').textContent = '';
      $('tsTemp').textContent = '–'; $('tsSky').textContent = '불러오는 중'; $('tsWave').textContent = '';
      var my = ++reqId;
      fetch('api/tide-cache.php?region=' + s, { cache: 'no-store' }).then(function (res) { if (!res.ok) throw 0; return res.json(); }).then(function (data) {
        if (my !== reqId) return;
        var ev = data && data.days && data.days[0] && data.days[0].events;
        var ul = $('tsTides'); ul.innerHTML = '';
        if (!ev || !ev.length) { ul.innerHTML = '<li class="muted">오늘 간조·만조 시각을 불러오지 못했어요</li>'; return; }
        ev.forEach(function (e) {
          var li = el('li', e.type === '만조' ? 'high' : ''); li.appendChild(el('span', 'k', e.type)); li.appendChild(el('b', null, e.time));
          ul.appendChild(li);
        });
        $('tsTideSrc').textContent = (data.source === 'beach' ? '기상청 해수욕장 조석' : '국립해양조사원 조석예보') + ' · ' + (data.point || r.name);
        state.lows = ev.filter(function (e) { return e.type === '간조'; }).map(function (e) { return e.time; });
        verdict(state);
        nextLow(data);
        plan(data, s, r, d);
      }).catch(function () { if (my === reqId) $('tsTides').innerHTML = '<li class="muted">간조·만조 정보 준비 중</li>'; });
      seaIndex(s, my);
      // 입구(첫 화면)는 크림빛 칸 안에 작게 들어가므로 밝은 쪽으로 그립니다 (2026-09-21)
      if (window.BADAGAJA_TIDEGRAPH && $('tsGraph')) window.BADAGAJA_TIDEGRAPH.mount($('tsGraph'), s, { dark: !document.body.classList.contains('home-gate'), coords: T.coords[s] || [r.lat, r.lng] });
      fetch(((r.jeju || r.coast) ? 'api/weather-jeju.php?region=' : 'api/weather.php?region=') + s, { cache: 'no-store' }).then(function (res) { if (!res.ok) throw 0; return res.json(); }).then(function (w) {
        if (my !== reqId) return;
        if (!w || w.available === false) { $('tsSky').textContent = '이 권역은 관측 정보가 없어요'; return; }
        $('tsTemp').textContent = (w.temp != null && w.temp !== '') ? w.temp + '°' : '–';
        $('tsSky').textContent = w.label || '';
        var ss = $('stSky'); if (ss) ss.textContent = w.label || '';
        if (w.wave != null && w.wave !== '') { $('tsWave').textContent = '파고 ' + w.wave + 'm · ' + (w.point || r.name); state.wave = parseFloat(w.wave); verdict(state); }
        var sw = $('stWave'); if (sw) sw.textContent = (w.wave != null && w.wave !== '') ? (w.wave + 'm') : ((w.point || r.name) + ' 관측');
        else $('tsWave').textContent = (w.point || r.name) + ' 관측';
      }).catch(function () { if (my === reqId) $('tsSky').textContent = '날씨 정보 준비 중'; });
    }
    // 생활해양예보지수 (갯벌체험·바다낚시·해수욕) — api/seaidx.php
    function seaIndex(s, my) {
      [].forEach.call(document.querySelectorAll('.ts-idx'), function (card) {
        var t = card.dataset.type, g = card.querySelector('.ti-grade'), p = card.querySelector('.ti-place'), d = card.querySelector('.ti-detail');
        card.className = 'ts-card ts-idx'; g.textContent = '–'; p.textContent = '불러오는 중'; d.textContent = '';
        fetch('api/seaidx.php?type=' + t + '&region=' + s).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (x) {
          if (my !== reqId) return;
          if (!x || !x.available) { card.classList.add('off'); g.textContent = '정보 없음'; p.textContent = '이 권역 가까이에 예보 장소가 없어요'; return; }
          card.classList.add('g' + x.grade); g.textContent = x.label;
          p.textContent = x.point + (x.outside ? ' (' + x.outside + ')' : '') + ' · ' + x.distance + 'km · ' + x.when;
          var det = x.detail || {}, parts = [];
          if (t === 'mudflat') { if (det.start && det.end && det.start !== det.end) parts.push('체험 가능 ' + det.start + '~' + det.end); if (det.weather) parts.push(det.weather); }
          if (t === 'beach') { if (det.open) parts.push(det.open === '폐장' ? '폐장 기간(안전요원 없음)' : det.open); if (det.watertemp) parts.push('수온 ' + det.watertemp + '℃'); if (det.wave) parts.push('파고 ' + det.wave + 'm'); }
          if (t === 'fishing') {
            if (x.fish && x.fish.length) parts.push(x.fish.slice(0, 3).map(function (f) { return f.fish + ' ' + f.label; }).join(' · '));
            if (det.watertemp) parts.push('수온 ' + det.watertemp + '℃');
          }
          d.textContent = parts.join(' · ');
        }).catch(function () { if (my === reqId) { card.classList.add('off'); g.textContent = '–'; p.textContent = '지수를 불러오지 못했어요'; } });
      });
    }
    function verdict(st) {
      var v = $('tsVerdict'), msg;
      var dayLow = null;
      if (st.lows && st.sun) {
        var a = toMin(st.sun.rise) + 60, b = toMin(st.sun.set) - 60;
        dayLow = st.lows.filter(function (t) { var x = toMin(t); return x >= a && x <= b; })[0] || null;
      }
      if (st.jeju) {
        // 제주는 해루질을 권하지 않으므로 낚시·안전 기준으로만 알려준다
        if (st.inten >= 68) msg = '물이 크게 들고 나는 사리 무렵이라 <b>조류가 셉니다</b>. 갯바위·방파제에서는 물이 차오르는 시각을 꼭 확인하세요.';
        else if (st.inten <= 32) msg = '조금 무렵이라 물살이 약해요. <b>방파제·갯바위 낚시</b>가 비교적 편한 날입니다.';
        else msg = '물살이 보통인 날이에요.' + (dayLow ? ' 간조는 <b>' + dayLow + '</b>입니다.' : '');
      } else if (st.inten >= 68) {
        if (dayLow) msg = '물이 크게 빠지는 날, <b>해루질하기 좋아요</b>. 낮 간조 <b>' + dayLow + '</b> 전후 2시간을 노려보세요.';
        else if (st.lows) msg = '물은 크게 빠지지만 <b>간조가 이른 아침·밤</b>이에요. 야간 해루질은 안전장비를 꼭 챙기세요.';
        else msg = '물이 크게 빠지는 사리 무렵, <b>해루질하기 좋은 시기</b>예요.';
      } else if (st.inten <= 32) {
        msg = '물이 적게 빠지는 조금 무렵이에요. 물살이 약해 <b>방파제·선착장 낚시</b>가 편한 날입니다.';
      } else {
        msg = '물 빠짐이 보통인 날이에요.' + (dayLow ? ' 간조 <b>' + dayLow + '</b> 전후로 갯벌이 드러납니다.' : ' 간조 시각에 맞춰 움직이세요.');
      }
      if (st.wave != null && st.wave >= 1.5) msg += ' <b>파고 ' + st.wave + 'm</b> — 갯바위·방파제 끝은 피하세요.';
      v.innerHTML = msg;
    }
    // ---------- 이번 주 언제 갈까 ----------
    // 1) 물때 계산만으로 먼저 그리고(week), 2) 조석 자료가 오면 실제 낮 간조 높이로 다시 그린다(plan)
    function hmText(hm) {                      // "13:33" → "오후 1시 33분"
      var p = hm.split(':'), h = +p[0], m = +p[1];
      var part = h < 12 ? '오전' : (h < 18 ? '오후' : '저녁'), hh = h % 12 === 0 ? 12 : h % 12;
      return part + ' ' + hh + '시' + (m ? ' ' + m + '분' : '');
    }
    function dayWord(d, i) { return i === 0 ? '오늘' : (i === 1 ? '내일' : DAY[d.getDay()] + '요일'); }
    function drawWeek(rows, jeju, byTide) {
      var w = $('tsWeek'); w.innerHTML = '';
      var lg = $('tpBasis') && $('tpBasis').previousElementSibling;
      if (lg) lg.textContent = jeju ? '막대가 짧을수록 물살이 약해 낚시가 편해요' : '막대가 길수록 물이 많이 빠져요';
      rows.forEach(function (x, i) {
        var c = el('div', 'ts-day' + (i === 0 ? ' today' : '') + (x.best ? ' best' : (x.good ? ' good' : '')));
        c.appendChild(el('span', 'star', x.best ? '★' : (x.good ? '☆' : '')));
        var bar = el('div', 'bar'), fill = el('i'); fill.style.height = x.h + '%'; bar.appendChild(fill); c.appendChild(bar);
        c.appendChild(el('b', null, i === 0 ? '오늘' : DAY[x.d.getDay()]));
        c.appendChild(el('span', 'dm', x.d.getDate() + ' · ' + x.m + '물'));
        c.title = (x.d.getMonth() + 1) + '월 ' + x.d.getDate() + '일 ' + x.m + '물' + (x.low ? ' · 낮 간조 ' + x.low.time : (byTide ? ' · 낮 간조 없음' : ''));
        w.appendChild(c);
      });
      var weekend = rows.filter(function (x) { var g = x.d.getDay(); return g === 0 || g === 6; });
      var note = $('tpNote');
      if (note) {
        var calm = weekend.length && weekend.every(function (x) { return x.inten <= 40; });
        var big = weekend.length && weekend.some(function (x) { return x.inten >= 68; });
        if (jeju) { note.hidden = true; }
        else if (calm) { note.innerHTML = '이번 주말은 <b>조금</b> 무렵이라 물이 적게 빠집니다. 해루질보다는 <b>낚시</b>가 낫습니다.'; note.hidden = false; }
        else if (big) { note.innerHTML = '이번 주말은 <b>사리</b> 무렵이라 물이 많이 빠집니다. 가족 해루질하기 좋은 주말이에요.'; note.hidden = false; }
        else note.hidden = true;
      }
    }
    function week(d0, jeju) {
      var rows = [];
      for (var i = 0; i < 7; i++) {
        var d = new Date(d0); d.setDate(d.getDate() + i);
        var m = T.calcMuldae(d), inten = T.calcIntensity(m);
        rows.push({ d: d, m: m, inten: inten, h: Math.max(8, Math.round(inten * 0.92)) });
      }
      var pick = rows.reduce(function (a, b) { return (jeju ? b.inten < a.inten : b.inten > a.inten) ? b : a; });
      pick.best = true;
      rows.forEach(function (x) { if (!x.best && (jeju ? x.inten <= 32 : x.inten >= 68)) x.good = true; });
      var i = rows.indexOf(pick);
      $('tpTitle').innerHTML = jeju ? '낚시는 물살이 약한 <em>' + dayWord(pick.d, i) + '</em>이 편해요'
                                    : '물이 가장 많이 빠지는 날은 <em>' + dayWord(pick.d, i) + '</em>이에요';
      $('tpLead').textContent = (pick.d.getMonth() + 1) + '월 ' + pick.d.getDate() + '일 · ' + pick.m + '물 · 음력으로 계산한 물때입니다';
      $('tpBasis').textContent = '물때 계산 기준';
      drawWeek(rows, jeju, false);
    }
    function plan(data, s, r, d0) {
      if (!data || !data.days || !data.days.length || !$('tsWeek')) return;
      var jeju = !!r.jeju, c = T.coords[s] || [r.lat, r.lng], rows = [];
      for (var i = 0; i < 7; i++) {
        var d = new Date(d0); d.setDate(d.getDate() + i);
        var key = (d.getMonth() + 1) + '/' + d.getDate();
        var day = data.days.filter(function (x) { return x.date === key; })[0];
        var sun = T.sunTimes(d, c[0], c[1]);
        var a = sun ? toMin(sun.rise) + 60 : 420, b = sun ? toMin(sun.set) - 60 : 1020, low = null;
        ((day && day.events) || []).forEach(function (e) {
          if (e.type !== '간조' || e.level == null || e.level === '') return;
          var t = toMin(e.time); if (t < a || t > b) return;
          if (!low || +e.level < low.level) low = { time: e.time, level: +e.level };
        });
        var m = T.calcMuldae(d);
        rows.push({ d: d, m: m, inten: T.calcIntensity(m), low: low });
      }
      var lv = rows.filter(function (x) { return x.low; }).map(function (x) { return x.low.level; });
      if (lv.length < 3) return;                    // 자료가 모자라면 계산값 그대로 둔다
      var mx = Math.max.apply(null, lv), mn = Math.min.apply(null, lv), span = Math.max(1, mx - mn);
      rows.forEach(function (x) { x.h = x.low ? Math.round(18 + (mx - x.low.level) / span * 76) : 6; });
      if (jeju) {                                   // 제주는 해루질을 권하지 않으므로 물살 약한 날(조금)을 고른다
        week(d0, true);
        rows.forEach(function (x) { x.best = false; x.good = x.inten <= 32; });
        var calm = rows.reduce(function (p, q) { return q.inten < p.inten ? q : p; }); calm.best = true; calm.good = false;
        drawWeek(rows, true, true);
        $('tpBasis').textContent = '막대: 낮 간조 기준';
        return;
      }
      var best = rows.filter(function (x) { return x.low; }).reduce(function (p, q) { return q.low.level < p.low.level ? q : p; });
      best.best = true;
      rows.forEach(function (x) { if (!x.best && x.low && x.low.level <= mn + span * 0.35) x.good = true; });
      var bi = rows.indexOf(best);
      $('tpTitle').innerHTML = '해루질은 <em>' + dayWord(best.d, bi) + '</em>이 가장 좋아요';
      $('tpLead').innerHTML = '<b>' + (best.d.getMonth() + 1) + '월 ' + best.d.getDate() + '일 ' + hmText(best.low.time) + ' 간조</b> · 이번 주 낮 시간에 물이 가장 많이 빠집니다';
      $('tpBasis').textContent = '낮 간조 기준 · ' + (data.point || r.name);
      drawWeek(rows, false, true);
    }
    // ---------- 다음 간조까지 남은 시간 ----------
    var nextTimer = null;
    function nextLow(data) {
      var box = $('tsNext'); if (!box || !data || !data.days) return;
      function paint() {
        var now = kst(), nowMin = now.getHours() * 60 + now.getMinutes(), found = null;
        for (var i = 0; i < Math.min(2, data.days.length) && !found; i++) {
          (data.days[i].events || []).some(function (e) {
            if (e.type !== '간조') return false;
            var t = toMin(e.time) + i * 1440;
            if (t >= nowMin - 40) { found = { time: e.time, diff: t - nowMin, tomorrow: i === 1 }; return true; }
            return false;
          });
        }
        if (!found) { box.hidden = true; return; }
        $('tsNextTime').textContent = (found.tomorrow ? '내일 ' : '') + found.time;
        var st = $('stTide'); if (st) st.textContent = (found.tomorrow ? '내일 ' : '') + '간조 ' + found.time;   // 여섯 걸음 04 칸
        if (found.diff <= 30) { $('tsNextLab').textContent = '지금은'; $('tsNextIn').textContent = found.diff < -10 ? '간조가 막 지났어요' : '간조 무렵이에요'; }
        else {
          var h = Math.floor(found.diff / 60), mm = found.diff % 60;
          $('tsNextLab').textContent = '지금부터';
          $('tsNextIn').textContent = (h ? h + '시간 ' : '') + (mm ? mm + '분' : '') + ' 뒤';
        }
        box.hidden = false;
      }
      paint();
      clearInterval(nextTimer); nextTimer = setInterval(paint, 60000);
    }
    select(slug, false);
  })();

  /* ---------- 홈 화면에 추가 안내 (휴대폰에서만, 닫으면 다시 안 보임) ---------- */
  (function install() {
    var box = $('tsInstall'); if (!box) return;
    var ua = navigator.userAgent || '';
    var standalone = (window.matchMedia && matchMedia('(display-mode: standalone)').matches) || navigator.standalone;
    if (standalone || store('bdg-install-off') || !/Mobi|Android|iPhone|iPad/i.test(ua)) return;
    var deferred = null;
    window.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); deferred = e; });
    var inApp = /NAVER|KAKAOTALK|Instagram|FBAN|FBAV|Line\/|DaumApps/i.test(ua);
    var ios = /iPhone|iPad|iPod/i.test(ua), samsung = /SamsungBrowser/i.test(ua);
    var steps = inApp ? ['지금은 앱 안에서 열린 화면이라 홈 화면에 추가할 수 없어요.', '화면 구석의 ⋮ 또는 ⋯ 메뉴에서 <b>다른 브라우저로 열기</b>를 누르세요.', '열린 브라우저에서 이 안내를 다시 눌러 주세요.']
      : ios ? ['사파리 아래쪽의 <b>공유 버튼</b>(네모에 위 화살표)을 누릅니다.', '목록을 올려 <b>홈 화면에 추가</b>를 누릅니다.', '오른쪽 위 <b>추가</b>를 누르면 끝입니다.']
      : samsung ? ['아래쪽 <b>≡ 메뉴</b>를 누릅니다.', '<b>현재 페이지 추가</b> → <b>홈 화면</b>을 고릅니다.', '<b>추가</b>를 누르면 끝입니다.']
      : ['오른쪽 위 <b>⋮ 메뉴</b>를 누릅니다.', '<b>홈 화면에 추가</b>(또는 앱 설치)를 누릅니다.', '<b>추가</b>를 누르면 끝입니다.'];
    box.hidden = false;
    var how = $('tsHowto');
    $('tsInstallGo').addEventListener('click', function () {
      if (deferred) { deferred.prompt(); deferred.userChoice.then(function (c) { if (c && c.outcome === 'accepted') { store('bdg-install-off', '1'); box.hidden = true; } }); deferred = null; return; }
      $('tsHowtoSteps').innerHTML = steps.map(function (t) { return '<li>' + t + '</li>'; }).join('');
      how.hidden = false; $('tsHowtoClose').focus();
    });
    function closeHow() { how.hidden = true; }
    $('tsHowtoClose').addEventListener('click', closeHow);
    how.addEventListener('click', function (e) { if (e.target === how) closeHow(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !how.hidden) closeHow(); });
    $('tsInstallX').addEventListener('click', function () { store('bdg-install-off', '1'); box.hidden = true; });
  })();

  /* ---------- ③ 권역 카드 개수 + 지도 ---------- */
  (function regions() {
    [].forEach.call(document.querySelectorAll('.rc-count'), function (n) {
      var r = R[n.getAttribute('data-r')]; if (!r) return;
      n.appendChild(el('span', null, '낚시 ' + r.fishing)); n.appendChild(el('span', null, '해루질 ' + r.gleaning));
    });
    var layout = $('hrLayout'), mapBox = $('hrMap');
    var key = (window.BADAGAJA_MAP || {}).kakaoJsKey;
    if (!mapBox || !key) { layout && layout.classList.add('no-map'); return; }
    var cards = {}; [].forEach.call(document.querySelectorAll('.rc'), function (c) { cards[c.getAttribute('data-slug')] = c; });
    var LEFT = ['sinan', 'muan', 'jindo', 'haenam', 'gangjin'];   // 이웃 권역과 겹치지 않게 이름표를 왼쪽에 둠
    var started = false;
    function start() {
      if (started) return; started = true;
      var s = document.createElement('script');
      s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=' + encodeURIComponent(key);
      s.onload = function () { try { kakao.maps.load(init); } catch (e) { layout.classList.add('no-map'); } };
      s.onerror = function () { layout.classList.add('no-map'); };
      document.head.appendChild(s);
    }
    function init() {
      var map = new kakao.maps.Map(mapBox, { center: new kakao.maps.LatLng(34.72, 126.95), level: 11 });
      // PC 는 마우스 휠로 확대·축소. 휴대폰도 두 손가락으로 확대됩니다 — 다만 처음 크기에서는
      // 지도를 끌 수 없게 두어 한 손가락으로 쓸면 쪽이 그대로 스크롤됩니다 (2026-09-23 주인 지시)
      var wheelOk = window.matchMedia('(min-width:1081px) and (hover:hover) and (pointer:fine)').matches;
      map.setZoomable(true);
      map.setDraggable(wheelOk);
      if (!wheelOk) {
        kakao.maps.event.addListener(map, 'zoom_changed', function () {
          map.setDraggable(map.getLevel() < 11);
        });
      }
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      var bounds = new kakao.maps.LatLngBounds(), pins = {};
      ORDER.forEach(function (r) {
        var pos = new kakao.maps.LatLng(r.lat, r.lng);
        var a = el('a', 'hr-pin' + (LEFT.indexOf(r.slug) > -1 ? ' left' : '')); a.href = r.slug + '.html'; a.style.setProperty('--c', r.color);
        a.title = r.name + ' 포인트 ' + (r.fishing + r.gleaning) + '곳';
        a.appendChild(el('i', 'dot')); var lb = el('span', 'lb', r.name + ' '); lb.appendChild(el('em', null, String(r.fishing + r.gleaning))); a.appendChild(lb);
        a.addEventListener('mouseenter', function () { hl(r.slug, true); });
        a.addEventListener('mouseleave', function () { hl(r.slug, false); });
        pins[r.slug] = a;
        new kakao.maps.CustomOverlay({ position: pos, content: a, yAnchor: .5, zIndex: 3 }).setMap(map);
        bounds.extend(pos);
      });
      function fit() { map.relayout(); map.setBounds(bounds, 30, 40, 30, 40); }
      fit(); setTimeout(fit, 400);
      window.addEventListener('resize', function () { clearTimeout(fit.t); fit.t = setTimeout(fit, 250); });
      function hl(s, on) { cards[s] && cards[s].classList.toggle('on', on); pins[s] && pins[s].classList.toggle('on', on); }
      Object.keys(cards).forEach(function (s) {
        cards[s].addEventListener('mouseenter', function () { hl(s, true); });
        cards[s].addEventListener('mouseleave', function () { hl(s, false); });
      });
    }
    if ('IntersectionObserver' in window) {
      var io = new IntersectionObserver(function (es) { if (es.some(function (e) { return e.isIntersecting; })) { io.disconnect(); start(); } }, { rootMargin: '400px' });
      io.observe(mapBox);
    } else start();
  })();

  /* ---------- ④ 이달의 제철·축제 ---------- */
  (function season() {
    if (!$('ssCatch')) return;
    var month = NOW.getMonth() + 1;
    var SYN = { '학공치': '학꽁치', '굴/석화': '굴', '석화굴': '굴', '자연산굴': '굴', '강굴': '굴', '벚굴': '벚굴', '뻘낙지': '낙지', '세발낙지': '낙지', '낙지(세발낙지)': '낙지', '물김': '김', '참꼬막': '꼬막', '새꼬막': '꼬막' };
    function base(n) { var k = n.replace(/\(.*?\)/g, '').replace(/\s/g, ''); return SYN[k] || SYN[n.replace(/\s/g, '')] || k; }
    function render() {
      var prev = (month + 10) % 12 + 1, next = month % 12 + 1;
      $('ssMonth').textContent = month + '월';
      $('ssPrev').setAttribute('aria-label', prev + '월 보기'); $('ssNext').setAttribute('aria-label', next + '월 보기');
      $('ssTitle').textContent = month + '월, 지금 ' + (SITE_JEJU ? '제주' : (SITE_ALL ? '전국' : '남도')) + ' 바다에서는';
      // 제철 (연중 제외)
      var groups = {};
      D.catch.forEach(function (c) {
        if (!c.m || c.m.length >= 12 || c.m.indexOf(month) < 0) return;
        var k = base(c.n);
        if (!groups[k]) groups[k] = { n: k, items: [], isNew: false };
        groups[k].items.push(c);
      });
      // NEW: 지난달에는 어느 권역에서도 제철이 아니었다가 이달 시작되는 것만
      var prevM = (month + 10) % 12 + 1;
      Object.keys(groups).forEach(function (k) {
        groups[k].isNew = groups[k].items.every(function (c) { return c.m.indexOf(prevM) < 0; });
      });
      var list = Object.keys(groups).map(function (k) { return groups[k]; }).sort(function (a, b) { return b.items.length - a.items.length || a.n.localeCompare(b.n, 'ko'); });
      var box = $('ssCatch'); box.innerHTML = ''; $('ssDetail').hidden = true;
      $('ssCatchCount').textContent = list.length + '종';
      if (!list.length) box.appendChild(el('p', 'ss-empty', '이 달에 표시할 제철 정보가 없어요.'));
      var LIMIT = 18, moreBtn = null;
      list.forEach(function (g, idx) {
        var regs = []; g.items.forEach(function (c) { if (regs.indexOf(c.r) < 0) regs.push(c.r); });
        var b = el('button', 'ss-chip' + (g.isNew ? ' new' : '')); b.type = 'button'; b.setAttribute('aria-expanded', 'false');
        if (idx >= LIMIT) b.hidden = true;
        // "13곳" 같은 숫자는 칩에서 빼고(2026-09-22 주인 — 공간을 넓게) 마우스를 올리면 보이게
        b.appendChild(document.createTextNode(g.n));
        b.title = regs.length + '개 권역' + (g.isNew ? ' · ' + month + '월부터 제철 시작' : '');
        b.addEventListener('click', function () { detail(g, b); });
        box.appendChild(b);
      });
      if (list.length > LIMIT) {
        moreBtn = el('button', 'ss-more', '나머지 ' + (list.length - LIMIT) + '종 더 보기'); moreBtn.type = 'button';
        moreBtn.addEventListener('click', function () { [].forEach.call(box.querySelectorAll('.ss-chip[hidden]'), function (x) { x.hidden = false; }); moreBtn.remove(); });
        box.appendChild(moreBtn);
      }
      // 축제: 한국관광공사 실제 일정(있으면 먼저) + 권역 페이지의 월별 대표 축제
      var y = NOW.getFullYear() + ((month < NOW.getMonth() + 1) ? 1 : 0);
      var mStart = new Date(y, month - 1, 1), mEnd = new Date(y, month, 0);
      var today0 = new Date(NOW.getFullYear(), NOW.getMonth(), NOW.getDate());
      var real = REAL_FEST.filter(function (x) { var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00'); return R[x.region] && s <= mEnd && e >= mStart && e >= today0 && (e - s) / 86400000 <= 60; });
      var key = function (n) { return n.replace(/20\d\d/g, '').replace(/[\s\d·()]/g, ''); };
      // 실제 일정에 이름이 있는 축제는(이미 끝났어도) 월별 '예정' 목록에서 뺌
      var realKeys = REAL_FEST.map(function (x) { return key(x.name); }).filter(function (k) { return k.length >= 2; });
      var fests = D.festivals.filter(function (f) { return f.m === month && !realKeys.some(function (k) { return k.indexOf(key(f.n)) > -1 || key(f.n).indexOf(k) > -1; }); }).sort(function (a, b) { return R[a.r].no - R[b.r].no; });
      // 오늘의 바다에서 고른 권역(예: 보성)의 축제를 맨 앞으로 — '보성인데 여수 축제가 먼저 나온다'는 지적 (2026-09-20)
      var mine = TODAY_SLUG && R[TODAY_SLUG] ? TODAY_SLUG : null;
      if (mine) {
        var first = function (a, b) { return (b.region === mine || b.r === mine) - (a.region === mine || a.r === mine); };
        real = real.slice().sort(first); fests = fests.slice().sort(first);
      }
      var fb = $('ssFest'); fb.innerHTML = ''; $('ssFestCount').textContent = (real.length + fests.length) ? (real.length + fests.length) + '개' : '';   // 0개는 숫자를 감춤 (2026-09-24)
      if (mine && (real.length || fests.length) && !real.some(function (x) { return x.region === mine; }) && !fests.some(function (f) { return f.r === mine; }))
        fb.appendChild(el('p', 'ss-empty', rname(mine) + '에는 ' + month + '월 축제가 없어요. 가까운 전남 축제를 보여 드려요.'));
      if (!real.length && !fests.length) fb.appendChild(el('p', 'ss-empty', month + '월에는 등록된 축제가 없어요. 다음 달을 확인해 보세요.'));
      var FLIMIT = 4, idx = 0;
      real.forEach(function (x) {
        var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00'), dd = Math.round((s - today0) / 86400000);
        var a = el('a', 'ss-fest real'); a.href = x.region + '.html#festival'; a.style.setProperty('--c', R[x.region].color);
        var top = el('span', 'r', rname(x.region) + ' · ' + (s.getMonth() + 1) + '.' + s.getDate() + '~' + (e.getMonth() + 1) + '.' + e.getDate());
        top.appendChild(el('em', dd <= 0 ? 'now' : '', dd <= 0 ? '진행 중' : 'D-' + dd)); a.appendChild(top);
        a.appendChild(el('b', null, x.name)); a.appendChild(el('span', null, (x.addr || '').replace(/^전남광주통합특별시\s*|^전라남도\s*/, '')));
        if (idx++ >= FLIMIT) a.hidden = true;
        fb.appendChild(a);
      });
      fests.forEach(function (f) {
        var a = el('a', 'ss-fest'); a.href = f.r + '.html#festival'; a.style.setProperty('--c', R[f.r].color);
        a.appendChild(el('span', 'r', rname(f.r) + ' · ' + month + '월 예정')); a.appendChild(el('b', null, f.n)); a.appendChild(el('span', null, f.d));
        if (idx++ >= FLIMIT) a.hidden = true;
        fb.appendChild(a);
      });
      fests = real.concat(fests);
      if (fests.length > FLIMIT) {
        var fm = el('button', 'ss-more', '축제 ' + (fests.length - FLIMIT) + '개 더 보기'); fm.type = 'button';
        fm.addEventListener('click', function () { [].forEach.call(fb.querySelectorAll('.ss-fest[hidden]'), function (x) { x.hidden = false; }); fm.remove(); });
        fb.appendChild(fm);
      }
    }
    function detail(g, btn) {
      var d = $('ssDetail'), open = btn.getAttribute('aria-expanded') === 'true';
      [].forEach.call($('ssCatch').children, function (x) { x.setAttribute && x.setAttribute('aria-expanded', 'false'); });
      if (open) { d.hidden = true; return; }
      btn.setAttribute('aria-expanded', 'true');
      d.innerHTML = ''; d.appendChild(el('h4', null, g.n + ' — 만날 수 있는 권역'));
      var ul = el('ul');
      g.items.sort(function (a, b) { return R[a.r].no - R[b.r].no; }).forEach(function (c) {
        var li = el('li'), a = el('a'); a.href = c.r + '.html#catch'; a.style.setProperty('--c', R[c.r].color);
        a.appendChild(el('b', null, rname(c.r))); a.appendChild(el('span', null, c.s + ' · ' + c.d));
        li.appendChild(a); ul.appendChild(li);
      });
      d.appendChild(ul); d.hidden = false;
    }
    $('ssPrev').addEventListener('click', function () { month = (month + 10) % 12 + 1; render(); });
    $('ssNext').addEventListener('click', function () { month = month % 12 + 1; render(); });
    var REAL_FEST = [];
    render();
    onRegion.push(render);
    fetch('api/tour.php?kind=festival&group=all').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      if (!d || !d.ok || !d.items) return;
      d.items = d.items.filter(function (x) { var r = R[x.region]; return r && (SITE_ALL || !!r.jeju === SITE_JEJU); });   // 이 화면(남도/제주/전국) 권역만
      REAL_FEST = d.items; render();
      if (SITE_ALL && $('statFest') && d.items.length) $('statFest').textContent = d.items.length;   // 전국 첫 화면: 관광공사 실시간 축제 수
      festBadges(d.items);
    }).catch(function () {});
  })();

  /* 권역 사진 카드: 진행 중이거나 30일 안에 시작하는 실제 축제 배지 */
  function festBadges(items) {
    var today0 = new Date(NOW.getFullYear(), NOW.getMonth(), NOW.getDate()), best = {};
    items.forEach(function (x) {
      var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00'), dd = Math.round((s - today0) / 86400000);
      if (e < today0 || dd > 30 || !R[x.region]) return;
      if ((e - s) / 86400000 > 60) return;   // '섬 방문의 해'처럼 연중 행사는 배지에서 제외
      if (!best[x.region] || dd < best[x.region].dd) best[x.region] = { dd: dd, x: x };
    });
    Object.keys(best).forEach(function (slug) {
      var card = document.querySelector('.rc[data-slug="' + slug + '"]'); if (!card) return;
      var b = best[slug], badge = el('span', 'rc-fest' + (b.dd <= 0 ? ' now' : ''), '🎉 ' + (b.dd <= 0 ? '축제 진행 중' : '축제 D-' + b.dd));
      badge.title = b.x.name; card.appendChild(badge);
    });
  }

  /* 첫 화면 숫자 네 칸은 위 stats()에서 자료를 세어 넣는다 (예전에는 마지막 칸만 숙소 수로 덮어썼다) */

  /* ---------- ⑤ 동행별 추천 코스 ---------- */
  (function courses() {
    var track = $('hcTrack');
    if (!track) return;
    var tabs = document.querySelectorAll('.hc-tabs button');
    var prevB = document.querySelector('.hc-arrow.prev'), nextB = document.querySelector('.hc-arrow.next');
    function render(k) {
      [].forEach.call(tabs, function (t) { t.setAttribute('aria-selected', t.dataset.k === k ? 'true' : 'false'); });
      track.innerHTML = '';
      D.courses.filter(function (c) { return c.k === k; }).sort(function (a, b) { return R[a.r].no - R[b.r].no; }).forEach(function (c) {
        var r = R[c.r], a = el('a', 'hc-card'); a.href = c.r + '.html#course'; a.style.setProperty('--c', r.color);
        var ph = el('div', 'ph' + (r.photo ? '' : ' noph')); if (r.photo) ph.dataset.bg = r.photo; ph.appendChild(el('span', null, rname(c.r))); a.appendChild(ph);
        var bd = el('div', 'bd'); bd.appendChild(el('h3', null, c.t));
        var ol = el('ol'); (c.s || []).forEach(function (s) { var li = el('li'); li.appendChild(el('b', null, s[0])); li.appendChild(el('span', null, s[1])); ol.appendChild(li); });
        bd.appendChild(ol); bd.appendChild(el('span', 'go', rname(c.r) + ' 권역 자세히 →')); a.appendChild(bd);
        track.appendChild(a);
      });
      track.scrollLeft = 0; lazy(); arrows();
    }
    function lazy() {
      var w = track.getBoundingClientRect();
      [].forEach.call(track.querySelectorAll('.ph[data-bg]'), function (p) {
        var b = p.getBoundingClientRect();
        if (b.left < w.right + w.width && b.bottom > -200 && b.top < innerHeight + 600) { p.style.backgroundImage = "url('" + p.dataset.bg + "')"; p.removeAttribute('data-bg'); }
      });
    }
    function arrows() {
      if (!prevB) return;
      prevB.disabled = track.scrollLeft < 10;
      nextB.disabled = track.scrollLeft + track.clientWidth >= track.scrollWidth - 10;
    }
    [].forEach.call(tabs, function (t) { t.addEventListener('click', function () { render(t.dataset.k); }); });
    track.addEventListener('scroll', function () { lazy(); arrows(); }, { passive: true });
    window.addEventListener('scroll', lazy, { passive: true });
    if (prevB) {
      prevB.addEventListener('click', function () { track.scrollBy({ left: -track.clientWidth * 0.9, behavior: 'smooth' }); });
      nextB.addEventListener('click', function () { track.scrollBy({ left: track.clientWidth * 0.9, behavior: 'smooth' }); });
    }
    render('couple');
  })();
})();
