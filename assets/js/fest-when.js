/* 축제가 지금 어느 때인가 — **보는 그날** 기준으로 (2026-10-01)
 *
 * ★ 왜 자바스크립트로 하나
 *   쪽을 만들 때 「이번 달」을 박으면, 10월에 지어 올린 쪽이
 *   11월에도 「이번 달」이라고 말합니다. 쪽은 그대로 있고 날은 갑니다.
 *   그래서 쪽에는 변하지 않는 「보통 4월」만 두고, 이번 달·다음 달은
 *   여기서 더합니다. 자바스크립트가 꺼져 있어도 「보통 4월」은
 *   그대로 읽힙니다.
 *
 * ★ 없는 것을 만들지 않습니다
 *   자료에 달만 있고 날짜·연도가 없습니다. 그러니 「10월 3일 개막」
 *   같은 말은 **적을 수 없습니다.** 할 수 있는 말만 합니다 —
 *   이번 달 · 다음 달 · 지난달에 지났음.
 */
(function () {
  var 몸 = document.body;
  var 달글 = 몸 && 몸.getAttribute('data-fest-month');
  if (!달글) { return; }
  var 달 = parseInt(달글, 10);
  if (!(달 >= 1 && 달 <= 12)) { return; }

  var 이달 = new Date().getMonth() + 1;
  var 남 = (달 - 이달 + 12) % 12;
  var 글 = '', 색 = '';
  if (남 === 0) { 글 = '이번 달입니다'; 색 = 'badge--green'; }
  else if (남 === 1) { 글 = '다음 달입니다'; 색 = 'badge--green'; }
  else if (남 <= 3) { 글 = 남 + '달 뒤'; }
  else if (남 >= 10) { 글 = '올해 것은 지났습니다'; }
  if (!글) { return; }

  // ① 머리 이름표에 한 칸 더합니다
  var 이름표칸 = document.querySelector('.header-tags');
  if (이름표칸) {
    var 새 = document.createElement('span');
    새.className = 'badge' + (색 ? ' ' + 색 : '');
    새.textContent = 글;
    이름표칸.appendChild(새);
  }

  // ② 핵심정보의 「언제」 칸에도 덧붙입니다 — 거기서 찾는 사람이 많습니다
  var 칸들 = document.querySelectorAll('.fest-facts .fact');
  for (var i = 0; i < 칸들.length; i++) {
    var 열쇠 = 칸들[i].querySelector('.f-k');
    var 값 = 칸들[i].querySelector('.f-v');
    if (열쇠 && 값 && 열쇠.textContent.trim() === '언제') {
      값.textContent = 값.textContent.trim() + ' — ' + 글;
      break;
    }
  }
})();
