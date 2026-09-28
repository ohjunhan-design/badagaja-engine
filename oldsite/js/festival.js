/* 축제 상세 페이지 — 올해 실제 일정을 한국관광공사 행사정보에서 가져와 표시 */
(function () {
  var main = document.querySelector('.fp');
  if (!main) return;
  var REGION = main.getAttribute('data-region'), NAME = main.getAttribute('data-fest') || '';
  var box = document.getElementById('fpLive');
  if (!box) return;
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function key(s) { return (s || '').replace(/20\d\d|제?\d+회/g, '').replace(/[\s\d·()（）]/g, ''); }
  function md(s) { var p = s.split('-'); return (+p[1]) + '월 ' + (+p[2]) + '일'; }

  // 올해 1월부터 받습니다 — 이번 달부터만 받아 이미 열린 축제가 '공개되지 않았습니다' 로 나왔습니다 (2026-09-24)
  var KST0 = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
  var TODAY = KST0.getFullYear() + '-' + ('0' + (KST0.getMonth() + 1)).slice(-2) + '-' + ('0' + KST0.getDate()).slice(-2);
  fetch('../api/tour.php?kind=festival&region=' + REGION + '&from=' + KST0.getFullYear() + '01').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    var items = (d && d.ok && d.items) || [];
    var k = key(NAME);
    var same = items.filter(function (x) { var kx = key(x.name); return kx.length >= 2 && (kx.indexOf(k) > -1 || k.indexOf(kx) > -1); });
    // 진행 중·다가오는 일정을 먼저, 없으면 올해 가장 최근에 끝난 일정
    var next = same.filter(function (x) { return x.end >= TODAY; }).sort(function (a, b) { return a.start < b.start ? -1 : 1; })[0];
    var hit = next || same.sort(function (a, b) { return a.end < b.end ? 1 : -1; })[0];
    box.innerHTML = '';
    if (!hit) {
      // 관광공사 행사정보에 없는 축제 — 예년에 열린 달을 함께 알려 줍니다 (2026-09-24)
      var mon = +(main.getAttribute('data-month') || 0);
      box.appendChild(el('b', null, mon ? '예년에는 ' + mon + '월에 열렸습니다' : '올해 일정이 아직 공개되지 않았습니다'));
      box.appendChild(document.createTextNode('올해 정확한 날짜는 한국관광공사 행사정보에 아직 없습니다. 등록되면 이 자리에 자동으로 표시되니, 그 전에는 주최 측 공지를 확인해 주세요.'));
      return;
    }
    var kst = new Date(Date.now() + (new Date().getTimezoneOffset() + 540) * 60000);
    var today = new Date(kst.getFullYear(), kst.getMonth(), kst.getDate());
    var s = new Date(hit.start + 'T00:00:00'), e = new Date(hit.end + 'T00:00:00');
    var dd = Math.round((s - today) / 86400000);
    box.appendChild(el('b', null, '올해 일정'));
    var line = el('div');
    var d1 = el('span', 'd', md(hit.start) + ' ~ ' + md(hit.end));
    line.appendChild(d1);
    if (e >= today) line.appendChild(el('span', 'dday', dd <= 0 ? '진행 중' : 'D-' + dd));
    else line.appendChild(el('span', 'dday', '올해 종료'));
    box.appendChild(line);
    if (hit.addr) box.appendChild(el('small', null, '📍 ' + hit.addr.replace(/^[가-힣]+(?:특별자치도|특별자치시|통합특별시|광역시|특별시|도)\s+/, '') + (hit.tel ? ' · ☎ ' + hit.tel : '')));
    box.appendChild(el('small', null, '자료: 한국관광공사 행사정보 · 변경될 수 있으니 방문 전 확인하세요'));
    // 검색엔진용 일정 (실제 날짜)
    try {
      var ld = document.querySelector('script[type="application/ld+json"]');
      if (ld) { var o = JSON.parse(ld.textContent); o.startDate = hit.start; o.endDate = hit.end; if (hit.img) o.image = hit.img; ld.textContent = JSON.stringify(o); }
    } catch (err) { }
  }).catch(function () {
    box.innerHTML = '';
    box.appendChild(el('b', null, '올해 일정을 불러오지 못했습니다'));
    box.appendChild(document.createTextNode('잠시 후 다시 확인해 주세요.'));
  });
})();
