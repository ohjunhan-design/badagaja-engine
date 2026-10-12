/* 바다 가까운 묵을 곳 (2026-10-12 주인 지시 ④)
 *
 * ★ 왜 이 칸이 생겼나
 *
 *   첫 화면이 「관광·맛집·숙소」를 약속하는데 **숙소만 없었습니다.**
 *   `engine/hubs_travel.py` 주석에 그 까닭이 적혀 있습니다 —
 *   「숙소 자료가 없습니다 … 없는 것을 있는 척 보내면 안 됩니다」.
 *
 *   그런데 **자료는 있었습니다.** `api/tour.php?kind=stay` 가
 *   한국관광공사 자료로 전남 227곳·제주 206곳을 이미 내주고
 *   있었습니다. 쪽이 쓰지 않았을 뿐입니다.
 *
 * ★ 자료가 있는 곳만 보입니다
 *
 *   전남 15권역 + 제주 7권역 = **22권역**뿐입니다.
 *   나머지 35권역은 `items` 가 비어 오므로 **칸을 지웁니다.**
 *   빈 표를 남기면 「눌렀는데 아무것도 없음」이 됩니다 —
 *   단추가 거짓말을 하는 것과 같습니다.
 *   권역 목록을 여기 **박지 않습니다.** 자료가 늘면 저절로 보입니다.
 *
 * ★ 개인 숙소로 바로 보내지 않습니다 (주인 규칙 12)
 *   누르면 지도 검색으로 갑니다. 예약 사이트로 보내지 않습니다.
 *
 * 짜임은 `tmap-rank.js` 를 그대로 따릅니다 — 같은 일을 다른 꼴로
 * 하면 나중에 한쪽만 고치게 됩니다.
 */
(function () {
  'use strict';
  var 자료 = window.BADAGAJA_STAY;
  if (!자료 || !자료.권역) { return; }
  var 칸 = document.getElementById('stayList');
  if (!칸) { return; }

  var API = 자료.api || 'api/';
  var 몇개 = 8;                       // 너무 길면 쪽이 늘어집니다

  function 숨기기() { 칸.remove(); }

  function 지도검색(말) {
    return 'https://map.kakao.com/?q=' + encodeURIComponent(말);
  }

  function 만들기(태그, 클래스, 글) {
    var e = document.createElement(태그);
    if (클래스) { e.className = 클래스; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  // 「전남광주통합특별시 여수시 돌산읍 …」 → 「돌산읍」
  // 앞의 시·도와 시군구는 이미 권역 이름으로 아니까 뒤만 보여 줍니다.
  function 짧은주소(주소) {
    var 칸들 = String(주소 || '').trim().split(/\s+/);
    if (칸들.length <= 2) { return ''; }
    return 칸들.slice(2, 4).join(' ');
  }

  fetch(API + 'tour.php?kind=stay&region=' + encodeURIComponent(자료.권역))
    .then(function (r) { if (!r.ok) { throw 0; } return r.json(); })
    .then(function (d) {
      if (!d || !d.ok || !d.items || !d.items.length) { return 숨기기(); }

      칸.appendChild(만들기('h2', 'stay-h', '🛏 바다 가까운 묵을 곳'));
      칸.appendChild(만들기('p', 'stay-sub',
        '한국관광공사 숙박 정보입니다. 값·빈방은 담지 않습니다 — '
        + '누르면 지도에서 찾아 드립니다.'));

      var 목록 = 만들기('ol', 'stay-ol');
      d.items.slice(0, 몇개).forEach(function (x) {
        if (!x || !x.name) { return; }
        var 줄 = 만들기('li');
        var a = document.createElement('a');
        a.href = 지도검색((자료.이름 || '') + ' ' + x.name);
        a.target = '_blank';
        a.rel = 'noopener';
        a.appendChild(만들기('span', 'stay-name', x.name));
        if (x.type) { a.appendChild(만들기('span', 'stay-type', x.type)); }
        var 어디 = 짧은주소(x.addr);
        if (어디) { a.appendChild(만들기('span', 'stay-where', 어디)); }
        줄.appendChild(a);
        목록.appendChild(줄);
      });
      if (!목록.children.length) { return 숨기기(); }
      칸.appendChild(목록);

      // ★ **보여 준 것을 뺀 나머지**를 적습니다 (2026-10-12)
      //   전에는 전체 수를 적어 「8곳 보여 주고 42곳이 더」가 됐습니다.
      //   손님이 세어 보면 바로 틀린 것을 압니다.
      if (d.items.length > 목록.children.length) {
        칸.appendChild(만들기('p', 'stay-more',
          '이 둘레에 ' + (d.items.length - 목록.children.length)
          + '곳이 더 있습니다.'));
      }
      칸.hidden = false;
    })
    .catch(숨기기);
}());
