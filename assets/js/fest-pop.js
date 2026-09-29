/* 축제 설명 팝업 (2026-09-29 주인 지적)
 *
 * ★ 「달마다 다른 얼굴의 행사에 전에 있던 팝업 설명창이 사라졌어」
 *
 *   옛 쪽에는 `.ip-overlay` 팝업이 있었습니다. 새 쪽은 설명을 카드에
 *   그대로 펼쳐 놓아 칸이 길어지고, **일정·가는 길처럼 더 적을 것**을
 *   넣을 자리가 없었습니다.
 *
 * ★ 자바스크립트가 안 돌아도 **아무것도 잃지 않습니다** (계약-23).
 *   카드에 이름과 설명이 이미 적혀 있습니다. 팝업은 거기에
 *   「언제·어디서·누구와·자세히 보기」를 **더해 주는 것**입니다.
 *
 * ★ 열면 되돌아갈 수 있어야 합니다 — Esc, 바깥 누르기, 닫기 단추.
 *   열 때 초점을 팝업으로 옮기고, 닫으면 누른 자리로 돌려놓습니다.
 */
(function () {
  'use strict';

  var 자료 = window.BADAGAJA_FEST;
  if (!자료 || !자료.length) { return; }

  var 겉 = null, 속 = null, 누른것 = null;

  function 만들기(태그, 반, 글) {
    var e = document.createElement(태그);
    if (반) { e.className = 반; }
    if (글 != null) { e.textContent = 글; }
    return e;
  }

  function 틀만들기() {
    겉 = 만들기('div', 'fp-overlay');
    겉.hidden = true;
    겉.addEventListener('click', function (e) {
      if (e.target === 겉) { 닫기(); }
    });

    속 = 만들기('div', 'fp-box');
    속.setAttribute('role', 'dialog');
    속.setAttribute('aria-modal', 'true');
    속.setAttribute('tabindex', '-1');

    var 닫 = 만들기('button', 'fp-close', '×');
    닫.type = 'button';
    닫.setAttribute('aria-label', '닫기');
    닫.addEventListener('click', 닫기);

    속.appendChild(닫);
    겉.appendChild(속);
    document.body.appendChild(겉);

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !겉.hidden) { 닫기(); }
    });
  }

  function 열기(하나, 부른것) {
    if (!겉) { 틀만들기(); }
    누른것 = 부른것 || null;

    // 닫기 단추만 남기고 비웁니다
    while (속.children.length > 1) { 속.removeChild(속.lastChild); }

    var 몸 = 만들기('div', 'fp-body');
    if (하나.때) { 몸.appendChild(만들기('p', 'fp-kicker', 하나.때)); }

    var 제목 = 만들기('h3', 'fp-title', 하나.이름);
    제목.id = 'fpTitle';
    몸.appendChild(제목);
    속.setAttribute('aria-labelledby', 'fpTitle');

    var 줄 = [];
    if (하나.곳) { 줄.push(하나.곳); }
    if (하나.누구와) { 줄.push(하나.누구와); }
    if (줄.length) { 몸.appendChild(만들기('p', 'fp-line', 줄.join(' · '))); }

    if (하나.설명) { 몸.appendChild(만들기('p', 'fp-desc', 하나.설명)); }

    var 단추줄 = 만들기('div', 'fp-actions');
    if (하나.주소) {
      var a = 만들기('a', 'fp-btn main', '자세히 보기 →');
      a.href = 하나.주소;
      단추줄.appendChild(a);
    }
    몸.appendChild(단추줄);

    // ★ 일정은 해마다 달라집니다 — 그대로 밝힙니다
    몸.appendChild(만들기('p', 'fp-note',
      '일정은 해마다 달라집니다. 가시기 전에 현지 공지를 확인해 주세요.'));

    속.appendChild(몸);

    겉.hidden = false;
    document.body.classList.add('fp-open');
    속.focus();
  }

  function 닫기() {
    if (!겉 || 겉.hidden) { return; }
    겉.hidden = true;
    document.body.classList.remove('fp-open');
    if (누른것 && 누른것.focus) { 누른것.focus(); }
    누른것 = null;
  }

  document.addEventListener('click', function (e) {
    var 단추 = e.target.closest ? e.target.closest('.month-item') : null;
    if (!단추) { return; }
    var i = parseInt(단추.getAttribute('data-fest'), 10);
    if (isNaN(i) || !자료[i]) { return; }
    e.preventDefault();
    열기(자료[i], 단추);
  });
})();
