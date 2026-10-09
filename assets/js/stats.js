/* 방문 기록 보기 — **주인만 보는 쪽** (2026-10-06)
 *
 * ★ 왜 다시 만드나
 *   옛 사이트의 stats.html 이 서버에 남아 돌고 있었습니다. 새 쪽들과
 *   생김새가 달랐고, 더 큰 문제는 **새 사이트 448쪽이 방문을 하나도
 *   안 세고 있었다**는 것입니다. 그래서 10월 기록이 넷뿐이었습니다.
 *
 * ★ 열쇠말은 **이 컴퓨터에만** 둡니다
 *   `localStorage` 에 넣고 서버에 물을 때만 꺼냅니다. 쪽에도 저장소에도
 *   적지 않습니다.
 *
 * ★ 서버가 죽어도 쪽은 삽니다 (계약-23)
 *   못 받으면 까닭을 적고 멈춥니다. 빈 화면을 보여 주지 않습니다.
 */
(function () {
  var 열쇠칸 = 'bgStatsToken';
  var 열쇠 = '';
  try { 열쇠 = localStorage.getItem(열쇠칸) || ''; } catch (e) {}

  function 찾기(id) { return document.getElementById(id); }
  function 수(n) { return (n || 0).toLocaleString('ko-KR'); }

  function 줄채우기(몸, 것, 링크냐) {
    몸.innerHTML = '';
    var 열쇠들 = Object.keys(것 || {});
    if (!열쇠들.length) {
      var 빈 = document.createElement('tr');
      var 칸 = document.createElement('td');
      칸.colSpan = 2;
      칸.textContent = '아직 기록이 없습니다';
      빈.appendChild(칸); 몸.appendChild(빈);
      return;
    }
    열쇠들.sort(function (a, b) { return (것[b] || 0) - (것[a] || 0); });
    열쇠들.forEach(function (k) {
      var 줄 = document.createElement('tr');
      var 앞 = document.createElement('td');
      if (링크냐 && k.charAt(0) === '/') {
        var a = document.createElement('a');
        a.href = k; a.textContent = k;
        a.target = '_blank'; a.rel = 'noopener';
        앞.appendChild(a);
      } else { 앞.textContent = k; }
      var 뒤 = document.createElement('td');
      뒤.className = 'st-n';
      뒤.textContent = 수(것[k]);
      줄.appendChild(앞); 줄.appendChild(뒤); 몸.appendChild(줄);
    });
  }

  function 막대그리기(날들) {
    var 칸 = 찾기('stDays');
    if (!칸) { return; }
    var 키들 = Object.keys(날들 || {}).sort();
    if (!키들.length) { 칸.innerHTML = '<p class="st-empty">아직 기록이 없습니다</p>'; return; }
    var 달 = 키들[0].slice(0, 7);
    var 해 = +달.slice(0, 4), 월 = +달.slice(5, 7);
    var 날수 = new Date(해, 월, 0).getDate();
    var 가장큰 = 1;
    키들.forEach(function (k) {
      var v = (날들[k] && 날들[k].views) || 0;
      if (v > 가장큰) { 가장큰 = v; }
    });
    var 몸 = '';
    for (var i = 1; i <= 날수; i++) {
      var 두자 = (i < 10 ? '0' : '') + i;
      var 키 = 달 + '-' + 두자;
      var 값 = (날들[키] && 날들[키].views) || 0;
      var 높이 = Math.round((값 / 가장큰) * 100);
      몸 += '<div class="st-bar" title="' + 키 + ' · 조회 ' + 값 + '">'
          + '<i style="height:' + 높이 + '%"></i>'
          + '<b>' + (i % 5 === 0 || i === 1 ? 두자 : '') + '</b></div>';
    }
    칸.innerHTML = 몸;
  }

  /* ★ **검색에서 왔는가** — 들어온 곳 이름으로 가립니다.
   *   서버가 주는 키가 호스트인지 전체 주소인지 모르므로,
   *   **글자 안에 들어 있는지**로 봅니다. 둘 다에서 먹힙니다.
   *   (짐작해 자료 모양을 정하지 않습니다)
   */
  var 검색엔진 = ['naver', 'google', 'daum', 'bing', 'yahoo',
                  'zum', 'duckduckgo', 'yandex', 'baidu'];
  function 검색이냐(k) {
    var s = (k || '').toLowerCase();
    for (var i = 0; i < 검색엔진.length; i++) {
      if (s.indexOf(검색엔진[i]) >= 0) { return true; }
    }
    return false;
  }
  function 직접이냐(k) {
    var s = (k || '').toLowerCase();
    return !s || s === '-' || s.indexOf('직접') >= 0
        || s === 'direct' || s === '(direct)' || s === 'none';
  }

  /* 유입 경로 막대 — 숫자를 글로만 적지 않습니다 (주인 규칙 6-1) */
  function 길막대(칸, from) {
    if (!칸) { return; }
    var 열쇠들 = Object.keys(from || {});
    if (!열쇠들.length) {
      칸.innerHTML = '<p class="st-empty">아직 기록이 없습니다</p>';
      return;
    }
    var 검 = 0, 직 = 0, 밖 = 0;
    열쇠들.forEach(function (k) {
      var v = from[k] || 0;
      if (직접이냐(k)) { 직 += v; }
      else if (검색이냐(k)) { 검 += v; }
      else { 밖 += v; }
    });
    var 모두 = 검 + 직 + 밖;
    if (!모두) {
      칸.innerHTML = '<p class="st-empty">아직 기록이 없습니다</p>';
      return;
    }
    var 몸 = '';
    [['검색', 검], ['직접', 직], ['그 밖', 밖]].forEach(function (p) {
      var 몫 = Math.round((p[1] / 모두) * 100);
      몸 += '<div class="st-path">'
          + '<span class="st-path__t">' + p[0] + '</span>'
          + '<span class="st-path__bar"><i style="width:' + 몫
          + '%"></i></span>'
          + '<span class="st-path__n">' + 몫 + '%</span></div>';
    });
    칸.innerHTML = 몸;
    return { 검색: 검, 모두: 모두 };
  }

  function 그리기(d) {
    var 이제 = new Date();
    var 오늘 = 날글(이제);
    var 오 = (d.days && d.days[오늘]) || { views: 0, visits: 0 };
    var 합 = d.sum || {};

    찾기('stTodayV').textContent = 수(오.visits);
    찾기('stMonthV').textContent = 수(합.visits);

    /* 어제 대비 — 어제 기록이 **있을 때만** 적습니다.
       없는데 0% 를 적으면 「안 늘었다」로 읽힙니다. */
    var 어제날 = new Date(이제.getTime() - 86400000);
    var 어 = d.days && d.days[날글(어제날)];
    var 덧 = 찾기('stDelta');
    if (덧) {
      if (어 && 어.visits) {
        var 율 = ((오.visits - 어.visits) / 어.visits) * 100;
        덧.textContent = '어제 ' + (율 >= 0 ? '+' : '')
                       + (Math.round(율 * 10) / 10) + '%';
        덧.className = 'stat-delta ' + (율 >= 0 ? 'up' : 'down');
      } else {
        덧.textContent = '';
        덧.className = 'stat-delta';
      }
    }

    var 길 = 길막대(찾기('stPaths'), 합.from);
    var 검칸 = 찾기('stSearch');
    if (검칸) {
      검칸.textContent = (길 && 길.모두)
        ? Math.round((길.검색 / 길.모두) * 100) + '%' : '—';
    }

    막대그리기(d.days);
    줄채우기(찾기('stPages'), 합.pages, true);
    줄채우기(찾기('stFrom'), 합.from, false);

    var 고르기 = 찾기('stMonthPick');
    if (고르기 && !고르기.dataset.채움) {
      고르기.innerHTML = '';
      (d.months || [d.month]).slice().reverse().forEach(function (m) {
        var o = document.createElement('option');
        o.value = m; o.textContent = m;
        if (m === d.month) { o.selected = true; }
        고르기.appendChild(o);
      });
      고르기.dataset.채움 = '1';
    }
  }

  function 알림(글) {
    var 칸 = 찾기('stMsg');
    if (칸) { 칸.textContent = 글; 칸.hidden = !글; }
  }

  /* ★ **열쇠말은 쪽 안에서 받습니다** (2026-10-06)
   *
   *   처음에는 `window.prompt()` 로 물었습니다. 두 가지가
   *   나빴습니다.
   *
   *   ① 손님(주인)에게 **브라우저 기본 창**이 튀어나옵니다.
   *      사이트 생김새와 아무 상관없는 거친 창입니다.
   *   ② 그 창이 뜨면 쪽이 **멈춥니다.** 헤드리스 크롬으로 재는
   *      검사기가 영영 안 끝나, 이 쪽 하나가 판정에서
   *      **240초**를 먹었습니다 (다른 쪽은 1초).
   *      그 240초가 판정 전체 시간의 큰 몫이었습니다.
   *
   *   쪽 안에 입력칸을 두면 둘 다 풀립니다.
   */
  function 열쇠칸보이기() {
    var 칸 = 찾기('stKeyBox');
    if (칸) { 칸.hidden = false; }
    var 넣는곳 = 찾기('stKey');
    if (넣는곳) { try { 넣는곳.focus(); } catch (e) {} }
  }

  function 받기(달) {
    if (!열쇠) {
      열쇠칸보이기();
      알림('열쇠말을 넣고 「보기」를 누르세요.');
      return;
    }
    알림('받는 중입니다…');
    var 주소 = '/api/stats.php?t=' + encodeURIComponent(열쇠)
             + (달 ? '&month=' + encodeURIComponent(달) : '');
    fetch(주소).then(function (r) { return r.json(); }).then(function (d) {
      if (!d.ok) {
        알림(d.reason || '못 받았습니다.');
        if (/열쇠말/.test(d.reason || '')) {
          try { localStorage.removeItem(열쇠칸); } catch (e) {}
          열쇠 = '';
        }
        return;
      }
      알림('');
      var 지움 = 찾기('stForget');
      if (지움) { 지움.hidden = false; }   // 열쇠말이 있을 때만 보입니다
      받은것 = d;
      앞달것 = null;          // 달이 바뀌면 이어 붙일 것도 새로
      그리기(d);
    }).catch(function () {
      // 서버가 죽어도 쪽은 삽니다 — 까닭을 적고 멈춥니다
      알림('서버에서 못 받았습니다. 잠시 뒤 다시 보세요.');
    });
  }

  /* ★ 기간 단추 — 자료는 **달 단위**로 옵니다. 오늘·7일·30일은
   *   받아 둔 날짜에서 **셉니다.** 30일이 앞 달에 걸치면 그만큼은
   *   빠지므로, 그 사실을 화면에 적습니다. 모르는 채로 적은
   *   숫자를 내보이지 않습니다.
   */
  var 받은것 = null;
  var 앞달것 = null;          // 월경계를 넘을 때 쓰는 **앞 달** 자료

  var 두자 = function (n) { return (n < 10 ? '0' : '') + n; };
  function 날글(t) {
    return t.getFullYear() + '-' + 두자(t.getMonth() + 1)
         + '-' + 두자(t.getDate());
  }
  function 달글(t) {
    return t.getFullYear() + '-' + 두자(t.getMonth() + 1);
  }

  /* ★ **「30일」이라 써놓고 9일만 세지 않습니다** (지피티 지시)
   *   자료는 달 단위로 옵니다. 기간이 앞 달에 걸치면 **앞 달을
   *   한 번 더 받아** 이어 붙입니다. 그래도 못 채우면 그 사실을
   *   카드에 적습니다 — 조용히 넘기지 않습니다.
   */
  function 앞달받기(달, 다음) {
    if (앞달것 && 앞달것._달 === 달) { 다음(); return; }
    if (!열쇠) { 다음(); return; }
    fetch('/api/stats.php?t=' + encodeURIComponent(열쇠)
          + '&month=' + encodeURIComponent(달))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.ok) { 앞달것 = d; 앞달것._달 = 달; }
        다음();
      }).catch(function () { 다음(); });
  }

  function 기간셈(범위) {
    if (!받은것) { return; }
    if (범위 === 'month') { 그리기(받은것); return; }
    var 날수 = 범위 === 'today' ? 1 : (범위 === '7d' ? 7 : 30);
    var 이제 = new Date();
    var 맨앞 = new Date(이제.getTime() - (날수 - 1) * 86400000);
    var 앞달 = 달글(맨앞);
    if (앞달 !== (받은것.month || '')) {
      앞달받기(앞달, function () { 기간그리기(범위, 날수); });
    } else {
      기간그리기(범위, 날수);
    }
  }

  function 기간그리기(범위, 날수) {
    var 이제 = new Date();
    var 더함 = 0, 빠진날 = 0;
    for (var i = 0; i < 날수; i++) {
      var k = 날글(new Date(이제.getTime() - i * 86400000));
      var 달 = k.slice(0, 7);
      var 그릇 = (달 === (받은것.month || '')) ? 받은것
               : (앞달것 && 달 === (앞달것.month || '') ? 앞달것 : null);
      if (!그릇) { 빠진날++; continue; }     // 끝내 못 받은 달
      var v = 그릇.days && 그릇.days[k];
      더함 += (v && v.visits) || 0;
    }
    찾기('stMonthV').textContent = 수(더함);
    var 카드 = 찾기('stMonthV').closest('.stat-card');
    카드.querySelector('.stat-label').textContent =
      범위 === 'today' ? '오늘 방문' : ('최근 ' + 날수 + '일 방문');
    카드.querySelector('.stat-what').textContent = 빠진날
      ? ('최근 ' + 날수 + '일 가운데 ' + (날수 - 빠진날)
         + '일만 셌습니다 — 나머지 ' + 빠진날 + '일은 못 받았습니다')
      : ('최근 ' + 날수 + '일을 더한 값입니다');
  }

  var 기간칸 = document.querySelector('.st-range');
  if (기간칸) {
    기간칸.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-range]');
      if (!b) { return; }
      var 들 = 기간칸.querySelectorAll('button');
      for (var i = 0; i < 들.length; i++) {
        들[i].className = 들[i] === b ? 'btn btn--sm btn--on' : 'btn btn--sm';
      }
      기간셈(b.getAttribute('data-range'));
    });
  }

  var 고르기 = 찾기('stMonthPick');
  if (고르기) {
    고르기.addEventListener('change', function () { 받기(this.value); });
  }
  var 지우기 = 찾기('stForget');
  if (지우기) {
    지우기.addEventListener('click', function () {
      try { localStorage.removeItem(열쇠칸); } catch (e) {}
      열쇠 = '';
      this.hidden = true;
      열쇠칸보이기();
      알림('열쇠말을 지웠습니다. 다시 넣어야 숫자가 보입니다.');
    });
  }

  /* 쪽 안 열쇠말 칸 — 「보기」를 누르거나 엔터를 치면 받습니다 */
  function 넣은것받기() {
    var 넣는곳 = 찾기('stKey');
    var 값 = (넣는곳 && 넣는곳.value || '').trim();
    if (!값) { 알림('열쇠말을 넣어 주세요.'); return; }
    열쇠 = 값;
    try { localStorage.setItem(열쇠칸, 열쇠); } catch (e) {}
    var 칸 = 찾기('stKeyBox');
    if (칸) { 칸.hidden = true; }
    if (넣는곳) { 넣는곳.value = ''; }
    받기('');
  }
  var 보기단추 = 찾기('stKeyGo');
  if (보기단추) { 보기단추.addEventListener('click', 넣은것받기); }
  var 넣는곳 = 찾기('stKey');
  if (넣는곳) {
    넣는곳.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') { e.preventDefault(); 넣은것받기(); }
    });
  }

  받기('');
})();
