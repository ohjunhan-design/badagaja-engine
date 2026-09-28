/* 축제 달력 — 묶음·달로 걸러 보기
 *
 * 자바스크립트가 없어도 축제 197개가 달마다 다 보입니다.
 * 이 파일이 하는 일은 「골라 보기」뿐입니다.
 *
 * ★ 화면에서 자료를 긁지 않습니다.
 *   카드에 data-group·data-month 를 **쪽을 만들 때 넣어** 두었습니다.
 *   글자 모양을 아무리 바꿔도 이 파일은 안 깨집니다.
 */
(function () {
  'use strict';

  var 묶음칸 = document.getElementById('groupFilter');
  var 달칸 = document.getElementById('monthFilter');
  var 목록 = document.getElementById('festList');
  if (!목록) return;

  var 카드들 = [].slice.call(목록.querySelectorAll('.fest-item'));
  var 덩이들 = [].slice.call(목록.querySelectorAll('.month-block'));
  var 빈칸 = document.getElementById('festEmpty');
  var 셈칸 = document.getElementById('festCount');

  var 지금묶음 = '전체';
  var 지금달 = '전체';

  function 다시그리기() {
    var 보인수 = 0;
    카드들.forEach(function (c) {
      var 맞나 = (지금묶음 === '전체'
                  || c.getAttribute('data-group') === 지금묶음)
              && (지금달 === '전체'
                  || c.getAttribute('data-month') === 지금달);
      c.hidden = !맞나;
      if (맞나) 보인수++;
    });
    // 남은 축제가 없는 달은 통째로 감춥니다
    덩이들.forEach(function (b) {
      var 남음 = [].slice.call(b.querySelectorAll('.fest-item'))
                   .some(function (c) { return !c.hidden; });
      b.hidden = !남음;
    });
    if (빈칸) 빈칸.hidden = 보인수 > 0;
    if (셈칸) 셈칸.textContent = '축제 ' + 보인수 + '개를 보이고 있습니다.';
  }

  function 단추달기(칸, 이름, 고르기) {
    if (!칸) return;
    칸.addEventListener('click', function (e) {
      var b = e.target.closest('button[' + 이름 + ']');
      if (!b || b.disabled) return;
      고르기(b.getAttribute(이름));
      [].forEach.call(칸.querySelectorAll('button'), function (x) {
        x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
      });
      다시그리기();
    });
  }

  단추달기(묶음칸, 'data-group', function (v) { 지금묶음 = v; });
  단추달기(달칸, 'data-month', function (v) { 지금달 = v; });

  // 이번 달을 먼저 보여 줍니다 — 가장 자주 찾는 것이라
  var 이번달 = String(new Date().getMonth() + 1);
  var 이번달단추 = 달칸 && 달칸.querySelector(
    'button[data-month="' + 이번달 + '"]:not([disabled])');
  if (이번달단추) {
    지금달 = 이번달;
    [].forEach.call(달칸.querySelectorAll('button'), function (x) {
      x.setAttribute('aria-pressed', x === 이번달단추 ? 'true' : 'false');
    });
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
