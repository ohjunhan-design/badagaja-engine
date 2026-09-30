/* 카카오내비 길안내 — 포인트 카드에서 곧장 출발합니다 (2026-09-30)
 *
 * ★ 주인 지적으로 되살립니다 — 옛 사이트에는 있었는데 새 사이트로
 *   오며 빠졌습니다. 「푸터에 피씨화면보기 기능이 사라졌어」를 계기로
 *   옛 기능 26가지를 대조하다 함께 찾았습니다.
 *
 * ★ 이 사이트의 마지막 걸음입니다 (주인 규칙 6-2) —
 *   「빠르게 찾고 → 조건을 확인하고 → 포인트를 고르고 → **실제로 나가는 것**」
 *   지도를 보는 것과 차에 타고 출발하는 것은 다릅니다.
 *
 * ★ **휴대폰에서만 보입니다.** PC 에서 내비를 켤 일은 없습니다.
 *   앱이 없거나 실패하면 카카오맵 길찾기 주소로 넘어갑니다 — 막히지 않습니다.
 */
(function () {
  'use strict';

  var 휴대폰 = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  if (!휴대폰) return;

  var SDK = 'https://t1.kakaocdn.net/kakao_js_sdk/2.8.3/kakao.min.js';
  var SRI = 'sha384-oroumrnFVE0xtgqyDZJARgERibXg2C28380uaUZz2kHDS5CR7tu20eGiOU6GkTpy';
  var 준비 = null;

  function 키찾기() {
    // ★ 쪽이 **이미 가진** 지도키를 씁니다 (계약-01 한 곳에서)
    //   따로 적어 두면 키를 바꿀 때 두 곳이 갈립니다.
    //   `<script type="application/json" id="쪽자료">` 안에 있습니다.
    try {
      var 칸 = document.getElementById('쪽자료');
      if (!칸) return null;
      return (JSON.parse(칸.textContent) || {}).지도키 || null;
    } catch (e) { return null; }
  }

  function 카카오() {
    if (준비) return 준비;
    준비 = new Promise(function (ok, no) {
      var 키 = 키찾기();
      if (!키) { no(); return; }
      if (window.Kakao && window.Kakao.isInitialized()) { ok(window.Kakao); return; }
      var s = document.createElement('script');
      s.src = SDK; s.integrity = SRI; s.crossOrigin = 'anonymous';
      s.onload = function () {
        try {
          if (!window.Kakao.isInitialized()) window.Kakao.init(키);
          ok(window.Kakao);
        } catch (e) { no(e); }
      };
      s.onerror = no;
      document.head.appendChild(s);
    });
    return 준비;
  }

  /* 누르면 내비를 켭니다. 안 되면 카카오맵 길찾기로 넘어갑니다. */
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-navi]');
    if (!t) return;
    e.preventDefault();
    var p = t.getAttribute('data-navi').split('|');
    var 이름 = p[0], 위도 = p[1], 경도 = p[2];
    var 대신가기 = function () {
      location.href = 'https://map.kakao.com/link/to/'
        + encodeURIComponent(이름) + ',' + 위도 + ',' + 경도;
    };
    카카오().then(function (K) {
      try {
        K.Navi.start({ name: 이름, x: +경도, y: +위도, coordType: 'wgs84' });
      } catch (x) { 대신가기(); }
    }).catch(대신가기);
  });

  /* 좌표가 있는 포인트 카드마다 단추를 붙입니다 */
  function 달기() {
    document.documentElement.classList.add('has-navi');
    var 칸들 = document.querySelectorAll('.card[data-lat][data-lng]');
    [].forEach.call(칸들, function (카드) {
      if (카드.querySelector('.navi')) return;
      var 위도 = 카드.getAttribute('data-lat');
      var 경도 = 카드.getAttribute('data-lng');
      if (!위도 || !경도) return;
      var 이름칸 = 카드.querySelector('.card-name');
      // 「1. 만대어촌체험마을」에서 번호를 뗍니다
      var 이름 = 이름칸
        ? 이름칸.textContent.replace(/^\s*\d+\.\s*/, '').trim()
        : '목적지';
      var a = document.createElement('a');
      a.className = 'navi';
      a.href = '#';
      a.setAttribute('data-navi', [이름, 위도, 경도].join('|'));
      a.textContent = '🚗 길안내';

      // ★ **「위치 확인하기」와 나란히** (2026-09-30 주인 지시)
      //   왼쪽은 자리를 보는 것, 오른쪽은 실제로 나가는 것.
      //   길안내가 더 강해야 합니다 — 이 사이트의 마지막 걸음입니다.
      var 줄 = 카드.querySelector('.card-go');
      if (!줄) {
        줄 = document.createElement('div');
        줄.className = 'card-go';
        카드.appendChild(줄);
      }
      줄.appendChild(a);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', 달기);
  } else {
    달기();
  }
  // 목록을 걸러 다시 그릴 때도 붙습니다
  window.BADAGAJA_NAVI = { 달기: 달기 };
})();
