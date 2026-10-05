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

  function 그리기(d) {
    var 이제 = new Date();
    var 두자 = function (n) { return (n < 10 ? '0' : '') + n; };
    var 오늘 = 이제.getFullYear() + '-' + 두자(이제.getMonth() + 1)
             + '-' + 두자(이제.getDate());
    var 오 = (d.days && d.days[오늘]) || { views: 0, visits: 0 };
    var 합 = d.sum || {};

    찾기('stToday').textContent = 수(오.views);
    찾기('stTodayV').textContent = 수(오.visits);
    찾기('stMonth').textContent = 수(합.views);
    찾기('stMonthV').textContent = 수(합.visits);

    var 기기 = 합.device || {};
    var 폰 = 기기.mobile || 0, 피시 = 기기.desktop || 0;
    var 모두 = 폰 + 피시;
    찾기('stMobile').textContent = 모두 ? Math.round((폰 / 모두) * 100) + '%' : '—';

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

  function 받기(달) {
    if (!열쇠) {
      열쇠 = window.prompt('열쇠말을 넣어 주세요') || '';
      if (!열쇠) { 알림('열쇠말이 있어야 숫자를 봅니다.'); return; }
      try { localStorage.setItem(열쇠칸, 열쇠); } catch (e) {}
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
      그리기(d);
    }).catch(function () {
      // 서버가 죽어도 쪽은 삽니다 — 까닭을 적고 멈춥니다
      알림('서버에서 못 받았습니다. 잠시 뒤 다시 보세요.');
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
      알림('열쇠말을 지웠습니다. 새로 고치면 다시 묻습니다.');
    });
  }
  받기('');
})();
