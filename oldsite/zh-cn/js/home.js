/* 바다가자 중국어(간체) 메인페이지 — 관광 + 한국 거주 중국인(유학생) 해루질·낚시 정보
 * 원본 js/home.js를 바탕으로 권역·축제·제철 먹거리·코스 + 포인트 검색(이름은 한국어 유지)
 * 데이터: zh-cn/js/home-data.js (zh-cn/build-zh-data.ps1로 생성), 물때 계산: zh-cn/js/app.js의 BADAGAJA_TIDE
 */
(function () {
  var D = window.BADAGAJA_HOME;
  if (!D) return;
  var T = window.BADAGAJA_TIDE || null;
  var R = {}; D.regions.forEach(function (r) { R[r.slug] = r; });
  var ORDER = D.regions.slice().sort(function (a, b) { return a.no - b.no; });
  // 제목·카드에는 행정구역을 붙여 중국 지명(海南省·长兴县 등)과 구별: 海南郡, 木浦市
  var ADM_SFX = { mokpo: "市", yeosu: "市", suncheon: "市", gwangyang: "市" };
  function adm(r) { return (r.coast || r.jeju) ? r.name : r.name + (ADM_SFX[r.slug] || "郡"); }
  // 전국 첫 화면(zh-cn/index.html, data-site="all") — 전남 15·제주 7·확대 권역 35를 묶음별로 (2026-09-20)
  var SITE_ALL = document.body.getAttribute('data-site') === 'all';
  var GROUP_ORDER = ['济州', '釜山·蔚山', '江原', '全南', '庆南', '忠南', '庆北', '仁川·京畿', '全北'];
  var ZN = window.BADAGAJA_COAST_ZH || {}, KC = window.BADAGAJA_COAST || {};
  var COASTS = Object.keys(ZN).map(function (s, i) {
    var z = ZN[s], k = KC[s] || {};
    return { slug: s, name: z.n, tag: z.g + ' ' + z.n, color: z.c || '#2F5D57', lat: k.lat, lng: k.lng, fishing: 0, gleaning: 0, photo: '', coast: !z.jeju, jeju: !!z.jeju, group: z.g, no: 100 + i };
  });
  var JEJU_COORD = { jejusi: [33.51, 126.52], aewol: [33.46, 126.33], jocheon: [33.54, 126.72], seongsan: [33.46, 126.93], seogwipo: [33.25, 126.56], daejeong: [33.22, 126.25], chuja: [33.96, 126.30] };
  if (SITE_ALL) {
    D.regions.forEach(function (r) { r.group = '全南'; });
    COASTS.forEach(function (r) { if (!r.lat && JEJU_COORD[r.slug]) { r.lat = JEJU_COORD[r.slug][0]; r.lng = JEJU_COORD[r.slug][1]; } R[r.slug] = r; });
    var PHOTO = { seongsan: 'img/jeju/photo/home-hero.jpg?v=951142953', busaneast: 'img/coast/busaneast-hero.jpg?v=2390918060', gangneung: 'img/coast/gangneung-hero.jpg?v=1162090535', tongyeong: 'img/coast/tongyeong-hero.jpg?v=2175099577', taean: 'img/coast/taean-hero.jpg?v=3125325243', pohang: 'img/coast/pohang-hero.jpg?v=1113267983', ganghwa: 'img/coast/ganghwa-hero.jpg?v=1780335185', gunsan: 'img/coast/gunsan-hero.jpg?v=4230525424', sokcho: 'img/coast/sokcho-hero.jpg?v=2457212343', namhae: 'img/coast/namhae-hero.jpg?v=3926067475' };
    Object.keys(PHOTO).forEach(function (k) { if (R[k]) R[k].photo = PHOTO[k]; });
    var all = COASTS.concat(ORDER); ORDER = [];
    GROUP_ORDER.forEach(function (g) { all.filter(function (r) { return r.group === g; }).forEach(function (r) { ORDER.push(r); }); });
  }

  // 권역 페이지 주소: 중국어 권역 페이지(zh-cn/<권역>.html, build-zh-regions.ps1로 생성)로 연결
  var ZH_REGION_PAGES = true;
  function page(slug, hash) { return (ZH_REGION_PAGES ? '' : '../') + slug + '.html' + (hash || ''); }
  function photo(p) { return '../' + p; }

  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function store(k, v) { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } }
  function norm(s) { return (s || '').replace(/\(.*?\)/g, '').replace(/[\s·\-（）]/g, '').toLowerCase(); }
  function kst() { return new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000); }
  var NOW = kst();
  var DAY = ['日', '一', '二', '三', '四', '五', '六'];

  // 서버가 한국어로 주는 값 → 간체
  var WEATHER = { '맑음': '晴', '구름많음': '多云', '흐림': '阴', '비': '雨', '비/눈': '雨夹雪', '눈': '雪', '소나기': '阵雨', '빗방울': '毛毛雨', '빗방울눈날림': '雨雪纷飞', '눈날림': '飘雪' };
  var GRADE = { '매우좋음': '非常适合', '좋음': '适合', '보통': '普通', '나쁨': '不太适合', '매우나쁨': '不适合' };
  var FISH = { '돌돔': '石鲷', '감성돔': '黑鲷', '참돔': '真鲷', '농어': '海鲈鱼', '우럭': '黑鲪', '볼락': '平鲉', '넙치': '牙鲆', '갈치': '带鱼', '벵에돔': '黑毛', '고등어': '青花鱼', '전갱이': '竹荚鱼', '숭어': '鲻鱼', '노래미': '斑头鱼', '기타어종': '其他鱼种' };
  // 음력 날짜(农历八月十四) — 중국 해안에서도 음력으로 물때를 말함
  function lunar(d) { var s = lunarCn(d); return s ? '农历' + s : ''; }
  function lunarCn(date){
    var CN = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
    function dayCn(n){ return n <= 10 ? '初' + CN[n] : n < 20 ? '十' + CN[n - 10] : n === 20 ? '二十' : n < 30 ? '廿' + CN[n - 20] : '三十'; }
    try {
      var mo = '', dy = '';
      new Intl.DateTimeFormat('zh-CN-u-ca-chinese', { month: 'long', day: 'numeric' }).formatToParts(date).forEach(function(p){ if (p.type === 'month') mo = p.value; if (p.type === 'day') dy = p.value; });
      var n = parseInt(dy, 10);
      return mo + (isNaN(n) ? dy : dayCn(n));
    } catch (e) { return ''; }
  }
  function when(w) { return (w || '').replace('오늘', '今天').replace('내일', '明天').replace('모레', '后天').replace('오전', '上午').replace('오후', '下午').replace(/\s+/g, ''); }
  function tideType(t) { return t === '만조' ? '满潮' : t === '간조' ? '干潮' : t; }

  /* ---------- ① 사진 슬라이드 ---------- */
  (function slides() {
    var box = $('hSlides'), cap = $('hCaption');
    if (!box) return;
    var HERO = SITE_ALL
      ? ['seongsan', 'busaneast', 'gangneung', 'boseong', 'tongyeong', 'taean', 'pohang', 'ganghwa', 'jindo', 'gunsan', 'sokcho', 'namhae']
      : ['boseong', 'jindo', 'sinan', 'goheung', 'muan', 'haenam', 'gwangyang', 'hampyeong', 'mokpo', 'suncheon', 'yeonggwang'];
    var list = HERO.map(function (s) { return R[s]; }).filter(Boolean);
    var nodes = [box.firstElementChild], cur = 0;
    for (var i = 1; i < list.length; i++) { var s = el('div', 'h-slide'); box.appendChild(s); nodes.push(s); }
    function load(i) { var n = nodes[i]; if (!n.style.backgroundImage) n.style.backgroundImage = "url('" + photo(list[i].photo) + "')"; }
    function show(i) {
      load(i); load((i + 1) % list.length);
      nodes[cur].classList.remove('on'); nodes[i].classList.add('on'); cur = i;
      if (cap) { cap.textContent = (list[i].jeju ? '济州 ' : '') + adm(list[i]); cap.href = page(list[i].slug); }
    }
    if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    setInterval(function () { if (!document.hidden) show((cur + 1) % list.length); }, 6500);
    window.addEventListener('load', function () { load(1); });
  })();

  /* ---------- ① 통합 검색: 지역 · 축제 · 제철 먹거리 · 코스 ---------- */
  (function search() {
    var input = $('hSearch'), out = $('hResults');
    if (!input) return;
    var species = {};
    D.catch.forEach(function (c) {
      var k = c.g; if (!species[k]) species[k] = { n: c.g, hay: '', regions: [] };
      species[k].hay += c.n + (c.std || '') + c.ko;
      if (species[k].regions.indexOf(c.r) < 0) species[k].regions.push(c.r);
    });
    var sel = -1;
    function regionOfToken(t) {
      for (var i = 0; i < ORDER.length; i++) { var r = ORDER[i]; if (t === r.name || t === r.name + '郡' || t === r.name + '市' || ((r.coast || r.jeju) && (t === r.group || r.name.split('·').indexOf(t) > -1))) return r.slug; }
      return null;
    }
    function has(hay, rest) { hay = norm(hay); return rest.every(function (t) { return hay.indexOf(t) > -1; }); }
    function run() {
      var q = input.value.trim();
      out.innerHTML = ''; sel = -1;
      if (!q) { out.hidden = true; input.setAttribute('aria-expanded', 'false'); return; }
      var toks = q.split(/\s+/), rFilter = null, rest = [];
      toks.forEach(function (t) { var s = regionOfToken(t); if (s) rFilter = s; else rest.push(norm(t)); });
      var groups = [];
      var regs = ORDER.filter(function (r) { return (rFilter === r.slug && !rest.length) || (rest.length && has(r.name + r.tag, rest)); });
      if (regs.length) groups.push(['地区', regs.slice(0, 4).map(function (r) { return { href: page(r.slug), tag: '地区', text: r.name, meta: r.tag }; })]);
      var fests = D.festivals.filter(function (f) { return (!rFilter || f.r === rFilter) && (rest.length ? has(f.n + f.d, rest) : !!rFilter); });
      if (fests.length) groups.push(['节庆', fests.slice(0, 5).map(function (f) { return { href: page(f.r, '#festival'), tag: f.m + '月', text: f.n, meta: R[f.r].name }; })]);
      if (rest.length) {
        var sp = Object.keys(species).map(function (k) { return species[k]; }).filter(function (s) { return has(s.n + s.hay, rest) && (!rFilter || s.regions.indexOf(rFilter) > -1); });
        if (sp.length) groups.push(['当季海鲜', sp.slice(0, 4).map(function (s) {
          var rs = rFilter ? [rFilter] : s.regions;
          return { href: page(rs[0], '#catch'), tag: '当季', text: s.n, meta: rs.map(function (x) { return R[x].name; }).slice(0, 4).join('·') + (rs.length > 4 ? ' 等' : '') };
        })]);
        var cs = D.courses.filter(function (c) { return (!rFilter || c.r === rFilter) && has(c.t + (c.s || []).map(function (x) { return x[1]; }).join(''), rest); });
        if (cs.length) groups.push(['旅游行程', cs.slice(0, 4).map(function (c) { return { href: page(c.r, '#course'), tag: '行程', text: c.t, meta: R[c.r].name + ' · ' + c.l }; })]);
      }
      // 교통: 역·터미널·공항 이름으로 권역 교통 안내 찾기 (권역 페이지 #access 섹션과 같은 내용)
      var ACCESS_KW = { sinan: '木浦站 木浦综合巴士站 木浦沿岸客运码头 渡轮 码头', muan: '木浦站 务安国际机场 机场 务安巴士站', mokpo: '木浦站 KTX 木浦综合巴士站 木浦沿岸客运码头 渡轮', yeonggwang: '灵光综合巴士站 光州松汀站 KTX', hampyeong: '咸平站 火车 咸平巴士站 光州松汀站', jindo: '珍岛公用巴士站 木浦站', haenam: '海南综合巴士站 木浦站', wando: '莞岛公用巴士站 莞岛沿岸客运码头 渡轮 光州综合巴士站', gangjin: '康津巴士站 光州综合巴士站', jangheung: '长兴公用巴士站 光州综合巴士站', boseong: '宝城站 筏桥站 火车 宝城巴士站', goheung: '高兴公营巴士站 顺天站 鹿洞港', yeosu: '丽水世博站 KTX 丽水综合巴士站 丽水机场 机场', suncheon: '顺天站 KTX 顺天综合巴士站', gwangyang: '光阳站 顺天站 光阳巴士站' };
      if (rest.length) {
        var acc = ORDER.filter(function (r) { return (!rFilter || r.slug === rFilter) && has(ACCESS_KW[r.slug] + '交通怎么去', rest); });
        if (acc.length) groups.push(['交通', acc.slice(0, 4).map(function (r) {
          var hit = ACCESS_KW[r.slug].split(' ').filter(function (w) { return rest.some(function (t) { return norm(w).indexOf(t) > -1; }); })[0] || '车站·巴士站';
          return { href: page(r.slug, '#access'), tag: '交通', text: '怎么去' + r.name, meta: hit };
        })]);
      }
      // 해루질·낚시 포인트 (이름은 한국 지도 앱 검색용으로 한국어 그대로)
      var KIND = { f: '海钓', g: '赶海' };
      var pts = (D.points || []).filter(function (p) {
        if (rFilter && p.r !== rFilter) return false;
        if (!rest.length) return !!rFilter;
        return has(p.n + p.t + KIND[p.k] + (p.k === 'f' ? '钓鱼' : '赶海捡贝'), rest);
      });
      if (pts.length) groups.push(['赶海·海钓地点 ' + pts.length + ' 处（仅供参考，不代表允许采集）', pts.slice(0, 8).map(function (p) {
        return { href: 'point/' + p.p + '#point-' + p.i, tag: KIND[p.k], cls: p.k, text: p.n, meta: R[p.r].name + ' · ' + p.t };
      })]);
      if (!groups.length) { out.appendChild(el('div', 'empty', '找不到符合“' + q + '”的结果。请试试地区名称（例：丽水）或节庆、美食（例：烟花、牡蛎）。')); }
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
    input.addEventListener('input', run);
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

  /* ---------- 권역 카드: 赶海·海钓 지점 수 + 지도 ---------- */
  (function regions() {
    [].forEach.call(document.querySelectorAll('.rc-count'), function (n) {
      var r = R[n.getAttribute('data-r')]; if (!r) return;
      var p = n.parentNode.querySelector('p'); if (p) p.textContent = r.tag;   // 카드 설명을 번역 사전 문장과 맞춤
      n.appendChild(el('span', null, '海钓 ' + r.fishing)); n.appendChild(el('span', null, '赶海 ' + r.gleaning));
    });
    // 지도 아래 트립닷컴 광고: 권역 카드·핀에 올리면 그 권역 호텔로 링크 변경 (도시 번호는 build-zh-regions.ps1과 같음)
    var TRIP_CITY = { sinan: 128277, muan: 4012, mokpo: 3986, yeonggwang: 128263, hampyeong: 88098, jindo: 128271, haenam: 121747, wando: 88101, gangjin: 128258, jangheung: 128246, boseong: 72369, goheung: 121740, yeosu: 4016, suncheon: 61663, gwangyang: 92459 };
    var ad = $('zhMapAd'), adTitle = $('zhMapAdTitle');
    function setAd(s) {
      if (!ad || !TRIP_CITY[s] || !R[s]) return;
      ad.href = 'https://sg.trip.com/hotels/list?city=' + TRIP_CITY[s] + '&locale=zh-SG&curr=CNY&Allianceid=10551794&SID=331105566&trip_sub1=&trip_sub3=D19822014';
      adTitle.textContent = '在 Trip.com 查看' + R[s].name + '酒店';
    }
    [].forEach.call(document.querySelectorAll('.rc'), function (c) {
      var s = c.getAttribute('data-slug');
      c.addEventListener('mouseenter', function () { setAd(s); });
      c.addEventListener('focus', function () { setAd(s); });
    });
    var layout = $('hrLayout'), mapBox = $('hrMap');
    var key = (window.BADAGAJA_MAP || {}).kakaoJsKey;
    if (!mapBox || !key) { layout && layout.classList.add('no-map'); return; }
    var cards = {}; [].forEach.call(document.querySelectorAll('.rc'), function (c) { cards[c.getAttribute('data-slug')] = c; });
    var LEFT = ['sinan', 'muan', 'jindo', 'haenam', 'gangjin'];
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
      // PC 에서는 마우스 휠로 확대·축소, 휴대폰·태블릿은 쪽이 함께 밀리지 않게 그대로 둡니다 (2026-09-23 주인 지시)
      var wheelOk = window.matchMedia('(min-width:1081px) and (hover:hover) and (pointer:fine)').matches;
      map.setZoomable(wheelOk);
      map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);
      var bounds = new kakao.maps.LatLngBounds(), pins = {};
      ORDER.forEach(function (r) {
        var pos = new kakao.maps.LatLng(r.lat, r.lng);
        var a = el('a', 'hr-pin' + (LEFT.indexOf(r.slug) > -1 ? ' left' : '')); a.href = page(r.slug); a.style.setProperty('--c', r.color);
        a.title = r.name + ' 赶海·海钓地点 ' + (r.fishing + r.gleaning) + ' 处';
        a.appendChild(el('i', 'dot')); var lb = el('span', 'lb', r.name + ' '); lb.appendChild(el('em', null, String(r.fishing + r.gleaning))); a.appendChild(lb);
        a.addEventListener('mouseenter', function () { hl(r.slug, true); setAd(r.slug); });
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

  /* ---------- 이달의 축제 · 제철 먹거리 ---------- */
  (function season() {
    if (!$('ssCatch')) return;
    var month = NOW.getMonth() + 1;
    // 같은 먹거리 묶음은 어종 대조표(i18n/species.json)의 g 값으로 처리
    function base(c) { return c.g || c.n; }
    function render() {
      var prev = (month + 10) % 12 + 1, next = month % 12 + 1;
      $('ssMonth').textContent = month + '月';
      $('ssPrev').setAttribute('aria-label', prev + '月'); $('ssNext').setAttribute('aria-label', next + '月');
      $('ssTitle').textContent = month + '月，' + (SITE_ALL ? '韩国' : '全南') + '海岸正热闹';
      // 축제
      var fests = D.festivals.filter(function (f) { return f.m === month; }).sort(function (a, b) { return R[a.r].no - R[b.r].no; });
      var fb = $('ssFest'); fb.innerHTML = ''; $('ssFestCount').textContent = fests.length + ' 场';
      if (!fests.length) fb.appendChild(el('p', 'ss-empty', month + '月暂无收录的节庆，请看看下个月。'));
      var FLIMIT = 4;
      fests.forEach(function (f, idx) {
        var a = el('a', 'ss-fest'); a.href = page(f.r, '#festival'); a.style.setProperty('--c', R[f.r].color);
        a.appendChild(el('span', 'r', R[f.r].name + ' · ' + month + '月')); a.appendChild(el('b', null, f.n)); a.appendChild(el('span', null, f.d));
        if (idx >= FLIMIT) a.hidden = true;
        fb.appendChild(a);
      });
      if (fests.length > FLIMIT) {
        var fm = el('button', 'ss-more', '查看其他 ' + (fests.length - FLIMIT) + ' 场节庆'); fm.type = 'button';
        fm.addEventListener('click', function () { [].forEach.call(fb.querySelectorAll('.ss-fest[hidden]'), function (x) { x.hidden = false; }); fm.remove(); });
        fb.appendChild(fm);
      }
      // 제철 먹거리 (연중 제외)
      var groups = {};
      D.catch.forEach(function (c) {
        if (!c.m || c.m.length >= 12 || c.m.indexOf(month) < 0) return;
        var k = base(c);
        if (!groups[k]) groups[k] = { n: k, items: [], isNew: false };
        groups[k].items.push(c);
      });
      var prevM = (month + 10) % 12 + 1;
      Object.keys(groups).forEach(function (k) { groups[k].isNew = groups[k].items.every(function (c) { return c.m.indexOf(prevM) < 0; }); });
      var list = Object.keys(groups).map(function (k) { return groups[k]; }).sort(function (a, b) { return b.items.length - a.items.length; });
      var box = $('ssCatch'); box.innerHTML = ''; $('ssDetail').hidden = true;
      $('ssCatchCount').textContent = list.length + ' 种';
      if (!list.length) box.appendChild(el('p', 'ss-empty', '这个月没有可显示的当季海鲜。'));
      var LIMIT = 18;
      list.forEach(function (g, idx) {
        var regs = []; g.items.forEach(function (c) { if (regs.indexOf(c.r) < 0) regs.push(c.r); });
        var b = el('button', 'ss-chip' + (g.isNew ? ' new' : '')); b.type = 'button'; b.setAttribute('aria-expanded', 'false');
        if (idx >= LIMIT) b.hidden = true;
        b.appendChild(document.createTextNode(g.n + ' ')); b.appendChild(el('small', null, regs.length + ' 区'));
        b.title = g.items[0].ko + (g.items[0].std ? ' · ' + g.items[0].std : '');
        if (g.isNew) b.title = month + '月起进入盛产期';
        b.addEventListener('click', function () { detail(g, b); });
        box.appendChild(b);
      });
      if (list.length > LIMIT) {
        var mb = el('button', 'ss-more', '查看其他 ' + (list.length - LIMIT) + ' 种'); mb.type = 'button';
        mb.addEventListener('click', function () { [].forEach.call(box.querySelectorAll('.ss-chip[hidden]'), function (x) { x.hidden = false; }); mb.remove(); });
        box.appendChild(mb);
      }
    }
    function detail(g, btn) {
      var d = $('ssDetail'), open = btn.getAttribute('aria-expanded') === 'true';
      [].forEach.call($('ssCatch').children, function (x) { x.setAttribute && x.setAttribute('aria-expanded', 'false'); });
      if (open) { d.hidden = true; return; }
      btn.setAttribute('aria-expanded', 'true');
      var f0 = g.items[0], kos = []; g.items.forEach(function (c) { if (kos.indexOf(c.ko) < 0) kos.push(c.ko); });
      d.innerHTML = ''; d.appendChild(el('h4', null, g.n + (f0.std && f0.std !== g.n ? '（' + f0.std + '）' : '') + ' — 可以吃到的地区'));
      d.appendChild(el('p', 'ss-ko', '韩语：' + kos.join(' / ') + '　在韩国点菜、问路时可以直接出示' + (f0.note ? '　·　' + f0.note : '')));
      var ul = el('ul');
      g.items.sort(function (a, b) { return R[a.r].no - R[b.r].no; }).forEach(function (c) {
        var li = el('li'), a = el('a'); a.href = page(c.r, '#catch'); a.style.setProperty('--c', R[c.r].color);
        a.appendChild(el('b', null, R[c.r].name)); a.appendChild(el('span', null, (c.n !== g.n ? c.n + ' · ' : '') + c.s + ' · ' + c.d));
        li.appendChild(a); ul.appendChild(li);
      });
      d.appendChild(ul); d.hidden = false;
    }
    $('ssPrev').addEventListener('click', function () { month = (month + 10) % 12 + 1; render(); });
    $('ssNext').addEventListener('click', function () { month = month % 12 + 1; render(); });
    render();
    // 권역 카드 배지: 진행 중이거나 30일 안에 시작하는 실제 축제(한국관광공사 일정)
    fetch('../api/tour.php?kind=festival').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      if (!d || !d.ok || !d.items) return;
      var today0 = new Date(NOW.getFullYear(), NOW.getMonth(), NOW.getDate()), best = {};
      d.items.forEach(function (x) {
        var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00'), dd = Math.round((s - today0) / 86400000);
        if (e < today0 || dd > 30 || !R[x.region] || (e - s) / 86400000 > 60) return;
        if (!best[x.region] || dd < best[x.region].dd) best[x.region] = { dd: dd };
      });
      Object.keys(best).forEach(function (slug) {
        var card = document.querySelector('.rc[data-slug="' + slug + '"]'); if (!card) return;
        var b = best[slug];
        card.appendChild(el('span', 'rc-fest' + (b.dd <= 0 ? ' now' : ''), '🎉 ' + (b.dd <= 0 ? '节庆进行中' : '节庆 D-' + b.dd)));
      });
    }).catch(function () {});
  })();

  /* 숫자 상자: 한국관광공사 등록 숙소 수 */
  fetch('../api/tour.php?kind=count').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    if (!d || !d.ok || !d.total) return;
    var b = $('statStays'); if (b) b.textContent = d.total;
  }).catch(function () {});

  /* ---------- 동행별 추천 코스 ---------- */
  (function courses() {
    var track = $('hcTrack');
    if (!track) return;
    var tabs = document.querySelectorAll('.hc-tabs button');
    var prevB = document.querySelector('.hc-arrow.prev'), nextB = document.querySelector('.hc-arrow.next');
    function render(k) {
      [].forEach.call(tabs, function (t) { t.setAttribute('aria-selected', t.dataset.k === k ? 'true' : 'false'); });
      track.innerHTML = '';
      D.courses.filter(function (c) { return c.k === k; }).sort(function (a, b) { return R[a.r].no - R[b.r].no; }).forEach(function (c) {
        var r = R[c.r], a = el('a', 'hc-card'); a.href = page(c.r, '#course'); a.style.setProperty('--c', r.color);
        var ph = el('div', 'ph'); ph.dataset.bg = photo(r.photo); ph.appendChild(el("span", null, adm(r))); a.appendChild(ph);
        var bd = el('div', 'bd'); bd.appendChild(el('h3', null, c.t));
        var ol = el('ol'); (c.s || []).forEach(function (s) { var li = el('li'); li.appendChild(el('b', null, s[0])); li.appendChild(el('span', null, s[1])); ol.appendChild(li); });
        bd.appendChild(ol); bd.appendChild(el('span', 'go', "看更多" + adm(r) + "信息 →")); a.appendChild(bd);
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

  /* ---------- 여행 참고: 오늘의 바다 (날씨 · 물때 · 바다지수) ---------- */
  (function today() {
    var box = $('tsRegions');
    if (!box || !T) return;
    var KEY = SITE_ALL ? 'bdg-today-all' : 'bdg-today-region';
    var slug = store(KEY);
    if (!R[slug]) slug = SITE_ALL ? 'jejusi' : 'yeosu';
    var reqId = 0;
    ORDER.forEach(function (r) {
      var b = el('button', null, r.name); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.r = r.slug; if (r.group) b.dataset.g = r.group;
      b.addEventListener('click', function () { select(r.slug, true); });
      box.appendChild(b);
    });
    var gbox = $('tsGroups'), curGroup = null;
    function showGroup(g) {
      curGroup = g;
      [].forEach.call(box.querySelectorAll('button'), function (b) { b.hidden = !!g && b.dataset.g !== g; });
      if (gbox) [].forEach.call(gbox.querySelectorAll('button'), function (b) { b.setAttribute('aria-selected', b.dataset.g === g ? 'true' : 'false'); });
    }
    if (SITE_ALL && gbox) GROUP_ORDER.forEach(function (g) {
      var b = el('button', null, g); b.type = 'button'; b.setAttribute('role', 'tab'); b.dataset.g = g;
      b.addEventListener('click', function () { showGroup(g); var first = ORDER.filter(function (r) { return r.group === g; })[0]; if (first && R[slug].group !== g) select(first.slug, true); });
      gbox.appendChild(b);
    });
    function toMin(hm) { var p = hm.split(':'); return +p[0] * 60 + +p[1]; }
    function select(s, user) {
      slug = s; if (user) store(KEY, s);
      if (SITE_ALL && gbox && R[s].group !== curGroup) showGroup(R[s].group);
      [].forEach.call(box.children, function (b) { b.setAttribute('aria-selected', b.dataset.r === s ? 'true' : 'false'); });
      if (user) { var on = box.querySelector('[aria-selected="true"]'); on && on.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' }); }
      var r = R[s], d = new Date(NOW.getFullYear(), NOW.getMonth(), NOW.getDate());
      var m = T.calcMuldae(d), inten = T.calcIntensity(m), lab = T.tideLabel(inten);
      var c = T.coords[s] || [r.lat, r.lng], sun = T.sunTimes(d, c[0], c[1]);
      $('tsTitle').textContent = "今天的" + adm(r) + "海边";
      $('tsDate').textContent = (d.getMonth() + 1) + '月' + d.getDate() + '日（' + DAY[d.getDay()] + '）韩国时间';
      $('tsMuldae').textContent = lab.text;
      $('tsMuldaeName').textContent = lunar(d);
      $('tsGauge').style.width = inten + '%';
      $('tsRise').textContent = sun ? sun.rise : '–'; $('tsSet').textContent = sun ? sun.set : '–';
      $('tsMore').href = page(s, '#tide'); $('tsMore').textContent = "查看" + adm(r) + "两周潮汐表 →";
      var state = { inten: inten, sun: sun, lows: null, wave: null };
      verdict(state);
      week(d);
      $('tsTides').innerHTML = '<li class="muted">加载中</li>'; $('tsTideSrc').textContent = '';
      $('tsTemp').textContent = '–'; $('tsSky').textContent = '加载中'; $('tsWave').textContent = '';
      var my = ++reqId;
      fetch('../api/tide-cache.php?region=' + s, { cache: 'no-store' }).then(function (res) { if (!res.ok) throw 0; return res.json(); }).then(function (data) {
        if (my !== reqId) return;
        var ev = data && data.days && data.days[0] && data.days[0].events;
        var ul = $('tsTides'); ul.innerHTML = '';
        if (!ev || !ev.length) { ul.innerHTML = '<li class="muted">无法加载今天的干潮·满潮时间</li>'; return; }
        ev.forEach(function (e) {
          var li = el('li', e.type === '만조' ? 'high' : ''); li.appendChild(el('span', 'k', tideType(e.type))); li.appendChild(el('b', null, e.time));
          ul.appendChild(li);
        });
        $('tsTideSrc').textContent = data.source === 'beach' ? '数据来源：韩国气象厅' : '数据来源：韩国国立海洋调查院';
        state.lows = ev.filter(function (e) { return e.type === '간조'; }).map(function (e) { return e.time; });
        verdict(state);
      }).catch(function () { if (my === reqId) $('tsTides').innerHTML = '<li class="muted">干潮·满潮数据准备中</li>'; });
      seaIndex(s, my);
      if (window.BADAGAJA_TIDEGRAPH && $('tsGraph')) window.BADAGAJA_TIDEGRAPH.mount($('tsGraph'), s, { dark: true, coords: T.coords[s] || [r.lat, r.lng] });
      fetch(((r.jeju || r.coast) ? '../api/weather-jeju.php?region=' : '../api/weather.php?region=') + s, { cache: 'no-store' }).then(function (res) { if (!res.ok) throw 0; return res.json(); }).then(function (w) {
        if (my !== reqId) return;
        if (!w || w.available === false) { $('tsSky').textContent = '此地区暂无观测数据'; return; }
        $('tsTemp').textContent = (w.temp != null && w.temp !== '') ? w.temp + '°' : '–';
        $('tsSky').textContent = WEATHER[w.label] || '';
        if (w.wave != null && w.wave !== '') { $('tsWave').textContent = '浪高 ' + w.wave + 'm'; state.wave = parseFloat(w.wave); verdict(state); }
      }).catch(function () { if (my === reqId) $('tsSky').textContent = '天气数据准备中'; });
    }
    // 생활해양예보지수 — 해수욕 · 갯벌체험 · 바다낚시
    function seaIndex(s, my) {
      [].forEach.call(document.querySelectorAll('.ts-idx'), function (card) {
        var t = card.dataset.type, g = card.querySelector('.ti-grade'), p = card.querySelector('.ti-place'), d = card.querySelector('.ti-detail');
        card.className = 'ts-card ts-idx'; g.textContent = '–'; p.textContent = '加载中'; d.textContent = '';
        fetch('../api/seaidx.php?type=' + t + '&region=' + s).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (x) {
          if (my !== reqId) return;
          if (!x || !x.available) { card.classList.add('off'); g.textContent = '暂无数据'; p.textContent = '此地区附近没有预报地点'; return; }
          card.classList.add('g' + x.grade); g.textContent = GRADE[x.label] || x.label;
          p.textContent = '最近预报点 ' + x.distance + 'km · ' + when(x.when);
          var det = x.detail || {}, parts = [];
          if (t === 'mudflat') { if (det.start && det.end && det.start !== det.end) parts.push('可体验时间 ' + det.start + '~' + det.end); if (det.weather) parts.push(WEATHER[det.weather] || ''); }
          if (t === 'beach') { if (det.open) parts.push(det.open === '폐장' ? '非开放期间（无救生员）' : '开放期间'); if (det.watertemp) parts.push('水温 ' + det.watertemp + '℃'); if (det.wave) parts.push('浪高 ' + det.wave + 'm'); }
          if (t === 'fishing') {
            if (x.fish && x.fish.length) parts.push(x.fish.slice(0, 3).map(function (f) { return (FISH[f.fish] || f.fish) + ' ' + (GRADE[f.label] || f.label); }).join(' · '));
            if (det.watertemp) parts.push('水温 ' + det.watertemp + '℃');
          }
          d.textContent = parts.filter(Boolean).join(' · ');
        }).catch(function () { if (my === reqId) { card.classList.add('off'); g.textContent = '–'; p.textContent = '无法加载指数'; } });
      });
    }
    function verdict(st) {
      var v = $('tsVerdict'), msg, dayLow = null;
      if (st.lows && st.sun) {
        var a = toMin(st.sun.rise) + 60, b = toMin(st.sun.set) - 60;
        dayLow = st.lows.filter(function (t) { var x = toMin(t); return x >= a && x <= b; })[0] || null;
      }
      if (st.inten >= 68) {
        if (dayLow) msg = '今天退潮幅度大，<b>适合参加赶海体验</b>。白天干潮约在 <b>' + dayLow + '</b>，体验场的活动一般安排在前后两小时，请提前预约，并在涨潮前上岸。';
        else if (st.lows) msg = '今天退潮幅度大，但<b>干潮在清晨或夜间</b>。不建议夜间独自下滩涂，白天可以去海边看风景和日落。';
        else msg = '正值大潮前后，<b>参加赶海体验的好时机</b>。';
      } else if (st.inten <= 32) {
        msg = '今天潮差小、海面较平稳，<b>适合防波堤·码头海钓</b>与搭船游岛。';
      } else {
        msg = '今天潮差适中。' + (dayLow ? '干潮 <b>' + dayLow + '</b> 前后可以看到泥滩。' : '可配合干潮时间安排海边行程。');
      }
      if (st.wave != null && st.wave >= 1.5) msg += ' <b>浪高 ' + st.wave + 'm</b>，请远离礁石与防波堤末端。';
      v.innerHTML = msg;
    }
    function week(d0) {
      var w = $('tsWeek'); w.innerHTML = '';
      for (var i = 0; i < 7; i++) {
        var d = new Date(d0); d.setDate(d.getDate() + i);
        var m = T.calcMuldae(d), inten = T.calcIntensity(m), spring = inten >= 68;
        var c = el('div', 'ts-day' + (i === 0 ? ' today' : '') + (spring ? ' spring' : ''));
        c.appendChild(el('span', null, i === 0 ? '今天' : '周' + DAY[d.getDay()] + ' ' + d.getDate()));
        var bar = el('div', 'bar'), fill = el('i'); fill.style.height = Math.max(8, Math.round(inten * 0.36)) + 'px'; bar.appendChild(fill); c.appendChild(bar);
        c.appendChild(el('b', null, T.tideLabel(inten).text));
        c.appendChild(el('span', 'good', spring ? '赶海 ◎' : (inten <= 32 ? '海钓 ◎' : '')));
        w.appendChild(c);
      }
    }
    select(slug, false);
  })();
})();
