/* 전국 물때표 쪽(tide/)의 2주 물때표 — 고른 권역에 맞춰 그립니다 (2026-09-23 주인 지시)
   · 권역 단추나 지도 핀으로 권역을 바꾸면 이 표도 함께 바뀝니다.
   · 물때 번호·물 빠짐은 계산값(7물때식), 간조·만조는 api/tide-cache.php(국립해양조사원 조석예보)입니다. */
(function () {
  var box = document.getElementById('tide14');
  if (!box) return;
  var T = window.BADAGAJA_TIDE;
  var DAY = ['일', '월', '화', '수', '목', '금', '토'];
  var cur = null, busy = false;

  function sel() {
    var on = document.querySelector('#tsRegions [aria-selected="true"]');
    return on && on.getAttribute('data-r');
  }
  function name() {
    var on = document.querySelector('#tsRegions [aria-selected="true"]');
    return on ? on.textContent.trim() : '';
  }

  function card(d, ev, isToday) {
    var m = T ? T.calcMuldae(d) : 0;
    var it = T ? T.calcIntensity(m) : 0;
    var lab = T ? T.tideLabel(it) : { text: '', cls: '' };
    var rows = (ev || []).map(function (e) {
      var high = e.type === '만조';
      return '<li class="' + (high ? 'h' : 'l') + '"><span class="k">' + (high ? '고' : '저') + '</span>' +
             '<span class="t">' + e.time + '</span><span class="v">' + (e.level != null ? e.level : '') + '</span></li>';
    }).join('');
    return '<div class="t14-day' + (isToday ? ' today' : '') + '">' +
             '<div class="t14-top"><b>' + (d.getMonth() + 1) + '/' + d.getDate() + '</b><span>' + DAY[d.getDay()] + '</span></div>' +
             '<div class="t14-mul ' + lab.cls + '"><b>' + m + '물</b><span>' + lab.text + '</span></div>' +
             '<div class="t14-bar"><i style="width:' + it + '%"></i></div>' +
             (rows ? '<ul class="t14-ev">' + rows + '</ul>' : '<p class="t14-wait">간조·만조 준비 중</p>') +
           '</div>';
  }

  function draw(days) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var out = '';
    for (var i = 0; i < 14; i++) {
      var d = new Date(today.getFullYear(), today.getMonth(), today.getDate() + i);
      var src = days && days[i];
      // 이레째부터는 접어 둡니다 — 단추를 누르면 펼칩니다.
      // 짝수(6칸)로 끊습니다 — 휴대폰은 두 줄씩이라 홀수면 마지막 줄에 한 칸만 남습니다 (2026-09-24 주인 지시)
      out += card(d, src && src.events, i === 0).replace('class="t14-day',
               i >= 6 ? 'class="t14-later t14-day' : 'class="t14-day');
    }
    box.innerHTML = out;
  }

  function load(slug) {
    if (!slug || slug === cur || busy) return;
    cur = slug; busy = true;
    draw(null);
    var t = document.getElementById('t14Title');
    var open = box.classList.contains('t14-open');
    if (t) t.textContent = name() + (open ? ' 2주 물때표' : ' 물때표');
    fetch('api/tide-cache.php?region=' + slug, { cache: 'no-store' })
      .then(function (r) { if (!r.ok) throw 0; return r.json(); })
      .then(function (d) {
        busy = false;
        draw(d && d.days);
        var s = document.getElementById('t14Src');
        if (s) s.textContent = '간조·만조: 국립해양조사원 조석예보 · ' + ((d && d.point) || '가까운 관측소') + ((d && d.updated) ? ' · ' + d.updated : '');
      })
      .catch(function () { busy = false; });
  }

  var box2 = document.getElementById('tsRegions');
  if (box2) box2.addEventListener('click', function () { setTimeout(function () { load(sel()); }, 80); });
  var t = setInterval(function () { var s = sel(); if (s) { clearInterval(t); load(s); } }, 400);
  setTimeout(function () { clearInterval(t); }, 12000);

  // 더보기 — 누르면 다음 주가 나오고 단추는 사라집니다
  var more = document.getElementById('t14More');
  if (more) {
    more.addEventListener('click', function () {
      box.classList.add('t14-open');
      more.hidden = true;
      var k = document.getElementById('t14Kick');
      if (k) k.textContent = '이번 주 · 다음 주';
      var t = document.getElementById('t14Title');
      if (t && t.textContent.indexOf('2주') < 0) t.textContent = t.textContent.replace(' 물때표', ' 2주 물때표');
    });
  }
})();
