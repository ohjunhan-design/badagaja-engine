/* 입구(첫 화면) 물때정보 칸 — 권역을 제주부터 차례로 넘겨 보여 줍니다. (2026-09-21)
 *
 * js/home.js 가 만들어 둔 권역 단추를 대신 눌러 주는 방식입니다.
 * home.js 안을 건드리지 않아, 참고서 쪽(guide/)과 물때 계산이 갈라지지 않습니다.
 * 사람이 사진이나 칸을 누르면 그 자리에서 멈춥니다 — 보던 곳이 저절로 바뀌면 불편합니다.
 */
(function () {
  var box = document.getElementById('tsRegions');
  if (!box) return;
  var btns = [].slice.call(box.querySelectorAll('button'));
  if (btns.length < 2) return;

  var JEJU = ['jejusi', 'aewol', 'jocheon', 'seongsan', 'seogwipo', 'daejeong', 'chuja'];
  var KEY = 'bdg-today-all';   // home.js 가 '내가 고른 바다'를 적어 두는 칸
  var STEP = 8000;             // 한 권역을 보여 주는 시간
  var timer = null, live = true;

  var photo = document.getElementById('gtPhoto');
  var tag = document.getElementById('gtTag');
  var title = document.getElementById('tsTitle');

  // 권역마다 사진이 놓인 곳이 다릅니다 — 제주는 img/jeju/photo, 전남은 img/<권역>,
  // 나머지 확대 권역은 img/coast 입니다. 제주시내만 따로 쓰는 사진이 없어 제주 대표 사진을 씁니다.
  var FALLBACK = 'img/sinan/hero.jpg';
  function photoOf(slug) {
    if (slug === 'jejusi') return 'img/jeju/photo/home-hero.jpg';
    if (JEJU.indexOf(slug) >= 0) return 'img/jeju/photo/' + slug + '-hero.jpg';
    var H = window.BADAGAJA_HOME;
    if (H && H.regions) {
      for (var i = 0; i < H.regions.length; i++) {
        if (H.regions[i].slug === slug) return H.regions[i].photo || ('img/' + slug + '/hero.jpg');
      }
    }
    return 'img/coast/' + slug + '-hero.jpg';
  }

  function paint(slug) {
    // 권역 이름은 home.js 가 '오늘 ○○ 바다는' 으로 적어 둡니다 — 거기서 꺼내 씁니다
    if (tag && title) {
      var m = /^오늘\s+(.+?)\s+바다는$/.exec((title.textContent || '').trim());
      if (m) tag.textContent = m[1];
    }
    if (photo && photo.getAttribute('data-slug') !== slug) {
      photo.setAttribute('data-slug', slug);
      // 사진이 없는 권역이 있어, 못 불러오면 조용히 기본 사진으로 되돌립니다
      photo.onerror = function () { this.onerror = null; this.src = FALLBACK; };
      photo.src = photoOf(slug);
      photo.alt = (tag && tag.textContent) ? tag.textContent + ' 바다' : '';
    }
  }

  function saved() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function restore(v) {
    // 저절로 넘어간 권역이 '내가 고른 바다'로 남으면 안 됩니다.
    try { if (v === null) localStorage.removeItem(KEY); else localStorage.setItem(KEY, v); } catch (e) { }
  }

  var i = 0;
  btns.forEach(function (b, n) { if (b.getAttribute('aria-selected') === 'true') i = n; });

  function show(n) {
    var keep = saved();
    btns[n].click();
    restore(keep);
    paint(btns[n].dataset.r);
  }
  function step() { if (!live) return; i = (i + 1) % btns.length; show(i); }
  function play() { pause(); timer = setInterval(step, STEP); }
  function pause() { if (timer) { clearInterval(timer); timer = null; } }
  function off() { live = false; pause(); }

  // 읽는 동안에는 넘기지 않습니다
  var panel = document.getElementById('tide');
  if (panel) {
    panel.addEventListener('mouseenter', pause);
    panel.addEventListener('mouseleave', function () { if (live) play(); });
  }
  // 다른 탭을 보고 있을 때는 쉬게 합니다 — 넘길 때마다 물때·날씨를 새로 부릅니다
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) pause(); else if (live) play();
  });

  show(i);   // 첫 권역의 사진·이름을 바로 맞춥니다
  play();
})();
