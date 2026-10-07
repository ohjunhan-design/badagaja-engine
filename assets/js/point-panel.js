/* 포인트 상세 패널 — 오른쪽 35% 를 **선택한 포인트의 즉석 상세**로
 * (2026-10-08 바깥 검수 지시)
 *
 *   「핵심은 오른쪽 35% 영역을 단순 포인트 목록이 아니라
 *     **"선택한 포인트의 즉석 상세 패널"**로 바꾸는 것입니다」
 *
 *   손님이 한 화면에서 이만큼을 끝내게 합니다 —
 *     지도에서 장소 선택 → 대상어종 확인 → 오늘 물때·그래프 확인
 *     → 출조 판단
 *   전에는 포인트를 고르고 나서 물때를 보려면 다른 쪽으로 나가야
 *   했습니다. 나갔다 오면 고른 것을 잊습니다.
 *
 * ★ 지켜야 하는 것 (지시 8가지)
 *   ① 물때 그래프는 **새로 계산하지 않습니다.** 기존 메인
 *      compact 그래프(`BADAGAJA_TIDEGRAPH.mount`)를 그대로 부르고,
 *      요약에 쓸 자료도 그쪽이 이미 받은 것을 **갈고리로 받습니다**.
 *   ② 관측소 이름이 오면 **「○○ 관측소 기준」을 반드시** 적습니다.
 *      포인트마다 관측소가 있는 것이 아니라 **권역 기준점**입니다.
 *      그것을 숨기면 손님이 포인트 바로 그 자리의 물때로 오해합니다.
 *   ③ 관측소 연결값이 없으면 **아무것도 추정하지 않습니다.**
 *      시각·수위를 지어내지 않고 「연결되어 있지 않습니다」라 적습니다.
 *   ④ 자료를 못 받아도 **포인트 정보는 그대로 둡니다.** 물때 영역만
 *      「현재 물때를 불러오지 못했습니다」로 바꿉니다.
 *   ⑤ **광고는 이 패널 안에도, 지도와 패널 사이에도 넣지 않습니다.**
 *   ⑥ 휴대폰에서는 지도 **바로 아래**에 선택 포인트가 옵니다
 *      (차림표가 1열로 접습니다 — `.point-hero-map`).
 *   ⑦ 지금은 **대표 포인트 쪽 한 곳**에만 싣습니다. 거기서 재어 본
 *      뒤에 틀로 넓힙니다.
 *
 * ★ 물때는 **한 번만 받습니다.** 포인트를 바꿔도 같은 권역이면 같은
 *   물때입니다. 포인트마다 다시 부르면 같은 것을 여러 번 받습니다.
 */
(function () {
  'use strict';

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  function 좌표글(p) {
    if (typeof p.위도 !== 'number' || typeof p.경도 !== 'number') { return ''; }
    return '북위 ' + p.위도.toFixed(4) + ' · 동경 ' + p.경도.toFixed(4);
  }

  function 달기(설정) {
    var 칸 = 설정.칸, 목록칸 = 설정.목록칸;
    if (!칸 || !목록칸) { return null; }

    /* ── 뼈대를 **한 번만** 만듭니다 ─────────────────────────
         포인트가 바뀔 때 머리(.pp-head)만 다시 그립니다. 물때와
         그래프는 그대로 둡니다 — 같은 권역이면 같은 물때입니다. */
    var 상세 = 만들기('div', 'pp');
    상세.hidden = true;

    var 뒤로 = 만들기('button', 'pp-back', '← 목록으로');
    뒤로.type = 'button';
    상세.appendChild(뒤로);

    var 머리 = 만들기('div', 'pp-head');
    상세.appendChild(머리);

    /* 물때 영역 — 제목 · 관측소 · 요약 · 「다음까지」 · 그래프 */
    var 물때 = 만들기('section', 'pp-tide');
    var 물때머리 = 만들기('div', 'pp-tide-head');
    물때머리.appendChild(만들기('h3', 'pp-tide-t', '오늘 물때'));
    var 역칸 = 만들기('span', 'pp-station');
    물때머리.appendChild(역칸);
    물때.appendChild(물때머리);
    var 요약 = 만들기('div', 'pp-ev');
    물때.appendChild(요약);
    var 다음줄 = 만들기('p', 'pp-next');
    다음줄.hidden = true;
    물때.appendChild(다음줄);
    var 안내 = 만들기('p', 'pp-tide-note', '오늘 물때를 불러오는 중…');
    물때.appendChild(안내);
    var 그래프칸 = 만들기('div', 'pp-graph');
    물때.appendChild(그래프칸);
    상세.appendChild(물때);

    /* 나가는 단추 둘 — 「전체정보」는 이 쪽 안, 「물때 자세히」는 물때 쪽 */
    var 단추줄 = 만들기('div', 'pp-go');
    var 전체 = 만들기('button', 'btn btn--dark pp-go-b', '포인트 전체정보');
    전체.type = 'button';
    단추줄.appendChild(전체);
    if (설정.물때주소) {
      var 자세히 = 만들기('a', 'btn btn--white pp-go-b', '물때 자세히');
      자세히.href = 설정.물때주소;
      단추줄.appendChild(자세히);
    }
    상세.appendChild(단추줄);
    칸.appendChild(상세);

    var 지금것 = null;

    뒤로.addEventListener('click', function () { 목록으로(); });
    전체.addEventListener('click', function () {
      if (지금것 && 설정.카드로) { 설정.카드로(지금것); }
    });

    /* ── 받은 물때를 담아 둡니다 ───────────────────────────
         ★ **없는 것을 만들지 않습니다** (지시 ③)
           `받았나` 가 false 인 동안은 「불러오는 중」이고,
           `실패` 면 「불러오지 못했습니다」입니다. 둘 다
           시각·수위를 **한 자도 적지 않습니다.** */
    var 물때자료 = { 받았나: false, 실패: false, 오늘: null, 내일: null, 관측소: '' };

    function 물때그리기() {
      요약.textContent = '';
      다음줄.hidden = true;
      역칸.textContent = 물때자료.관측소
        ? 물때자료.관측소 + ' 관측소 기준' : '';

      if (!물때자료.받았나) {
        안내.hidden = false;
        안내.textContent = '오늘 물때를 불러오는 중…';
        return;
      }
      if (물때자료.실패) {
        /* ★ 지시 ④ — 포인트 정보는 그대로 두고 **물때 영역만** */
        안내.hidden = false;
        안내.textContent = '현재 물때를 불러오지 못했습니다.';
        그래프칸.hidden = true;
        return;
      }
      var 들 = 물때자료.오늘 || [];
      if (!들.length) {
        /* ★ 지시 ③ — 관측소 연결값이 없으면 **임의 추정 금지** */
        안내.hidden = false;
        안내.textContent = '이 권역은 기준 관측소가 연결되어 있지 않습니다. '
          + '시각과 수위를 짐작해 적지 않습니다.';
        그래프칸.hidden = true;
        return;
      }
      안내.hidden = true;
      그래프칸.hidden = false;

      /* 콘티 그대로 — 「▲ 만조 04:12  312cm」 */
      var 넷 = 들.slice(0, 4);
      var N = window.BADAGAJA_TIDENEXT;
      var 다음것 = N ? N.찾기(넷, 물때자료.내일) : null;
      넷.forEach(function (e) {
        var 간 = (e.type === '간조');
        var 한 = 만들기('div', 'pp-ev-1 ' + (간 ? 'low' : 'high'));
        한.appendChild(만들기('b', 'pp-ev-k', 간 ? '▼ 간조' : '▲ 만조'));
        한.appendChild(만들기('span', 'pp-ev-t', e.time));
        /* 수위는 **있을 때만** 적습니다 */
        if (e.level || e.level === 0) {
          한.appendChild(만들기('span', 'pp-ev-h', e.level + 'cm'));
        }
        if (다음것 && !다음것.내일 && 다음것.때 === e) {
          한.className += ' is-next';
        }
        요약.appendChild(한);
      });
      var 말 = N ? N.글(넷, 물때자료.내일) : '';
      if (말) { 다음줄.textContent = 말; 다음줄.hidden = false; }
    }

    /* ── 그래프 — **기존 compact renderer 를 그대로 부릅니다** (지시 ①)
         `data-events="off"` 로 그래프 머리의 알약 줄을 끕니다.
         바로 위에 같은 네 시각이 요약으로 있어 두 번 나옵니다. */
    function 그래프세우기() {
      if (!window.BADAGAJA_TIDEGRAPH || !설정.권역) {
        물때자료.받았나 = true; 물때자료.실패 = true; 물때그리기(); return;
      }
      그래프칸.setAttribute('data-events', 'off');
      window.BADAGAJA_TIDEGRAPH.mount(그래프칸, 설정.권역, {
        api: 설정.api || 'api/',
        받으면: function (d) {
          /* 관측소 이름은 시계열 쪽이 더 또렷합니다 (지시 ②) */
          if (d && d.station) { 물때자료.관측소 = d.station; }
          if (!d) { 물때자료.받았나 = true; 물때자료.실패 = true; }
          물때그리기();
        },
        물때받으면: function (전체) {
          물때자료.받았나 = true;
          if (!전체 || !전체.days || !전체.days.length) {
            /* 시계열은 왔는데 고·저조 예보가 없을 수 있습니다.
               그때도 **짐작하지 않습니다** — 빈 채로 둡니다. */
            물때자료.오늘 = null; 물때자료.내일 = null;
          } else {
            물때자료.오늘 = (전체.days[0] || {}).events || null;
            물때자료.내일 = (전체.days[1] || {}).events || null;
            if (!물때자료.관측소 && 전체.point) {
              물때자료.관측소 = 전체.point;
            }
          }
          물때그리기();
        }
      });
    }

    function 머리그리기(p) {
      머리.textContent = '';
      머리.appendChild(만들기('h2', 'pp-name', p.차례 + '. ' + p.이름));

      var 표 = 만들기('p', 'pp-chips');
      /* 확인상태 — 「확인된 자리」인지 「대략 위치」인지 */
      표.appendChild(만들기('span', 'pp-chip ' + (p.어림 ? 'is-area' : 'is-ok'),
        p.어림 ? '대략 위치' : '확인된 자리'));
      if (p.지형) { 표.appendChild(만들기('span', 'pp-chip', p.지형)); }
      if (p.등급) { 표.appendChild(만들기('span', 'pp-chip', p.등급 + '급')); }
      머리.appendChild(표);

      if (p.대상 && p.대상.length) {
        var 어 = 만들기('p', 'pp-fish');
        어.appendChild(만들기('b', 'pp-lbl', '대상어종'));
        어.appendChild(만들기('span', null, p.대상.join(' · ')));
        머리.appendChild(어);
      }

      /* 위치 — **자료에 있는 것만**. 좌표가 없으면 그 줄을 안 둡니다 */
      var 자리 = 좌표글(p);
      if (자리 || p.메모) {
        var 곳 = 만들기('p', 'pp-where');
        곳.appendChild(만들기('b', 'pp-lbl', '위치'));
        if (자리) { 곳.appendChild(만들기('span', 'pp-xy', 자리)); }
        if (p.메모) { 곳.appendChild(만들기('span', 'pp-memo', p.메모)); }
        머리.appendChild(곳);
      }
      if (p.출입 && p.출입 !== '자유') {
        머리.appendChild(만들기('p', 'pp-warn', '출입 ' + p.출입));
      }
    }

    function 보이기(p, 끌어올까) {
      if (!p) { return; }
      지금것 = p;
      머리그리기(p);
      목록칸.hidden = true;
      상세.hidden = false;
      if (!그래프칸.getAttribute('data-세움')) {
        그래프칸.setAttribute('data-세움', '1');
        그래프세우기();
      }
      /* 휴대폰에서 지도 아래 패널이 화면 밖일 수 있습니다.
         말풍선에서 **일부러 눌러 들어온 때만** 끌어올립니다 —
         핀을 누를 때마다 쪽이 움직이면 비교하기 어렵습니다. */
      if (끌어올까) {
        try { 상세.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }
        catch (e) { }
      }
    }

    function 목록으로() {
      상세.hidden = true;
      목록칸.hidden = false;
      지금것 = null;
    }

    return { 보이기: 보이기, 목록으로: 목록으로,
             지금것: function () { return 지금것; } };
  }

  window.BADAGAJA_POINTPANEL = { 달기: 달기 };
})();
