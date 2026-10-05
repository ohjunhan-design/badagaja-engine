/* 방문 기록 — **쿠키를 쓰지 않습니다** (2026-10-06 주인 지시)
 *
 * ★ 왜 다시 넣나
 *   옛 사이트에는 쪽마다 이 줄이 있었는데 새 사이트를 지으며
 *   빠졌습니다. 그래서 **448쪽이 방문을 하나도 안 세고** 있었습니다.
 *   10월 한 달 기록이 넷뿐이었는데, 그 넷마저 서버에 남아 있던
 *   옛 쪽에서 우연히 잡힌 것이었습니다.
 *
 * ★ 무엇을 보내나 — 세 가지뿐입니다
 *     p  어느 쪽을 봤나 (주소만)
 *     r  어디서 들어왔나 (앞 쪽 주소)
 *     n  이 탭에서 처음인가
 *   누구인지는 보내지 않습니다. 쿠키도 안 씁니다.
 *
 * ★ 안 세는 자리
 *   내 컴퓨터(file:·localhost)에서는 안 셉니다. 만들며 여는 것까지
 *   세면 숫자가 거짓이 됩니다.
 *
 * ★ 기록이 안 되어도 **화면은 멀쩡해야 합니다**
 *   서버가 죽어도 손님은 모르게 합니다 (계약-23 — 바깥이 죽어도
 *   사이트는 삽니다).
 */
(function () {
  try {
    if (location.protocol === 'file:'
        || /^(localhost|127\.|0\.0\.0\.0$)/.test(location.hostname)) { return; }

    var 처음 = '0';
    try {
      if (!sessionStorage.getItem('bgHit')) {
        sessionStorage.setItem('bgHit', '1');
        처음 = '1';
      }
    } catch (e) { /* 저장이 막힌 브라우저에서는 첫 방문을 안 셉니다 */ }

    // ★ **api/ 는 언제나 뿌리에 있습니다** (2026-10-06)
    //   옛 코드는 스크립트 주소에서 `js/hit.js` 를 잘라 뿌리를
    //   찾았습니다. 새 틀은 쪽마다 깊이가 달라(`rig/float.html`,
    //   `point/jeju/aewol_fishing.html`) 그 길이 흔들립니다.
    //   서버에서 api/ 는 늘 뿌리에 있으므로 `/api/` 로 못 박습니다.
    var 주소 = '/api/hit.php'
             + '?p=' + encodeURIComponent(location.pathname || '/')
             + '&n=' + 처음
             + '&r=' + encodeURIComponent(document.referrer || '')
             + '&_=' + Date.now();

    if (navigator.sendBeacon) { navigator.sendBeacon(주소); }
    else { var 그림 = new Image(); 그림.src = 주소; }
  } catch (e) { /* 기록이 실패해도 화면에 영향을 주지 않습니다 */ }
})();
