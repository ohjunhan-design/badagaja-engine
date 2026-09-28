/* 바다가자 포인트 지도 (카카오맵)
 * - 카드의 data-lat / data-lng / data-loc(pin|area) 값으로 지도에 표시
 * - 일반지도 / 위성지도 전환, 번호 핀(등급 색), 대략 위치는 점선 원
 * - 키가 없거나 카카오맵 로드 실패 시 기존 번호 지도를 그대로 둠
 */
// 메인 검색 등에서 #point-N 으로 들어오면 해당 카드를 펼쳐 보여줌 (모바일 10개 제한·필터에 가려진 경우 포함)
(function () {
  if (!/^#point-\d+$/.test(location.hash)) return;
  function go() {
    var b = document.querySelector('.map-point[data-target="' + location.hash.slice(1) + '"]');
    if (b) b.click();
  }
  if (document.readyState === 'complete') setTimeout(go, 50); else window.addEventListener('load', function () { setTimeout(go, 50); });
})();

(function () {
  var cfg = window.BADAGAJA_MAP || {};
  var wrap = document.getElementById('mapWrap');
  var grid = document.getElementById('pointsGrid');
  if (!cfg.kakaoJsKey || !wrap || !grid) return;

  var cards = [].slice.call(grid.querySelectorAll('.card[id^="point-"]'));
  var pts = [];

  // 카드에서 포인트 이름을 찾습니다.
  //
  // ★ 2026-09-26 — 여기가 6일 동안 깨져 있었습니다.
  //   9월 20일 글자 모양을 전남 기준으로 통일하면서 카드 이름 줄이
  //   font-weight:800 에서 font-weight:700;font-size:1.08rem 으로 바뀌었는데,
  //   이 코드는 그대로 800 을 찾고 있었습니다. 그래서 지도 풍선에
  //   이름 대신 "point-0" 같은 아이디가 떴습니다.
  //
  //   인라인 스타일로 요소를 찾으면 디자인을 고칠 때마다 조용히 깨집니다.
  //   여러 모양을 받아들이고, 그래도 못 찾으면 첫 줄 글을 씁니다.
  function 이름찾기(c) {
    var t = c.querySelector('[style*="font-size:1.08rem"]')
         || c.querySelector('[style*="font-weight:700"]');
    if (t) return t.textContent.trim();
    // 마지막 기댈 곳 — 카드 맨 앞 줄의 글
    var first = c.firstElementChild && c.firstElementChild.firstElementChild;
    return first ? first.textContent.trim() : '';
  }

  cards.forEach(function (c, i) {
    var lat = parseFloat(c.getAttribute('data-lat')), lng = parseFloat(c.getAttribute('data-lng'));
    var title = 이름찾기(c) || c.id;
    var b = c.querySelector('.badge[class*="grade-"]'), m = b && b.className.match(/grade-([ABC])/);
    pts.push({ card: c, id: c.id, no: (title.match(/^(\d+)\./) || [0, i + 1])[1], name: title.replace(/^\d+\.\s*/, ''),
      grade: m ? m[1] : 'C', lat: lat, lng: lng, loc: c.getAttribute('data-loc') || 'pin', has: !isNaN(lat) && !isNaN(lng) });
  });
  var withPos = pts.filter(function (p) { return p.has; });
  if (!withPos.length) return;

  var s = document.createElement('script');
  s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=' + encodeURIComponent(cfg.kakaoJsKey);
  s.onload = function () { try { kakao.maps.load(init); } catch (e) {} };
  document.head.appendChild(s);

  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

  function reveal(id) {
    var btn = document.querySelector('.map-point[data-target="' + id + '"]');
    if (btn) { btn.click(); return; }
    var c = document.getElementById(id); if (c) c.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function init() {
    wrap.classList.add('kmap-on');
    wrap.classList.remove('m-hide');
    var legendRow = wrap.nextElementSibling; if (legendRow) legendRow.classList.remove('m-hide');
    var sec = document.getElementById('map');
    var h2 = sec && sec.querySelector('h2'); if (h2) h2.textContent = h2.textContent.replace('포인트 번호 지도', '포인트 지도');
    var desc = sec && sec.querySelector('h2 + p');
    if (desc) {
      desc.classList.remove('m-hide');
      desc.textContent = '번호 핀은 그 장소, 점선 원은 대략 위치입니다. 현장 표지판과 규정을 확인하세요.';
    }

    var box = el('div', 'kmap'); wrap.appendChild(box);
    var map = new kakao.maps.Map(box, { center: new kakao.maps.LatLng(withPos[0].lat, withPos[0].lng), level: 9 });
    map.setZoomable(false);
    map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);

    // 일반 / 위성 전환
    var tbar = el('div', 'kmap-type');
    [['ROADMAP', '일반지도'], ['HYBRID', '위성지도']].forEach(function (t, i) {
      var b = el('button', i === 0 ? 'on' : '', t[1]); b.type = 'button';
      b.addEventListener('click', function () {
        map.setMapTypeId(kakao.maps.MapTypeId[t[0]]);
        [].forEach.call(tbar.children, function (x) { x.classList.toggle('on', x === b); });
      });
      tbar.appendChild(b);
    });
    wrap.appendChild(tbar);

    // 스크롤 확대 잠금 (페이지 스크롤 방해 방지)
    var lock = el('button', 'kmap-lock', '지도를 눌러 확대·이동'); lock.type = 'button';
    wrap.appendChild(lock);
    function unlock() { map.setZoomable(true); lock.hidden = true; }
    lock.addEventListener('click', unlock);
    kakao.maps.event.addListener(map, 'click', unlock);
    kakao.maps.event.addListener(map, 'dragstart', unlock);

    // 같은 좌표 겹침 분산
    var seen = {};
    withPos.forEach(function (p) {
      var k = p.lat.toFixed(4) + ',' + p.lng.toFixed(4), n = seen[k] = (seen[k] || 0) + 1;
      if (n > 1) { var a = n * 2.4, r = 0.0009 * Math.sqrt(n); p.dlat = p.lat + r * Math.sin(a); p.dlng = p.lng + r * Math.cos(a); }
      else { p.dlat = p.lat; p.dlng = p.lng; }
    });

    var bounds = new kakao.maps.LatLngBounds();
    var pop = new kakao.maps.CustomOverlay({ yAnchor: 1.25, zIndex: 20 });
    var ring = new kakao.maps.Circle({ strokeWeight: 2, strokeColor: '#C07B22', strokeOpacity: .9, strokeStyle: 'dash', fillColor: '#C07B22', fillOpacity: .12 });
    var active = null;

    function open(p) {
      if (active) active.dom.classList.remove('on');
      active = p; p.dom.classList.add('on');
      var pos = new kakao.maps.LatLng(p.dlat, p.dlng);
      var card = el('div', 'kmap-pop');
      var x = el('button', 'x', '×'); x.type = 'button'; x.setAttribute('aria-label', '닫기');
      x.addEventListener('click', function () { pop.setMap(null); ring.setMap(null); p.dom.classList.remove('on'); active = null; });
      card.appendChild(x);
      card.appendChild(el('b', null, p.no + '. ' + p.name));
      card.appendChild(el('span', 'acc ' + p.loc, p.loc === 'area' ? '대략 위치 (주변 지역)' : '검색된 장소 위치'));
      var row = el('div', 'act');
      var go = el('button', 'go', '상세 카드 보기'); go.type = 'button';
      go.addEventListener('click', function () { reveal(p.id); });
      // 카카오맵 바로가기·길찾기 링크는 두지 않습니다 (2026-09-20)
      row.appendChild(go); card.appendChild(row);
      pop.setContent(card); pop.setPosition(pos); pop.setMap(map);
      if (p.loc === 'area') { ring.setPosition(pos); ring.setRadius(900); ring.setMap(map); } else ring.setMap(null);
      if (map.getLevel() > 7) map.setLevel(p.loc === 'area' ? 7 : 6, { anchor: pos });
      map.panTo(pos);
    }

    withPos.forEach(function (p) {
      var d = el('button', 'kpin g' + p.grade + (p.loc === 'area' ? ' area' : ''), p.no);
      d.type = 'button'; d.title = p.name;
      d.addEventListener('click', function (e) { e.stopPropagation(); open(p); });
      p.dom = d;
      new kakao.maps.CustomOverlay({ position: new kakao.maps.LatLng(p.dlat, p.dlng), content: d, yAnchor: .5, zIndex: p.loc === 'area' ? 1 : 2 }).setMap(map);
      bounds.extend(new kakao.maps.LatLng(p.dlat, p.dlng));
    });
    var touched = false;
    function fit() { map.relayout(); map.setBounds(bounds, 50, 40, 50, 40); }
    fit(); setTimeout(fit, 300); setTimeout(fit, 1200);
    kakao.maps.event.addListener(map, 'dragstart', function () { touched = true; });
    kakao.maps.event.addListener(map, 'zoom_start', function () { touched = true; });

    // 범례 + 지도에 없는 포인트
    var chip = wrap.querySelector('.map-chip');
    var missing = pts.filter(function (p) { return !p.has; });
    if (chip) chip.textContent = '📍 지도 표시 ' + withPos.length + '곳' + (missing.length ? ' · 위치 미확인 ' + missing.length + '곳' : '');
    if (legendRow) {
      var hint = [].slice.call(legendRow.children).filter(function (x) { return /번호를 누르면/.test(x.textContent); })[0];
      if (hint) hint.textContent = '핀을 누르면 정보·길찾기';
      legendRow.appendChild(el('span', 'badge kmap-leg', '● 장소 위치'));
      legendRow.appendChild(el('span', 'badge kmap-leg area', '◌ 대략 위치'));
    }

    // 카드마다 "지도에서 보기"
    withPos.forEach(function (p) {
      var link = p.card.querySelector('.maplink');
      var b = el('button', 'maplink kmap-card', '🗺️ 지도에서 보기'); b.type = 'button';
      b.addEventListener('click', function () {
        (sec || wrap).scrollIntoView({ behavior: 'smooth', block: 'start' });
        setTimeout(function () { map.relayout(); if (map.getLevel() > 8) map.setLevel(8); open(p); }, 450);
      });
      if (link) link.parentNode.insertBefore(b, link); else p.card.appendChild(b);
    });

    var rt;
    window.addEventListener('resize', function () {
      clearTimeout(rt);
      rt = setTimeout(function () { if (touched || active) map.relayout(); else fit(); }, 200);
    });
  }
})();
