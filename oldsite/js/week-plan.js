/* 이번 주 언제 갈까 — 권역 페이지 물때표 위에 붙는 칸 (2026-09-18)
 * 1) 음력 물때 계산으로 먼저 그리고, 2) app.js 가 불러온 조석 자료(bada:tide 이벤트)가 오면
 *    7일 동안 '낮 시간 간조'의 실제 높이로 다시 그려 가장 많이 빠지는 날을 고릅니다.
 * 제주 권역은 해루질을 권하지 않으므로 물살이 약한 날(낚시)을 고릅니다.
 * 필요한 것: js/app.js 의 window.BADAGAJA_TIDE, 페이지의 <div id="weekPlan"></div>
 */
(function () {
  var box = document.getElementById('weekPlan');
  var T = window.BADAGAJA_TIDE;
  if (!box || !T) return;
  var slug = document.body.getAttribute('data-region') || '';
  var jeju = /^(jejusi|aewol|jocheon|seongsan|seogwipo|daejeong|chuja)$/.test(slug);
  var DAY = ['일', '월', '화', '수', '목', '금', '토'];
  var c = T.coords && T.coords[slug];

  box.innerHTML =
    '<div class="wp-kick">이번 주 언제 갈까</div>' +
    '<h3 class="wp-title"></h3><p class="wp-lead"></p>' +
    '<div class="wp-week" role="list"></div>' +
    '<div class="wp-legend"><span class="wp-lg"></span><span class="wp-basis"></span></div>' +
    '<p class="wp-note" hidden></p>';
  var $ = function (s) { return box.querySelector(s); };

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function toMin(hm) { var p = String(hm).split(':'); return +p[0] * 60 + +p[1]; }
  function hmText(hm) {                                  // "13:33" → "오후 1시 33분"
    var p = hm.split(':'), h = +p[0], m = +p[1];
    var part = h < 12 ? '오전' : (h < 18 ? '오후' : '저녁'), hh = h % 12 === 0 ? 12 : h % 12;
    return part + ' ' + hh + '시' + (m ? ' ' + m + '분' : '');
  }
  function dayWord(d, i) { return i === 0 ? '오늘' : (i === 1 ? '내일' : DAY[d.getDay()] + '요일'); }
  function today() { var n = new Date(); return new Date(n.getFullYear(), n.getMonth(), n.getDate()); }

  function draw(rows, byTide) {
    var w = $('.wp-week'); w.innerHTML = '';
    $('.wp-lg').textContent = jeju ? '막대가 짧을수록 물살이 약해 낚시가 편해요' : '막대가 길수록 물이 많이 빠져요';
    rows.forEach(function (x, i) {
      var d = el('div', 'wp-day' + (i === 0 ? ' today' : '') + (x.best ? ' best' : (x.good ? ' good' : '')));
      d.setAttribute('role', 'listitem');
      d.appendChild(el('span', 'star', x.best ? '★' : (x.good ? '☆' : '')));
      var bar = el('div', 'bar'), fill = el('i'); fill.style.height = x.h + '%'; bar.appendChild(fill); d.appendChild(bar);
      d.appendChild(el('b', null, i === 0 ? '오늘' : DAY[x.d.getDay()]));
      d.appendChild(el('span', 'dm', x.d.getDate() + ' · ' + x.m + '물'));
      d.title = (x.d.getMonth() + 1) + '월 ' + x.d.getDate() + '일 ' + x.m + '물' + (x.low ? ' · 낮 간조 ' + x.low.time : (byTide ? ' · 낮 간조 없음' : ''));
      w.appendChild(d);
    });
    var note = $('.wp-note');
    var weekend = rows.filter(function (x) { var g = x.d.getDay(); return g === 0 || g === 6; });
    var calm = weekend.length && weekend.every(function (x) { return x.inten <= 40; });
    var big = weekend.length && weekend.some(function (x) { return x.inten >= 68; });
    if (jeju) note.hidden = true;
    else if (calm) { note.innerHTML = '이번 주말은 <b>조금</b> 무렵이라 물이 적게 빠집니다. 해루질보다는 <b>낚시</b>가 낫습니다.'; note.hidden = false; }
    else if (big) { note.innerHTML = '이번 주말은 <b>사리</b> 무렵이라 물이 많이 빠집니다. 가족 해루질하기 좋은 주말이에요.'; note.hidden = false; }
    else note.hidden = true;
  }

  function base() {
    var d0 = today(), rows = [];
    for (var i = 0; i < 7; i++) {
      var d = new Date(d0); d.setDate(d.getDate() + i);
      var m = T.calcMuldae(d);
      rows.push({ d: d, m: m, inten: T.calcIntensity(m) });
    }
    return rows;
  }

  // 1) 계산만으로
  function byCalc() {
    var rows = base();
    rows.forEach(function (x) { x.h = Math.max(8, Math.round(x.inten * 0.92)); });
    var pick = rows.reduce(function (a, b) { return (jeju ? b.inten < a.inten : b.inten > a.inten) ? b : a; });
    pick.best = true;
    rows.forEach(function (x) { if (!x.best && (jeju ? x.inten <= 32 : x.inten >= 68)) x.good = true; });
    var i = rows.indexOf(pick);
    $('.wp-title').innerHTML = jeju ? '낚시는 물살이 약한 <em>' + dayWord(pick.d, i) + '</em>이 편해요'
                                    : '물이 가장 많이 빠지는 날은 <em>' + dayWord(pick.d, i) + '</em>이에요';
    $('.wp-lead').textContent = (pick.d.getMonth() + 1) + '월 ' + pick.d.getDate() + '일 · ' + pick.m + '물 · 음력으로 계산한 물때입니다';
    $('.wp-basis').textContent = '물때 계산 기준';
    draw(rows, false);
  }

  // 2) 조석 자료로 — 해가 뜬 뒤 1시간 ~ 지기 1시간 전 사이의 간조 중 가장 낮은 것
  function byTide(data) {
    if (!data || !data.days || !data.days.length) return;
    var rows = base();
    rows.forEach(function (x) {
      var key = (x.d.getMonth() + 1) + '/' + x.d.getDate();
      var day = data.days.filter(function (y) { return y.date === key; })[0];
      var sun = c ? T.sunTimes(x.d, c[0], c[1]) : null;
      var a = sun ? toMin(sun.rise) + 60 : 420, b = sun ? toMin(sun.set) - 60 : 1020;
      ((day && day.events) || []).forEach(function (e) {
        if (e.type !== '간조' || e.level == null || e.level === '') return;
        var t = toMin(e.time); if (t < a || t > b) return;
        if (!x.low || +e.level < x.low.level) x.low = { time: e.time, level: +e.level };
      });
    });
    var lv = rows.filter(function (x) { return x.low; }).map(function (x) { return x.low.level; });
    if (lv.length < 3) return;                               // 자료가 모자라면 계산값 그대로
    var mx = Math.max.apply(null, lv), mn = Math.min.apply(null, lv), span = Math.max(1, mx - mn);
    rows.forEach(function (x) { x.h = x.low ? Math.round(18 + (mx - x.low.level) / span * 76) : 6; });
    var where = data.point ? ' · ' + data.point : '';
    if (jeju) {
      var calm = rows.reduce(function (p, q) { return q.inten < p.inten ? q : p; });
      calm.best = true;
      rows.forEach(function (x) { if (!x.best && x.inten <= 32) x.good = true; });
      var ci = rows.indexOf(calm);
      $('.wp-title').innerHTML = '낚시는 물살이 약한 <em>' + dayWord(calm.d, ci) + '</em>이 편해요';
      $('.wp-lead').innerHTML = (calm.d.getMonth() + 1) + '월 ' + calm.d.getDate() + '일 · ' + calm.m + '물' +
        (calm.low ? ' · 낮 간조 <b>' + hmText(calm.low.time) + '</b>' : '') + ' · 조류가 약해 갯바위·방파제가 비교적 편합니다';
      $('.wp-basis').textContent = '막대: 낮 간조 기준' + where;
      draw(rows, true);
      return;
    }
    var best = rows.filter(function (x) { return x.low; }).reduce(function (p, q) { return q.low.level < p.low.level ? q : p; });
    best.best = true;
    rows.forEach(function (x) { if (!x.best && x.low && x.low.level <= mn + span * 0.35) x.good = true; });
    var bi = rows.indexOf(best);
    $('.wp-title').innerHTML = '해루질은 <em>' + dayWord(best.d, bi) + '</em>이 가장 좋아요';
    $('.wp-lead').innerHTML = '<b>' + (best.d.getMonth() + 1) + '월 ' + best.d.getDate() + '일 ' + hmText(best.low.time) +
      ' 간조</b> · 이번 주 낮 시간에 물이 가장 많이 빠집니다. 간조 앞뒤 2시간이 좋아요';
    $('.wp-basis').textContent = '낮 간조 기준' + where;
    draw(rows, true);
  }

  byCalc();
  if (T.data) byTide(T.data);
  document.addEventListener('bada:tide', function (e) { byTide(e.detail); });
})();
