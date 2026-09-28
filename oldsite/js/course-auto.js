/* 매월 자동 갱신되는 추천 코스 (권역 페이지 #course)
 * 쓰는 자료 — 모두 공개 데이터이며, 블로그 글을 가져오지 않습니다.
 *  · 실제 방문 통계: 한국관광공사 관광빅데이터(TMAP Mobility 제공) 목적지 순위  api/places.php
 *  · 관광지: 한국관광공사 국문 관광정보  api/tour.php?kind=spot
 *  · 이번 달 축제: 한국관광공사 행사정보  api/tour.php?kind=festival
 *  · 어촌체험휴양마을: 바다여행(한국어촌어항공단)  data/fishing-villages.json
 *  · 해루질·낚시 포인트: 사이트 자체 정리 자료  window.BADAGAJA_POINTS_GEO
 * 데이터가 바뀌면 코스도 따라 바뀌고, 달이 바뀌면 축제·순위·순서가 자동으로 갱신됩니다.
 * 자료를 못 받으면 HTML에 적힌 기존 코스를 그대로 둡니다.
 */
(function () {
  var REGION = document.body.getAttribute('data-region');
  var grid = document.querySelector('#course .course-grid');
  if (!REGION || !grid) return;
  // 제주 권역은 직접 확인한 해안 명소로 짠 코스를 그대로 보여준다 (관광지 목록에 내륙 공원이 많아 자동 코스가 바다와 멀어짐)
  if (/^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(REGION)) return;
  if (window.BADAGAJA_COAST && window.BADAGAJA_COAST[REGION]) return;   // 전국 확대 권역은 조사한 코스를 그대로 둔다
  var NAME = { sinan: '신안', muan: '무안', mokpo: '목포', yeonggwang: '영광', hampyeong: '함평', jindo: '진도', haenam: '해남', wando: '완도', gangjin: '강진', jangheung: '장흥', boseong: '보성', goheung: '고흥', yeosu: '여수', suncheon: '순천', gwangyang: '광양',
    jejusi: '제주시', aewol: '애월', jocheon: '조천', seongsan: '성산', seogwipo: '서귀포', daejeong: '대정', chuja: '추자도' }[REGION] || '';
  var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
  var MONTH = kst.getMonth() + 1;

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function has(s, re) { return re.test(s || ''); }
  function j(url) { return fetch(url).then(function (r) { if (!r.ok) throw 0; return r.json(); }); }
  var taken = {};                         // 코스끼리 같은 곳이 겹치지 않게 기억해 둔다
  function pick(list, n, seed) {          // 달마다 조금씩 다른 순서로 고름
    var out = [], used = {};
    function take(pool) {
      for (var i = 0; i < pool.length && out.length < n; i++) {
        var k = (i + seed) % pool.length, v = pool[k];
        if (!v || used[v.name || v]) continue;
        used[v.name || v] = 1; taken[v.name || v] = 1; out.push(v);
      }
    }
    take(list.filter(function (v) { return v && !taken[v.name || v]; }));   // 아직 안 쓴 곳 먼저
    if (out.length < n) take(list);                                        // 모자라면 겹치더라도 채운다
    return out;
  }
  function pickNew(list, n, seed) {       // 겹치느니 비우는 편이 나은 자리에 쓴다
    return pick(list.filter(function (v) { return v && !taken[v.name || v]; }), n, seed);
  }
  // 어느 권역이든 오전·오후·저녁 세 칸은 채운다(체험마을이나 해변이 없는 곳도 있다)
  function fillThree(st, pool, seedBase, mk) {
    for (var g = 0; st.length < 3 && g < 8; g++) {
      var x = pickNew(pool, 1, seedBase + g)[0] || pick(pool, 1, seedBase + g)[0];
      if (!x) break;
      st.splice(Math.max(0, st.length - 1), 0, { t: '', x: mk(x) });
    }
    var label = ['오전', '오후', '저녁'];
    st.forEach(function (s, i) { if (i < 3) s.t = label[i]; });
  }

  Promise.all([
    j('api/places.php?region=' + REGION + '&type=food&limit=60').catch(function () { return null; }),
    j('api/tour.php?kind=spot&region=' + REGION).catch(function () { return null; }),
    j('api/tour.php?kind=festival&region=' + REGION).catch(function () { return null; }),
    j('data/fishing-villages.json').catch(function () { return null; })
  ]).then(function (res) {
    // 관광빅데이터는 "이 지역을 찾은 사람들이 간 곳"이라 옆 시·군 가게가 많이 섞인다.
    // 코스는 그 지역 안에서 도는 일정이므로 실제 소재지(area)가 같은 곳만 쓴다.
    var regionName = (res[0] && res[0].regionName) || '';
    var food = ((res[0] && res[0].items) || []).filter(function (f) {
      return !regionName || !f.area || f.area === regionName;
    });
    var spots = (res[1] && res[1].items) || [];
    // 하루 코스로 차를 몰고 도는 일정이라, 여객선을 타야 닿는 섬은 뺀다.
    // 연륙교가 놓인 섬(신안 천사대교·임자대교·증도대교, 완도 신지·고금·약산, 여수 돌산·낭도 등)은 그대로 둔다.
    (function dropFerryOnly() {
      var FERRY = {                                   // 주소의 읍·면으로 거르는 것
        sinan: /흑산면|비금면|도초면|하의면|신의면|장산면/,
        yeonggwang: /낙월면/,
        jindo: /조도면/,
        wando: /보길면|청산면|소안면|노화읍|생일면|금당면|금일읍/,
        yeosu: /삼산면|남면/,
        seongsan: /우도면/,                           // 제주: 우도·가파도·마라도는 배로만
        daejeong: /가파리|마라리/
      }[REGION];
      var FERRY_SPOT = {                              // 같은 읍·면 안에서도 배로만 가는 곳
        sinan: /기점|소악도|병풍도/,
        yeosu: /개도|제도|여자도|상화도|하화도/,
        mokpo: /외달도|달리도|율도/,
        goheung: /시산도|지죽도|취도/,
        seongsan: /우도/,
        daejeong: /가파도|마라도/,
        aewol: /비양도|차귀도/
      }[REGION];
      if (!FERRY && !FERRY_SPOT) return;
      var land = spots.filter(function (s) {
        var hay = (s.addr || '') + ' ' + (s.name || '');
        if (FERRY && FERRY.test(s.addr || '')) return false;
        if (FERRY_SPOT && FERRY_SPOT.test(hay)) return false;
        return true;
      });
      if (land.length >= 6) spots = land;
    })();
    // 권역 중심에서 너무 먼 곳도 뺀다
    (function keepNear() {
      var R = (window.BADAGAJA_HOME && window.BADAGAJA_HOME.regions) || [];
      var me = null;
      R.forEach(function (r) { if (r.slug === REGION) me = r; });
      if (!me || !me.lat) return;
      function km(a, b, c, d) {
        var t = Math.PI / 180, x = (c - a) * t, y = (d - b) * t;
        var h = Math.sin(x / 2) * Math.sin(x / 2) + Math.cos(a * t) * Math.cos(c * t) * Math.sin(y / 2) * Math.sin(y / 2);
        return 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
      }
      var near = spots.filter(function (s) { return s.lat && km(me.lat, me.lng, s.lat, s.lng) <= 25; });
      if (near.length >= 6) spots = near;          // 남는 게 너무 적으면 원래대로 둔다
    })();
    var fests = (res[2] && res[2].items) || [];
    // 여객선을 타야 닿는 체험마을은 하루 코스에 넣지 않는다
    // (완도 보옥=보길도, 여수 손죽=손죽도·안도=안도, 진도 관매·창유·관호=조도면, 고흥 연홍도)
    var FERRY_VIL = /보옥마을|손죽마을|안도마을|관매마을|창유마을|관호마을|연홍도마을/;
    var vil = ((res[3] && res[3].villages) || []).filter(function (v) {
      return v.region === REGION && !FERRY_VIL.test(v.name || '');
    });
    if (!food.length && !spots.length) return;                      // 자료가 없으면 기존 코스 유지
    var baseLabel = (res[0] && res[0].baseLabel) || '';

    /* ---- 분류 ---- */
    function byGroup(re) { return food.filter(function (f) { return has(f.group + f.category, re); }); }
    var cafes = byGroup(/카페|찻집|제과/), light = byGroup(/간이|분식|치킨|패스트/);
    var special = byGroup(/전문음식|향토/), korean = special.concat(byGroup(/한식/)).filter(function (f) { return !has(f.name, /해장국|국밥|프랜차이즈/); });
    var anyFood = food.slice();
    function spotBy(re) { return spots.filter(function (s) { return has(s.name + ' ' + s.kind + ' ' + s.addr, re); }); }
    var sunset = spotBy(/노을|일몰|전망|낙조|등대|공원|해안도로|둘레길/);
    var beach = spotBy(/해변|해수욕장|백사장/);
    var calm = spotBy(/사찰|절$|암$|유적|고택|서원|박물관|기념관|정원|수목원|생태|공원|테마/);
    var indoor = spotBy(/박물관|과학관|미술관|전시|기념관|센터|아쿠아리움|동물원|수족관/);
    var outdoor = spotBy(/해변|해수욕장|공원|둘레길|해안도로|숲|수목원|섬|전망/);
    var island = spotBy(/섬|도$|항|포구/);
    var seed = MONTH;

    /* ---- 이번 달 축제 ---- */
    var today = new Date(kst.getFullYear(), kst.getMonth(), kst.getDate());
    var festNow = fests.filter(function (f) {
      var s = new Date(f.start + 'T00:00:00'), e = new Date(f.end + 'T00:00:00');
      if ((e - s) / 86400000 > 45) return false;                 // 1년 내내 하는 캠페인은 제외
      return e >= today && s <= new Date(today.getTime() + 45 * 86400000);
    }).sort(function (a, b) { return a.start < b.start ? -1 : 1; })[0];

    /* ---- 코스 만들기 ---- */
    function step(time, text) { return { t: time, x: text }; }
    function fname(f) { return f ? f.name + (f.branch ? ' ' + f.branch : '') : null; }
    var courses = [];

    // 코스는 오전·오후·저녁 세 칸으로만 짠다. 식당은 정해 주지 않고 고를 곳만 알려 준다.
    function spotText(s) { return s.name + (s.kind ? ' — ' + s.kind : ''); }
    var EAT = '{EAT}';

    // ① 연인 — 해안 명소를 돌고 노을로 마무리
    (function () {
      var v = pick(sunset.length >= 2 ? sunset : outdoor, 2, seed), other = pick(outdoor.concat(calm), 3, seed + 5);
      var first = v[0] || other[0] || pick(spots, 1, seed + 12)[0];
      var mid = other.filter(function (x) { return !first || x.name !== first.name; })[0] || pick(spots, 1, seed + 13)[0];
      var last = v[1] || v[0];
      var st = [];
      if (first) st.push(step('오전', spotText(first)));
      if (mid && (!first || mid.name !== first.name)) st.push(step('오후', spotText(mid)));
      if (last && (!first || last.name !== first.name)) st.push(step('저녁', last.name + '에서 노을 보기 · ' + EAT));
      else st.push(step('저녁', EAT));
      fillThree(st, spots, seed + 20, spotText);
      courses.push({ cls: 'couple', badge: '연인과의 여행', title: NAME + ' 노을 따라 걷는 하루', steps: st, why: '해안 명소를 노을 시간에 맞춰 이었습니다.' });
    })();

    // ② 부모님 — 걷기 부담이 적은 곳, 축제가 있으면 오후에
    (function () {
      var p = pickNew(calm.length ? calm : spots, 3, seed + 1), st = [];
      if (p.length < 3) p = p.concat(pickNew(spots, 3 - p.length, seed + 14));
      if (p.length < 3) p = p.concat(pick(spots, 3 - p.length, seed + 16));
      if (p[0]) st.push(step('오전', spotText(p[0])));
      if (festNow) st.push(step('오후', festNow.name + ' 들르기 (' + festNow.start.slice(5).replace('-', '.') + '~' + festNow.end.slice(5).replace('-', '.') + ')'));
      else if (p[1]) st.push(step('오후', spotText(p[1])));
      else { var alt = pick(spots, 1, seed + 15)[0]; if (alt) st.push(step('오후', spotText(alt))); }
      st.push(step('저녁', (p[2] ? p[2].name + ' 둘러보기 · ' : '') + EAT));
      fillThree(st, spots, seed + 30, spotText);
      courses.push({ cls: 'parents', badge: '부모님과의 여행', title: NAME + ', 천천히 보는 길', steps: st, why: '걷기 부담이 적은 명소 위주로 골랐습니다.' });
    })();

    // ③ 아이 — 체험이 있으면 오전에(간조 시간에 맞춰 열립니다)
    (function () {
      var vilSorted = vil.slice().sort(function (a, b) {          // 갯벌 체험이 있는 마을을 먼저
        function score(x) { return (x.ex || []).some(function (e2) { return /갯벌|바지락|조개|백합|맛조개|꼬막/.test(e2.n); }) ? 0 : 1; }
        return score(a) - score(b);
      });
      var v = vilSorted[0], b1 = pickNew(beach.length ? beach : outdoor, 2, seed + 3), i1 = pickNew(indoor, 1, seed + 1)[0], st = [];
      if (v) st.push(step('오전', v.name + ' 갯벌·어촌 체험 (예약 필수 · ' + (v.tel || '전화 확인') + ')'));
      else if (b1[0]) st.push(step('오전', b1[0].name + '에서 물놀이·모래놀이'));
      var pm = i1 || b1[v ? 0 : 1] || pickNew(calm, 1, seed + 6)[0] || pick(spots, 1, seed + 9)[0];
      if (pm) st.push(step('오후', i1 && pm === i1 ? pm.name + ' — 날씨가 궂어도 괜찮은 실내' : spotText(pm)));
      st.push(step('저녁', EAT));
      fillThree(st, spots, seed + 40, spotText);
      courses.push({
        cls: 'kids', badge: '아이들과의 여행', title: NAME + ' 체험 반, 쉬는 시간 반', steps: st,
        why: v ? '어촌체험휴양마을은 간조 시간에 맞춰 열리니 예약할 때 집합 시각을 확인하세요.'
          : (/^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(REGION) ? '해변과 날씨가 궂어도 괜찮은 실내 시설로 구성했습니다.' : '갯벌 체험장이 없어 해변과 실내 시설로 구성했습니다.')
      });
    })();

    /* ---- 그리기 ---- */
    var ok = courses.filter(function (c) { return c.steps.length >= 3; });
    if (ok.length < 3) return;
    grid.innerHTML = '';
    ok.forEach(function (c) {
      var card = el('div', 'course-card auto');
      card.appendChild(el('div', 'course-badge ' + c.cls, c.badge));
      card.appendChild(el('h3', 'serif', c.title));
      c.steps.forEach(function (s) {
        var row = el('div', 'course-step');
        row.appendChild(el('span', 'c-time', s.t));
        var tx = el('span', 'c-text');
        if (s.x.indexOf('{EAT}') > -1) {          // 식사 안내는 맛집 구역으로 가는 링크로 넣는다
          var parts = s.x.split('{EAT}');
          if (parts[0]) tx.appendChild(document.createTextNode(parts[0]));
          tx.appendChild(document.createTextNode('식사는 아래 '));
          var link = el('a', null, '먹거리·인기 맛집'); link.href = '#eat'; tx.appendChild(link);
          tx.appendChild(document.createTextNode('에서 골라 보세요'));
          if (parts[1]) tx.appendChild(document.createTextNode(parts[1]));
        } else { tx.textContent = s.x; }
        row.appendChild(tx);
        card.appendChild(row);
      });
      card.appendChild(el('p', 'course-why', c.why));
      grid.appendChild(card);
    });
    var head = document.querySelector('#course .section-head p');
    if (head) head.textContent = '동행에 따라 어울리는 코스를 ' + MONTH + '월 기준으로 자동으로 구성했습니다. 실제 방문이 많은 곳(관광빅데이터)과 이번 달 축제, 체험마을 정보를 반영합니다.';
    var note = el('p', 'course-src', '자료: 한국관광공사 관광빅데이터(TMAP Mobility 제공)' + (baseLabel ? ' ' + baseLabel + ' 기준' : '') + ' · 한국관광공사 관광지·행사정보 · 바다여행 어촌체험휴양마을 · 매월 자동 갱신 · 영업시간과 예약 여부는 방문 전 확인하세요.');
    grid.parentNode.appendChild(note);
  }).catch(function () { });
})();
