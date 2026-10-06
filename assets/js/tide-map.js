/* 전국 물때 지도 — 권역을 **지도에서 고릅니다** (2026-10-02)
 *
 * ★ 새로 만든 것이 아니라 **되살린 것**입니다
 *   옛 사이트에 `oldsite/js/tide-map.js` 가 있었습니다. 주인 지시로
 *   만든 것이었는데(2026-09-23), 새 사이트를 짜며 빠뜨렸습니다.
 *   주인이 먼저 찾으셨습니다 — 「언제 물때 페이지에 지도가 들어갈까?」
 *
 *   옛 것의 **배율 단계**를 그대로 살립니다.
 *     배율 13 이상 — 점만
 *     배율 12      — 권역 이름
 *     배율 11 이하 — 이름 + **오늘 간조 시각**
 *
 * ★ 겉모습은 지피티 시안 `tide-map-selector-v1.html` 그대로입니다.
 *   「옛 동작을 되살리되, 현재 지도 UI 규칙에 맞춰 다시 입힙니다.
 *     처음부터 새로 짜지 않습니다」
 *
 * ★ 핀을 눌러도 **바로 넘어가지 않습니다**
 *   「지도에서 여러 권역을 비교해보고 싶은 사람에게 핀 클릭 즉시
 *     페이지 이동은 너무 공격적입니다」 — 오른쪽 카드만 바뀌고,
 *   손님이 단추를 눌러야 넘어갑니다.
 *
 * ★ 카드 57장은 **지우지 않습니다** (계약-23)
 *   접어 두고 「57권역 목록으로 보기」로 폅니다. 지도를 못 받으면
 *   저절로 펴집니다.
 */
(function () {
  'use strict';

  var 칸 = document.getElementById('tideMap');
  if (!칸) { return; }
  var 자료칸 = document.getElementById('물때지도자료');
  if (!자료칸) { return; }
  var 자료;
  try { 자료 = JSON.parse(자료칸.textContent); } catch (e) { return; }

  var 권역들 = (자료.권역들 || []).filter(function (r) {
    return typeof r.위도 === 'number' && typeof r.경도 === 'number';
  });
  /* ★ **지도가 못 떠도 2주 상세는 세웁니다** (계약-23)
       카카오 지도는 **바깥**입니다. 그것이 죽어도 14일 물때는
       보여야 합니다 — 자료는 우리 서버에서 받고 달력은 계산으로
       나옵니다. 전에는 여기서 통째로 빠져나가, 권역 쪽에서
       「14일 물때표 보기」를 눌러 와도 아무 일이 안 생겼습니다. */
  if (!권역들.length || !자료.지도키 || !window.BADAGAJA_MAP) {
    펴기();
    상세세우기();
    return;
  }

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  // 지도를 못 받으면 **카드 목록을 저절로 폅니다** (계약-23)
  function 펴기() {
    /* ★ **지도를 못 받았다고 몸통에 적습니다** (2026-10-02 바깥 검수)
         차림표가 그것을 보고 2열을 1열로 접습니다. 기능만 살리고
         화면을 반쯤 비워 두면 「깨진 쪽」으로 보입니다. */
    try { document.body.classList.add('tide-map-failed'); } catch (e) {}
    칸.hidden = true;
    var d = document.getElementById('allRegions');
    if (d) { d.open = true; }
  }

  var 지도 = null, 고른것 = null, 지금모드 = '';
  var 카드 = document.getElementById('tidePick');
  var 거르개 = document.getElementById('tideMapFilter');
  var 지금묶음 = '전국';

  /* ★ **지도를 못 받아도 2주 상세는 세웁니다** (계약-23)
       카카오 지도는 바깥입니다. 인터넷이 막히거나 열쇠가 안 먹어도
       14일 물때는 보여야 합니다 — 자료는 우리 서버에서 받고,
       물때 번호는 계산으로 나옵니다.
       전에는 `.catch(펴기)` 로 끝나 상세가 통째로 안 세워졌습니다. */
  window.BADAGAJA_MAP.불러오기(자료.지도키)
    .then(그리기)
    .catch(function () { 펴기(); 상세세우기(); });

  function 그리기() {
    var 판 = 만들기('div', 'tm-canvas');
    칸.appendChild(판);
    // 전국이 한 장에 들어오는 배율로 엽니다 (옛 것과 같은 자리)
    지도 = window.BADAGAJA_MAP.만들기(판, { 중심: [35.55, 127.6], 배율: 13 });

    조작단추();
    핀찍기();
    맞추기();
    setTimeout(맞추기, 300);
    setTimeout(맞추기, 1200);

    // 배율이 바뀔 때마다 핀 꼴을 바꿉니다
    if (window.kakao && kakao.maps) {
      kakao.maps.event.addListener(지도.날것, 'zoom_changed', 꼴고치기);
      kakao.maps.event.addListener(지도.날것, 'idle', 꼴고치기);
    }
    꼴고치기();
    /* ★ **?region= 으로 들어오면 그 권역 + 자동 펼침** (지피티 결정)
         권역 쪽에서 「14일 물때표 보기」를 누른 분입니다. 무엇을
         보러 왔는지 분명하므로 **이 경우만** 저절로 폅니다.
         보통 핀 클릭은 선택만 바꿉니다 — 비교하는 분에게 매번
         펴지면 시끄럽습니다. */
    var 처음것 = 권역찾기(주소권역());
    고르기(처음것 || 권역들[0], true);
    상세세우기();        // ★ 지도가 떴을 때도 **같은 함수**가 세웁니다
  }

  function 주소권역() {
    try {
      var m = /[?&]region=([^&#]+)/.exec(window.location.search || '');
      return m ? decodeURIComponent(m[1]) : '';
    } catch (e) { return ''; }
  }

  function 보일것() {
    if (지금묶음 === '전국') { return 권역들; }
    return 권역들.filter(function (r) { return r.묶음이름 === 지금묶음; });
  }

  function 맞추기() {
    if (!지도) { return; }
    지도.맞추기(보일것().map(function (r) { return [r.위도, r.경도]; }));
  }

  // ── 배율에 따라 핀 꼴 바꾸기 (옛 것 그대로) ──────────────
  function 꼴고치기() {
    if (!지도 || !지도.날것) { return; }
    var 배 = 지도.날것.getLevel();
    var 모드 = 배 >= 13 ? 'dot' : (배 >= 12 ? 'name' : 'tide');
    if (모드 === 지금모드) { return; }
    지금모드 = 모드;
    권역들.forEach(function (r) {
      if (!r.단추) { return; }
      r.단추.className = 'tm-pin tm-pin--' + 모드
                         + (r === 고른것 ? ' on' : '');
      r.단추.textContent = '';
      if (모드 === 'dot') { return; }
      r.단추.appendChild(만들기('span', null, r.이름));
      if (모드 === 'tide' && r.간조) {
        r.단추.appendChild(만들기('small', null, '간조 ' + r.간조));
      }
    });
  }

  function 핀찍기() {
    권역들.forEach(function (r) {
      var b = 만들기('button', 'tm-pin tm-pin--dot');
      b.type = 'button';
      b.title = r.이름;
      b.setAttribute('aria-label', r.이름 + ' 물때 보기');
      b.addEventListener('click', function (e) {
        e.stopPropagation(); 고르기(r);
      });
      r.단추 = b;
      r.올린것 = 지도.핀(r.위도, r.경도, b, { 층: 2 });
    });
  }

  // ── 지도 위 조작 — 권역 지도와 **같은 자리** ───────────
  function 조작단추() {
    var 종류칸 = 만들기('div', 'tm-type');
    종류칸.setAttribute('role', 'group');
    종류칸.setAttribute('aria-label', '지도 종류');
    var 기억 = null;
    try { 기억 = localStorage.getItem('badagaja.map-type'); } catch (e) { /* 막히면 그만 */ }
    var 첫것 = (기억 === '위성') ? 1 : 0;
    var 들 = [];
    ['일반', '위성'].forEach(function (이름, i) {
      var b = 만들기('button', 'tm-type-b' + (i === 첫것 ? ' on' : ''), 이름);
      b.type = 'button';
      b.setAttribute('aria-pressed', i === 첫것 ? 'true' : 'false');
      b.addEventListener('click', function () {
        지도.종류(이름);
        try { localStorage.setItem('badagaja.map-type', 이름); } catch (e) { /* 그만 */ }
        들.forEach(function (x, j) {
          x.classList.toggle('on', j === i);
          x.setAttribute('aria-pressed', j === i ? 'true' : 'false');
        });
      });
      들.push(b); 종류칸.appendChild(b);
    });
    if (첫것 === 1) { 지도.종류('위성'); }
    칸.appendChild(종류칸);

    var 배율칸 = 만들기('div', 'tm-zoom');
    배율칸.setAttribute('aria-label', '지도 확대 축소');
    [['＋', 1, '확대'], ['－', -1, '축소']].forEach(function (x) {
      var b = 만들기('button', 'tm-zoom-b', x[0]);
      b.type = 'button';
      b.setAttribute('aria-label', x[2]);
      b.addEventListener('click', function () { 지도.확대(x[1]); 꼴고치기(); });
      배율칸.appendChild(b);
    });
    칸.appendChild(배율칸);

    // 범례는 **작게** — 이 지도는 낚시/해루질을 가르지 않습니다
    var 범 = 만들기('div', 'tm-legend');
    범.appendChild(만들기('span', null, '확대하면 오늘 간조 시각이 보입니다'));
    칸.appendChild(범);

    var 켬 = false;
    var 켜기 = 만들기('button', 'tm-lock', '지도 이동 켜기');
    켜기.type = 'button';
    켜기.setAttribute('aria-pressed', 'false');
    켜기.addEventListener('click', function () {
      켬 = !켬;
      지도.조작(켬);
      켜기.textContent = 켬 ? '지도 이동 끄기' : '지도 이동 켜기';
      켜기.setAttribute('aria-pressed', String(켬));
    });
    칸.appendChild(켜기);
    지도.누를때(function () {
      if (!켬 && window.innerWidth > 760) { 켬 = true; 지도.조작(true); }
    });

    // 광역 거르기 — 57개를 다 두지 않고 묶음으로 (지피티 지시)
    if (거르개) {
      [].forEach.call(거르개.querySelectorAll('button[data-group]'),
        function (b) {
          b.addEventListener('click', function () {
            지금묶음 = b.getAttribute('data-group');
            [].forEach.call(거르개.querySelectorAll('button[data-group]'),
              function (x) {
                var 켜 = x === b;
                x.classList.toggle('on', 켜);
                x.setAttribute('aria-pressed', String(켜));
              });
            권역들.forEach(function (r) {
              if (r.단추) {
                r.단추.hidden = !(지금묶음 === '전국'
                                  || r.묶음이름 === 지금묶음);
              }
            });
            맞추기();
          });
        });
    }
  }


  /* ── 2주 상세 — 전폭으로 지도 아래 (2026-10-02 지피티 시안 v1) ──
   *
   *   · 기본 **접힘**. 핀 클릭은 선택만 바꿉니다
   *   · 「2주 물때 보기」를 눌러야 펼칩니다
   *   · 펼친 채로 다른 핀을 고르면 **내용만** 갱신, 열린 상태 유지
   *   · /tide/?region=buan#tide-detail 로 들어오면 그 권역 + 자동 펼침
   *
   *   14일 달력·그래프·「언제 갈까」는 **tide.js 가 그립니다.**
   *   여기서는 자료를 넘겨 주기만 합니다 (계약-01 한 곳에서).
   */
  /* ★ **그 자리에서 찾습니다** (2026-10-02 브라우저에서 잡았습니다)
       전에는 여기서 `var 상세 = ...` 로 담아 두었습니다. 그런데
       지도가 못 뜨면 **이 줄보다 앞에서** `상세세우기()` 가 불립니다.
       `var` 는 이름만 끌어올려지고 **값은 그 자리에서** 들어가므로,
       그때 `상세` 는 `undefined` 였습니다. 그래서 2주 상세가
       조용히 안 세워졌습니다 — 오류도 안 났습니다. */
  function 상세칸() { return document.getElementById('tide-detail'); }
  function 상세이름칸() { return document.getElementById('tdName'); }

  function 상세갱신(r) {
    var 이름칸 = 상세이름칸();
    if (!이름칸 || !r) { return; }   // ★ 고른 것이 없으면 조용히 넘어갑니다
    이름칸.textContent = r.이름 + ' 2주 물때';
    /* ★ **관측소도 함께 바꿉니다** (2026-10-02 캡처에서 잡았습니다)
         쪽을 만들 때 첫 권역(강화)으로 찍혀 나갑니다. 이름만 바꾸고
         관측소를 안 바꾸면 「부안 2주 물때 … 강화대교 관측소 기준」
         처럼 **서로 다른 두 곳**이 한 칸에 적힙니다. */
    var 관칸 = document.getElementById('tdStation');
    if (관칸) {
      관칸.textContent = r.관측소 ? (r.관측소 + ' 관측소 기준') : '';
    }
    var 입구 = window.BADAGAJA_TIDE_NEW;
    if (입구 && 입구.갈아끼우기) {
      입구.갈아끼우기(r.id, r.관측소 || '', 받은것[r.id] || null);
      // ★ 자료가 **안 와도** 맞춥니다 (계약-23). 오면 한 번 더.
      자리맞추기();
    }
    그래프그리기(r);
  }

  function 상세펴기(r, 부드럽게) {
    var 상세 = 상세칸();
    if (!상세) { return; }
    상세.open = true;
    상세갱신(r || 고른것);
    try {
      상세.scrollIntoView({
        behavior: 부드럽게 === false ? 'auto' : 'smooth',
        block: 'start'
      });
    } catch (e) { /* 옛 브라우저 */ }
  }

  /* ★ **자료가 들어온 뒤 한 번만** 자리를 다시 맞춥니다 (바깥 검수)
       직접 진입(`#tide-detail`)에서 첫 화면이 통째로 비었습니다.
       자료가 오기 전에 스크롤해 두면, 14일 카드가 들어와 쪽이
       길어진 뒤 그 자리는 엉뚱한 곳이 됩니다. */
  var 자리맞춘횟수 = 0;

  /* ★ **자리를 직접 셈합니다** (2026-10-02 브라우저에서 재고 고침)
       `scrollIntoView` 는 **부르는 그 순간의 쪽 길이**로 셈합니다.
       이 쪽은 들어온 뒤에도 계속 길어집니다 — 지도를 못 받으면
       57권역 목록이 펼쳐지고, 14일 자료가 와서 카드가 채워지고,
       그래프가 그려집니다. 그 사이에 부르면 어긋납니다.

       실제로 상세는 문서 3,918px 자리인데 스크롤이 16,905px 에
       가 있었습니다. 첫 화면이 통째로 비었습니다. */
  function 자리맞추기() {
    /* ★ **두 번까지** 맞춥니다 (2026-10-02)
         ① 상세를 편 직후 — 자료가 안 와도 (계약-23)
         ② 자료가 들어와 쪽 길이가 정해진 뒤 — 이것이 최종
       전에는 자료가 온 뒤에만 한 번 불렀습니다. 로컬은 API 가
       404 라 자료가 영영 안 와서 **한 번도 안 불렸고**, 브라우저
       기본 해시 점프만 남아 9,245px 어긋났습니다. */
    /* ★ **쪽이 안정될 때까지 몇 번 맞춥니다** (2026-10-02)
         이 쪽은 들어온 뒤에도 계속 길이가 바뀝니다 — 카카오 지도가
         늦게 뜨거나 못 뜨고, 57권역 목록이 접혔다 펴지고, 14일
         자료가 옵니다. 한 번만 맞추면 그 뒤 바뀐 것에 어긋납니다.
         시간차를 두고 몇 번 맞춰 **마지막 것이 이기게** 합니다. */
    if (자리맞춘횟수 >= 2) { return; }
    if (String(window.location.hash || '') !== '#tide-detail') { return; }
    var 상세 = 상세칸();
    if (!상세) { return; }
    자리맞춘횟수 += 1;
    /* ★ **`requestAnimationFrame` 을 안 씁니다** (2026-10-02)
         rAF 는 **탭이 보이지 않으면 멈춥니다.** 뒤쪽 탭, 최소화한
         창, 헤드리스 캡처에서 그렇습니다. 진단을 심어 보니 이
         함수가 **한 번도 안 불렸습니다** — 콜백이 영영 안 왔던
         것입니다. 오류도 안 나서 더 안 보였습니다.
         `setTimeout` 은 숨은 탭에서도 (느려질 뿐) 돕니다. */
    var 두번 = function (일) {
      window.setTimeout(일, 0);
    };
    두번(function () {
      var 상세2 = 상세칸();
      if (!상세2) { return; }
      var 위 = 상세2.getBoundingClientRect().top
             + (window.pageYOffset || document.documentElement.scrollTop || 0);
      var 갈곳 = Math.max(0, Math.round(위 - 88));   // 머리띠 높이만큼 띄웁니다
      try {
        window.scrollTo({ top: 갈곳, behavior: 'auto' });
      } catch (e) {
        window.scrollTo(0, 갈곳);
      }
    });
  }

  /* 「2주 물때 보기」 — 넘어가지 않고 아래에서 폅니다.
     자바스크립트가 죽으면 href 가 그 권역 쪽으로 데려갑니다 (계약-23).

     ★ **지도와 떼어 놓습니다.** 지도가 못 떠도 이 단추와
       `?region=` 은 돌아야 합니다. */
  var 상세세웠나 = false;

  function 상세세우기() {
    if (상세세웠나 || !상세칸()) { return; }
    상세세웠나 = true;

    var 열기단추 = 카드 && 카드.querySelector('[data-open-tide]');
    if (열기단추) {
      열기단추.addEventListener('click', function (e) {
        e.preventDefault();
        상세펴기(고른것 || 권역찾기(주소권역()) || 권역들[0]);
      });
    }

    // ?region=buan#tide-detail 로 들어왔으면 그 권역으로 저절로 폅니다
    var 부른것 = 권역찾기(주소권역());
    if (부른것) {
      if (!고른것) { 고르기(부른것, true); }
      // ★ 여기서는 **스크롤하지 않습니다.** 쪽이 아직 길어지는
      //   중이라 어디로 가든 어긋납니다. 자료가 들어온 뒤
      //   `자리맞추기()` 가 한 번만 제대로 맞춥니다.
      상세칸().open = true;
      상세갱신(부른것);
      /* ★ **바인딩 직후 한 번만** 잡습니다 (바깥 검수 조건)
           「임의로 500ms, 1000ms 처럼 긴 시간을 기다리는 식이면
             안 되고, 실제 상세 DOM/데이터 바인딩 직후 짧게 한 번
             실행하는 구조를 유지하세요」
           여기가 ① 상세를 편 직후입니다. 14일 자료가 꽂히면
           `상세갱신` 이 ②로 한 번 더 부릅니다 — 그때가 쪽 길이가
           정해진 때라 그것이 최종입니다. 시간에 기대지 않고
           **일이 끝난 때**에 맞춥니다. */
      자리맞추기();
    }
  }

  function 권역찾기(아이디) {
    if (!아이디) { return null; }
    for (var i = 0; i < 권역들.length; i++) {
      if (권역들[i].id === 아이디) { return 권역들[i]; }
    }
    return null;
  }


  /* ── 오늘 시간별 물높이 그래프 ────────────────────────
   *
   *   ★ 2026-10-02 공개 서버 캡처에서 잡았습니다
   *     「오늘 시간별 물높이」 칸이 **비어 있었습니다.**
   *     `tide-graph.js` 는 **스스로 돌지 않습니다** —
   *     `BADAGAJA_TIDEGRAPH.mount()` 를 불러 줘야 합니다.
   *     권역 쪽에는 부르는 코드가 있는데 `/tide/` 에는 **칸만**
   *     있었습니다. 또 「문구만 있고 기능은 없는」 꼴이었습니다.
   *
   *   ★ `/tide/` 는 권역이 바뀌므로 **고를 때마다** 다시 그립니다.
   */
  var 그린권역 = null;

  function 그래프그리기(r) {
    if (!r || 그린권역 === r.id) { return; }
    var 칸 = document.getElementById('tideGraph');
    if (!칸 || !window.BADAGAJA_TIDEGRAPH) { return; }
    그린권역 = r.id;
    칸.textContent = '';
    칸.style.display = '';
    try {
      window.BADAGAJA_TIDEGRAPH.mount(칸, r.id, { api: 자료.api || '../api/' });
    } catch (e) { /* 못 그려도 14일 카드는 그대로 (계약-23) */ }
    // 자료가 안 오면 **빈 칸을 남기지 않습니다**
    window.setTimeout(function () {
      if (그린권역 === r.id && !칸.querySelector('.tg-plot')) {
        칸.style.display = 'none';
      }
    }, 8000);
  }

  // ── 고른 권역 카드 ────────────────────────────────────
  function 고르기(r, 처음) {
    고른것 = r;
    권역들.forEach(function (x) {
      if (x.단추) { x.단추.classList.toggle('on', x === r); }
    });
    if (!카드) { return; }

    var 그림 = 카드.querySelector('.tp-img');
    if (그림 && r.사진) {
      if (그림.getAttribute('src') !== r.사진) { 그림.setAttribute('src', r.사진); }
      그림.alt = r.이름 + ' 바다';
    }
    var 이 = 카드.querySelector('.tp-name'); if (이) { 이.textContent = r.이름; }
    var 한 = 카드.querySelector('.tp-sub'); if (한) { 한.textContent = r.한줄 || ''; }
    var 관 = 카드.querySelector('.tp-station');
    if (관) {
      관.textContent = r.관측소 ? (r.관측소 + ' 관측소 기준') : '';
    }
    ['tp-go', 'tp-guide'].forEach(function (c, i) {
      var a = 카드.querySelector('.' + c);
      if (a) { a.href = i === 0 ? (r.물때주소 || r.주소) : r.주소; }
    });
    물때채우기(r);

    /* ★ **아래 2주 물때도 함께 바꿉니다** (2026-10-06 주인 지시)
         주인 — 「권역 누르면 더보기 버튼이 아니라 처음부터
         물때관련 정보를 보여주면 좋겠어」

         상세는 이제 **처음부터 펼쳐져** 있습니다(`<details open>`).
         그런데 여기서 갱신하지 않으면 핀을 바꿔도 아래는 **첫
         권역 그대로**입니다 — 「고흥」을 눌렀는데 아래에 「강화
         2주 물때」가 남아 있는 꼴이 됩니다.

         스크롤은 하지 않습니다. 핀을 고르는 것은 **보는 자리를
         옮기는 일이 아니라 고르는 일**입니다. 손님이 지도를
         보고 있는데 화면이 저절로 내려가면 더 불편합니다. */
    if (상세칸()) { 상세갱신(r); }

    if (!처음 && window.innerWidth <= 760) {
      카드.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  // ── 고른 권역의 **오늘 간·만조**를 받아 카드에 채웁니다 ──
  //
  //   ★ **빈 흰 칸으로 두지 않습니다** (2026-10-02 지피티 보정)
  //     「물때가 없으면 빈 흰 공간 대신 작은 상태 영역을 표시.
  //       실제 서버 값이 들어오면 그 영역을 숨기고 간·만조 4개 표시」
  //
  //   ★ 못 받아도 쪽은 그대로 씁니다 (계약-23). 안내 글만 남습니다.
  // ★ **14일 응답을 통째로 기억합니다** (2026-10-02 지피티 원칙)
  //   전에는 `days[0].events` 만 떼어 두고 나머지 13일을 버렸습니다.
  //   2주 상세가 같은 자료를 쓰므로 **한 번만 받아 나눠 씁니다.**
  var 받은것 = {};        // 권역 → 14일 응답 통째
  function 물때채우기(r) {
    var 칸들 = 카드.querySelector('.tp-events');
    var 안내 = 카드.querySelector('.tp-empty');
    if (!칸들 || !안내) { return; }

    function 그리기(들) {
      if (!들 || !들.length) {
        /* ★ 정적 글은 「자동으로 불러옵니다」로 두고,
           정말 못 받았을 때만 여기서 바꿉니다.
           검색엔진은 정적 글만 읽으므로 실패문구가 색인되지
           않습니다 (2026-10-07 바깥 전수감사). */
        안내.textContent = '오늘 간조·만조 시각을 지금 불러오지 '
          + '못했습니다. 잠시 뒤에 다시 보세요.';
        칸들.hidden = true; 안내.hidden = false; return;
      }
      칸들.textContent = '';
      들.slice(0, 4).forEach(function (e) {
        var 간 = (e.type === '간조');
        var 한 = 만들기('div', 'tp-ev ' + (간 ? 'low' : 'high'),
                        (간 ? '간조 ' : '만조 ') + e.time);
        칸들.appendChild(한);
      });
      칸들.hidden = false; 안내.hidden = true;
    }

    if (받은것[r.id]) {
      그리기(((받은것[r.id].days || [])[0] || {}).events || []);
      상세갱신(r);
      return;
    }
    칸들.hidden = true; 안내.hidden = false;
    // 지도 쪽은 뿌리에서 한 칸 안이라 '../api/' 입니다
    var API = 자료.api || '../api/';
    fetch(API + 'tide-cache.php?region=' + encodeURIComponent(r.id))
      .then(function (x) { return x.ok ? x.json() : null; })
      .then(function (j) {
        if (!j || !j.days || !j.days.length) { return; }
        받은것[r.id] = j;              // ★ 통째로 둡니다
        if (고른것 !== r) { return; }
        그리기((j.days[0] || {}).events || []);
        상세갱신(r);
      })
      .catch(function () { /* 못 받으면 안내 글이 그대로 남습니다 */ });
  }
})();
