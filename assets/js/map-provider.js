/* 지도 제공자 경계 — **카카오 전용 코드를 이 파일에 가둡니다** (2026-10-02)
 *
 * ★ 왜 만들었나
 *   주인 질문 — 「카카오 api가 좋은지 네이버 api 사용이 좋은지
 *   물어봐줘, 추후에라도 변경할테니」
 *
 *   지피티 판단 — 「지금은 **카카오 유지**가 맞습니다. 카카오는
 *   지금 필요한 ROADMAP/HYBRID · ZoomControl · CustomOverlay ·
 *   LatLngBounds · setDraggable · setZoomable 을 모두 공식 API 로
 *   제공하고, **이미 검증되어 있습니다.** 지금 바꾸면 디자인
 *   개선보다 지도 SDK 교체 작업이 더 커집니다」
 *
 *   「다만 **갈아끼울 자리는 만들어 둡니다.** 거대한 지도 추상화
 *   계층을 만들지는 마세요. 카카오 전용 코드를 한 파일에 가두고,
 *   바깥에서는 공통 이름 몇 개만 호출하는 정도로 둡니다」
 *
 * ★ 그래서 이 파일이 하는 일은 **딱 그만큼**입니다.
 *   지금은 카카오 하나뿐입니다. 네이버로 바꿀 일이 생기면
 *   그때 `네이버지도()` 를 더하면 됩니다. 미리 만들지 않습니다.
 *
 * 바깥에서 쓰는 이름 (제공자가 바뀌어도 이것만 그대로면 됩니다)
 *   불러오기(열쇠)        → 약속. SDK 를 싣습니다
 *   만들기(칸, {중심,배율}) → 지도 하나
 *   .종류(이름)           → '일반' | '위성'
 *   .조작(켤까)           → 끌기·확대를 켜고 끕니다
 *   .맞추기(자리들, 여백)  → 다 보이게 범위를 맞춥니다
 *   .핀(자리, 요소, 옵션)  → 핀 하나. 돌려받은 것에 .지우기()
 *   .어림원(자리, 반지름)  → 대략 위치 점선 원
 *   .확대(만큼)           → + / −
 *   .누를때(함수)         → 지도를 누르면
 */
(function () {
  'use strict';

  var 실린것 = null;        // SDK 를 두 번 싣지 않습니다

  function 불러오기(열쇠) {
    if (실린것) { return 실린것; }
    실린것 = new Promise(function (됐다, 안됐다) {
      if (window.kakao && window.kakao.maps && window.kakao.maps.Map) {
        return 됐다();
      }
      if (!열쇠) { return 안됐다(new Error('지도 열쇠가 없습니다')); }
      var s = document.createElement('script');
      s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey='
            + encodeURIComponent(열쇠);
      s.onload = function () {
        try { kakao.maps.load(function () { 됐다(); }); }
        catch (e) { 안됐다(e); }
      };
      s.onerror = function () { 안됐다(new Error('지도를 불러오지 못했습니다')); };
      document.head.appendChild(s);
    });
    return 실린것;
  }

  function 자리(위도, 경도) { return new kakao.maps.LatLng(위도, 경도); }

  function 만들기(칸, 옵션) {
    옵션 = 옵션 || {};
    var 중심 = 옵션.중심 || [36.5, 127.8];
    var 지도 = new kakao.maps.Map(칸, {
      center: 자리(중심[0], 중심[1]),
      level: 옵션.배율 || 9
    });
    // ★ 처음에는 **잠가 둡니다** — 쪽을 넘기다 손가락이 지도에 닿으면
    //   쪽이 안 넘어가고 지도만 움직입니다. 핀은 잠긴 채로도 눌립니다.
    지도.setZoomable(false);
    지도.setDraggable(false);

    var 것 = {
      날것: 지도,

      종류: function (이름) {
        지도.setMapTypeId(이름 === '위성'
          ? kakao.maps.MapTypeId.HYBRID      // 위성 + 글자
          : kakao.maps.MapTypeId.ROADMAP);
        return 것;
      },

      조작: function (켤까) {
        지도.setZoomable(!!켤까);
        지도.setDraggable(!!켤까);
        return 것;
      },

      확대: function (만큼) {
        지도.setLevel(지도.getLevel() - (만큼 || 1));
        return 것;
      },

      맞추기: function (자리들, 여백) {
        if (!자리들 || !자리들.length) { return 것; }
        var 테 = new kakao.maps.LatLngBounds();
        자리들.forEach(function (p) { 테.extend(자리(p[0], p[1])); });
        지도.relayout();
        // ★ 여백을 **고정 px** 로 주면 좁은 화면에서 쓸 폭이 거의 안 남아
        //   지도가 엉뚱하게 넓어집니다 — 휴대폰에서 서울까지 보였습니다
        //   (2026-09-26). 지도 크기에 견주어 정합니다.
        var w = 칸.clientWidth || 360, h = 칸.clientHeight || 240;
        var 가 = (여백 && 여백.가로) || Math.max(12, Math.min(50, Math.round(w * 0.07)));
        var 세 = (여백 && 여백.세로) || Math.max(10, Math.min(40, Math.round(h * 0.07)));
        지도.setBounds(테, 세, 가, 세, 가);
        return 것;
      },

      핀: function (위도, 경도, 요소, 옵션2) {
        옵션2 = 옵션2 || {};
        var 덮 = new kakao.maps.CustomOverlay({
          position: 자리(위도, 경도),
          content: 요소,
          yAnchor: 옵션2.세로기준 != null ? 옵션2.세로기준 : 0.5,
          zIndex: 옵션2.층 || 2
        });
        덮.setMap(지도);
        return { 날것: 덮, 지우기: function () { 덮.setMap(null); } };
      },

      // 자리를 꼭 집지 못한 곳 — **점선 원**으로 「이 언저리」라고 말합니다
      어림원: function (위도, 경도, 반지름) {
        var 원 = new kakao.maps.Circle({
          center: 자리(위도, 경도), radius: 반지름 || 300,
          strokeWeight: 2, strokeColor: '#C07B22', strokeOpacity: 0.9,
          strokeStyle: 'dash', fillColor: '#C07B22', fillOpacity: 0.12
        });
        원.setMap(지도);
        return { 날것: 원, 지우기: function () { 원.setMap(null); } };
      },

      누를때: function (함수) {
        kakao.maps.event.addListener(지도, 'click', 함수);
        kakao.maps.event.addListener(지도, 'dragstart', 함수);
        return 것;
      },

      다시재기: function () { 지도.relayout(); return 것; }
    };
    return 것;
  }

  window.BADAGAJA_MAP = {
    이름: '카카오',
    불러오기: 불러오기,
    만들기: 만들기
  };
})();
