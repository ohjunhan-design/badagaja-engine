# -*- coding: utf-8 -*-
"""쪽의 **칸마다 세로 몇 px 에 있는지** 잽니다 (2026-10-02).

★ 왜 만들었나

  주인이 지피티에 「공간 활용성 — **스크롤이 길어질수록 사람은
  흥미를 잃는다**」를 물으셨습니다. 그 자리에서 제가 할 일은
  취향을 보태는 것이 아니라 **잰 값을 내놓는 것**입니다
  (주인 규칙 6-2 — 기계가 잰 것과 사람 눈으로 본 것을 가릅니다).

  마침 같은 날 겪은 일이 있습니다. 휴대폰 폭으로 찍으려고
  3200px 짜리 그림을 만들었는데 **물때 그래프가 안 찍혔습니다.**
  그림 밖에 있었기 때문입니다 — 390px 화면에서 그래프는
  **3,100px 넘게 내려가야** 나옵니다. 휴대폰 한 화면이 약 700px
  이니 **네 화면 반**을 넘겨야 보이는 자리입니다.

★ 이 도구가 내는 것
  칸 이름 · 꼭대기 y · 높이 · 몇 번째 화면인지
  그리고 **「첫 화면에 무엇이 보이는가」**

쓰는 법
  python engine/measure_scroll.py site/jejusi.html 390
"""
import json
import os
import subprocess
import sys
import tempfile
import urllib.parse

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import machine                 # noqa: E402
from engine import shot_tide               # noqa: E402
from engine import io as _io               # noqa: E402

# 한 화면 — 휴대폰은 대략 이만큼 보입니다 (주소줄·아래띠 뺀 값)
한화면 = {360: 640, 390: 684, 412: 732, 1440: 820}

# ★ **쪽이 스스로 재어 부모에게 보냅니다** (postMessage)
#   file:// 끼리는 같은 출처가 아니라 부모가 iframe 속을 못 읽습니다.
#   안쪽에서 재어 내보내면 출처가 달라도 건너갑니다.
재는글 = r'''<script>
window.addEventListener('load', function () {
  setTimeout(function () {
    var 것들 = [];
    // ★ 쪽마다 짜임이 달라 **한 갈래만 보면 셋밖에 안 잡힙니다.**
    //   큰 칸을 두루 봅니다 — 겹치는 것은 아래에서 거릅니다.
    var 봄 = document.querySelectorAll(
      'header, section, main > article, main > div, ' +
      '.tide-strip, .tide-graph, footer');
    var 쓴것 = {};
    for (var i = 0; i < 봄.length; i++) {
      var e = 봄[i];
      var r = e.getBoundingClientRect();
      if (r.height < 60) { continue; }
      // 같은 자리에서 시작하는 것은 **가장 바깥 하나만** 셉니다
      var 키 = Math.round(r.top + window.scrollY / 1) + '';
      if (쓴것[키]) { continue; }
      쓴것[키] = 1;
      var 제목 = e.querySelector('h1,h2,h3');
      것들.push({
        이름: String(e.id || e.className || e.tagName).slice(0, 44),
        제목: 제목 ? 제목.textContent.trim().slice(0, 30) : '',
        y: Math.round(r.top + window.scrollY),
        h: Math.round(r.height)
      });
    }
    try {
      parent.postMessage('MEAS' + JSON.stringify({
        전체높이: document.body.scrollHeight, 칸: 것들 }), '*');
    } catch (e) {}
  }, 2500);
});
</script>'''


def 재기(쪽길, 폭):
    집 = tempfile.mkdtemp(prefix='bada-meas-')
    # 가짜 물때를 심은 복사본 + 재는 스크립트를 함께 넣습니다
    임시 = shot_tide.심은쪽(쪽길)
    글 = _io.read(임시)
    글 = (글.replace('</body>', 재는글 + '</body>', 1)
          if '</body>' in 글 else 글 + 재는글)
    _io.write(임시, 글)
    주소 = 'file:///' + urllib.parse.quote(
        os.path.abspath(임시).replace('\\', '/'), safe='/:')
    # iframe 틀 안에서 재야 **진짜 폭**입니다 (윈도 크롬 500px 하한)
    래퍼 = os.path.join(집, 'wrap.html')
    _io.write(래퍼, '''<!DOCTYPE html><html><head><meta charset="utf-8">
<style>html,body{margin:0}iframe{display:block;width:%dpx;height:900px;
border:0}</style></head><body><iframe id="f" src="%s"></iframe>
<script>
 window.addEventListener('message', function (e) {
   var m = String(e.data || '');
   if (m.indexOf('MEAS') === 0) {
     document.body.setAttribute('data-meas', m.slice(4));
   }
 });
</script></body></html>''' % (폭, 주소))

    깃발 = machine.크롬앞머리() + [
        '--window-size=%d,900' % max(폭, 520),
        '--virtual-time-budget=9000', '--dump-dom',
        'file:///' + urllib.parse.quote(래퍼.replace('\\', '/'), safe='/:'),
    ]
    r = subprocess.run(깃발, capture_output=True, timeout=180)
    글 = r.stdout.decode('utf-8', 'replace')
    if os.path.isfile(임시):
        os.remove(임시)
    자리 = 글.find('data-meas="')
    if 자리 < 0:
        return None
    끝 = 글.find('"', 자리 + 11)
    속 = 글[자리 + 11:끝]
    # --dump-dom 은 속성값을 HTML 로 적습니다 — 따옴표가 &quot; 입니다
    for a, b in (('&quot;', '"'), ('&amp;', '&'), ('&lt;', '<'),
                 ('&gt;', '>')):
        속 = 속.replace(a, b)

    return json.loads(속)


def main():
    if len(sys.argv) < 2:
        print('쓰는 법: python engine/measure_scroll.py <쪽.html> [폭]')
        return 2
    폭 = int(sys.argv[2]) if len(sys.argv) > 2 else 390
    쟀 = 재기(sys.argv[1], 폭)
    if not 쟀:
        print('못 쟀습니다 — 쪽이 안 열렸거나 칸을 못 찾았습니다')
        return 1
    화면 = 한화면.get(폭, 700)
    print()
    print('%s · 폭 %dpx · 한 화면 %dpx 로 봅니다'
          % (os.path.basename(sys.argv[1]), 폭, 화면))
    print('쪽 전체 길이 **%dpx** — 화면 %.1f 개'
          % (쟀['전체높이'], 쟀['전체높이'] / 화면))
    print()
    print('%-28s %7s %7s  %s' % ('칸', '꼭대기', '높이', '몇 번째 화면'))
    print('-' * 68)
    for c in 쟀['칸']:
        번째 = c['y'] / 화면 + 1
        이름 = (c['제목'] or c['이름'])[:26]
        print('%-28s %7d %7d  %4.1f 번째'
              % (이름, c['y'], c['h'], 번째))
    return 0


if __name__ == '__main__':
    sys.exit(main())
