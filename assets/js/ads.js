/* 광고를 그립니다.  자료: data/raw/ads.json → assets/js/ads-data.js
 *
 * ★ 가장 중요한 것 — 광고가 **안 떠도 쪽이 멀쩡해야 합니다**
 *
 *   광고는 바깥 것입니다. 쿠팡 서버가 느리거나, 광고 차단기가 막거나,
 *   불러오기가 실패하면 **언제든 빈자리가 됩니다.**
 *
 *   그때 빈 상자가 덩그러니 남으면 쪽이 어색해집니다.
 *   그래서 자리는 처음에 **높이 0** 이고, 광고가 실제로 들어왔을 때만
 *   펴집니다. 안 들어오면 그대로 둡니다 — 아무 자리도 안 씁니다.
 *
 *   ★ hidden(display:none) 을 쓰면 안 됩니다 (2026-09-26 겪은 일)
 *     처음에는 hidden 으로 접어 두었는데, display:none 인 것은
 *     IntersectionObserver 가 **영영 못 봅니다.** 늦게 부르려고
 *     관찰하는데 관찰이 안 되니 광고가 한 번도 안 떴습니다.
 *     지금은 CSS 가 height:0 으로 두었다가 data-ad-state="떴음"
 *     이 달리면 폅니다.
 *
 *   (계약-23 바깥 자료가 죽어도 사이트는 산다)
 *
 * ★ 늦게 부릅니다
 *   화면에 다가올 때 비로소 쿠팡 스크립트를 받습니다. 첫 화면이
 *   빨리 떠야 하기 때문입니다.
 */
(function () {
  'use strict';

  var A = window.바다가자광고;
  if (!A || !A.켬) return;          // 꺼 두었으면 스크립트조차 안 받습니다

  var ZH = (document.documentElement.lang || '').indexOf('zh') === 0;
  var 받는중 = false;
  var 기다리는것 = [];

  function 글자(s) {
    return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function 말(키) {
    var t = A.표시 || {};
    return (ZH && t[키 + '_zh']) || t[키] || '';
  }

  /* 쿠팡 스크립트를 한 번만 받습니다 */
  function 쿠팡준비(하기) {
    if (window.PartnersCoupang) return 하기();
    기다리는것.push(하기);
    if (받는중) return;
    받는중 = true;
    var s = document.createElement('script');
    s.src = 'https://ads-partners.coupang.com/g.js';
    s.async = true;
    s.onload = function () {
      var 목록 = 기다리는것;
      기다리는것 = [];
      목록.forEach(function (f) { try { f(); } catch (e) {} });
    };
    s.onerror = function () {
      // 못 받았습니다. 자리는 접힌 채로 둡니다 — 빈 상자를 안 남깁니다
      기다리는것 = [];
    };
    document.head.appendChild(s);
  }

  /* 칸보다 넓은 배너를 줄여 넣습니다.
     휴대폰에서 가로로 넘치는 것을 막는 마지막 그물입니다. */
  function 맞추기(칸, 가로, 세로) {
    var 속 = 칸.querySelector('.ad-box');
    if (!속) return;
    var 쓸수있는폭 = 칸.clientWidth;
    if (!쓸수있는폭 || !가로 || 쓸수있는폭 >= 가로) {
      속.style.transform = '';
      속.style.height = '';
      return;
    }
    var 비율 = 쓸수있는폭 / 가로;
    속.style.transformOrigin = 'top center';
    속.style.transform = 'scale(' + 비율 + ')';
    속.style.height = Math.round(세로 * 비율) + 'px';
  }

  /* ★ **광고가 안 오면 바깥 띠까지 감춥니다** (2026-09-30 주인 지적)
   *
   *   주인 말씀 — 「이 부분에 쿠팡 광고 사라짐」
   *              「한번보면 안보이는기능은 삭제해버려 사이트에서」
   *
   *   광고 자리 자체는 이미 접혀 있었습니다(높이 1px). 그런데 그것을
   *   감싼 `.g-ad` 가 **안쪽 여백 18px** 을 그대로 차지해
   *   첫 쪽 한가운데에 까닭 없는 **빈 띠**가 남아 있었습니다.
   *   손님에게는 「뭔가 안 뜬 자리」로 보입니다.
   *
   *   그 띠 안의 자리가 **하나도 안 떴으면** 띠를 통째로 감춥니다.
   *   광고가 살아나면 저절로 다시 보입니다 —
   *   지우는 것이 아니라 **못 뜰 때만 숨기는** 것입니다.
   */
  function 띠살피기(칸) {
    var 띠 = 칸.parentNode;
    while (띠 && !(띠.className &&
                   String(띠.className).indexOf('g-ad') >= 0)) {
      띠 = 띠.parentNode;
    }
    if (!띠 || !띠.querySelectorAll) return;
    if (띠.querySelector('.ad-slot[data-ad-state="떴음"]')) {
      띠.style.display = '';
      return;
    }
    // 아직 결과를 기다리는 자리가 있으면 그대로 둡니다
    var 기다림 = [].some.call(띠.querySelectorAll('.ad-slot'), function (e) {
      if (window.getComputedStyle(e).display === 'none') return false;
      return !e.getAttribute('data-ad-state');
    });
    if (!기다림) 띠.style.display = 'none';
  }

  /* 광고가 실제로 들어왔는지 보고, 들어왔을 때만 폅니다 */
  function 들어왔나(칸, 배너, 편다) {
    var 속 = 칸.querySelector('.ad-box');
    if (!속) return;
    var 잰횟수 = 0;
    var 재기 = setInterval(function () {
      잰횟수 += 1;
      // 쿠팡이 iframe 을 넣으면 들어온 것입니다
      var 있나 = 속.querySelector('iframe, img, ins');
      if (있나) {
        clearInterval(재기);
        편다();
        맞추기(칸, 배너.가로, 배너.세로);
        띠살피기(칸);
        return;
      }
      if (잰횟수 >= 20) {          // 10초를 기다렸는데 안 오면
        clearInterval(재기);
        칸.setAttribute('data-ad-state', '안옴');   // 접힌 채로 둡니다
        띠살피기(칸);
      }
    }, 500);
  }

  function 그리기(칸) {
    var 이름 = 칸.getAttribute('data-ad-slot');
    var 자리 = (A.자리 || {})[이름];
    if (!자리 || !자리.켬) return;
    var 배너 = (A.배너 || {})[자리.배너];
    if (!배너) return;

    var 아이디 = 'ad-' + 이름.replace(/[^a-z0-9-]/gi, '') + '-' +
                 Math.random().toString(36).slice(2, 8);

    칸.innerHTML =
      '<p class="ad-label"><span class="ad-badge">' + 글자(말('배지')) +
      '</span>' + 글자(말('글')) + '</p>' +
      '<div class="ad-box" id="' + 아이디 + '"></div>';

    쿠팡준비(function () {
      try {
        // ★ **첫번째도전과 똑같이 부릅니다** (2026-09-30 주인 지시)
        //   「메인화면 광고부터 넣어줘 첫번째 도전 참고해서」
        //
        //   배너 번호는 첫번째도전과 **같았는데도**(PC 1032048 ·
        //   휴대폰 1032049) 이쪽에서만 안 떴습니다.
        //   옛 js/ads.js 와 견주니 부르는 **꼴**이 달랐습니다 —
        //     · 크기를 **글자**로 줍니다  width: String(W)
        //     · container 에 **요소 자체**를 넘깁니다 (아이디 글자가 아니라)
        //   쿠팡 g.js 는 이 꼴을 기대합니다. 숫자와 아이디 문자열을
        //   주면 예외를 던지고(우리 자리가 「탈남」이었습니다) 조용히
        //   아무것도 안 그립니다.
        new window.PartnersCoupang.G({
          id: 배너.id,
          template: 배너['틀'],
          trackingCode: 배너['추적'],
          width: String(배너['가로']),
          height: String(배너['세로']),
          container: 칸.querySelector('.ad-box')
        });
      } catch (e) {
        칸.setAttribute('data-ad-state', '탈남');
        띠살피기(칸);
        return;                    // 접힌 채로 둡니다
      }
      들어왔나(칸, 배너, function () {
        // ★ 이 표시를 다는 순간 CSS 가 자리를 폅니다 (height:0 → auto)
        칸.setAttribute('data-ad-state', '떴음');
      });
    });
  }

  /* 화면에 다가오면 그립니다 */
  var 살피기 = ('IntersectionObserver' in window)
    ? new IntersectionObserver(function (것들) {
        것들.forEach(function (x) {
          if (!x.isIntersecting) return;
          살피기.unobserve(x.target);
          그리기(x.target);
        });
      }, { rootMargin: '300px' })
    : null;

  function 달기(칸) {
    var 이름 = 칸.getAttribute('data-ad-slot');
    var 자리 = (A.자리 || {})[이름];
    if (!자리 || !자리.켬) return;

    // 기기가 안 맞으면 아예 건드리지 않습니다 (접힌 그대로)
    var 넓나 = window.matchMedia('(min-width:768px)').matches;
    if (자리.기기 === 'pc' && !넓나) return;
    if (자리.기기 === 'mobile' && 넓나) return;

    if (살피기) 살피기.observe(칸);
    else 그리기(칸);
  }

  function 시작() {
    var 칸들 = document.querySelectorAll('.ad-slot[data-ad-slot]');
    [].forEach.call(칸들, 달기);

    /* ★ 안전망 — 관찰이 안 걸려도 결국 그립니다 (2026-09-26)
     *
     *   IntersectionObserver 는 생각보다 잘 안 걸립니다.
     *     · 높이가 0 인 자리를 못 봅니다
     *     · 화면 밖 iframe 안에서는 아예 멈춥니다
     *     · 브라우저·설정에 따라 다르게 돕니다
     *
     *   관찰만 믿었다가 광고가 한 번도 안 뜬 적이 있습니다.
     *   **광고가 안 뜨면 수입이 0 입니다.** 늦게 부르는 이득보다
     *   안 뜨는 손해가 훨씬 큽니다.
     *
     *   그래서 2초 뒤에도 손대지 않은 자리가 있으면 그냥 그립니다.
     *   2초면 첫 화면은 이미 떴습니다. 성능에 영향이 없습니다.
     */
    setTimeout(function () {
      [].forEach.call(document.querySelectorAll('.ad-slot[data-ad-slot]'),
        function (칸) {
          if (칸.getAttribute('data-ad-state')) return;   // 이미 손댔음
          if (칸.innerHTML) return;                       // 이미 그렸음
          var 자리 = (A.자리 || {})[칸.getAttribute('data-ad-slot')];
          if (!자리 || !자리.켬) return;
          var 넓나 = window.matchMedia('(min-width:768px)').matches;
          if (자리.기기 === 'pc' && !넓나) return;
          if (자리.기기 === 'mobile' && 넓나) return;
          if (살피기) { try { 살피기.unobserve(칸); } catch (e) {} }
          그리기(칸);
        });
    }, 2000);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', 시작);
  } else {
    시작();
  }

  // 창 크기가 바뀌면 다시 맞춥니다 (가로로 넘치지 않게)
  var 늦추기;
  window.addEventListener('resize', function () {
    clearTimeout(늦추기);
    늦추기 = setTimeout(function () {
      [].forEach.call(document.querySelectorAll('.ad-slot[data-ad-state="떴음"]'),
        function (칸) {
          var 자리 = (A.자리 || {})[칸.getAttribute('data-ad-slot')];
          var 배너 = 자리 && (A.배너 || {})[자리.배너];
          if (배너) 맞추기(칸, 배너['가로'], 배너['세로']);
        });
    }, 150);
  });
})();
