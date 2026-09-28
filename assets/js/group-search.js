/* 묶음 쪽 검색 — 이 묶음 안의 것을 찾습니다 (2026-09-28)
 *
 * ★ 왜 만들었나
 *   옛 묶음 쪽에는 「충남 권역·포인트·제철 해산물·축제·명소 검색」
 *   칸이 있었습니다. 새 쪽에서 빠져 engine/check_design.py 가
 *   「입력칸 1 → 0」으로 잡았습니다.
 *
 * ★ 옛 것과 무엇이 다른가
 *   옛 검색은 자료를 여러 개 나눠 받고, 「9월 해루질」처럼 말로 쓴
 *   검색까지 알아들었습니다. 그만큼 깨질 곳도 많았습니다.
 *   여기서는 **이 묶음 안의 것을 이름으로 찾는 것**만 합니다.
 *   자료는 쪽에 미리 심어 두어 바깥에 물어보지 않습니다 —
 *   인터넷이 느려도 검색은 바로 됩니다.
 *
 * ★ 자료는 쪽이 심어 줍니다 (window.BADAGAJA_GROUP_SEARCH)
 *   engine/build.py 가 넣습니다. 여기서 목록을 만들지 않습니다.
 */
(function () {
  'use strict';

  var 칸 = document.getElementById('groupSearch');
  if (!칸) return;
  var 결과칸 = document.getElementById('groupSearchOut');
  var 자료 = window.BADAGAJA_GROUP_SEARCH || [];
  if (!자료.length) return;

  /* 찾기 쉽게 다듬습니다 — 사이 띄움과 가운뎃점을 지웁니다 */
  function 다듬기(글) {
    return String(글 || '').toLowerCase().replace(/[\s·・\-_()]/g, '');
  }

  /* 미리 다듬어 둡니다 — 칠 때마다 다시 하지 않게 */
  var 찾을것 = 자료.map(function (x) {
    return { 것: x, 키: 다듬기(x.n) + ' ' + 다듬기(x.k || '') };
  });

  var 갈래이름 = {
    region: '권역', point: '포인트', catch: '제철',
    fest: '축제', spot: '명소', course: '코스'
  };

  function 그리기(찾은것, 물음) {
    if (!결과칸) return;
    if (!물음) { 결과칸.hidden = true; 결과칸.innerHTML = ''; return; }
    if (!찾은것.length) {
      결과칸.hidden = false;
      결과칸.innerHTML = '<p class="gs-none">「' + 새기기(물음)
        + '」 로는 찾지 못했습니다. 권역 이름이나 어종 이름으로 찾아보세요.</p>';
      return;
    }
    var 줄 = 찾은것.slice(0, 12).map(function (x) {
      return '<a class="gs-row" href="' + 새기기(x.것.u) + '">'
        + '<span class="gs-kind">' + (갈래이름[x.것.t] || '') + '</span>'
        + '<b>' + 새기기(x.것.n) + '</b>'
        + (x.것.k ? '<small>' + 새기기(x.것.k) + '</small>' : '')
        + '</a>';
    }).join('');
    var 더 = 찾은것.length > 12
      ? '<p class="gs-more">그 밖 ' + (찾은것.length - 12) + '가지</p>' : '';
    결과칸.hidden = false;
    결과칸.innerHTML = 줄 + 더;
  }

  function 새기기(글) {
    return String(글 == null ? '' : 글)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function 찾기() {
    var 물음 = 다듬기(칸.value);
    if (!물음) { 그리기([], ''); return; }
    var 앞선것 = [], 뒤선것 = [];
    for (var i = 0; i < 찾을것.length; i++) {
      var 자리 = 찾을것[i].키.indexOf(물음);
      if (자리 === 0) 앞선것.push(찾을것[i]);
      else if (자리 > 0) 뒤선것.push(찾을것[i]);
    }
    그리기(앞선것.concat(뒤선것), 칸.value.trim());
  }

  var 기다림 = null;
  칸.addEventListener('input', function () {
    clearTimeout(기다림);
    기다림 = setTimeout(찾기, 90);
  });

  /* 많이 찾는 말 — 누르면 그대로 넣습니다 */
  var 빠른칸 = document.getElementById('groupQuick');
  if (빠른칸) {
    빠른칸.addEventListener('click', function (e) {
      var b = e.target.closest('[data-q]');
      if (!b) return;
      칸.value = b.getAttribute('data-q');
      칸.focus();
      찾기();
    });
  }

  /* 빠져나가기 — 첫 화면으로 돌아옵니다 */
  칸.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { 칸.value = ''; 그리기([], ''); }
  });
})();
