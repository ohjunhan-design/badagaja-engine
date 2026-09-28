/* 축제 달력 — 권역으로 걸러 보기 · 이번 달로 바로 가기 (2026-09-23 주인 지시)
   축제는 '언제'가 먼저라 달별 차례는 그대로 두고, 그 위에서 권역만 골라 봅니다.
   자료에 좌표가 없어 지도 대신 이 방식을 씁니다. */
(function () {
  var wrap = document.querySelector('.fi-grp');
  if (!wrap) return;
  var cards = [].slice.call(document.querySelectorAll('.fi-grid > a[data-g]'));
  var months = [].slice.call(document.querySelectorAll('.fi-month'));
  if (!cards.length) return;

  function count(sec) { return sec.querySelectorAll('.fi-grid > a:not([hidden])').length; }

  function apply(g) {
    cards.forEach(function (a) { a.hidden = !!(g && a.getAttribute('data-g') !== g); });
    var total = 0;
    months.forEach(function (sec) {
      var n = count(sec);
      total += n;
      sec.hidden = n === 0;
      var em = sec.querySelector('h2 em');
      if (em) em.textContent = '축제 ' + n + '개';
    });
    var none = document.getElementById('fiNone');
    if (none) none.hidden = total > 0;
    // 달 차례에서 빈 달은 흐리게
    [].forEach.call(document.querySelectorAll('.fi-toc a[href^="#m"]'), function (a) {
      var sec = document.getElementById(a.getAttribute('href').slice(1));
      a.classList.toggle('off', !!(sec && sec.hidden));
    });
  }

  wrap.addEventListener('click', function (e) {
    var b = e.target.closest('button[data-g]');
    if (!b) return;
    [].forEach.call(wrap.querySelectorAll('button[data-g]'), function (x) {
      x.classList.toggle('on', x === b);
      x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
    });
    apply(b.getAttribute('data-g'));
  });

  // 이번 달로 바로 가기 — 그 달에 축제가 없으면 가장 가까운 다음 달로
  var now = document.getElementById('fiNow');
  if (now) now.addEventListener('click', function () {
    var m = new Date().getMonth() + 1, sec = null;
    for (var i = 0; i < 12 && !sec; i++) {
      var t = document.getElementById('m' + (((m - 1 + i) % 12) + 1));
      if (t && !t.hidden) sec = t;
    }
    if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });

  apply('');
})();
