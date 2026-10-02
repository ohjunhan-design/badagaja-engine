/* 축제 달력 — 달·지역으로 골라 보기
 *
 * ★ 자바스크립트가 없어도 축제 197개가 달마다 **다 보입니다.**
 *   달 묶음(<details>)을 **펼친 채로** 만들어 두고, 이 파일이
 *   이번 달만 남기고 접습니다. 거꾸로 하면 이 파일이 죽을 때
 *   축제가 한 줄도 안 보입니다 (계약-23).
 *
 * ★ 화면에서 자료를 긁지 않습니다.
 *   카드에 data-group·data-month 를 **쪽을 만들 때 넣어** 두었습니다.
 *   글자 모양을 아무리 바꿔도 이 파일은 안 깨집니다.
 *
 * ★ **보는 날**로 이번 달을 다시 맞춥니다 (2026-10-02)
 *   쪽은 만든 날의 달로 찍혀 나갑니다. 달이 바뀐 뒤에도 캐시된
 *   쪽이 남을 수 있어, 여기서 오늘 달로 고쳐 줍니다.
 */
(function () {
  'use strict';

  var 묶음칸 = document.getElementById('groupFilter');
  var 달칸 = document.getElementById('monthFilter');
  var 목록 = document.getElementById('festList');
  if (!목록) return;

  var 카드들 = [].slice.call(목록.querySelectorAll('.fest-item'));
  var 덩이들 = [].slice.call(목록.querySelectorAll('.month-group'));
  var 사진카드들 = [].slice.call(
    document.querySelectorAll('#festFeature .fest-pick'));
  var 빈칸 = document.getElementById('festEmpty');
  var 셈칸 = document.getElementById('festCount');
  var 제목칸 = document.getElementById('festHeadTitle');
  var 칩 = document.getElementById('festNowChip');

  var 달이름 = ['1월', '2월', '3월', '4월', '5월', '6월',
                '7월', '8월', '9월', '10월', '11월', '12월'];

  var 지금묶음 = '전체';
  var 지금달 = '전체';

  /* ★ **달 고르기는 감추지 않습니다** (2026-10-02 눈으로 보고 고침)
       지피티 지시는 「이번 달만 기본 펼침, **나머지는 접힘**」입니다.
       처음에는 다른 달을 통째로 감춰, 11월부터 9월까지가 쪽에서
       사라졌습니다. 축제 197개를 다 두라는 지시를 어긴 셈입니다.

         달  → **접기·펼치기**만
         지역 → 거르기 (그 지역 축제가 없는 달만 감춥니다) */
  function 지역맞나(c) {
    return 지금묶음 === '전체'
        || c.getAttribute('data-group') === 지금묶음;
  }
  function 맞나(c) {
    return 지역맞나(c)
        && (지금달 === '전체'
            || c.getAttribute('data-month') === 지금달);
  }

  function 다시그리기() {
    카드들.forEach(function (c) { c.hidden = !지역맞나(c); });

    var 보인수 = 0;
    덩이들.forEach(function (b) {
      var 안것 = [].slice.call(b.querySelectorAll('.fest-item'));
      var 남은수 = countShown(안것);
      b.hidden = !남은수;
      if (!남은수) return;
      var 달 = b.getAttribute('data-month');
      var 고른달인가 = (지금달 === '전체') || (달 === 지금달);
      b.open = 고른달인가;
      b.classList.toggle('month-group--now', 달 === 지금달);
      if (고른달인가) 보인수 += 남은수;
      var 셈 = b.querySelector('.month-title span');
      if (셈) 셈.textContent = '축제 ' + 남은수 + '개';
    });

    // 사진 카드 — 고른 달·지역에 맞는 것만
    var 보인사진 = 0;
    사진카드들.forEach(function (c) {
      var 켬 = 맞나(c) && 보인사진 < 3;
      c.hidden = !켬;
      if (켬) 보인사진++;
    });

    if (빈칸) 빈칸.hidden = 보인수 > 0;
    if (제목칸) {
      제목칸.textContent =
        (지금달 === '전체' ? '한 해 모든 달' : 달이름[+지금달 - 1])
        + ' 축제 ' + 보인수 + '개';
    }
    if (셈칸) {
      셈칸.textContent = 보인사진
        ? '사진이 있는 축제를 먼저 보여 주고, 아래에서 모두 볼 수 있습니다.'
        : '아래 목록에서 모두 볼 수 있습니다.';
    }
  }

  function countShown(것들) {
    var n = 0;
    것들.forEach(function (c) { if (!c.hidden) n++; });
    return n;
  }

  function 단추달기(칸, 이름, 고르기) {
    if (!칸) return;
    칸.addEventListener('click', function (e) {
      var b = e.target.closest('button[' + 이름 + ']');
      if (!b || b.disabled) return;
      고르기(b.getAttribute(이름));
      [].forEach.call(칸.querySelectorAll('button'), function (x) {
        x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
        x.classList.toggle('month-btn--now',
                           x === b && x.classList.contains('month-btn'));
      });
      다시그리기();
    });
  }

  단추달기(묶음칸, 'data-group', function (v) { 지금묶음 = v; });
  단추달기(달칸, 'data-month', function (v) { 지금달 = v; });

  /* ── 이번 달을 먼저 보여 줍니다 — 가장 자주 찾는 것이라
       ★ **쪽에는 달이 안 적혀 있습니다** (2026-10-02)
         달이 바뀌면 캐시에 남은 쪽이 틀리고, 검색엔진이 읽는
         HTML 도 틀립니다. 그래서 이달을 고르는 일은 **오로지
         여기서** 합니다. 이 파일이 죽으면 한 해 전체가 보입니다 —
         틀린 달이 보이는 것보다 낫습니다. */
  var 이번달 = String(new Date().getMonth() + 1);
  var 이번달단추 = 달칸 && 달칸.querySelector(
    'button[data-month="' + 이번달 + '"]:not([disabled])');
  if (!이번달단추 && 달칸) {
    // 그 달에 축제가 하나도 없으면 가장 가까운 달을 고릅니다
    var 있는것 = [].slice.call(
      달칸.querySelectorAll('button[data-month]:not([disabled])'));
    있는것.sort(function (a, b) {
      return 거리(a) - 거리(b);
    });
    이번달단추 = 있는것[0];
    이번달 = 이번달단추 && 이번달단추.getAttribute('data-month');
  }
  function 거리(b) {
    var d = Math.abs(+b.getAttribute('data-month') - +이번달);
    return Math.min(d, 12 - d);
  }
  if (이번달단추) {
    지금달 = 이번달;
    [].forEach.call(달칸.querySelectorAll('button'), function (x) {
      var 켬 = x === 이번달단추;
      x.setAttribute('aria-pressed', 켬 ? 'true' : 'false');
      x.classList.toggle('month-btn--now', 켬);
    });
    /* ★ **고른 달이 보이게 밀어 줍니다** (2026-10-02 눈으로 보고)
         휴대폰에서 달 단추는 가로로 밀립니다. 10월은 오른쪽
         끝이라 쪽을 열었을 때 **화면 밖**에 있었습니다.
         손님은 이번 달이 골라져 있는 줄 모릅니다.
         `scrollIntoView` 는 쪽 **전체를 세로로도** 움직입니다.
         가로만 손댑니다. */
    if (달칸.scrollWidth > 달칸.clientWidth) {
      달칸.scrollLeft = Math.max(0, 이번달단추.offsetLeft
        - (달칸.clientWidth - 이번달단추.offsetWidth) / 2);
    }
    // 머리 칩도 오늘 달로 맞춥니다
    if (칩) {
      var 셈 = 이번달단추.querySelector('span');
      칩.textContent = 달이름[+이번달 - 1] + ' · '
                     + ((셈 && 셈.textContent) || '');
    }
  }

  var 위로 = document.getElementById('toTop');
  if (위로) {
    위로.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    window.addEventListener('scroll', function () {
      위로.classList.toggle('show', window.scrollY > 600);
    }, { passive: true });
  }

  다시그리기();
})();
