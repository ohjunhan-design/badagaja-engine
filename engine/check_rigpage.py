# -*- coding: utf-8 -*-
"""**채비 쪽이 실제로 제대로 그려지는가** (2026-10-08)

★ 왜 이 검사가 있나 — 바깥 검수가 배포 뒤 확인 항목을 못박았습니다

    「배포 후에는 최소한 float_rod 포함 채비 16쪽에서:
       · 초기 overlay 숨김
       · 확대 CTA 정상
       · horizontal overflow 없음
       · 1100px 초과 렌더 없음
      이 네 개만 다시 확인하면 됩니다」

    손으로 네 가지를 볼 수도 있지만, **한 번 읽고 마는 것이 아니라
    앞으로도 저절로 지켜지게** 합니다 (규칙 26).

    2026-10-08 — `.rig-zoom` 이 두 뜻으로 쓰여 1372×980 짜리 확대
    그림이 채비 16쪽 전부에서 늘 펼쳐져 본문을 가렸습니다.
    그때 기존 검사기 가운데 어느 것도 이 넷을 보지 않았습니다.

무엇을 보나 (쪽마다 네 가지)

    ① 확대 칸이 **처음에는 숨어** 있는가 (`display:none`)
    ② 「크게 보기」가 **늘 보이고** 충분히 큰가
       — PC 44px · 모바일 46px, hover 전용 금지 (바깥 검수 기준)
    ③ 가로로 **넘치지 않는가**
    ④ **1100px 넘게 그려지는 그림이 없는가**

쓰는 법
    python engine/check_rigpage.py
"""
import io
import os
import re
import sys
import json
import glob
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io as _io          # noqa: E402
from engine import machine            # noqa: E402
from engine import mustmeasure        # noqa: E402
from engine import check_render as R  # noqa: E402
from engine import check_cover as C   # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 바깥 검수가 정한 기준
최대그림폭 = 1100
누름최소PC = 44
누름최소모바일 = 46

재는스크립트 = """
<script>
(function () {
  function 재자() {
    var 난것 = { 폭: innerWidth, 넘침: document.body.scrollWidth > innerWidth,
                 숨어야할것: [], 큰그림: [], 확대단추: null };
    // ① 확대 칸이 처음에 숨어 있는가
    var 칸들 = document.querySelectorAll('[id^="guide-"]');
    for (var i = 0; i < 칸들.length; i++) {
      var s = getComputedStyle(칸들[i]);
      if (s.display !== 'none') {
        var r = 칸들[i].getBoundingClientRect();
        난것.숨어야할것.push({
          아이디: 칸들[i].id, 표시: s.display,
          폭: Math.round(r.width), 높이: Math.round(r.height)
        });
      }
    }
    // ② 「크게 보기」가 늘 보이고 큰가
    var b = document.querySelector('.rig-guide-hint, .rig-guide-open');
    if (b) {
      var br = b.getBoundingClientRect(), bs = getComputedStyle(b);
      난것.확대단추 = {
        글: (b.textContent || '').trim().slice(0, 20),
        높이: Math.round(br.height), 폭: Math.round(br.width),
        보임: bs.display !== 'none' && bs.visibility !== 'hidden'
              && bs.opacity !== '0'
      };
    }
    // ④ 1100px 넘게 그려지는 그림
    var 그림들 = document.querySelectorAll('img, svg, picture');
    for (var j = 0; j < 그림들.length; j++) {
      var gr = 그림들[j].getBoundingClientRect();
      if (gr.width > __최대폭__) {
        난것.큰그림.push({
          태그: 그림들[j].tagName, 폭: Math.round(gr.width),
          높이: Math.round(gr.height),
          주소: (그림들[j].currentSrc || 그림들[j].src || '')
                .split('/').pop().slice(0, 30)
        });
      }
    }
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    try { parent.document.body.appendChild(d); }
    catch (e) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 250);
  else addEventListener('load', function () { setTimeout(재자, 250); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=1280, 높이=2200):
    글 = _io.read(쪽길)
    글 = 글.replace('</body>',
                    재는스크립트.replace('__최대폭__', str(최대그림폭))
                    + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-rigpage-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        _io.write(사본, 글)
        R._자산옮기기(임시)
        # ★ **사진을 옮겨야 잽니다** — 없으면 확대 그림 크기가 0 이 되어
        #   「탈 없음」이 나옵니다 (2026-10-08에 그렇게 속았습니다)
        C._그쪽사진옮기기(임시, 쪽길, 글)
        틀 = os.path.join(임시, '틀.html')
        _io.write(틀, (R.틀쪽.replace('__쪽__', R._틀에서부를길(임시, 사본))
                       .replace('__폭__', str(폭))
                       .replace('__높이__', str(높이))))
        나옴 = subprocess.run(
            machine.크롬앞머리() + [
                '--hide-scrollbars',
                '--window-size=%d,%d' % (폭 + 40, 높이 + 60),
                '--virtual-time-budget=3000', '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=90)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('크롬이 결과를 안 돌려줬습니다')
        import html as _h
        잰것 = json.loads(_h.unescape(m.group(1)))
        if 잰것.get('폭') != 폭:
            raise RuntimeError('틀 폭이 %s 로 잡혔습니다' % 잰것.get('폭'))
        return 잰것
    finally:
        shutil.rmtree(임시, ignore_errors=True)


def 채비쪽들():
    """**자료에서 찾습니다** — 이름을 코드에 박지 않습니다.

    채비 쪽은 「확대 칸(`id="guide-…"`)이 있는 쪽」입니다.
    목록 쪽(index·parts)은 그것이 없어 저절로 빠집니다.
    """
    난것 = []
    for p in _io.쪽들(NEW):
        글 = _io.read(p, default='')
        if 'id="guide-' in 글 and 'rig-guide' in 글:
            난것.append(p)
    return sorted(난것)


def main():
    print()
    print('  채비 쪽이 실제로 제대로 그려지는가')
    print('  (바깥 검수가 정한 배포 뒤 확인 네 가지)')
    print()

    것들 = 채비쪽들()
    mustmeasure.있어야한다(것들, '채비 쪽', 최소=10, 어디=NEW)

    막음, 알림 = [], []
    잰쪽 = 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        for 폭, 누름최소 in ((1280, 누름최소PC), (375, 누름최소모바일)):
            try:
                잰것 = 쪽재기(p, 폭=폭)
            except Exception as e:                    # noqa: BLE001
                알림.append('%s %dpx — 못 쟀습니다 (%s)'
                            % (짧, 폭, str(e)[:40]))
                continue
            잰쪽 += 1
            # ① 처음에 숨어 있는가
            for x in 잰것['숨어야할것']:
                막음.append('%s %dpx — 확대 칸 `%s` 가 처음부터 펼쳐져 '
                            '있습니다 (%d×%d · %s)'
                            % (짧, 폭, x['아이디'], x['폭'], x['높이'],
                               x['표시']))
            # ② 「크게 보기」가 늘 보이고 큰가
            b = 잰것.get('확대단추')
            if not b:
                막음.append('%s %dpx — 「크게 보기」가 없습니다' % (짧, 폭))
            elif not b['보임']:
                막음.append('%s %dpx — 「크게 보기」가 안 보입니다 '
                            '(hover 전용 금지)' % (짧, 폭))
            elif b['높이'] < 누름최소:
                막음.append('%s %dpx — 「크게 보기」가 %dpx 입니다 '
                            '(%d 넘어야)' % (짧, 폭, b['높이'], 누름최소))
            # ③ 가로 넘침
            if 잰것['넘침']:
                막음.append('%s %dpx — 가로로 넘칩니다' % (짧, 폭))
            # ④ 너무 큰 그림
            for g in 잰것['큰그림']:
                막음.append('%s %dpx — 그림이 %dpx 로 그려집니다 '
                            '(%d 넘음 · %s)'
                            % (짧, 폭, g['폭'], 최대그림폭,
                               g['주소'] or g['태그']))

    mustmeasure.있어야한다(range(잰쪽), '잰 것', 최소=10, 어디=NEW)
    print('  채비 쪽 %d개 × 두 폭 = %d번 그려 봤습니다'
          % (len(것들), 잰쪽))
    print()

    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:4]:
            print('  ~ %s' % t)
        print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        print()
        print('  바깥 검수가 정한 네 가지입니다 —')
        print('  초기 숨김 · 확대 CTA · 가로 넘침 · %dpx 초과 그림'
              % 최대그림폭)
        return 1

    print('  · 초기 숨김 · 확대 CTA · 가로 넘침 · %dpx 초과 그림 —'
          ' 네 가지 모두 괜찮습니다' % 최대그림폭)
    return 0


if __name__ == '__main__':
    sys.exit(main())
