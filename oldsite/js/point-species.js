/* 포인트 상세 페이지 — "대상 / 예상 대상" 줄의 어종 이름을 잡는 법 안내 페이지로 연결
 * 자료: data/species-index.json (build-species-index.ps1 로 생성)
 * 이름이 목록에 없는 어종은 글자 그대로 둔다.
 */
(function () {
  var cs = document.currentScript, BASE = (cs && cs.getAttribute('src') || '').replace(/js\/point-species\.js.*$/, '') || '../';   // 이 스크립트를 부른 경로 기준(point/ 는 ../, point/chungnam/ 은 ../../)
  var cards = document.querySelectorAll('#points .card');
  if (!cards.length || !window.fetch) return;

  function norm(s) { return (s || '').replace(/\(.*?\)/g, '').replace(/[\s·]/g, ''); }

  fetch(BASE + 'data/species-index.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
    var by = {};
    (d.species || []).forEach(function (s) {
      by[norm(s.n)] = s;
      (s.alias || []).forEach(function (a) { if (a) by[norm(a)] = s; });
    });

    function find(name) {
      var key = norm(name);
      if (by[key]) return by[key];
      for (var k in by) { if (k.length >= 2 && (key.indexOf(k) === 0 || k.indexOf(key) === 0)) return by[k]; }
      return null;
    }

    var linked = 0;
    [].forEach.call(cards, function (card) {
      [].forEach.call(card.querySelectorAll('div > b'), function (b) {
        if (!/대상\s*:/.test(b.textContent)) return;
        var line = b.parentNode, txt = line.lastChild;            // <b>대상:</b> 뒤의 글자 부분
        if (!txt || txt.nodeType !== 3) return;
        var parts = txt.nodeValue.split(/,\s*/), frag = document.createDocumentFragment(), hit = false;
        frag.appendChild(document.createTextNode((txt.nodeValue.match(/^\s*/) || [''])[0]));   // "대상:" 뒤 한 칸 유지
        parts.forEach(function (raw, i) {
          if (i) frag.appendChild(document.createTextNode(', '));
          var name = raw.trim(), sp = name ? find(name) : null;
          if (!sp) { frag.appendChild(document.createTextNode(raw)); return; }
          hit = true; linked++;
          var a = document.createElement('a');
          a.href = BASE + sp.sec + '/' + sp.slug + '.html';
          a.className = 'sp-link';
          a.title = sp.n + (sp.sec === 'catch' ? ' 잡는 법 보기' : ' 낚는 법 보기');
          a.textContent = name;
          frag.appendChild(a);
        });
        if (hit) line.replaceChild(frag, txt);
      });
    });

    if (!linked) return;
    var note = document.createElement('p');
    note.className = 'sp-link-note';
    note.textContent = '어종 이름을 누르면 잡는 법·채비·시기 안내로 이동합니다.';
    var head = document.querySelector('#points .wrap');
    if (head) head.insertBefore(note, head.children[1] || null);
  }).catch(function () { });
})();
