/* 바다가자 중국어(간체) 권역 페이지 — 숙소 목록 · 물높이 그래프 · 권역 이동줄
 * 물때표·날씨·아이콘은 zh-cn/js/app.js, 그래프는 zh-cn/js/tide-graph.js가 담당
 */
(function () {
  var REGION = document.body.getAttribute('data-region');
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  /* 물높이 그래프 */
  var g = document.getElementById('zrGraph'), T = window.BADAGAJA_TIDE;
  if (g && window.BADAGAJA_TIDEGRAPH) window.BADAGAJA_TIDEGRAPH.mount(g, REGION, { coords: T && T.coords[REGION] });

  /* 권역 이동줄: 현재 권역이 보이도록 가로 위치 맞춤 */
  var list = document.querySelector('.region-nav .rn-list'), on = list && list.querySelector('a.on');
  if (on) list.scrollLeft = Math.max(0, on.offsetLeft - (list.clientWidth - on.offsetWidth) / 2);

  /* 숙소: 한국관광공사 등록 숙소 (이름은 한국어 그대로 — 지도 앱 검색용) */
  var TYPE = { '관광호텔': '酒店', '호텔': '酒店', '리조트': '度假村', '콘도미니엄': '度假公寓', '콘도': '度假公寓', '펜션': '民宿', '민박': '民宿', '게스트하우스': '青旅 / 民宿', '유스호스텔': '青年旅舍', '한옥': '韩屋', '모텔': '汽车旅馆', '서비스드레지던스': '服务式公寓', '생활숙박시설': '服务式公寓', '홈스테이': '家庭寄宿', '캠핑': '露营' };
  var box = document.getElementById('zrStays');
  if (!box) return;
  /* 숙소 칸 광고(Trip.com) — 한국어판 js/region-extra.js 와 같게: 숙소 카드 맨 끝, 한 줄(4칸)을 꽉 채우면 하나를 빼고 그 자리에.
     광고가 꺼져 있으면 광고 스크립트조차 안 받음 · 설정은 data/ads.json 'region-stay' (문구는 *_zh) (2026-09-22) */
  function adsLoad(cb) {
    if (window.BadagajaAds) return cb();
    var v = ((document.querySelector('script[src*="region.js"]') || {}).src || '').split('?v=')[1] || '';
    function js(src, ok) { var s = document.createElement('script'); s.src = src + (v ? '?v=' + v : ''); s.onload = ok; document.head.appendChild(s); }
    js('../js/ads-data.js', function () {
      if (!window.BADAGAJA_ADS || !window.BADAGAJA_ADS.enabled) return;
      js('../js/ads.js', cb);
    });
  }
  function stayAd(row) {
    adsLoad(function () {
      if (!window.BadagajaAds.willShow('region-stay')) return;
      var cards = row.querySelectorAll('.zr-stay');
      if (cards.length && cards.length % 4 === 0) cards[cards.length - 1].remove();
      var ad = el('aside', 'ad-slot'); ad.setAttribute('data-ad-slot', 'region-stay'); ad.hidden = true;
      var src = row.querySelector('.zr-src');
      row.insertBefore(ad, src);
      window.BadagajaAds.mount(ad);
    });
  }
  fetch('../api/tour.php?kind=stay&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    var items = (d && d.items) || [];
    if (!items.length) throw 0;
    items = items.slice().sort(function (a, b) { return (b.img ? 1 : 0) - (a.img ? 1 : 0); }).slice(0, 8);
    box.innerHTML = '';
    items.forEach(function (it) {
      var c = el('div', 'zr-stay');
      var ph = el('div', 'zr-stay-ph' + (it.img ? '' : ' empty'));
      if (it.img) {
        var im = el('img'); im.src = it.img.replace(/^http:/, 'https:'); im.alt = ''; im.loading = 'lazy'; ph.appendChild(im);
        // 관광공사 사진은 _image3_1 / _image2_1 가운데 한쪽만 남은 경우가 있습니다 — 한국어판처럼 한 번 바꿔 보고, 안 되면 사진 칸을 비웁니다 (2026-09-24)
        (function (im, ph) { im.addEventListener('error', function () {
          var s = im.getAttribute('src') || '', alt2 = s.indexOf('_image3_1') > -1 ? s.replace('_image3_1', '_image2_1') : s.indexOf('_image2_1') > -1 ? s.replace('_image2_1', '_image3_1') : '';
          if (alt2 && !im.dataset.retry) { im.dataset.retry = '1'; im.src = alt2; return; }
          im.remove(); ph.classList.add('empty');
        }); })(im, ph);
      }
      c.appendChild(ph);
      var bd = el('div', 'zr-stay-bd');
      bd.appendChild(el('span', 'zr-stay-type', TYPE[it.type] || '住宿'));
      bd.appendChild(el('b', null, it.name));
      bd.appendChild(el('span', 'zr-stay-addr', (it.addr || '').replace(/^전남광주통합특별시\s*|^전라남도\s*/, '')));
      var maps = el('div', 'zr-maps'), q = encodeURIComponent(it.name);   // 유학생이 많이 쓰는 네이버 지도를 앞에
      [['Naver 地图 ↗', 'https://map.naver.com/p/search/' + q], ['Kakao 地图 ↗', 'https://map.kakao.com/?q=' + q]].forEach(function (m) { var a = el('a', 'zr-map', m[0]); a.href = m[1]; a.target = '_blank'; a.rel = 'noopener'; maps.appendChild(a); });
      bd.appendChild(maps);
      c.appendChild(bd); box.appendChild(c);
    });
    stayAd(box);
    box.appendChild(el('p', 'zr-src', '数据来源：韩国观光公社　·　住宿名称为韩文'));
  }).catch(function () { box.innerHTML = '<p class="zr-loading">暂时无法加载住宿信息，请稍后再试。</p>'; });
})();

/* 티맵 목적지 인기 순위 (한국관광공사 관광빅데이터, TMAP 제공) — 가게 이름은 지도 검색용으로 한국어 그대로 */
(function () {
  var REGION = document.body.getAttribute('data-region'), box = document.getElementById('tmapRank');
  if (!box) return;
  var KO = { sinan: '신안', muan: '무안', mokpo: '목포', yeonggwang: '영광', hampyeong: '함평', jindo: '진도', haenam: '해남', wando: '완도', gangjin: '강진', jangheung: '장흥', boseong: '보성', goheung: '고흥', yeosu: '여수', suncheon: '순천', gwangyang: '광양' };
  var CAT = { '한식': '韩餐', '중식': '中餐', '일식': '日料', '양식': '西餐', '분식': '韩式小吃', '간이음식': '小吃·简餐', '전문음식': '特色餐厅', '음식점기타': '餐饮', '패스트푸드': '快餐', '카페/찻집': '咖啡·茶馆', '제과점': '面包店', '베이커리': '面包店', '주점': '酒馆', '해산물': '海鲜', '뷔페': '自助餐', '고기': '烤肉' };
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  var IS_JEJU = /^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(REGION);
  if (IS_JEJU) KO[REGION] = '제주';
  // 카카오 장소 검색으로 주소·电话·详情 붙이기 (../js/kakao-places.js)
  var T = window.BADAGAJA_TIDE, center = T && T.coords && T.coords[REGION];
  function enrich(list) {
    function go() { if (!list._badaRun) window.BadaKakaoEnrich(list, { prefix: '../', center: IS_JEJU ? center : null, region: REGION, strict: true, onDone: function (n) { if (!n) box.hidden = true; }, koLang: true, label: { tel: '电话', detail: 'Kakao 详情' } }); else if (list._badaSeen) list._badaRun(); }
    if (window.BadaKakaoEnrich) return go();
    var s = document.createElement('script'); s.src = '../js/kakao-places.js?v=zh49'; s.onload = go; document.head.appendChild(s);
  }
  fetch((IS_JEJU ? '../api/places-jeju.php' : '../api/places.php') + '?region=' + REGION + '&type=food&limit=40').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    if (!d || !d.ok || !d.items || !d.items.length || d.region !== REGION) return;   // 모르는 권역은 보성 자료가 옴
    var isCafe = function (x) { return /카페|찻집/.test(x.group || x.category || ''); };
    var cafe = d.items.filter(isCafe), food = d.items.filter(function (x) { return !isCafe(x); });
    var ym = /^(\d{4})(\d{2})$/.exec(d.baseYm || ''), base = ym ? ym[1] + '年' + (+ym[2]) + '月' : '';
    box.innerHTML = '';
    var head = el('div', 'tr-head');
    head.appendChild(el('h3', 'serif', '🚗 最近很多人去的地方'));
    head.appendChild(el('p', null, (d.mode === 'related' ? '去过本地区景点的人，还常去这些地方（根据 TMAP 导航目的地数据）' : '根据 TMAP 导航的目的地搜索整理的人气排行') + (base ? '（' + base + '数据）' : '') + '，反映的是去的人多，不是口味评分。店名为韩文，点击可在 Naver 地图中搜索。'));
    box.appendChild(head);
    var tabs = el('div', 'tr-tabs'), list = el('ol', 'tr-list');
    function render(arr) {
      list.innerHTML = '';
      arr.slice(0, 20).forEach(function (x, i) {
        var full = x.name + (x.branch ? ' ' + x.branch : ''), q = encodeURIComponent((KO[REGION] || '') + ' ' + full);
        var li = el('li'), a = el('a'); a.href = 'https://map.naver.com/p/search/' + q; a.target = '_blank'; a.rel = 'noopener';
        li.setAttribute('data-q', (KO[REGION] || '') + ' ' + full); li.setAttribute('data-name', x.name); if (i >= 10) li.hidden = true;
        a.appendChild(el('b', 'rk', String(i + 1)));
        var nm = el('span', 'nm', full); nm.lang = 'ko'; a.appendChild(nm);
        a.appendChild(el('span', 'ct', CAT[x.group] || CAT[x.category] || '餐饮'));
        li.appendChild(a);
        var k = el('a', 'zr-tmap-kakao', 'Kakao'); k.href = 'https://map.kakao.com/?q=' + q; k.target = '_blank'; k.rel = 'noopener'; li.appendChild(k);
        list.appendChild(li);
      });
      enrich(list);
    }
    [['餐厅', food], ['咖啡·茶馆', cafe]].forEach(function (t, i) {
      if (!t[1].length) return;
      var b = el('button', i === 0 ? 'on' : '', t[0] + ' TOP ' + Math.min(10, t[1].length)); b.type = 'button';
      b.addEventListener('click', function () { [].forEach.call(tabs.children, function (x) { x.classList.toggle('on', x === b); }); render(t[1]); });
      tabs.appendChild(b);
    });
    box.appendChild(tabs); box.appendChild(list);
    box.appendChild(el('p', 'tr-src', '数据来源：韩国观光公社旅游大数据（TMAP Mobility 提供）· 营业时间和菜单请以店家为准'));
    render(food.length ? food : cafe);
    box.hidden = false;
  }).catch(function () {});
})();
/* 축제 실제 일정 (한국관광공사 행사정보) — 사전에 있는 축제는 중국어 이름, 없으면 한국어 이름 그대로 */
(function () {
  var REGION = document.body.getAttribute('data-region'), box = document.getElementById('festReal');
  if (!box) return;
  var names = {}; try { names = JSON.parse(box.getAttribute('data-names') || '{}'); } catch (e) {}
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function key(s) { return (s || '').replace(/20\d\d|제?\d+회/g, '').replace(/[\s\d·()（）]/g, ''); }
  function zhName(ko) {
    var k = key(ko); if (k.length < 2) return null;
    for (var n in names) { var kn = key(n); if (kn.length >= 2 && (k.indexOf(kn) > -1 || kn.indexOf(k) > -1)) return names[n]; }
    return null;
  }
  fetch('../api/tour.php?kind=festival&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    var items = (d && d.ok && d.items) || [];
    var today = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000); today.setHours(0, 0, 0, 0);
    items = items.filter(function (x) { return new Date(x.end + 'T00:00:00') >= today; });
    if (!items.length) return;
    box.appendChild(el('h3', 'serif', '📅 即将举办的节庆 · 最新日期'));
    var row = el('div', 'fr-row');
    items.slice(0, 6).forEach(function (x) {
      var s = new Date(x.start + 'T00:00:00'), e = new Date(x.end + 'T00:00:00'), zh = zhName(x.name);
      var card = el('a', 'fr-card'); card.href = 'https://map.naver.com/p/search/' + encodeURIComponent(x.name); card.target = '_blank'; card.rel = 'noopener';
      if (x.img) { var im = el('img'); im.src = x.img.replace(/^http:/, 'https:'); im.alt = ''; im.loading = 'lazy'; card.appendChild(im); }
      var b = el('div', 'fr-body'), dd = Math.round((s - today) / 86400000);
      b.appendChild(el('span', 'fr-badge' + (dd <= 0 ? ' now' : ''), dd <= 0 ? '进行中' : 'D-' + dd));
      b.appendChild(el('b', null, zh || x.name));
      if (zh) { var ko = el('span', 'fr-addr', '韩文：' + x.name); card.lang = 'zh'; b.appendChild(ko); }
      b.appendChild(el('span', 'fr-date', (s.getMonth() + 1) + '月' + s.getDate() + '日 ~ ' + (e.getMonth() + 1) + '月' + e.getDate() + '日'));
      if (x.addr) { var ad = el('span', 'fr-addr', x.addr.replace(/^전남광주통합특별시\s*|^전라남도\s*/, '')); ad.lang = 'ko'; b.appendChild(ad); }
      card.appendChild(b); row.appendChild(card);
    });
    box.appendChild(row);
    box.appendChild(el('p', 'fr-src', '日期：韩国观光公社活动信息 · 图片：韩国观光公社（公共使用许可第3类型）· 出发前请确认主办方公告'));
    box.hidden = false;
  }).catch(function () {});
})();

/* 더보기 버튼: data-more="목록 id" 의 숨긴 항목 펼치기 */
[].forEach.call(document.querySelectorAll('button[data-more]'), function (btn) {
  btn.addEventListener('click', function () {
    var list = document.getElementById(btn.getAttribute('data-more')); if (!list) return;
    [].forEach.call(list.querySelectorAll('[hidden]'), function (x) { x.hidden = false; });
    btn.remove();
  });
});
/* 생활해양예보지수(국립해양조사원) — 해수욕 · 갯벌체험 · 바다낚시. 한국어 지명은 표시하지 않고 거리만 */
(function () {
  var REGION = document.body.getAttribute('data-region'), box = document.getElementById('zrIdx');
  if (!box) return;
  var GRADE = { '매우좋음': '非常适合', '좋음': '适合', '보통': '普通', '나쁨': '不太适合', '매우나쁨': '不适合' };
  var WEATHER = { '맑음': '晴', '구름많음': '多云', '흐림': '阴', '비': '雨', '비/눈': '雨夹雪', '눈': '雪', '소나기': '阵雨' };
  var FISH = { '돌돔': '石鲷', '감성돔': '黑鲷', '참돔': '真鲷', '농어': '海鲈鱼', '우럭': '黑鲪', '볼락': '平鲉', '넙치': '牙鲆', '갈치': '带鱼', '벵에돔': '黑毛', '고등어': '青花鱼', '전갱이': '竹荚鱼', '숭어': '鲻鱼', '노래미': '斑头鱼', '기타어종': '其他鱼种' };
  function when(w) { return (w || '').replace('오늘', '今天').replace('내일', '明天').replace('오전', '上午').replace('오후', '下午').replace(/\s+/g, ''); }
  [].forEach.call(box.querySelectorAll('.zr-idx-card'), function (card) {
    var t = card.getAttribute('data-type'), g = card.querySelector('b'), p = card.querySelector('small');
    fetch('../api/seaidx.php?type=' + t + '&region=' + REGION).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (x) {
      if (!x || !x.available) { card.classList.add('off'); g.textContent = '暂无数据'; p.textContent = '附近没有预报地点'; return; }
      card.classList.add('g' + x.grade); g.textContent = GRADE[x.label] || x.label;
      var det = x.detail || {}, parts = ['最近预报点 ' + x.distance + 'km · ' + when(x.when)];
      if (t === 'mudflat' && det.start && det.end && det.start !== det.end) parts.push('可体验 ' + det.start + '~' + det.end);
      if (t === 'beach') { if (det.open) parts.push(det.open === '폐장' ? '非开放期（无救生员）' : '开放期间'); if (det.watertemp) parts.push('水温 ' + det.watertemp + '℃'); }
      if (t === 'fishing' && x.fish && x.fish.length) parts.push(x.fish.slice(0, 2).map(function (f) { return (FISH[f.fish] || f.fish) + ' ' + (GRADE[f.label] || f.label); }).join(' · '));
      if (det.weather && WEATHER[det.weather]) parts.push(WEATHER[det.weather]);
      p.textContent = parts.join(' · ');
    }).catch(function () { card.classList.add('off'); g.textContent = '–'; p.textContent = '暂时无法加载'; });
  });
})();
/* 어촌체험마을 — 방문한 달(한국 시간) 기준으로 "이번 달 운영 가능성" 표시·정렬. 가격은 싣지 않고, 수집 1년이 지나면 경고 */
(function () {
  var wrap = document.getElementById('villages');
  if (!wrap) return;
  var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000), now = kst.getMonth() + 1;
  function has(dm) { return dm === 'all' || (dm && dm.split(',').indexOf(String(now)) >= 0); }
  var src = wrap.querySelector('.zv-src[data-collected]');
  if (src) {
    var p = src.getAttribute('data-collected').split('-'), age = (kst.getFullYear() - +p[0]) * 12 + (now - +p[1]);
    if (age >= 12) { src.classList.add('old'); src.insertBefore(document.createTextNode('⚠ 这份资料已超过一年未更新，项目和时间可能已经变化，请以电话确认为准。 '), src.firstChild); }
  }
  var grid = wrap.querySelector('.zv-grid');
  if (!grid) return;
  var cards = [].slice.call(grid.querySelectorAll('.zv-card')), open = 0;
  cards.forEach(function (c, i) {
    var dm = c.getAttribute('data-m'), badge = c.querySelector('.zv-now');
    var ul = c.querySelector('.zv-ex'), more = ul.querySelector('.zv-more');
    [].forEach.call(c.querySelectorAll('li[data-m]'), function (li) { li.classList.add(has(li.getAttribute('data-m')) ? 'on' : 'off'); });
    [].forEach.call(ul.querySelectorAll('li.off'), function (li) { ul.insertBefore(li, more); });
    c._o = i;
    if (!dm) { c._k = 1; return; }
    if (has(dm)) { c._k = 0; open++; badge.textContent = now + '月有登记项目'; badge.className = 'zv-now yes'; }
    else { c._k = 2; badge.textContent = now + '月一般不开放'; badge.className = 'zv-now no'; }
    badge.hidden = false;
  });
  cards.sort(function (a, b) { return a._k - b._k || a._o - b._o; }).forEach(function (c) { grid.appendChild(c); });
  var m = document.getElementById('zvMonth');
  if (m) { m.textContent = '现在是 ' + now + ' 月：' + (open ? '有 ' + open + ' 处登记了本月开放的项目，已排在前面（参考）。' : '本地区没有登记本月开放的项目，可以电话问问或看看其他地区。'); m.hidden = false; }
})();
/* 当季海鲜卡片上标出禁渔期 — 한국어판 자료(../data/fishery-rules.json)를 그대로 쓴다 */
(function () {
  var cards = document.querySelectorAll('.zr-catch[data-ko]');
  if (!cards.length || !window.fetch) return;
  var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
  var M = kst.getMonth() + 1, D = kst.getDate();
  function norm(s) { return (s || '').replace(/\(.*?\)/g, '').replace(/[\s·]/g, ''); }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  // 시·도가 따로 정한 금어기(낙지·참문어 banBy) — 이 권역의 도. 한국어판 region-extra.js 와 같은 판단 (2026-09-22)
  var RG = document.body.getAttribute('data-region') || '';
  var GRP = /^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(RG) ? '제주'
    : /^(changwon|geoje|goseong|namhae|sacheon|tongyeong)$/.test(RG) ? '경남'
    : /^(ganghwa|ongjin|yeongjong|daebu|hwaseong)$/.test(RG) ? '인천·경기'
    : document.body.hasAttribute('data-coast') ? '' : '전남';
  var GRP_ZH = { '전남': '全南', '경남': '庆南', '인천·경기': '仁川·京畿', '제주': '济州' };
  function banOf(s) { return (s.banBy && s.banBy[GRP]) || s.ban; }
  function inBan(s) {
    if (!s.ban || s.byNotice) return false;
    return banOf(s).some(function (b) {
      var a = b[0] * 100 + b[1], z = b[2] * 100 + b[3], t = M * 100 + D;
      return a <= z ? (t >= a && t <= z) : (t >= a || t <= z);
    });
  }
  function cnDate(t) {
    if (!t) return '';
    return t.replace(/다음 해\s*/g, '次年').replace(/(\d+)월\s*(\d+)일/g, '$1月$2日')
      .replace(/(\d+)월/g, '$1月').replace(/\s*~\s*/g, '～').replace(/\s+/g, '');
  }
  Promise.all([
    fetch('../data/fishery-rules.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }),
    fetch('i18n/rules.json').then(function (r) { return r.ok ? r.json() : {}; })
  ]).then(function (res) {
    var d = res[0], TR = res[1] || {};
    var by = {};
    d.species.forEach(function (s) {
      by[norm(s.n)] = s;
      if (s.alias) s.alias.split(/[,·]/).forEach(function (a) { by[norm(a)] = s; });
    });
    function sizeText(t) {
      if (!t) return '';
      if (TR.size && TR.size[t]) return TR.size[t];
      var out = t;
      if (TR.sizeTerm) { for (var k in TR.sizeTerm) out = out.replace(k, TR.sizeTerm[k]); }
      return out.replace(/\s*이하/g, '以下').replace(/\s+/g, '');
    }
    function banText(s) {
      if (s.banBy && s.banBy[GRP]) return s.banBy[GRP].map(function (b) { return b[0] + '月' + b[1] + '日～' + b[2] + '月' + b[3] + '日'; }).join('，') + '（' + GRP_ZH[GRP] + '）';
      if (s.byNotice && TR.byNoticeText && TR.byNoticeText[s.banText]) return TR.byNoticeText[s.banText];
      if (TR.banText && TR.banText[s.banText]) return TR.banText[s.banText];
      return cnDate(s.banText);
    }
    [].forEach.call(cards, function (card) {
      var key = norm(card.getAttribute('data-ko')), rule = by[key];
      if (!rule) {
        for (var k in by) { if (k.length >= 2 && (key.indexOf(k) === 0 || k.indexOf(key) === 0)) { rule = by[k]; break; } }
      }
      if (!rule || card.querySelector('.cc-rule')) return;
      var box = el('a', 'cc-rule'); box.href = 'jinyuqi.html#find';
      if (inBan(rule)) {
        box.classList.add('now');
        box.appendChild(el('b', null, '现在禁捕'));
        box.appendChild(el('span', null, banText(rule)));
      } else if (rule.byNotice) {
        box.appendChild(el('b', null, '有禁渔期'));
        box.appendChild(el('span', null, banText(rule)));
      } else if (rule.banText) {
        box.appendChild(el('b', null, '禁渔期'));
        box.appendChild(el('span', null, banText(rule)));
      }
      if (rule.size) box.appendChild(el('span', 'cc-size', '最小尺寸：' + sizeText(rule.size)));
      if (box.children.length) card.appendChild(box);
    });
  }).catch(function () { });
})();
