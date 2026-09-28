/* 바다가자 중국어(간체) 포인트 지도 — 카드의 data-lat / data-lng / data-loc(pin|area)로 카카오맵에 번호 핀 표시
 * 원본 point/point-map.js의 한국어판과 분리된 중국어 전용 스크립트
 */
// 권역 이동줄: 현재 권역이 보이도록 가로 위치 맞춤
(function () {
  var list = document.querySelector('.region-nav .rn-list'), on = list && list.querySelector('a.on');
  if (on) list.scrollLeft = Math.max(0, on.offsetLeft - (list.clientWidth - on.offsetWidth) / 2);
})();

(function () {
  var cfg = window.BADAGAJA_MAP || {};
  var box = document.getElementById('zpMap'), grid = document.getElementById('zpGrid');
  if (!box || !grid) return;
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  var cards = [].slice.call(grid.querySelectorAll('.zp-card'));
  var pts = cards.map(function (c) {
    var lat = parseFloat(c.getAttribute('data-lat')), lng = parseFloat(c.getAttribute('data-lng'));
    return { card: c, id: c.id, no: c.getAttribute('data-no'), name: c.getAttribute('data-name'), grade: c.getAttribute('data-grade') || 'C', loc: c.getAttribute('data-loc') || 'pin', lat: lat, lng: lng, has: !isNaN(lat) && !isNaN(lng) };
  });
  var withPos = pts.filter(function (p) { return p.has; });
  function fallback(msg) { box.innerHTML = ''; box.appendChild(el('p', 'zp-map-fallback', msg)); }
  if (!cfg.kakaoJsKey || !withPos.length) { fallback('暂时无法显示地图，请使用下方各地点的地图链接。'); return; }

  // #point-N 으로 들어오면 해당 카드 강조
  function focusCard(id) {
    var c = document.getElementById(id); if (!c) return;
    c.scrollIntoView({ behavior: 'smooth', block: 'center' });
    c.classList.add('hl'); setTimeout(function () { c.classList.remove('hl'); }, 2200);
  }
  if (/^#point-\d+$/.test(location.hash)) window.addEventListener('load', function () { setTimeout(function () { focusCard(location.hash.slice(1)); }, 300); });

  var s = document.createElement('script');
  s.src = 'https://dapi.kakao.com/v2/maps/sdk.js?autoload=false&appkey=' + encodeURIComponent(cfg.kakaoJsKey);
  s.onload = function () { try { kakao.maps.load(init); } catch (e) { fallback('地图加载失败，请使用下方各地点的地图链接。'); } };
  s.onerror = function () { fallback('地图加载失败，请使用下方各地点的地图链接。'); };
  document.head.appendChild(s);

  function init() {
    box.innerHTML = '';
    var map = new kakao.maps.Map(box, { center: new kakao.maps.LatLng(withPos[0].lat, withPos[0].lng), level: 9 });
    map.setZoomable(false);
    map.addControl(new kakao.maps.ZoomControl(), kakao.maps.ControlPosition.RIGHT);

    var tbar = el('div', 'kmap-type');
    [['ROADMAP', '普通地图'], ['HYBRID', '卫星地图']].forEach(function (t, i) {
      var b = el('button', i === 0 ? 'on' : '', t[1]); b.type = 'button';
      b.addEventListener('click', function () { map.setMapTypeId(kakao.maps.MapTypeId[t[0]]); [].forEach.call(tbar.children, function (x) { x.classList.toggle('on', x === b); }); });
      tbar.appendChild(b);
    });
    box.appendChild(tbar);
    var lock = el('button', 'kmap-lock', '点击地图后可缩放'); lock.type = 'button'; box.appendChild(lock);
    function unlock() { map.setZoomable(true); lock.hidden = true; }
    lock.addEventListener('click', unlock);
    kakao.maps.event.addListener(map, 'click', unlock);
    kakao.maps.event.addListener(map, 'dragstart', unlock);

    var seen = {};
    withPos.forEach(function (p) {
      var k = p.lat.toFixed(4) + ',' + p.lng.toFixed(4), n = seen[k] = (seen[k] || 0) + 1;
      if (n > 1) { var a = n * 2.4, r = 0.0009 * Math.sqrt(n); p.dlat = p.lat + r * Math.sin(a); p.dlng = p.lng + r * Math.cos(a); } else { p.dlat = p.lat; p.dlng = p.lng; }
    });
    var bounds = new kakao.maps.LatLngBounds();
    var pop = new kakao.maps.CustomOverlay({ yAnchor: 1.25, zIndex: 20 });
    var ring = new kakao.maps.Circle({ strokeWeight: 2, strokeColor: '#C07B22', strokeOpacity: .9, strokeStyle: 'dash', fillColor: '#C07B22', fillOpacity: .12 });
    var active = null;
    function open(p) {
      if (active) active.dom.classList.remove('on');
      active = p; p.dom.classList.add('on');
      var pos = new kakao.maps.LatLng(p.dlat, p.dlng), card = el('div', 'kmap-pop');
      var x = el('button', 'x', '×'); x.type = 'button'; x.setAttribute('aria-label', '关闭');
      x.addEventListener('click', function () { pop.setMap(null); ring.setMap(null); p.dom.classList.remove('on'); active = null; });
      card.appendChild(x);
      var t = el('b', null, p.no + '. ' + p.name); t.lang = 'ko'; card.appendChild(t);
      card.appendChild(el('span', 'acc ' + p.loc, p.loc === 'area' ? '大致位置（附近区域）' : '搜索到的位置'));
      var row = el('div', 'act');
      var go = el('button', 'go', '查看详情'); go.type = 'button';
      go.addEventListener('click', function () { focusCard(p.id); });
      var nav = el('a', 'nav', 'Naver 地图'); nav.href = 'https://map.naver.com/p/search/' + encodeURIComponent(p.name); nav.target = '_blank'; nav.rel = 'noopener';
      row.appendChild(go); row.appendChild(nav); card.appendChild(row);
      pop.setContent(card); pop.setPosition(pos); pop.setMap(map);
      if (p.loc === 'area') { ring.setPosition(pos); ring.setRadius(900); ring.setMap(map); } else ring.setMap(null);
      if (map.getLevel() > 7) map.setLevel(p.loc === 'area' ? 7 : 6, { anchor: pos });
      map.panTo(pos);
    }
    withPos.forEach(function (p) {
      var d = el('button', 'kpin g' + p.grade + (p.loc === 'area' ? ' area' : ''), p.no); d.type = 'button'; d.title = p.name;
      d.addEventListener('click', function (e) { e.stopPropagation(); open(p); });
      p.dom = d;
      new kakao.maps.CustomOverlay({ position: new kakao.maps.LatLng(p.dlat, p.dlng), content: d, yAnchor: .5, zIndex: p.loc === 'area' ? 1 : 2 }).setMap(map);
      bounds.extend(new kakao.maps.LatLng(p.dlat, p.dlng));
      // 카드에 "在地图上查看" 버튼
      var b = el('button', 'zp-onmap', '🗺️ 在地图上查看'); b.type = 'button';
      b.addEventListener('click', function () { document.getElementById('map').scrollIntoView({ behavior: 'smooth', block: 'start' }); setTimeout(function () { map.relayout(); open(p); }, 450); });
      var maps = p.card.querySelector('.zr-maps'); if (maps) maps.insertBefore(b, maps.firstChild);
    });
    function fit() { map.relayout(); map.setBounds(bounds, 50, 40, 50, 40); }
    fit(); setTimeout(fit, 300);
    var rt; window.addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(function () { if (!active) fit(); else map.relayout(); }, 200); });
  }
})();
