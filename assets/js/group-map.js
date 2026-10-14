/* 묶음 쪽 권역 지도 — 실제 지도 (2026-09-29 주인 지시 「이런 지도 말고 실제 지도로해줘」)
 *
 * ★ 전에는 직접 그린 **그림 지도**였습니다.
 *   땅 모양을 다각형으로 그려 권역 점을 찍었습니다.
 *   가볍고 열쇠도 필요 없었지만, 주인 말씀대로 **실제 지도가 아닙니다** —
 *   섬이 어디인지, 길이 어떤지, 얼마나 먼지를 알 수 없습니다.
 *
 * ★ 지도가 안 떠도 쪽은 그대로 쓸 수 있어야 합니다 (계약-23).
 *   열쇠가 없거나 카카오가 안 오면 **칸을 조용히 숨깁니다.**
 *   옆에 권역 카드가 그대로 있어 고르는 데 지장이 없습니다.
 *
 * ★ 일반·위성 단추는 assets/js/map-type.js 가 답니다.
 */
(function () {
  'use strict';

  var 자료 = window.BADAGAJA_GROUPMAP;
  var 칸 = document.getElementById('groupMap');
  if (!칸 || !자료) { return; }

  var 있는것 = (자료.권역들 || []).filter(function (r) {
    return typeof r.위도 === 'number' && typeof r.경도 === 'number';
  });

  if (!자료.지도키 || !있는것.length) { 숨기기(); return; }

  var s = document.createElement('script');
  s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey='
        + encodeURIComponent(자료.지도키);
  s.onload = function () {
    try { kakao.maps.load(만들기); } catch (e) { 숨기기(); }
  };
  s.onerror = 숨기기;
  document.head.appendChild(s);

  function 숨기기() {
    칸.classList.add('gm-off');
  }

  function 만들기() {
    var 그림 = document.createElement('div');
    그림.className = 'gm-canvas';
    칸.appendChild(그림);
    칸.classList.add('gm-on');

    var 지도 = new kakao.maps.Map(그림, {
      center: new kakao.maps.LatLng(있는것[0].위도, 있는것[0].경도),
      level: 10
    });
    /* ★ **첫 표시부터 바로 조작됩니다** (2026-10-14 주인 직접 지시)
     *
     *   전에는 `setZoomable(false)` 로 잠가 두고 「눌러서 켜기」
     *   오버레이를 덮었습니다. 주인 — 「사람들은 참아, 불편한
     *   것보다 귀찮음을 더 싫어해」. 물때 쪽에서 이미 없앤
     *   절차이며, 묶음 쪽도 같게 맞춥니다.
     *
     *   ★ 쪽 세로 스크롤과 부딪히지 않게 `touch-action` 을
     *     차림표에서 `pan-y pinch-zoom` 으로 둡니다 — 한 손가락
     *     세로 쓸기는 쪽이 받고, 두 손가락 핀치는 지도가 받습니다.
     */
    지도.setZoomable(true);
    지도.setDraggable(true);
    지도.addControl(new kakao.maps.ZoomControl(),
                    kakao.maps.ControlPosition.RIGHT);

    // ★ **눌러서 휠 확대를 켭니다** (2026-09-30 주인 지시)
    //   「지도가 마우스 휠버튼으로 크기 조절되게 만들어」
    //
    //   처음부터 휠을 열어 두면 **쪽을 내리다 지도에 걸려**
    //   화면이 멋대로 확대됩니다. 그래서 포인트 지도와 같은 방식으로,
    //   한 번 누르면 그때부터 휠이 듣게 합니다
    //   (assets/js/point-list.js 의 `map-lock` 과 같은 짜임).
    /* ★ 잠금 오버레이를 **두지 않습니다** (2026-10-14)
       위에서 이미 열어 두었습니다. 덮개를 두면 첫 누름이
       지도에 안 닿아 핀도 못 누릅니다. */

    if (window.BADAGAJA_MAPTYPE) {
      window.BADAGAJA_MAPTYPE.달기(지도, 칸);
    }

    var 테두리 = new kakao.maps.LatLngBounds();
    있는것.forEach(function (r) {
      var 자리 = new kakao.maps.LatLng(r.위도, r.경도);
      var a = document.createElement('a');
      a.className = 'gmp';
      a.href = r.주소;
      a.setAttribute('aria-label', r.이름 + ' 포인트 ' + r.수 + '곳');
      a.innerHTML = '<span class="gmp-dot" aria-hidden="true"></span>'
                  + '<span class="gmp-name"></span>';
      a.querySelector('.gmp-name').textContent = r.이름;
      new kakao.maps.CustomOverlay({
        position: 자리, content: a, yAnchor: 1, zIndex: 3
      }).setMap(지도);
      테두리.extend(자리);
    });

    if (있는것.length > 1) {
      지도.setBounds(테두리, 34, 34, 34, 34);
    } else {
      지도.setLevel(8);
    }

    // 칸 크기가 바뀌면 지도가 어긋납니다 — 다시 맞춥니다
    if (window.ResizeObserver) {
      var 늦게 = null;
      new ResizeObserver(function () {
        clearTimeout(늦게);
        늦게 = setTimeout(function () {
          지도.relayout();
          if (있는것.length > 1) { 지도.setBounds(테두리, 34, 34, 34, 34); }
        }, 120);
      }).observe(그림);
    }
  }
})();
