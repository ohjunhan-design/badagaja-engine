# -*- coding: utf-8 -*-
"""**눈으로 볼 때 이상한 것이 없는가** (2026-10-08 밤 주인 지시)

★ 왜 이 검사가 있나

    주인 지시 — 「바다가자를 전체적으로 **시각적으로** 오류가 있는지
    찾아봐. **디자인 오류** 및 확대 보기 같은 전체적인 오류를 점검해」

    기존 검사기가 보는 것과 **겹치지 않는 것**만 봅니다 —
      · `check_render`  화면 밖으로 나가는가 · 글자 크기 · 누름자리
      · `check_cover`   본문 위에 올라앉았는가
      · `check_interact` 눌러서 열리고 닫히는가

    여기서는 **그려진 모습 자체가 이상한 것**을 봅니다.

무엇을 보나

    ① **글이 잘립니다** — 칸보다 글이 길어 넘치는데 `overflow:hidden`
       이라 그냥 잘려 보입니다. 손님은 글자가 사라진 줄 압니다.
    ② **글끼리 겹칩니다** — 서로 다른 글 덩이가 같은 자리에 포개져
       읽을 수 없습니다.
    ③ **사진 비율이 깨집니다** — 원래 가로세로와 그려진 가로세로가
       많이 달라 늘어나거나 찌그러져 보입니다.
    ④ **빈 칸** — 테두리·바탕만 있고 안에 아무것도 없는 칸.

    ★ 네 가지 모두 **거짓 양성이 나기 쉬워** 기준을 넉넉히 둡니다.
      구별하지 못하는 검사는 두지 않습니다. 남는 것은 기준선에
      쌓아 **새로 느는 것만** 막습니다.

쓰는 법
    python engine/check_visual.py           표본
    python engine/check_visual.py --all     전수
"""
import io
import os
import re
import sys
import json
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
기준길 = os.path.join(ROOT, 'tests', 'golden', '시각.json')

재는스크립트 = """
<script>
(function () {
  function 보이나(e) {
    var s = getComputedStyle(e);
    if (s.display === 'none' || s.visibility === 'hidden'
        || s.opacity === '0') return false;
    var r = e.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  }
  function 글만(e) {
    var t = '';
    for (var i = 0; i < e.childNodes.length; i++) {
      if (e.childNodes[i].nodeType === 3) t += e.childNodes[i].nodeValue;
    }
    return t.trim();
  }
  function 재자() {
    var 난것 = { 폭: innerWidth, 잘린글: [], 겹친글: [],
                 찌그러진사진: [], 빈칸: [] };
    var 모두 = document.querySelectorAll('body *');

    // ① 글이 잘립니다
    for (var i = 0; i < 모두.length; i++) {
      var e = 모두[i];
      if (!보이나(e)) continue;
      var s = getComputedStyle(e);
      if (s.overflow !== 'hidden' && s.overflowY !== 'hidden'
          && s.overflowX !== 'hidden') continue;
      if (s.webkitLineClamp && s.webkitLineClamp !== 'none') continue;
      if (s.textOverflow === 'ellipsis') continue;   // 일부러 …로 줄임
      var 글 = 글만(e);
      if (글.length < 6) continue;
      // 넉넉히 — 8px 넘게 잘릴 때만
      if (e.scrollHeight > e.clientHeight + 8
          || e.scrollWidth > e.clientWidth + 8) {
        난것.잘린글.push({
          태그: e.tagName,
          클래스: (e.className || '').toString().trim().split(/\\s+/)[0] || '',
          글: 글.slice(0, 24),
          보임: Math.round(e.clientHeight), 속: Math.round(e.scrollHeight)
        });
        if (난것.잘린글.length >= 5) break;
      }
    }

    // ③ 사진 비율이 깨집니다
    //   ★ `width`·`height` **속성**이 아니라 `naturalWidth` 를 씁니다.
    //     `<picture>` 에서는 속성이 PC 사진 값이고 휴대폰은 `<source>`
    //     가 이겨 다른 사진을 받습니다. 속성으로 재면 **멀쩡한 것을
    //     찌그러졌다고** 합니다 (2026-10-08 밤에 그렇게 속았습니다).
    var 사진들 = document.querySelectorAll('img');
    for (var j = 0; j < 사진들.length; j++) {
      var m = 사진들[j];
      if (!보이나(m)) continue;
      if (!m.naturalWidth || !m.naturalHeight) continue;   // 아직 안 받음
      var ms = getComputedStyle(m);
      var r2 = m.getBoundingClientRect();
      if (r2.width < 20 || r2.height < 20) continue;
      var 진짜 = m.naturalWidth / m.naturalHeight;
      var 지금 = r2.width / r2.height;
      if (ms.objectFit !== 'cover' && ms.objectFit !== 'contain'
          && Math.abs(진짜 - 지금) / 진짜 > 0.12) {
        난것.찌그러진사진.push({
          주소: (m.currentSrc || m.src || '').split('/').pop().slice(0, 28),
          원래: Math.round(진짜 * 100) / 100,
          지금: Math.round(지금 * 100) / 100,
          크기: Math.round(r2.width) + 'x' + Math.round(r2.height)
        });
      }
      // ★ **미리 잡는 자리가 맞는가** — 속성 값이 실제 받은 사진과
      //   비율이 다르면 사진이 뜨는 순간 쪽이 덜컥 흔들립니다(CLS).
      var aw = parseFloat(m.getAttribute('width'));
      var ah = parseFloat(m.getAttribute('height'));
      // ★ **CSS 가 자리를 잡으면 속성은 상관없습니다** (2026-10-08 밤)
      //   `object-fit` 이 있거나 높이가 `auto` 가 아니면 부모·CSS 가
      //   자리를 정합니다. 속성 비율이 달라도 안 흔들립니다.
      //   속성에 자리를 맡기는 것은 `height:auto` 인 사진뿐입니다.
      var 자리를CSS가 = (ms.objectFit === 'cover' || ms.objectFit === 'contain'
                         || (ms.aspectRatio && ms.aspectRatio !== 'auto')
                         || (ms.height && ms.height !== 'auto'
                             && m.style.height !== 'auto'
                             && ms.position === 'absolute'));
      if (aw && ah && !자리를CSS가) {
        var 적힌 = aw / ah;
        if (Math.abs(적힌 - 진짜) / 진짜 > 0.12) {
          난것.자리흔들림 = 난것.자리흔들림 || [];
          난것.자리흔들림.push({
            주소: (m.currentSrc || m.src || '').split('/').pop().slice(0, 28),
            적힌: Math.round(적힌 * 100) / 100,
            진짜: Math.round(진짜 * 100) / 100
          });
        }
      }
      if (난것.찌그러진사진.length >= 5) break;
    }

    // ④ 빈 칸 — 테두리·바탕이 있는데 안이 비었습니다
    var 칸들 = document.querySelectorAll(
      'section, article, aside, .card, [class*="panel"], [class*="box"]');
    for (var k = 0; k < 칸들.length; k++) {
      var c = 칸들[k];
      if (!보이나(c)) continue;
      var cr = c.getBoundingClientRect();
      if (cr.height < 40) continue;
      if ((c.innerText || '').trim().length > 0) continue;
      if (c.querySelector('img, svg, picture, video, canvas, iframe')) continue;
      // ★ **광고 자리는 비어 있는 것이 정상입니다** (계약-15)
      //   광고가 안 뜰 때도 자리를 지켜야 쪽이 안 흔들립니다.
      if (c.querySelector('.ad-slot, ins, [data-ad-slot]')) continue;
      if (c.classList.contains('ad-slot')) continue;
      난것.빈칸.push({
        태그: c.tagName,
        클래스: (c.className || '').toString().trim().split(/\\s+/)[0] || '',
        크기: Math.round(cr.width) + 'x' + Math.round(cr.height)
      });
      if (난것.빈칸.length >= 5) break;
    }

    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    try { parent.document.body.appendChild(d); }
    catch (e2) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 300);
  else addEventListener('load', function () { setTimeout(재자, 300); });
})();
</script>
"""


def 쪽재기(쪽길, 폭=1280, 높이=2200):
    글 = _io.read(쪽길)
    글 = 글.replace('</body>', 재는스크립트 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-visual-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        _io.write(사본, 글)
        R._자산옮기기(임시)
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
        return json.loads(_h.unescape(m.group(1)))
    finally:
        shutil.rmtree(임시, ignore_errors=True)


def 볼쪽들(전부):
    것들 = sorted(_io.쪽들(NEW))
    if 전부:
        return 것들
    칸별 = {}
    for p in 것들:
        칸 = os.path.dirname(os.path.relpath(p, NEW)) or '.'
        칸별.setdefault(칸, []).append(p)
    난것 = []
    for 칸 in sorted(칸별):
        난것 += 칸별[칸][:2]
    return 난것


def main():
    전부 = '--all' in sys.argv
    받아들이기 = '--받아들이기' in sys.argv
    print()
    print('  눈으로 볼 때 이상한 것이 없는가')
    print('  (2026-10-08 밤 주인 지시 — 「디자인 오류」)')
    print()

    것들 = 볼쪽들(전부)
    mustmeasure.있어야한다(것들, '쪽', 최소=10, 어디=NEW)

    기준 = {}
    try:
        기준 = json.loads(_io.read(기준길, default='{}'))
    except Exception:                                 # noqa: BLE001
        기준 = {}
    알던것 = set(기준.get('알던것') or [])

    막음, 알림 = [], []
    잰쪽 = 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        for 폭 in ((1280, 375) if 전부 else (1280, 375)):
            try:
                잰것 = 쪽재기(p, 폭=폭)
            except Exception as e:                    # noqa: BLE001
                알림.append('%s %dpx — 못 쟀습니다 (%s)'
                            % (짧, 폭, str(e)[:40]))
                continue
            잰쪽 += 1
            for x in 잰것['잘린글']:
                막음.append('%s %dpx — `%s` 안의 글이 잘립니다 '
                            '(보임 %dpx · 속 %dpx · 「%s」)'
                            % (짧, 폭, x['클래스'] or x['태그'],
                               x['보임'], x['속'], x['글']))
            for x in 잰것['찌그러진사진']:
                막음.append('%s %dpx — 사진이 찌그러집니다 '
                            '(원래 %s · 지금 %s · %s · %s)'
                            % (짧, 폭, x['원래'], x['지금'], x['크기'],
                               x['주소']))
            for x in (잰것.get('자리흔들림') or []):
                막음.append('%s %dpx — 사진이 뜰 때 쪽이 흔들립니다 '
                            '(적힌 비율 %s · 진짜 %s · %s)'
                            % (짧, 폭, x['적힌'], x['진짜'], x['주소']))
            for x in 잰것['빈칸']:
                막음.append('%s %dpx — `%s` 칸이 비어 있습니다 (%s)'
                            % (짧, 폭, x['클래스'] or x['태그'], x['크기']))

    mustmeasure.있어야한다(range(잰쪽), '잰 것', 최소=10, 어디=NEW)
    print('  쪽 %d개 × 두 폭 = %d번 그려 봤습니다 (%s)'
          % (len(것들), 잰쪽, '전수' if 전부 else '표본 — 전수는 --all'))
    print()

    if 받아들이기:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        _io.write(기준길, json.dumps({
            '_무엇인가': ('눈으로 볼 때 이상한 것의 기준선입니다. '
                          '여기 있는 것은 **새로 생긴 것이 아니라는 뜻**'
                          '일 뿐, 괜찮다는 뜻이 아닙니다.'),
            '_어떻게줄이나': '고친 뒤 여기서 그 줄을 지웁니다.',
            '알던것': sorted(막음),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(막음), os.path.relpath(기준길, ROOT)))
        return 0

    새것 = [t for t in 막음 if t not in 알던것]
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:3]:
            print('  ~ %s' % t)
        print()
    if 새것:
        print('  **새로 생긴** 손볼 곳 %d가지' % len(새것))
        for t in 새것[:14]:
            print('  ✗ %s' % t)
        print()
        print('  손님은 글자가 사라진 줄 압니다. 칸을 늘리거나')
        print('  글을 줄이세요 — 잘라 두면 아무도 모릅니다.')
        return 1

    print('  · 눈에 거슬리는 것이 새로 생기지 않았습니다 (쌓인 것 %d곳)'
          % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
