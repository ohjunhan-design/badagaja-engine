/* 방문 기록 보내기 — 쿠키를 쓰지 않고, 어느 쪽을 봤는지와 들어온 곳만 서버에 알립니다.
   같은 탭에서 처음 열었을 때만 n=1(첫 방문)을 함께 보냅니다. */
(function () {
  try {
    if (location.protocol === 'file:' || /^(localhost|127\.)/.test(location.hostname)) return;
    var isNew = '0';
    try {
      if (!sessionStorage.getItem('bgHit')) { sessionStorage.setItem('bgHit', '1'); isNew = '1'; }
    } catch (e) { /* 저장이 막힌 브라우저에서는 첫 방문을 세지 않습니다 */ }
    var path = location.pathname || '/';
    var base = document.currentScript && document.currentScript.src ? document.currentScript.src.replace(/js\/hit\.js.*$/, '') : '';
    var url = base + 'api/hit.php?p=' + encodeURIComponent(path) + '&n=' + isNew +
              '&r=' + encodeURIComponent(document.referrer || '') + '&_=' + Date.now();
    if (navigator.sendBeacon) { navigator.sendBeacon(url); }
    else { var i = new Image(); i.src = url; }
  } catch (e) { /* 기록 실패가 화면에 영향을 주지 않게 합니다 */ }
})();
