/* 바다가자닷컴 광고 — 모든 쪽 공통 (2026-09-22)
   설정: data/ads.json → tools/build-ads.py → js/ads-data.js (window.BADAGAJA_ADS)
   · 쪽에 박힌 자리: <aside class="ad-slot" data-ad-slot="자리이름" hidden></aside> — 불러오면 저절로 채움
   · 스크립트가 나중에 만드는 자리(숙소 칸 등): BadagajaAds.willShow('자리') 로 먼저 묻고,
     자리를 붙인 뒤 BadagajaAds.mount(el). 이 파일은 광고가 켜졌을 때만 불러오게 해도 됩니다(BadagajaAdsLoad)
   · 전체 스위치(enabled)·자리 스위치가 꺼졌거나 기기가 맞지 않으면 아무것도 불러오지 않습니다. PC = 901px 이상
   · 칸이 화면 가까이 올 때 불러오고, 칸보다 넓은 배너는 비율대로 줄여 보입니다
   · 표시: 배너 첫 부분에 '광고 · ○○'(쿠팡 경제적 이해관계 표기 가이드). 중국어 쪽은 '广告 · ○○'
   · 못 불러오면 칸을 숨겨 빈자리를 남기지 않습니다 */
(function () {
  var A = window.BADAGAJA_ADS || { enabled: false, slots: {} };
  var ZH = /^zh/i.test(document.documentElement.lang || '');
  var PC = window.matchMedia('(min-width: 901px)').matches;

  function cfgOf(name) {
    if (!A.enabled) return null;
    var c = A.slots && A.slots[name];
    if (!c) return null;
    // 자리를 꺼 두었으면(data/ads.json 의 on:false) 싣지 않습니다.
    // 이 줄이 없어 꺼도 계속 나왔습니다 — 광고 관리가 듣지 않던 원인입니다 (2026-09-24)
    if (c.on === false) return null;
    if (c.device === 'pc' && !PC) return null;
    if (c.device === 'mobile' && PC) return null;
    if (ZH && c.banner.provider === 'coupang') return null;   // 쿠팡은 한국 서비스라 중국어 쪽에는 싣지 않음
    return c;
  }
  function tx(b, key) { return (ZH && b[key + '_zh']) || b[key] || ''; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function regionName() {
    var t = (document.title || '').split(/[\s\-|·]/)[0];
    return t || '';
  }

  var coupang = null;   // g.js 는 한 번만 받습니다
  function withCoupang(cb) {
    if (window.PartnersCoupang) return cb();
    if (!coupang) {
      coupang = [];
      var s = document.createElement('script');
      s.src = 'https://ads-partners.coupang.com/g.js'; s.async = true;
      s.onload = function () { var q = coupang; coupang = []; q.forEach(function (f) { f(); }); };
      s.onerror = function () { var q = coupang; q.forEach(function (f) { f(true); }); };
      document.head.appendChild(s);
    }
    coupang.push(cb);
  }
  function fitter(slot, W, H) {
    var wait = 0;
    function fit() {
      var el = slot.querySelector('iframe'); if (!el) return;
      // 자리보다 넓은 배너만 줄입니다. 키우지 않습니다 —
      //   · 기준점이 왼쪽 위라 키우면 오른쪽으로 삐져나가 가로 스크롤이 생깁니다
      //   · 배너가 들어가는 칸이 762px 이라 760px 배너는 이미 꽉 찹니다. 키울 까닭이 없습니다
      //   · 쿠팡 배너는 iframe 안의 그림이라 늘리면 그대로 흐려집니다
      // 폭을 아직 못 재는 순간이 있습니다. 그대로 두면 scale(0) 이 걸려 배너가 사라집니다 (2026-09-24)
      // 부모 폭을 대신 쓰면 안 됩니다 — 부모가 더 넓어서 줄여야 할 배너를 안 줄이고 넘칩니다
      var w = slot.clientWidth;
      // 아직 자리가 안 잡혔으면 조금 뒤 다시. 영영 0 이어도 3초면 그만둡니다
      if (!(w >= 40)) { if (++wait <= 15) setTimeout(fit, 200); return; }
      var s = Math.min(1, w / W);
      if (!(s > 0)) s = 1;
      el.style.display = 'block';   // 쿠팡이 감싸는 div 는 inline 이라 transform 이 안 먹어 iframe 에 겁니다
      el.style.transformOrigin = '0 0';
      el.style.transform = s !== 1 ? 'scale(' + s + ')' : '';
      el.style.marginLeft = Math.max(0, (w - W * s) / 2) + 'px';
      slot.style.height = Math.ceil(H * s) + 'px';
      slot.style.minHeight = '0';
    }
    var n = 0, t = setInterval(function () { if (slot.querySelector('iframe') || ++n > 40) { clearInterval(t); fit(); } }, 150);
    window.addEventListener('resize', fit);
  }
  function labelHtml(b) {
    var badge = ZH ? '广告' : (A.label && A.label.badge) || '광고';
    return '<span class="ad-badge">' + esc(badge) + '</span>' + esc(tx(b, 'label') || (A.label && A.label.text) || '');
  }

  // "지금은 {season} 철이에요" — data/species-index.json 에서 이번 달에 잡을 수 있고 지금 금어기가 아닌 대상 둘.
  // 철이 짧은 대상(그 달다운 것)을 앞에. 못 읽으면 fallback 문구 그대로
  function seasonTitle(el, tpl) {
    var me = document.querySelector('script[src*="js/ads.js"]');   // ads.js 자리에서 사이트 뿌리를 찾습니다
    var root = me ? me.getAttribute('src').replace(/js\/ads\.js.*$/, '') : '';
    fetch(root + 'data/species-index.json').then(function (r) { return r.json(); }).then(function (d) {
      var now = new Date(), M = now.getMonth() + 1, t = M * 100 + now.getDate();
      function banned(s) {
        var b = s.ban; if (!b || b.length < 4) return false;   // [시작월, 일, 끝월, 일]
        var a = b[0] * 100 + b[1], z = b[2] * 100 + b[3]; return a <= z ? (t >= a && t <= z) : (t >= a || t <= z);
      }
      var list = (d.species || []).filter(function (s) { return (s.months || []).indexOf(M) > -1 && !banned(s); });
      list.sort(function (a, b) { return a.months.length - b.months.length || (b.regions || []).length - (a.regions || []).length; });
      var names = list.slice(0, 2).map(function (s) { return s.n; });
      if (names.length) el.textContent = tpl.replace('{season}', names.join('·'));
    }).catch(function () {});
  }

  function render(box, cfg) {
    var b = cfg.banner;
    box.hidden = false; box.classList.remove('ad-wait');
    if (b.provider === 'link') {
      // 제휴 링크를 옆 카드와 같은 모양으로 — 사진 자리는 브랜드 색 바탕으로 실제 숙소 사진과 한눈에 다르게
      var title = tx(b, 'title').replace('{region}', regionName());
      box.classList.add('ad-linkcard');
      box.innerHTML = '<a class="ad-card" href="' + esc(tx(b, 'url')) + '" target="_blank" rel="sponsored nofollow noopener">' +
        '<span class="ad-card-ph" style="background:' + esc(b.color || '#287DFA') + '"><span class="ad-card-brand">✈ ' + esc(b.brand || '') + '</span>' +
        '<span class="ad-card-label">' + labelHtml(b) + '</span></span>' +
        '<span class="ad-card-bd"><b>' + esc(title) + '</b><span>' + esc(tx(b, 'desc')) + '</span></span></a>';
      return;
    }
    var W = +b.width, H = +b.height, it = cfg.intro;
    if (it) {
      // 문구 + 배너 (첫 화면 가운데 등) — 문구는 달 이름 없이, 제목은 이번 달 제철 대상을 저절로 (손으로 달마다 고치지 않게)
      box.classList.add('ad-intro');
      box.innerHTML = '<p class="ad-label">' + labelHtml(b) + '</p><div class="ad-intro-row">' +
        '<div class="ad-intro-txt"><span class="ad-intro-kicker">' + esc(tx(it, 'kicker')) + '</span>' +
        '<b class="ad-intro-title">' + esc(tx(it, 'fallback')) + '</b><span class="ad-intro-desc">' + esc(tx(it, 'desc')) + '</span></div>' +
        '<div class="ad-body" style="min-height:' + H + 'px"></div></div>';
      if (it.title && !ZH) seasonTitle(box.querySelector('.ad-intro-title'), it.title);
    } else {
      // 자리 설정에 label:false 면 '광고 · 쿠팡 파트너스' 줄을 붙이지 않습니다 (2026-09-25 주인 지시)
      var lab = (cfg.label === false) ? '' : '<p class="ad-label">' + labelHtml(b) + '</p>';
      box.innerHTML = lab + '<div class="ad-body" style="min-height:' + H + 'px"></div>';
    }
    var slot = box.querySelector('.ad-body');
    if (b.provider === 'coupang') {
      withCoupang(function (failed) {
        if (failed) { box.hidden = true; return; }
        try {
          new window.PartnersCoupang.G({ id: b.id, template: b.template, trackingCode: b.trackingCode,
            width: String(W), height: String(H), tsource: b.tsource || '', container: slot });
          fitter(slot, W, H);
        } catch (e) { box.hidden = true; }
      });
    } else { box.hidden = true; }
  }

  var io = 'IntersectionObserver' in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return;
      io.unobserve(e.target);
      var c = cfgOf(e.target.getAttribute('data-ad-slot'));
      if (c) render(e.target, c); else e.target.hidden = true;
    });
  }, { rootMargin: '400px 0px' }) : null;

  function mount(box) {
    if (!box || box._adMounted) return; box._adMounted = true;
    var cfg = cfgOf(box.getAttribute('data-ad-slot'));
    if (!cfg) { box.hidden = true; return; }
    if (cfg.banner.provider === 'link' || !io) return render(box, cfg);   // 링크 카드는 가벼워 바로
    box.hidden = false; box.classList.add('ad-wait'); io.observe(box);   // 숨긴 칸은 관찰되지 않아 자리만 보이게
  }

  window.BadagajaAds = { willShow: function (name) { return !!cfgOf(name); }, mount: mount };
  [].forEach.call(document.querySelectorAll('.ad-slot[data-ad-slot]'), mount);

  // 권역 카드 칸(.rc-grid)이 줄을 다 채우지 못해 빈 칸이 생기면 그 칸에만 광고 (hub-grid-pc, 2026-09-22)
  // 광고 칸은 .rc 가 아니라 aside.ad-slot — 권역 수·지도 연결·번호를 세는 스크립트(.rc)에 섞이지 않습니다
  if (cfgOf('hub-grid-pc')) {
    [].forEach.call(document.querySelectorAll('.rc-grid'), function (g) {
      if (g.querySelector('.ad-slot')) return;
      var n = [].filter.call(g.children, function (c) { return c.classList.contains('rc'); }).length;
      var cols = (getComputedStyle(g).gridTemplateColumns || '').split(' ').filter(function (x) { return /px$/.test(x); }).length;
      if (!n || cols < 2 || n % cols === 0) return;   // 숨겨진 칸(열 없음)·꽉 찬 칸은 그대로
      var a = document.createElement('aside');
      a.className = 'ad-slot rc-ad'; a.setAttribute('data-ad-slot', 'hub-grid-pc'); a.setAttribute('aria-label', ZH ? '广告' : '광고');
      g.appendChild(a); mount(a);
    });
  }
})();
