/* 전국 물때 지도 — 권역을 **지도에서 고릅니다** (2026-10-02)
 *
 * ★ 새로 만든 것이 아니라 **되살린 것**입니다
 *   옛 사이트에 `oldsite/js/tide-map.js` 가 있었습니다. 주인 지시로
 *   만든 것이었는데(2026-09-23), 새 사이트를 짜며 빠뜨렸습니다.
 *   주인이 먼저 찾으셨습니다 — 「언제 물때 페이지에 지도가 들어갈까?」
 *
 *   옛 것의 **배율 단계**를 그대로 살립니다.
 *     배율 13 이상 — 점만
 *     배율 12      — 권역 이름
 *     배율 11 이하 — 이름 + **오늘 간조 시각**
 *
 * ★ 겉모습은 지피티 시안 `tide-map-selector-v1.html` 그대로입니다.
 *   「옛 동작을 되살리되, 현재 지도 UI 규칙에 맞춰 다시 입힙니다.
 *     처음부터 새로 짜지 않습니다」
 *
 * ★ 핀을 눌러도 **바로 넘어가지 않습니다**
 *   「지도에서 여러 권역을 비교해보고 싶은 사람에게 핀 클릭 즉시
 *     페이지 이동은 너무 공격적입니다」 — 오른쪽 카드만 바뀌고,
 *   손님이 단추를 눌러야 넘어갑니다.
 *
 * ★ 카드 57장은 **지우지 않습니다** (계약-23)
 *   접어 두고 「57권역 목록으로 보기」로 폅니다. 지도를 못 받으면
 *   저절로 펴집니다.
 */
(function () {
  'use strict';

  var 칸 = document.getElementById('tideMap');
  if (!칸) { return; }
  var 자료칸 = document.getElementById('물때지도자료');
  if (!자료칸) { return; }
  var 자료;
  try { 자료 = JSON.parse(자료칸.textContent); } catch (e) { return; }

  var 권역들 = (자료.권역들 || []).filter(function (r) {
    return typeof r.위도 === 'number' && typeof r.경도 === 'number';
  });
  if (!권역들.length || !자료.지도키 || !window.BADAGAJA_MAP) {
    펴기(); return;
  }

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  // 지도를 못 받으면 **카드 목록을 저절로 폅니다** (계약-23)
  function 펴기() {
    칸.hidden = true;
    var d = document.getElementById('allRegions');
    if (d) { d.open = true; }
  }

  var 지도 = null, 고른것 = null, 지금모드 = '';
  var 카드 = document.getElementById('tidePick');
  var 거르개 = document.getElementById('tideMapFilter');
  var 지금묶음 = '전국';

  window.BADAGAJA_MAP.불러오기(자료.지도키).then(그리기).catch(펴기);

  function 그리기() {
    var 판 = 만들기('div', 'tm-canvas');
    칸.appendChild(판);
    // 전국이 한 장에 들어오는 배율로 엽니다 (옛 것과 같은 자리)
    지도 = window.BADAGAJA_MAP.만들기(판, { 중심: [35.55, 127.6], 배율: 13 });

    조작단추();
    핀찍기();
    맞추기();
    setTimeout(맞추기, 300);
    setTimeout(맞추기, 1200);

    // 배율이 바뀔 때마다 핀 꼴을 바꿉니다
    if (window.kakao && kakao.maps) {
      kakao.maps.event.addListener(지도.날것, 'zoom_changed', 꼴고치기);
      kakao.maps.event.addListener(지도.날것, 'idle', 꼴고치기);
    }
    꼴고치기();
    if (권역들.length) { 고르기(권역들[0], true); }
  }

  function 보일것() {
    if (지금묶음 === '전국') { return 권역들; }
    return 권역들.filter(function (r) { return r.묶음이름 === 지금묶음; });
  }

  function 맞추기() {
    if (!지도) { return; }
    지도.맞추기(보일것().map(function (r) { return [r.위도, r.경도]; }));
  }

  // ── 배율에 따라 핀 꼴 바꾸기 (옛 것 그대로) ──────────────
  function 꼴고치기() {
    if (!지도 || !지도.날것) { return; }
    var 배 = 지도.날것.getLevel();
    var 모드 = 배 >= 13 ? 'dot' : (배 >= 12 ? 'name' : 'tide');
    if (모드 === 지금모드) { return; }
    지금모드 = 모드;
    권역들.forEach(function (r) {
      if (!r.단추) { return; }
      r.단추.className = 'tm-pin tm-pin--' + 모드
                         + (r === 고른것 ? ' on' : '');
      r.단추.textContent = '';
      if (모드 === 'dot') { return; }
      r.단추.appendChild(만들기('span', null, r.이름));
      if (모드 === 'tide' && r.간조) {
        r.단추.appendChild(만들기('small', null, '간조 ' + r.간조));
      }
    });
  }

  function 핀찍기() {
    권역들.forEach(function (r) {
      var b = 만들기('button', 'tm-pin tm-pin--dot');
      b.type = 'button';
      b.title = r.이름;
      b.setAttribute('aria-label', r.이름 + ' 물때 보기');
      b.addEventListener('click', function (e) {
        e.stopPropagation(); 고르기(r);
      });
      r.단추 = b;
      r.올린것 = 지도.핀(r.위도, r.경도, b, { 층: 2 });
    });
  }

  // ── 지도 위 조작 — 권역 지도와 **같은 자리** ───────────
  function 조작단추() {
    var 종류칸 = 만들기('div', 'tm-type');
    종류칸.setAttribute('role', 'group');
    종류칸.setAttribute('aria-label', '지도 종류');
    var 기억 = null;
    try { 기억 = localStorage.getItem('badagaja.map-type'); } catch (e) { /* 막히면 그만 */ }
    var 첫것 = (기억 === '위성') ? 1 : 0;
    var 들 = [];
    ['일반', '위성'].forEach(function (이름, i) {
      var b = 만들기('button', 'tm-type-b' + (i === 첫것 ? ' on' : ''), 이름);
      b.type = 'button';
      b.setAttribute('aria-pressed', i === 첫것 ? 'true' : 'false');
      b.addEventListener('click', function () {
        지도.종류(이름);
        try { localStorage.setItem('badagaja.map-type', 이름); } catch (e) { /* 그만 */ }
        들.forEach(function (x, j) {
          x.classList.toggle('on', j === i);
          x.setAttribute('aria-pressed', j === i ? 'true' : 'false');
        });
      });
      들.push(b); 종류칸.appendChild(b);
    });
    if (첫것 === 1) { 지도.종류('위성'); }
    칸.appendChild(종류칸);

    var 배율칸 = 만들기('div', 'tm-zoom');
    배율칸.setAttribute('aria-label', '지도 확대 축소');
    [['＋', 1, '확대'], ['－', -1, '축소']].forEach(function (x) {
      var b = 만들기('button', 'tm-zoom-b', x[0]);
      b.type = 'button';
      b.setAttribute('aria-label', x[2]);
      b.addEventListener('click', function () { 지도.확대(x[1]); 꼴고치기(); });
      배율칸.appendChild(b);
    });
    칸.appendChild(배율칸);

    // 범례는 **작게** — 이 지도는 낚시/해루질을 가르지 않습니다
    var 범 = 만들기('div', 'tm-legend');
    범.appendChild(만들기('span', null, '확대하면 오늘 간조 시각이 보입니다'));
    칸.appendChild(범);

    var 켬 = false;
    var 켜기 = 만들기('button', 'tm-lock', '지도 이동 켜기');
    켜기.type = 'button';
    켜기.setAttribute('aria-pressed', 'false');
    켜기.addEventListener('click', function () {
      켬 = !켬;
      지도.조작(켬);
      켜기.textContent = 켬 ? '지도 이동 끄기' : '지도 이동 켜기';
      켜기.setAttribute('aria-pressed', String(켬));
    });
    칸.appendChild(켜기);
    지도.누를때(function () {
      if (!켬 && window.innerWidth > 760) { 켬 = true; 지도.조작(true); }
    });

    // 광역 거르기 — 57개를 다 두지 않고 묶음으로 (지피티 지시)
    if (거르개) {
      [].forEach.call(거르개.querySelectorAll('button[data-group]'),
        function (b) {
          b.addEventListener('click', function () {
            지금묶음 = b.getAttribute('data-group');
            [].forEach.call(거르개.querySelectorAll('button[data-group]'),
              function (x) {
                var 켜 = x === b;
                x.classList.toggle('on', 켜);
                x.setAttribute('aria-pressed', String(켜));
              });
            권역들.forEach(function (r) {
              if (r.단추) {
                r.단추.hidden = !(지금묶음 === '전국'
                                  || r.묶음이름 === 지금묶음);
              }
            });
            맞추기();
          });
        });
    }
  }

  // ── 고른 권역 카드 ────────────────────────────────────
  function 고르기(r, 처음) {
    고른것 = r;
    권역들.forEach(function (x) {
      if (x.단추) { x.단추.classList.toggle('on', x === r); }
    });
    if (!카드) { return; }

    var 그림 = 카드.querySelector('.tp-img');
    if (그림 && r.사진) {
      if (그림.getAttribute('src') !== r.사진) { 그림.setAttribute('src', r.사진); }
      그림.alt = r.이름 + ' 바다';
    }
    var 이 = 카드.querySelector('.tp-name'); if (이) { 이.textContent = r.이름; }
    var 한 = 카드.querySelector('.tp-sub'); if (한) { 한.textContent = r.한줄 || ''; }
    var 관 = 카드.querySelector('.tp-station');
    if (관) {
      관.textContent = r.관측소 ? (r.관측소 + ' 관측소 기준') : '';
    }
    ['tp-go', 'tp-guide'].forEach(function (c, i) {
      var a = 카드.querySelector('.' + c);
      if (a) { a.href = i === 0 ? (r.물때주소 || r.주소) : r.주소; }
    });
    // 오늘 물때 — **계산은 tide.js 한 곳에서** 합니다 (계약-01).
    //   여기서는 그 칸에 권역만 알려 주고 다시 그리게 합니다.
    var 띠 = document.getElementById('tideStrip');
    if (띠 && 띠.getAttribute('data-region') !== r.id) {
      띠.setAttribute('data-region', r.id);
      띠.setAttribute('data-station', r.관측소 || '');
      if (window.BADAGAJA_TIDE_REDRAW) { window.BADAGAJA_TIDE_REDRAW(); }
    }
    if (!처음 && window.innerWidth <= 760) {
      카드.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
})();
