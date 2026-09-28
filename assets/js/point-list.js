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
  var 지금찾기 = '';

  function 다시그리기() {
    var 보인수 = 0;
    포인트.forEach(function (p) {
      if (!p.el) return;
      var 맞나 = (지금걸름 === '전체' || p.지형 === 지금걸름)
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

    // 카드마다 '지도에서 자리 보기'
    좌표있는것.forEach(function (p) {
      if (!p.el) return;
      var a = 만들기('button', 'maplink maplink--map', '지도에서 자리 보기 ↑');
      a.type = 'button';
      a.addEventListener('click', function () {
        지도칸.scrollIntoView({ behavior: 'smooth', block: 'center' });
        setTimeout(function () { 열기(p); }, 400);
      });
      p.el.appendChild(a);
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
    var 가기 = 만들기('button', 'go', '자세히 보기');
    가기.type = 'button';
    가기.addEventListener('click', function () { 카드로(p); });
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
