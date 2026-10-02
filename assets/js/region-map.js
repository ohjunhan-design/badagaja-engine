/* 권역 쪽 포인트 지도 + 사진카드 (2026-10-02)
 *
 * ★ 지피티가 준 `region-point-map-controls-v2.html` 을 그대로 옮겼습니다.
 *   주인 지시 — 「디자인부분은 너가 항상 의뢰를 해서 지피티의
 *   사진이 오면 그걸 사용하면됨」. 치수·색·자리를 다시 해석하지
 *   않았습니다.
 *
 * ★ 왜 권역 쪽에 지도가 필요한가
 *   재 보니 모바일 390px 에서 **낚시 포인트가 6.2번째 화면**에서야
 *   나왔습니다. 이 사이트에서 손님이 가장 알고 싶은 것인데
 *   네 화면 반을 넘겨야 닿았습니다.
 *   지피티 — 「43개 포인트를 처음부터 다 노출할 이유가 없습니다.
 *     지도에서 하나 선택 → 선택한 카드 1개 크게. 화면 하나에서
 *     해결됩니다」
 *
 * ★ 자리 (지피티가 확정) — 네 모서리가 겹치지 않게
 *     지도 **밖** 위 : 전체 / 낚시 / 해루질 거르기
 *     좌상단        : 일반 / 위성
 *     우상단        : ＋ / －
 *     좌하단        : 낚시·해루질 색 범례
 *     하단 가운데   : 「지도 이동 켜기」 — **모바일만**
 *
 * ★ 덮개로 지도를 통째로 막지 않습니다 (바뀐 점)
 *   전에는 투명 단추가 지도를 다 덮어 **핀을 누르는 데도 한
 *   단계가 더** 들었습니다. 이제 끌기·확대만 잠그고 핀은
 *   잠긴 채로도 바로 눌립니다.
 *
 * ★ 지도가 안 떠도 쪽은 그대로 쓸 수 있어야 합니다 (계약-23).
 *   아래 낚시·해루질 단추가 그대로 있으니 칸만 조용히 숨깁니다.
 */
(function () {
  'use strict';

  var 칸 = document.getElementById('regionPointMap');
  if (!칸) { return; }
  var 자료칸 = document.getElementById('권역지도자료');
  if (!자료칸) { return; }
  var 자료;
  try { 자료 = JSON.parse(자료칸.textContent); } catch (e) { return; }

  var 포인트 = (자료.포인트 || []).filter(function (p) {
    return typeof p.위도 === 'number' && typeof p.경도 === 'number';
  });
  if (!포인트.length || !자료.지도키 || !window.BADAGAJA_MAP) {
    칸.hidden = true; return;
  }

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  var 지도 = null, 핀들 = [], 지금갈래 = '전체', 고른것 = null;
  var 거르개 = document.getElementById('regionMapFilter');
  var 카드 = document.getElementById('regionPickCard');

  // ── 지도 ──────────────────────────────────────────────
  window.BADAGAJA_MAP.불러오기(자료.지도키).then(그리기).catch(function () {
    칸.hidden = true;
  });

  function 그리기() {
    var 판 = 만들기('div', 'rm-canvas');
    칸.appendChild(판);
    지도 = window.BADAGAJA_MAP.만들기(판, {
      중심: [포인트[0].위도, 포인트[0].경도], 배율: 8
    });

    조작단추();
    핀찍기();
    맞추기();
    setTimeout(맞추기, 300);
    setTimeout(맞추기, 1200);
    if (포인트.length) { 고르기(포인트[0], true); }
  }

  function 맞추기() {
    if (!지도) { return; }
    지도.맞추기(보일것().map(function (p) { return [p.위도, p.경도]; }));
  }

  function 보일것() {
    if (지금갈래 === '전체') { return 포인트; }
    return 포인트.filter(function (p) { return p.갈래 === 지금갈래; });
  }

  // ── 지도 위 조작 ───────────────────────────────────────
  function 조작단추() {
    // ① 좌상단 — 일반 / 위성
    //   ★ 고른 것을 기억합니다 (map-type.js 와 같은 열쇠를 씁니다)
    //     쪽을 옮길 때마다 다시 누르게 하지 않습니다.
    var 종류칸 = 만들기('div', 'rm-type');
    종류칸.setAttribute('role', 'group');
    종류칸.setAttribute('aria-label', '지도 종류');
    var 기억 = null;
    try { 기억 = localStorage.getItem('badagaja.map-type'); } catch (e) { /* 막혀 있으면 그만 */ }
    var 첫것 = (기억 === '위성') ? 1 : 0;
    var 종류들 = [];
    ['일반', '위성'].forEach(function (이름, i) {
      var b = 만들기('button', 'rm-type-b' + (i === 첫것 ? ' on' : ''), 이름);
      b.type = 'button';
      b.setAttribute('aria-pressed', i === 첫것 ? 'true' : 'false');
      b.addEventListener('click', function () {
        지도.종류(이름);
        try { localStorage.setItem('badagaja.map-type', 이름); } catch (e) { /* 그만 */ }
        종류들.forEach(function (x, j) {
          x.classList.toggle('on', j === i);
          x.setAttribute('aria-pressed', j === i ? 'true' : 'false');
        });
      });
      종류들.push(b);
      종류칸.appendChild(b);
    });
    if (첫것 === 1) { 지도.종류('위성'); }
    칸.appendChild(종류칸);

    // ② 우상단 — ＋ / －
    var 배율칸 = 만들기('div', 'rm-zoom');
    배율칸.setAttribute('aria-label', '지도 확대 축소');
    [['＋', 1, '확대'], ['－', -1, '축소']].forEach(function (x) {
      var b = 만들기('button', 'rm-zoom-b', x[0]);
      b.type = 'button';
      b.setAttribute('aria-label', x[2]);
      b.addEventListener('click', function () { 지도.확대(x[1]); });
      배율칸.appendChild(b);
    });
    칸.appendChild(배율칸);

    // ④ 좌하단 — 색 범례
    var 범례 = 만들기('div', 'rm-legend');
    [['fish', '낚시'], ['glean', '해루질']].forEach(function (x) {
      var 한 = 만들기('span', null);
      한.appendChild(만들기('i', 'rm-dot rm-dot--' + x[0]));
      한.appendChild(document.createTextNode(x[1]));
      범례.appendChild(한);
    });
    칸.appendChild(범례);

    // ③ 하단 가운데 — 지도 이동 켜기 (모바일만. 차림표가 가립니다)
    //   ★ 지도를 **덮지 않습니다.** 잠긴 채로도 핀은 눌립니다.
    var 켬 = false;
    var 켜기 = 만들기('button', 'rm-lock', '지도 이동 켜기');
    켜기.type = 'button';
    켜기.setAttribute('aria-pressed', 'false');
    켜기.addEventListener('click', function () {
      켬 = !켬;
      지도.조작(켬);
      켜기.textContent = 켬 ? '지도 이동 끄기' : '지도 이동 켜기';
      켜기.setAttribute('aria-pressed', String(켬));
    });
    칸.appendChild(켜기);

    // PC 에서는 눌러서 켭니다 — 단추가 안 보이므로 지도를 눌러 풉니다
    지도.누를때(function () {
      if (!켬 && window.innerWidth > 760) { 켬 = true; 지도.조작(true); }
    });

    // 지도 **밖** 거르기 — 네 모서리를 지도 조작에 내줍니다
    if (거르개) {
      [].forEach.call(거르개.querySelectorAll('button[data-kind]'),
        function (b) {
          b.addEventListener('click', function () {
            지금갈래 = b.getAttribute('data-kind');
            [].forEach.call(거르개.querySelectorAll('button[data-kind]'),
              function (x) {
                var 켜 = x === b;
                x.classList.toggle('on', 켜);
                x.setAttribute('aria-pressed', String(켜));
              });
            핀보이기();
            맞추기();
          });
        });
    }
  }

  // ── 핀 ────────────────────────────────────────────────
  function 핀찍기() {
    // 같은 자리에 여럿이면 조금씩 벌려 놓습니다 — 안 그러면 하나만 보입니다
    var 본자리 = {};
    포인트.forEach(function (p) {
      var 열쇠 = p.위도.toFixed(4) + ',' + p.경도.toFixed(4);
      var n = 본자리[열쇠] = (본자리[열쇠] || 0) + 1;
      if (n > 1) {
        var 각 = n * 2.4, r = 0.0009 * Math.sqrt(n);
        p.그릴위도 = p.위도 + r * Math.sin(각);
        p.그릴경도 = p.경도 + r * Math.cos(각);
      } else { p.그릴위도 = p.위도; p.그릴경도 = p.경도; }
    });

    포인트.forEach(function (p) {
      var b = 만들기('button',
        'rm-pin rm-pin--' + (p.갈래 === '해루질' ? 'glean' : 'fish'),
        p.갈래 === '해루질' ? '해' : '낚');
      b.type = 'button';
      b.title = p.이름;
      b.setAttribute('aria-label', p.이름 + ' — ' + (p.갈래 || '낚시'));
      b.addEventListener('click', function (e) {
        e.stopPropagation(); 고르기(p);
      });
      p.단추 = b;
      p.올린것 = 지도.핀(p.그릴위도, p.그릴경도, b, { 층: p.어림 ? 1 : 2 });
      핀들.push(p);
    });
  }

  function 핀보이기() {
    포인트.forEach(function (p) {
      var 보임 = (지금갈래 === '전체' || p.갈래 === 지금갈래);
      if (p.단추) { p.단추.hidden = !보임; }
    });
  }

  // ── 사진카드 ──────────────────────────────────────────
  function 고르기(p, 처음) {
    고른것 = p;
    포인트.forEach(function (x) {
      if (x.단추) { x.단추.classList.toggle('on', x === p); }
    });
    if (!카드) { return; }
    카드.hidden = false;

    var 그림 = 카드.querySelector('.rp-img');
    if (그림) {
      var 길 = p.사진 || 자료.대표사진 || '';
      if (길 && 그림.getAttribute('src') !== 길) { 그림.setAttribute('src', 길); }
      그림.alt = p.이름 + ' 둘레 바다';
    }
    var 제목 = 카드.querySelector('.rp-name');
    if (제목) { 제목.textContent = p.이름; }
    var 수 = 카드.querySelector('.rp-count');
    if (수) {
      수.textContent = (p.갈래 === '해루질' ? '해루질' : '낚시') + ' 포인트';
    }
    var 글 = 카드.querySelector('.rp-desc');
    if (글) { 글.textContent = p.지형 || 자료.한줄 || ''; }
    var 화살 = 카드.querySelector('.rp-arrow');
    if (화살 && p.주소) { 화살.href = p.주소; }
    if (!처음) {
      // 고른 것이 보이게 — 모바일은 카드가 지도 아래라 안 보입니다
      if (window.innerWidth <= 760) {
        카드.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }
})();
