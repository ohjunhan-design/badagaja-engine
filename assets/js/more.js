/* 긴 목록을 「더 보기」로 접습니다 (2026-09-30 주인 지시)
 *
 * 주인 말씀 — 「하루코스 너무많아 더보기버튼으로 축소해」
 *   전남 묶음 쪽은 코스가 **45개**였습니다. 끝까지 내리는 데만
 *   한참 걸리고, 아래에 있는 축제·먹거리 칸은 아예 못 봅니다.
 *
 * ★ **자바스크립트가 접고 자바스크립트가 폅니다.**
 *   CSS 로 감추면 자바스크립트가 안 도는 분께는 **영영 안 보입니다.**
 *   여기서 접으므로, 스크립트가 없으면 처음부터 다 보입니다
 *   (계약-23 — 바깥 것이 죽어도 쪽은 삽니다).
 *
 * 쓰는 법 — 목록 칸에 data-more="6" 을 답니다. 6개만 보이고
 *   나머지는 「더 보기」를 누를 때 펴집니다.
 */
(function () {
  'use strict';

  function 접기(칸) {
    var 몇 = parseInt(칸.getAttribute('data-more'), 10);
    if (!몇 || 몇 < 1) return;
    var 것들 = [];
    for (var i = 0; i < 칸.children.length; i++) {
      것들.push(칸.children[i]);
    }
    if (것들.length <= 몇) return;        // 접을 만큼 많지 않습니다

    var 숨긴것 = 것들.slice(몇);
    숨긴것.forEach(function (e) { e.style.display = 'none'; });

    var 줄 = document.createElement('div');
    줄.className = 'more-row';
    var 단추 = document.createElement('button');
    단추.type = 'button';
    단추.className = 'more-btn';
    단추.setAttribute('aria-expanded', 'false');
    단추.textContent = '더 보기 (' + 숨긴것.length + '개) ▾';
    줄.appendChild(단추);
    칸.parentNode.insertBefore(줄, 칸.nextSibling);

    var 폈나 = false;
    단추.addEventListener('click', function () {
      폈나 = !폈나;
      숨긴것.forEach(function (e) { e.style.display = 폈나 ? '' : 'none'; });
      단추.setAttribute('aria-expanded', 폈나 ? 'true' : 'false');
      단추.textContent = 폈나
        ? '접기 ▴'
        : '더 보기 (' + 숨긴것.length + '개) ▾';
      if (!폈나) {
        // 접을 때는 목록 맨 위로 돌려 놓습니다 —
        // 안 그러면 화면이 저 아래에 덩그러니 남습니다
        var 위 = 칸.getBoundingClientRect().top + window.pageYOffset - 80;
        window.scrollTo({ top: 위, behavior: 'smooth' });
      }
    });
  }

  function 시작() {
    var 칸들 = document.querySelectorAll('[data-more]');
    [].forEach.call(칸들, 접기);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', 시작);
  } else {
    시작();
  }
})();
