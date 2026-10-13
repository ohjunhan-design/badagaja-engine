/* 지도 종류 바꾸기 — 일반 / 위성 (2026-09-29 주인 지시 「위성지도도 볼 수 있게 만들고」)
 *
 * ★ 왜 따로 두나
 *   지도가 두 곳에 있습니다 — 묶음 쪽 권역 지도, 권역 쪽 포인트 지도.
 *   단추를 각각 만들면 한쪽만 고치고 다른 쪽을 잊습니다.
 *   한 곳에서 만들어 둘 다 씁니다.
 *
 * ★ 왜 위성이 필요한가
 *   갯바위·갯벌은 **길 이름이 없습니다.** 일반 지도에서는
 *   빈 바다로만 보입니다. 위성으로 보면 바위가 어디까지
 *   드러나는지, 어디로 걸어 들어가는지가 보입니다.
 *
 * ★ 고른 것을 기억합니다 — 쪽을 옮길 때마다 다시 누르게 하지 않습니다.
 *   다만 브라우저가 막아 두면 그냥 일반 지도로 둡니다(터지지 않습니다).
 */
(function () {
  'use strict';

  var 기억열쇠 = 'badagaja.map-type';

  function 기억읽기() {
    try { return localStorage.getItem(기억열쇠); } catch (e) { return null; }
  }
  function 기억쓰기(값) {
    try { localStorage.setItem(기억열쇠, 값); } catch (e) { /* 막혀 있으면 그만둡니다 */ }
  }

  /* 지도 위에 「일반 · 위성」 단추를 답니다.
     지도 = kakao.maps.Map · 칸 = 단추를 담을 곳 */
  function 달기(지도, 칸) {
    if (!window.kakao || !kakao.maps || !지도 || !칸) { return; }

    var 갈래 = [
      ['일반', kakao.maps.MapTypeId.ROADMAP],
      ['위성', kakao.maps.MapTypeId.HYBRID]   // HYBRID = 위성 + 글자
    ];
    var 줄 = document.createElement('div');
    줄.className = 'map-type';
    줄.setAttribute('role', 'group');
    줄.setAttribute('aria-label', '지도 종류');

    /* ★ **처음에는 위성** 입니다 (2026-10-13 주인 지시)
       주인 — 「시작할때 위성지도가 나왔으면 좋겠고」

       바닷가는 자리가 곧 정보입니다. 일반 지도는 바위·갯벌이
       빈 바다로만 보이지만, 위성은 어디까지 걸어 들어갈 수
       있는지가 그대로 보입니다.

       ★ 손님이 **일부러 「일반」을 고르면 그 선택을 지킵니다.**
         기억에 '일반' 이 적혀 있을 때만 일반으로 엽니다. */
    var 첫것 = 기억읽기() === '일반' ? 0 : 1;
    var 단추들 = [];

    갈래.forEach(function (한, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'mt-btn' + (i === 첫것 ? ' on' : '');
      b.textContent = 한[0];
      b.setAttribute('aria-pressed', i === 첫것 ? 'true' : 'false');
      b.addEventListener('click', function () {
        지도.setMapTypeId(한[1]);
        기억쓰기(한[0]);
        단추들.forEach(function (x, j) {
          x.classList.toggle('on', j === i);
          x.setAttribute('aria-pressed', j === i ? 'true' : 'false');
        });
      });
      단추들.push(b);
      줄.appendChild(b);
    });

    if (첫것 === 1) { 지도.setMapTypeId(갈래[1][1]); }
    칸.appendChild(줄);
    return 줄;
  }

  window.BADAGAJA_MAPTYPE = { 달기: 달기 };
})();
