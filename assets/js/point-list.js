/* 포인트 목록 쪽 — 검색 · 걸러내기 · 지도
 *
 * ★ 화면에서 자료를 긁지 않습니다 (2026-09-26)
 *   옛 사이트의 지도는 카드 HTML 을 뒤져 이름을 찾았습니다.
 *       c.querySelector('div[style*="font-weight:800"]')
 *   9월 20일 글자 모양을 다듬자 이 줄이 아무것도 못 찾게 되었고,
 *   지도 풍선에 이름 대신 "point-0" 이 **6일 동안** 떴습니다.
 *
 *   그래서 여기서는 쪽에 함께 실린 자료(<script id="쪽자료">)만 읽습니다.
 *   디자인이 아무리 바뀌어도 이 파일은 안 깨집니다.
 *
 * 자바스크립트가 꺼져 있어도 목록은 그대로 보입니다.
 * 이 파일이 하는 일은 전부 '있으면 더 편한' 것들입니다.
 */
(function () {
  'use strict';

  var 자료칸 = document.getElementById('쪽자료');
  if (!자료칸) return;
  var 자료;
  try { 자료 = JSON.parse(자료칸.textContent); } catch (e) { return; }
  var 포인트 = 자료.포인트 || [];
  if (!포인트.length) return;

  var 목록 = document.getElementById('pointsGrid');
  var 빈칸 = document.getElementById('empty');
  var 찾기칸 = document.getElementById('searchInput');
  var 걸름 = document.getElementById('filter');

  // 아이디로 카드를 바로 찾습니다
  var 카드 = {};
  포인트.forEach(function (p) {
    var el = document.getElementById(p.id);
    if (el) { 카드[p.id] = el; p.el = el; }
    // 찾을 때 쓸 글 — 미리 만들어 둡니다
    p.찾을글 = [p.이름, p.지형 || ''].concat(p.대상 || []).join(' ').toLowerCase();
  });

  // ── 걸러내기 · 찾기 ────────────────────────────────────
  var 지금걸름 = '전체';
  // ★ **어종으로 거르기** (2026-10-01 주인 확정 — 104종)
  //   지형과 **따로** 걸립니다. 둘 다 걸면 둘 다 맞아야 보입니다.
  var 지금어종 = '전체';
  var 지금찾기 = '';

  function 다시그리기() {
    var 보인수 = 0;
    포인트.forEach(function (p) {
      if (!p.el) return;
      var 맞나 = (지금걸름 === '전체' || p.지형 === 지금걸름)
              && (지금어종 === '전체'
                  || (p.대상 || []).indexOf(지금어종) >= 0)
              && (!지금찾기 || p.찾을글.indexOf(지금찾기) >= 0);
      p.el.hidden = !맞나;
      p.보임 = 맞나;
      if (맞나) 보인수++;
    });
    if (빈칸) 빈칸.hidden = 보인수 > 0;
    if (지도그림) 핀다시();
    알리기(보인수);
  }

  // 화면을 읽어 주는 분들께도 결과를 알립니다
  var 알림칸 = null;
  function 알리기(n) {
    if (!알림칸) {
      알림칸 = document.createElement('p');
      알림칸.className = 'sr-only';
      알림칸.setAttribute('aria-live', 'polite');
      목록.parentNode.insertBefore(알림칸, 목록);
    }
    알림칸.textContent = '포인트 ' + n + '곳을 보이고 있습니다.';
  }

  if (걸름) {
    걸름.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-filter]');
      if (!b) return;
      지금걸름 = b.getAttribute('data-filter');
      [].forEach.call(걸름.querySelectorAll('button'), function (x) {
        x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
      });
      다시그리기();
    });
  }

  // ── 어종 거르개 ───────────────────────────────────────
  var 어종칸 = document.getElementById('fishFilter');
  if (어종칸) {
    어종칸.addEventListener('click', function (e) {
      var 더 = e.target.closest('button[data-more]');
      if (더) {
        // 접어 둔 어종을 폅니다. 한 번 펴면 그대로 둡니다.
        [].forEach.call(어종칸.querySelectorAll('button[hidden]'),
          function (x) { x.hidden = false; });
        더.remove();
        return;
      }
      var b = e.target.closest('button[data-fish]');
      if (!b) return;
      지금어종 = b.getAttribute('data-fish');
      [].forEach.call(어종칸.querySelectorAll('button[data-fish]'),
        function (x) {
          x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
        });
      다시그리기();
    });
  }

  if (찾기칸) {
    var 늦추기 = null;
    찾기칸.addEventListener('input', function () {
      clearTimeout(늦추기);
      늦추기 = setTimeout(function () {
        지금찾기 = 찾기칸.value.trim().toLowerCase();
        다시그리기();
      }, 120);
    });
  }

  // ── 맨 위로 ───────────────────────────────────────────
  var 위로 = document.getElementById('toTop');
  if (위로) {
    위로.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    window.addEventListener('scroll', function () {
      위로.classList.toggle('show', window.scrollY > 600);
    }, { passive: true });
  }

  // ── 상세 패널 ─────────────────────────────────────────
  //
  // ★ 오른쪽 35% 를 **선택한 포인트의 즉석 상세**로 (2026-10-08 지시)
  //   손님이 한 화면에서 「장소 고르기 → 어종 보기 → 오늘 물때
  //   보기 → 나갈지 정하기」를 끝내게 합니다.
  //
  // ★ 패널이 안 실린 쪽에서는 **아무 일도 안 일어납니다.**
  //   지시 ⑦ — 「처음부터 전 지역 확장하지 말고 대표 쪽 1개에서
  //   먼저 구현·검증 후 템플릿 확장」. 그래서 없으면 없는 대로
  //   돌아가게 둡니다 — 옛 움직임(카드로 내려가기)이 그대로입니다.
  var 패널 = null;
  (function 패널달기() {
    if (!자료.상세패널 || !window.BADAGAJA_POINTPANEL) { return; }
    var 패널칸 = document.getElementById('phmPicks');
    var 목록칸 = document.getElementById('phmList');
    if (!패널칸 || !목록칸) { return; }
    패널 = window.BADAGAJA_POINTPANEL.달기({
      칸: 패널칸,
      목록칸: 목록칸,
      권역: 자료.권역,
      // 단추에 「여수 물때 자세히」처럼 권역 이름을 넣습니다 —
      // 포인트 바로 그 자리가 아니라 **권역 기준 관측소** 값입니다
      권역이름: 자료.권역이름,
      api: 자료.api,
      물때주소: 자료.물때주소,
      // 「포인트 전체정보」 — 아래 전체 목록의 그 카드로 내려갑니다
      카드로: function (p) { 카드로(p); }
    });
    /* ★ **오른쪽 카드를 누르면 지도도 움직입니다** (양방향)
         한쪽만 움직이면 「내가 고른 것이 어디지」를 또 찾게 됩니다. */
    목록칸.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-point]');
      if (!b) { return; }
      var 아이디 = b.getAttribute('data-point');
      var 찾은 = 포인트.filter(function (p) { return p.id === 아이디; })[0];
      if (!찾은) { return; }
      /* 지도가 떴으면 그 자리로 보내고(열기 가 패널도 엽니다),
         지도를 못 받았으면 패널만 엽니다 — 지도는 바깥입니다. */
      if (지도 && 찾은.핀) { 열기(찾은); }
      else { 패널.보이기(찾은, true); }
    });
  })();

  // ── 지도 ──────────────────────────────────────────────
  var 지도칸 = document.getElementById('pointMap');
  var 지도그림 = null, 지도 = null, 핀 = {}, 풍선 = null, 어림원 = null;
  var 좌표있는것 = 포인트.filter(function (p) {
    return typeof p.위도 === 'number' && typeof p.경도 === 'number';
  });

  if (지도칸 && 자료.지도키 && 좌표있는것.length) {
    var s = document.createElement('script');
    s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey='
          + encodeURIComponent(자료.지도키);
    s.onload = function () {
      try { kakao.maps.load(지도만들기); } catch (e) { 지도없음('지도를 불러오지 못했습니다'); }
    };
    s.onerror = function () { 지도없음('지도를 불러오지 못했습니다'); };
    document.head.appendChild(s);
  } else if (지도칸) {
    지도없음(좌표있는것.length ? '' : '이 권역은 아직 좌표가 없는 포인트뿐입니다');
  }

  function 지도없음(글) {
    // 지도가 없어도 쪽은 그대로 쓸 수 있어야 합니다 (계약-23)
    지도칸.classList.add('map-off');
    if (글) {
      var p = document.createElement('p');
      p.className = 'map-note';
      p.textContent = 글 + ' — 아래 목록과 「지도에서 보기」는 그대로 쓰실 수 있습니다.';
      지도칸.appendChild(p);
    }
  }

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) e.className = 반;
    if (글 != null) e.textContent = 글;
    return e;
  }

  function 지도만들기() {
    지도그림 = 만들기('div', 'map-canvas');
    지도칸.appendChild(지도그림);
    지도칸.classList.add('map-on');

    지도 = new kakao.maps.Map(지도그림, {
      center: new kakao.maps.LatLng(좌표있는것[0].위도, 좌표있는것[0].경도),
      level: 9
    });
    지도.setZoomable(false);          // 쪽을 넘기다 실수로 확대되지 않게
    지도.addControl(new kakao.maps.ZoomControl(),
                    kakao.maps.ControlPosition.RIGHT);

    // ★ 일반·위성 단추 (2026-09-29 주인 지시)
    //   갯바위·갯벌은 길 이름이 없어 일반 지도에서는 빈 바다로
    //   보입니다. 위성으로 봐야 어디로 걸어 들어가는지 압니다.
    if (window.BADAGAJA_MAPTYPE) {
      window.BADAGAJA_MAPTYPE.달기(지도, 지도칸);
    }

    풍선 = new kakao.maps.CustomOverlay({ yAnchor: 1.25, zIndex: 20 });
    어림원 = new kakao.maps.Circle({
      strokeWeight: 2, strokeColor: '#C07B22', strokeOpacity: .9,
      strokeStyle: 'dash', fillColor: '#C07B22', fillOpacity: .12
    });

    // 같은 자리에 여럿이면 조금씩 벌려 놓습니다 — 안 그러면 하나만 보입니다
    var 본자리 = {};
    좌표있는것.forEach(function (p) {
      var 키 = p.위도.toFixed(4) + ',' + p.경도.toFixed(4);
      var n = 본자리[키] = (본자리[키] || 0) + 1;
      if (n > 1) {
        var 각 = n * 2.4, r = 0.0009 * Math.sqrt(n);
        p.그릴위도 = p.위도 + r * Math.sin(각);
        p.그릴경도 = p.경도 + r * Math.cos(각);
      } else { p.그릴위도 = p.위도; p.그릴경도 = p.경도; }
    });

    var 테두리 = new kakao.maps.LatLngBounds();
    좌표있는것.forEach(function (p) {
      var b = 만들기('button', 'pin pin--' + (p.등급 || 'C')
                     + (p.어림 ? ' pin--area' : ''), String(p.차례));
      b.type = 'button';
      b.title = p.이름;
      b.setAttribute('aria-label', p.차례 + '. ' + p.이름);
      b.addEventListener('click', function (e) { e.stopPropagation(); 열기(p); });
      핀[p.id] = b;
      p.핀 = b;
      new kakao.maps.CustomOverlay({
        position: new kakao.maps.LatLng(p.그릴위도, p.그릴경도),
        content: b, yAnchor: .5, zIndex: p.어림 ? 1 : 2
      }).setMap(지도);
      테두리.extend(new kakao.maps.LatLng(p.그릴위도, p.그릴경도));
    });

    function 맞추기() {
      지도.relayout();
      // 여백을 고정 픽셀로 주면 좁은 화면에서 쓸 폭이 거의 안 남아
      // 지도가 엉뚱하게 넓어집니다 — 휴대폰에서 서울까지 보였습니다 (2026-09-26).
      // 지도 크기에 견주어 정합니다.
      var w = 지도그림.clientWidth || 360;
      var h = 지도그림.clientHeight || 240;
      var 가로 = Math.max(12, Math.min(50, Math.round(w * 0.07)));
      var 세로 = Math.max(10, Math.min(40, Math.round(h * 0.07)));
      지도.setBounds(테두리, 세로, 가로, 세로, 가로);
    }
    맞추기();
    setTimeout(맞추기, 300);
    setTimeout(맞추기, 1200);

    // 스크롤 확대는 눌러서 켭니다
    // 글은 차림표(::after)가 넣습니다 — 읽히게 바탕을 깔기 위해서입니다.
    // 화면을 읽어 주는 분들께는 aria-label 로 알립니다
    var 잠금 = 만들기('button', 'map-lock');
    잠금.type = 'button';
    잠금.setAttribute('aria-label', '지도를 눌러 확대·이동을 켭니다');
    지도칸.appendChild(잠금);
    function 풀기() { 지도.setZoomable(true); 잠금.hidden = true; }
    잠금.addEventListener('click', 풀기);
    kakao.maps.event.addListener(지도, 'click', 풀기);
    kakao.maps.event.addListener(지도, 'dragstart', 풀기);

    /* 카드마다 **「위치 확인하기」** (2026-09-30 주인 지시)
       전에는 이름이 「지도에서 자리 보기 ↑」였고, 그 위에 카카오맵으로
       나가는 「지도에서 보기 →」가 또 있었습니다. 둘을 하나로 합쳤습니다. */
    좌표있는것.forEach(function (p) {
      if (!p.el) return;
      var a = 만들기('button', 'maplink maplink--map', '📍 위치 확인하기');
      a.type = 'button';
      a.addEventListener('click', function () {
        지도칸.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(function () { 열기(p); }, 400);
      });
      // 길안내와 나란히 놓습니다 — 자리를 보는 것과 나가는 것
      var 줄 = p.el.querySelector('.card-go') || p.el;
      줄.appendChild(a);
    });

    알림줄();
  }

  function 알림줄() {
    var 없는것 = 포인트.length - 좌표있는것.length;
    var p = 만들기('p', 'map-note',
      '핀을 누르면 그 자리 정보가 나옵니다. 점선 원은 대략 위치입니다.'
      + ' 지도에 ' + 좌표있는것.length + '곳'
      + (없는것 ? ' · 위치를 아직 못 잡은 곳 ' + 없는것 : ''));
    지도칸.parentNode.appendChild(p);
  }

  function 열기(p) {
    Object.keys(핀).forEach(function (k) { 핀[k].classList.remove('on'); });
    if (p.핀) p.핀.classList.add('on');

    /* ★ 핀을 누르면 **오른쪽이 그 포인트의 상세로 바뀝니다**
         (2026-10-08 지시 — 「지도 점 클릭 또는 말풍선 자세히
         보기 → 오른쪽을 선택 포인트 상세로 전환」)
         여기서는 **쪽을 움직이지 않습니다.** 핀을 누를 때마다
         화면이 뛰면 여러 자리를 견주기 어렵습니다 — 일부러
         「자세히 보기」를 누른 때만 끌어올립니다. */
    if (패널) { 패널.보이기(p, false); }

    var 자리 = new kakao.maps.LatLng(p.그릴위도, p.그릴경도);
    var 상자 = 만들기('div', 'map-pop');
    var 닫기 = 만들기('button', 'x', '×');
    닫기.type = 'button';
    닫기.setAttribute('aria-label', '닫기');
    닫기.addEventListener('click', function () {
      풍선.setMap(null); 어림원.setMap(null);
      if (p.핀) p.핀.classList.remove('on');
    });
    상자.appendChild(닫기);
    상자.appendChild(만들기('b', null, p.차례 + '. ' + p.이름));
    if (p.대상 && p.대상.length) {
      상자.appendChild(만들기('span', 'sub', p.대상.slice(0, 4).join(' · ')));
    }
    상자.appendChild(만들기('span', 'acc' + (p.어림 ? ' area' : ''),
      p.어림 ? '대략 위치 (주변 지역)' : '확인된 자리'));
    /* ★ 「자세히 보기」가 **오른쪽 상세 패널**을 엽니다 (2026-10-08)
         전에는 아래 전체 목록까지 내려보냈습니다. 그러면 지도가
         화면에서 사라지고, 물때를 보려면 또 다른 쪽으로 나가야
         했습니다 — 돌아오면 고른 것을 잊습니다.
         패널이 없는 쪽에서는 옛 움직임 그대로 카드로 내려갑니다. */
    var 가기 = 만들기('button', 'go', '자세히 보기');
    가기.type = 'button';
    가기.addEventListener('click', function () {
      if (패널) { 패널.보이기(p, true); } else { 카드로(p); }
    });
    상자.appendChild(가기);

    풍선.setContent(상자);
    풍선.setPosition(자리);
    풍선.setMap(지도);
    if (p.어림) { 어림원.setPosition(자리); 어림원.setRadius(900); 어림원.setMap(지도); }
    else 어림원.setMap(null);
    if (지도.getLevel() > 7) 지도.setLevel(p.어림 ? 7 : 6, { anchor: 자리 });
    지도.panTo(자리);
  }

  function 카드로(p) {
    if (!p.el) return;
    // 걸러내기에 가려져 있으면 먼저 풀어 줍니다
    if (p.el.hidden) {
      지금걸름 = '전체';
      지금어종 = '전체';
      지금찾기 = '';
      if (찾기칸) 찾기칸.value = '';
      if (걸름) {
        [].forEach.call(걸름.querySelectorAll('button'), function (x) {
          x.setAttribute('aria-pressed',
            x.getAttribute('data-filter') === '전체' ? 'true' : 'false');
        });
      }
      다시그리기();
    }
    p.el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    p.el.classList.add('flash');
    setTimeout(function () { p.el.classList.remove('flash'); }, 1600);
  }

  function 핀다시() {
    // 걸러낸 것은 지도에서도 감춥니다 — 목록과 지도가 어긋나면 헷갈립니다
    포인트.forEach(function (p) {
      if (p.핀) p.핀.hidden = (p.보임 === false);
    });
  }

  // 주소에 #포인트아이디 가 붙어 들어오면 그 카드를 보여 줍니다
  if (location.hash.length > 1) {
    var 찾은 = 포인트.filter(function (p) { return '#' + p.id === location.hash; })[0];
    if (찾은) setTimeout(function () { 카드로(찾은); }, 300);
  }

  다시그리기();
})();
