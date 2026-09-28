/* 관광·맛집·숙소 — 전국 57권역 여행 자료 (2026-09-23)
   자료: data/travel-data.json (tools/build-travel-data.py 가 모읍니다)
   권역을 고르면 그 권역의 명소·맛집·코스·축제·체험마을을 갈래별로 그립니다.
   전국 목록(이번 달 축제·동행별 코스)은 갈래 탭과 겹쳐서 뺐습니다 (2026-09-23 주인 지시). */
(function () {
  var D = null, cur = null, tab = 'spots', theme = '';
  var THEMES = ['가족', '연인', '부모님', '혼자', '친구'];
  var NOW_M = new Date().getMonth() + 1;

  function $(id) { return document.getElementById(id); }
  function el(t, c, x) { var e = document.createElement(t); if (c) e.className = c; if (x != null) e.textContent = x; return e; }
  function esc(s) { return String(s == null ? '' : s); }

  var TAB = [
    ['spots', '명소'], ['eat', '맛집'], ['courses', '코스'],
    ['festivals', '축제'], ['villages', '체험마을']
  ];

  function region(slug) {
    for (var i = 0; i < D.regions.length; i++) if (D.regions[i].slug === slug) return D.regions[i];
    return null;
  }

  /* 권역 단추 — 묶음별로 묶어서 */
  function drawPicker() {
    var box = $('tvPick'); if (!box) return;
    box.innerHTML = '';
    var groups = {};
    D.regions.forEach(function (r) { (groups[r.group] = groups[r.group] || []).push(r); });
    Object.keys(D.groups).forEach(function (g) {
      if (!groups[g]) return;
      var row = el('div', 'tv-grow');
      row.appendChild(el('b', null, D.groups[g]));
      groups[g].forEach(function (r) {
        var b = el('button', 'tv-rbtn', r.name);
        b.type = 'button';
        b.setAttribute('data-slug', r.slug);
        b.addEventListener('click', function () { pick(r.slug, true); });
        row.appendChild(b);
      });
      box.appendChild(row);
    });
  }

  function markPicked() {
    [].forEach.call(document.querySelectorAll('#tvPick .tv-rbtn'), function (b) {
      b.classList.toggle('on', b.getAttribute('data-slug') === cur);
    });
  }

  /* 갈래 단추 — 자료가 없는 갈래는 흐리게 */
  function drawTabs(r) {
    var box = $('tvTabs'); box.innerHTML = '';
    TAB.forEach(function (t) {
      var n = (r[t[0]] || []).length;
      var b = el('button', 'tv-tab' + (t[0] === tab ? ' on' : '') + (n ? '' : ' off'), '');
      b.type = 'button';
      b.appendChild(el('span', null, t[1]));
      b.appendChild(el('em', null, String(n)));
      if (n) b.addEventListener('click', function () {
        tab = t[0];
        if (tab !== 'courses') theme = '';     // 코스를 떠나면 동행 거르기는 풉니다
        drawTabs(r); drawThemePick(r); drawList(r);
      });
      box.appendChild(b);
    });
  }

  /* 동행 거르기 — 코스 탭에서만, 그 권역에 실제로 있는 동행만 (2026-09-23 주인 지시) */
  function drawThemePick(r) {
    var box = $('tvThemePick'); if (!box) return;
    var have = [];
    (r.courses || []).forEach(function (c) {
      THEMES.forEach(function (t) {
        if ((c.theme || '').indexOf(t) >= 0 && have.indexOf(t) < 0) have.push(t);
      });
    });
    if (tab !== 'courses' || have.length < 2) { box.hidden = true; box.innerHTML = ''; return; }
    box.hidden = false;
    box.innerHTML = '';
    [''].concat(have).forEach(function (t) {
      var b = el('button', 'tv-tbtn' + (t === theme ? ' on' : ''), t || '전체');
      b.type = 'button';
      b.addEventListener('click', function () { theme = t; drawThemePick(r); drawList(r); });
      box.appendChild(b);
    });
  }

  function card(html) { var d = el('div', 'tv-card'); d.innerHTML = html; return d; }

  function drawList(r) {
    var box = $('tvList'); box.innerHTML = '';
    var list = r[tab] || [];
    if (!list.length) {
      box.appendChild(el('p', 'tv-none', '이 권역에는 아직 이 갈래 자료가 없습니다.'));
      return;
    }
    if (tab === 'spots') {
      list.forEach(function (x) {
        box.appendChild(card('<b>' + esc(x.name) + '</b>'
          + (x.kind ? '<span class="tv-kind">' + esc(x.kind) + '</span>' : '')
          + (x.addr ? '<small>' + esc(x.addr) + '</small>' : '')
          + (x.desc ? '<p>' + esc(x.desc) + '</p>' : '')));
      });
    } else if (tab === 'eat') {
      list.forEach(function (x) {
        box.appendChild(card('<b>' + esc(x.name) + '</b>'
          + (x.when ? '<span class="tv-when">' + esc(x.when) + '</span>' : '')
          + (x.desc ? '<p>' + esc(x.desc) + '</p>' : '')));
      });
    } else if (tab === 'courses') {
      var cs = theme ? list.filter(function (x) { return (x.theme || '').indexOf(theme) >= 0; }) : list;
      if (!cs.length) { box.appendChild(el('p', 'tv-none', theme + '과 함께 갈 코스는 아직 없습니다.')); return; }
      cs.forEach(function (x) {
        var steps = (x.steps || []).map(function (s) { return '<li>' + esc(s) + '</li>'; }).join('');
        box.appendChild(card('<b>' + esc(x.title) + '</b>'
          + (x.theme ? '<span class="tv-theme">' + esc(x.theme) + '</span>' : '')
          + (steps ? '<ol class="tv-steps">' + steps + '</ol>' : '')));
      });
    } else if (tab === 'festivals') {
      // 이번 달에 열리는 것을 앞에 놓고 표시합니다 (2026-09-23 주인 지시)
      list.slice().sort(function (a, b) {
        var an = a.m === NOW_M ? 0 : 1, bn = b.m === NOW_M ? 0 : 1;
        return an - bn || (a.m || 0) - (b.m || 0);
      }).forEach(function (x) {
        var now = x.m === NOW_M;
        box.appendChild(card('<b>' + esc(x.n) + '</b>'
          + (x.m ? '<span class="tv-when' + (now ? ' now' : '') + '">' + x.m + '월'
                 + (now ? ' · 이번 달' : '') + '</span>' : '')
          + (x.place || x.d ? '<p>' + esc(x.place || x.d) + '</p>' : '')));
      });
    } else {
      list.forEach(function (x) {
        var nm = x.name || x.n || '';
        box.appendChild(card('<b>' + esc(nm) + '</b>'
          + (x.addr ? '<small>' + esc(x.addr) + '</small>' : '')
          + (x.desc ? '<p>' + esc(x.desc) + '</p>' : '')));
      });
    }
  }

  function pick(slug, scroll) {
    var r = region(slug); if (!r) return;
    cur = slug;
    $('tvName').textContent = r.name;
    $('tvGroup').textContent = D.groups[r.group] || '';
    var link = $('tvMore');
    if (link) { link.href = r.slug + '.html'; link.textContent = r.name + ' 권역 쪽 보기 →'; }
    if (!(r[tab] || []).length) {           // 고른 갈래가 비었으면 자료가 있는 갈래로
      for (var i = 0; i < TAB.length; i++) if ((r[TAB[i][0]] || []).length) { tab = TAB[i][0]; break; }
    }
    drawTabs(r); drawThemePick(r); drawList(r); markPicked();
    try { localStorage.setItem('badagaja-travel-region', slug); } catch (e) { }
    if (scroll) {
      var t = $('tvPanel');
      if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  // 자료는 js/travel-data.js 가 실어 줍니다 (서버가 data/ 폴더를 막아 두어 직접 못 읽습니다)
  D = window.BADAGAJA_TRAVEL_DATA;
  if (!D || !D.regions || !D.regions.length) {
    var w = $('tvWait');
    if (w) w.textContent = '여행 자료를 불러오지 못했습니다. 잠시 뒤 다시 열어 보세요.';
    return;
  }
  drawPicker();
  var start = '';
  try { start = localStorage.getItem('badagaja-travel-region') || ''; } catch (e) { }
  if (!region(start)) start = D.regions[0].slug;
  pick(start, false);
  window.BADAGAJA_TRAVEL = { pick: pick };   // 밖에서 권역을 고를 때 씁니다
  var wait = $('tvWait'); if (wait) wait.hidden = true;
})();
