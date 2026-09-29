/* 요즘 많이 찾아가는 곳 — 티맵 목적지 인기 순위 (2026-09-29 주인 지적)
 *
 * ★ 「맛집정보에 예전 티맵데이터기반 추천이 있었는데 그게 사라졌어」
 *
 *   옛 쪽에는 `#tmapRank` 칸이 있었습니다. 새 쪽에는 **아예 없었습니다.**
 *   자료(api/places.php)는 그대로 살아 있었습니다 —
 *   한국관광공사 관광빅데이터(TMAP Mobility 제공).
 *
 * ★ **맛 평가가 아닙니다.** 내비게이션 목적지 순위입니다.
 *   그대로 밝힙니다. 「맛집 순위」라 하면 거짓이 됩니다.
 *
 * ★ 개인 가게 쪽으로 연결하지 않습니다 (주인 규칙 12).
 *   누르면 **카카오 지도 검색**으로 갑니다 — 어디인지만 알려 줍니다.
 *
 * ★ 자료를 못 받으면 **칸을 조용히 없앱니다** (계약-23).
 *   빈 네모가 남으면 「뭔가 깨졌나」 싶습니다.
 *
 * ★ api 주소는 밖에서 받습니다. 묶음 쪽은 주소가 폴더(/chungnam/)라
 *   'api/...' 로 고정하면 한 칸 아래를 가리켜 404 가 납니다.
 *   (2026-09-29 물때 그래프에서 똑같이 겪었습니다)
 */
(function () {
  'use strict';

  var 자료 = window.BADAGAJA_TMAP;
  var 칸 = document.getElementById('tmapRank');
  if (!칸 || !자료 || !자료.권역) { return; }

  var API = 자료.api || 'api/';

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  function 숨기기() { 칸.remove(); }

  function 지도검색(말) {
    return 'https://map.kakao.com/?q=' + encodeURIComponent(말);
  }

  fetch(API + 'places.php?region=' + encodeURIComponent(자료.권역)
        + '&type=food&limit=40')
    .then(function (r) { if (!r.ok) { throw 0; } return r.json(); })
    .then(function (d) {
      // ★ 서버가 모르는 권역이면 **딴 권역 자료**를 돌려줍니다.
      //   그대로 보여 주면 거짓말이 됩니다 — 권역이 다르면 접습니다.
      if (!d || !d.ok || !d.items || !d.items.length
          || d.region !== 자료.권역) {
        return 숨기기();
      }

      var 카페 = d.items.filter(function (x) {
        return /카페|찻집/.test(x.group || x.category || '');
      });
      var 밥집 = d.items.filter(function (x) {
        return !/카페|찻집/.test(x.group || x.category || '');
      });

      칸.textContent = '';
      var 머리 = 만들기('div', 'tr-head');
      머리.appendChild(만들기('h3', 'serif', '🚗 요즘 많이 찾아가는 곳'));
      머리.appendChild(만들기('p', 'tr-why',
        '내비게이션 목적지 검색을 바탕으로 한 순위입니다 ('
        + (d.baseLabel || '') + ' 기준). '
        + '맛 평가가 아니라 얼마나 많이 찾아갔는가입니다.'));
      칸.appendChild(머리);

      var 탭 = 만들기('div', 'tr-tabs');
      var 목록 = 만들기('ol', 'tr-list');

      function 그리기(것들) {
        목록.textContent = '';
        것들.slice(0, 10).forEach(function (x, i) {
          var 말 = 자료.이름 + ' ' + x.name + (x.branch ? ' ' + x.branch : '');
          var li = 만들기('li');
          var a = 만들기('a');
          a.href = 지도검색(말);
          a.target = '_blank';
          a.rel = 'noopener';
          a.setAttribute('aria-label',
            (i + 1) + '위 ' + x.name + ' — 지도에서 보기');
          a.appendChild(만들기('b', 'rk', String(i + 1)));
          a.appendChild(만들기('span', 'nm',
            x.name + (x.branch ? ' ' + x.branch : '')));
          a.appendChild(만들기('span', 'ct', x.category || ''));
          li.appendChild(a);
          목록.appendChild(li);
        });
      }

      [['식당', 밥집], ['카페', 카페]].forEach(function (한, i) {
        if (!한[1].length) { return; }
        var b = 만들기('button', i === 0 ? 'on' : '',
          한[0] + ' ' + Math.min(10, 한[1].length) + '곳');
        b.type = 'button';
        b.addEventListener('click', function () {
          [].forEach.call(탭.children, function (x) {
            x.classList.toggle('on', x === b);
          });
          그리기(한[1]);
        });
        탭.appendChild(b);
      });

      칸.appendChild(탭);
      칸.appendChild(목록);
      칸.appendChild(만들기('p', 'tr-src',
        '출처 · ' + (d.source || '한국관광공사 관광빅데이터(TMAP Mobility 제공)')
        + ' · 누르면 지도에서 찾아 줍니다. 영업 여부는 가시기 전에 확인해 주세요.'));

      그리기(밥집.length ? 밥집 : 카페);
      칸.hidden = false;
    })
    .catch(숨기기);
})();
