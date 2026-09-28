/* 카카오톡 공유 · 카카오내비 길안내 (Kakao SDK for JavaScript, 지도용 JavaScript 키 · 등록 도메인에서만 동작)
 * - 공유: 푸터 바로 위에 [카카오톡 공유][링크 복사] 줄을 붙임. 페이지의 og 태그(제목·설명·사진)로 카드가 만들어짐
 * - 길안내: data-navi="이름|위도|경도" 가 붙은 요소를 누르면 카카오내비 앱이 목적지를 찍고 열림(휴대폰에서만 보임)
 *   window.BadaNaviButton(이름, 위도, 경도) 로 버튼을 만들어 쓸 수 있음
 * 사용: <script src="(경로)js/kakao-share.js?v=…" defer></script>
 */
(function () {
  var SELF = (document.currentScript && document.currentScript.src) || '';
  var ROOT = SELF ? SELF.replace(/js\/kakao-share\.js.*$/, '') : '';
  var MOBILE = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
  var SDK = 'https://t1.kakaocdn.net/kakao_js_sdk/2.8.3/kakao.min.js';
  var SRI = 'sha384-oroumrnFVE0xtgqyDZJARgERibXg2C28380uaUZz2kHDS5CR7tu20eGiOU6GkTpy';
  var ready = null;

  function script(src, sri) {
    return new Promise(function (ok, no) {
      var s = document.createElement('script'); s.src = src; s.onload = ok; s.onerror = no;
      if (sri) { s.integrity = sri; s.crossOrigin = 'anonymous'; }
      document.head.appendChild(s);
    });
  }
  function kakao() {
    if (ready) return ready;
    ready = (window.BADAGAJA_MAP ? Promise.resolve() : script(ROOT + 'point/map-config.js')).then(function () {
      var key = (window.BADAGAJA_MAP || {}).kakaoJsKey;
      if (!key) throw 0;
      return (window.Kakao ? Promise.resolve() : script(SDK, SRI)).then(function () {
        if (!Kakao.isInitialized()) Kakao.init(key);
        return Kakao;
      });
    });
    return ready;
  }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function toast(msg) {
    var t = el('div', 'ks-toast', msg); document.body.appendChild(t);
    setTimeout(function () { t.classList.add('on'); }, 10);
    setTimeout(function () { t.classList.remove('on'); setTimeout(function () { t.remove(); }, 300); }, 2200);
  }
  function canonical() { var c = document.querySelector('link[rel="canonical"]'); return (c && c.href) || location.href.split('#')[0]; }

  /* ---------- 공유 줄 ---------- */
  function shareBar() {
    var foot = document.querySelector('footer.site-footer');
    if (!foot || document.querySelector('.ks-bar')) return;
    var bar = el('div', 'ks-bar'), inner = el('div', 'wrap ks-inner');
    inner.appendChild(el('span', 'ks-label', '이 페이지를 친구와 함께 보세요'));
    var k = el('button', 'ks-btn ks-kakao'); k.type = 'button';
    k.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5c-5 0-9 3.2-9 7.1 0 2.5 1.7 4.7 4.2 6l-.9 3.4c-.1.3.3.6.6.4l4-2.6c.4 0 .7.1 1.1.1 5 0 9-3.2 9-7.2S17 3.5 12 3.5z" fill="currentColor"/></svg><span>카카오톡 공유</span>';
    k.addEventListener('click', function () {
      kakao().then(function (K) { K.Share.sendScrap({ requestUrl: canonical() }); })
        .catch(function () { toast('카카오톡 공유를 불러오지 못했어요. 링크 복사를 이용해 주세요.'); });
    });
    var c = el('button', 'ks-btn ks-copy', '🔗 링크 복사'); c.type = 'button';
    c.addEventListener('click', function () {
      var u = canonical();
      (navigator.clipboard ? navigator.clipboard.writeText(u) : Promise.reject()).then(function () { toast('링크를 복사했어요'); })
        .catch(function () { window.prompt('아래 링크를 복사하세요', u); });
    });
    inner.appendChild(k); inner.appendChild(c);
    if (navigator.share && MOBILE) {
      var m = el('button', 'ks-btn ks-more', '더보기'); m.type = 'button';
      m.addEventListener('click', function () { navigator.share({ title: document.title, url: canonical() }).catch(function () {}); });
      inner.appendChild(m);
    }
    bar.appendChild(inner);
    foot.parentNode.insertBefore(bar, foot);
  }

  /* ---------- 카카오내비 길안내 ---------- */
  window.BadaNaviButton = function (name, lat, lng, label) {
    if (!MOBILE || !lat || !lng) return null;
    var a = el('a', 'ks-navi', label || '🚗 카카오내비'); a.href = '#';
    a.setAttribute('data-navi', [name, lat, lng].join('|'));
    return a;
  };
  document.addEventListener('click', function (e) {
    var t = e.target.closest && e.target.closest('[data-navi]'); if (!t) return;
    e.preventDefault();
    var p = t.getAttribute('data-navi').split('|');
    kakao().then(function (K) { K.Navi.start({ name: p[0], x: +p[2], y: +p[1], coordType: 'wgs84' }); })
      .catch(function () { location.href = 'https://map.kakao.com/link/to/' + encodeURIComponent(p[0]) + ',' + p[1] + ',' + p[2]; });
  });
  function naviAll() {
    if (!MOBILE) return;
    document.documentElement.classList.add('ks-mobile');
    // 포인트 페이지: 정확한 위치(pin)로 적힌 카드의 카카오맵 링크 옆에 내비 버튼
    [].forEach.call(document.querySelectorAll('.card[data-loc="pin"][data-lat] .maplink'), function (a) {
      var m = /link\/to\/([^,]+),/.exec(a.getAttribute('href') || ''); var card = a.closest('.card');
      var nv = window.BadaNaviButton(m ? decodeURIComponent(m[1]) : '목적지', card.getAttribute('data-lat'), card.getAttribute('data-lng'), '🚗 카카오내비 길안내');
      if (nv) { nv.classList.add('maplink'); a.parentNode.insertBefore(nv, a.nextSibling); }
    });
  }

  function start() { shareBar(); /* naviAll() — 카카오내비 길안내 버튼은 붙이지 않습니다 (2026-09-20) */ }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
