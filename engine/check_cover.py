# -*- coding: utf-8 -*-
"""**본문을 덮는 것이 없는가** (2026-10-08)

★ 왜 이 검사가 있나 — 오늘 손님이 보는 쪽이 실제로 가려졌습니다

    `.rig-zoom` 이 두 뜻으로 쓰여, 1372×980 짜리 확대 그림이
    **채비 16쪽 전부에서 늘 펼쳐져** 본문을 덮었습니다.

    기존 검사기 가운데 **어느 것도 이것을 못 잡았습니다.**
      · `check_render` 는 「화면 **밖으로 나가는가**」를 봅니다.
        덮는 것은 화면 **안**에 있어 넘침이 0 입니다.
      · `check_photos` 는 「보이는 것이 있는가」를 봅니다.
        덮는 그림도 「보이는 것」이라 오히려 통과합니다.
      · `check_cssdup` 은 차림표 짜임을 봅니다 — 원인은 잡지만,
        원인이 **다른 꼴**로 나타나면 못 잡습니다.

    그래서 **결과를 직접 잽니다** — 쪽을 그려 놓고
    「본문 위에 올라앉은 큰 것이 있는가」를 봅니다.

무엇을 재나

    `position:absolute|fixed` 이고 **보이며**, 넓이가 본문 폭의 70%
    이상이고 높이가 400px 넘는 것. 그런 것은 손님 눈에 **다른 것을
    가립니다.**

    ★ **깔린 것과 덮은 것을 쪽이 스스로 말하게** 가립니다.
      히어로 배경은 `aria-hidden="true"` 입니다 — 읽히지 않는
      꾸밈이고 그 위에 글이 올라갑니다. 덮개는 반대로 읽혀야
      합니다(닫기 단추·그림 설명). 크기로는 못 가립니다.

    ★ 일부러 덮는 것은 **봐 줍니다** —
      · 아래 차림표(`.tabbar`)·맨 위로 단추처럼 작고 가장자리인 것
      · `:target`·`:hover` 로만 펴지는 것 (평소에는 안 보입니다)
      · 쪽이 스스로 「덮개」라고 밝힌 것 (`[data-overlay]`·`dialog`)

쓰는 법
    python engine/check_cover.py              표본
    python engine/check_cover.py --all        전수 (오래 걸립니다)
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

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 손님 눈을 가린다고 볼 크기
덮는폭비 = 0.70
덮는높이 = 400

재는스크립트 = """
<script>
(function () {
  function 재자() {
    var 난것 = { 폭: innerWidth, 덮는것: [] };
    var 모두 = document.querySelectorAll('body *');
    for (var i = 0; i < 모두.length; i++) {
      var e = 모두[i], s = getComputedStyle(e);
      if (s.position !== 'absolute' && s.position !== 'fixed') continue;
      if (s.display === 'none' || s.visibility === 'hidden'
          || s.opacity === '0') continue;
      // 쪽이 스스로 「덮개」라 밝힌 것은 봐 줍니다
      if (e.hasAttribute('data-overlay') || e.tagName === 'DIALOG') continue;
      if (e.closest('[data-overlay],dialog')) continue;
      // ★ **읽히지 않는 꾸밈은 덮개가 아닙니다** (2026-10-08)
      //   히어로 배경은 `aria-hidden="true"` — 「손님에게 읽히지 않는
      //   꾸밈」이라는 뜻이고, 그 위에 글이 올라갑니다.
      //   덮개는 반대로 **읽혀야 합니다**(닫기 단추·그림 설명).
      //   크기로는 둘을 못 가립니다.
      if (e.getAttribute('aria-hidden') === 'true') continue;
      if (e.closest('[aria-hidden="true"]')) continue;
      var r = e.getBoundingClientRect();
      if (r.width < innerWidth * __폭비__ || r.height < __높이__) continue;
      난것.덮는것.push({
        태그: e.tagName,
        클래스: (e.className && e.className.baseVal !== undefined
                 ? e.className.baseVal : (e.className || '')).toString()
                 .trim().split(/\\s+/)[0] || '',
        아이디: e.id || '',
        폭: Math.round(r.width), 높이: Math.round(r.height),
        자리: s.position
      });
      if (난것.덮는것.length >= 4) break;
    }
    var d = document.createElement('div');
    d.id = '__잰결과__';
    d.style.display = 'none';
    d.textContent = JSON.stringify(난것);
    // 바깥 틀에 붙입니다 — `--dump-dom` 은 틀만 찍습니다
    try { parent.document.body.appendChild(d); }
    catch (e2) { document.body.appendChild(d); }
  }
  if (document.readyState === 'complete') setTimeout(재자, 250);
  else addEventListener('load', function () { setTimeout(재자, 250); });
})();
</script>
"""


_그림주소 = re.compile(r'(?:src|srcset)="([^"]+\.(?:webp|jpg|jpeg|png|svg|avif))"',
                       re.I)


def _그쪽사진옮기기(임시, 쪽길, 글):
    """그 쪽이 **실제로 거는 사진만** 옮깁니다.

    ★ 왜 꼭 옮겨야 하나 (2026-10-08에 겪음)
      `check_render` 는 사진을 안 옮깁니다(71MB). `<img>` 에
      width·height 가 적혀 있어 **자리는** 잡히기 때문입니다.
      그런데 확대 칸의 그림은 `width:auto;height:auto` 라
      **파일이 없으면 크기가 0** 이 됩니다. 그래서 1372×980 짜리
      덮개를 「없다」고 셌습니다 — **검사가 헛돌았습니다.**
    """
    밭 = os.path.dirname(쪽길)
    옮김 = 0
    for 주 in set(_그림주소.findall(글)):
        주 = 주.split()[0].strip()
        if 주.startswith(('http:', 'https:', 'data:', '//')):
            continue
        원 = os.path.normpath(os.path.join(밭, 주))
        if not os.path.isfile(원):
            continue
        받는곳 = os.path.join(임시, os.path.relpath(원, NEW))
        try:
            os.makedirs(os.path.dirname(받는곳), exist_ok=True)
            shutil.copyfile(원, 받는곳)
            옮김 += 1
        except OSError:
            pass
    return 옮김


def 쪽재기(쪽길, 폭=1280, 높이=2200):
    글 = _io.read(쪽길)
    낌 = (재는스크립트.replace('__폭비__', str(덮는폭비))
          .replace('__높이__', str(덮는높이)))
    글 = 글.replace('</body>', 낌 + '</body>')
    임시 = tempfile.mkdtemp(prefix='badagaja-cover-')
    try:
        사본 = R._사본자리(임시, 쪽길)
        _io.write(사본, 글)
        R._자산옮기기(임시)
        _그쪽사진옮기기(임시, 쪽길, 글)
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


def 표본고르기(전부):
    """**자료에서 고릅니다** — 쪽 이름을 코드에 박지 않습니다
       (기억 「시험에 이름을 박지 않기」)"""
    것들 = sorted(_io.쪽들(NEW))
    if 전부:
        return 것들
    # 칸(폴더)마다 하나씩 + 뿌리에서 둘 — 쪽 **종류**를 고루 봅니다
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
    print()
    print('  본문을 덮는 것이 없는가')
    print('  (2026-10-08 — 확대 그림이 채비 16쪽을 덮고 있었습니다)')
    print()

    것들 = 표본고르기(전부)
    mustmeasure.있어야한다(것들, '쪽', 최소=10, 어디=NEW)

    기준길 = os.path.join(ROOT, 'tests', 'golden', '덮는것.json')
    기준 = {}
    try:
        기준 = json.loads(_io.read(기준길, default='{}'))
    except Exception:                                 # noqa: BLE001
        기준 = {}
    알던것 = set(기준.get('알던것') or [])
    받아들이기 = '--받아들이기' in sys.argv

    막음, 알림 = [], []
    잰쪽 = 0
    for p in 것들:
        짧 = os.path.relpath(p, NEW).replace(os.sep, '/')
        try:
            잰것 = 쪽재기(p)
        except Exception as e:                        # noqa: BLE001
            알림.append('%s — 못 쟀습니다 (%s)' % (짧, str(e)[:50]))
            continue
        잰쪽 += 1
        for x in 잰것['덮는것']:
            이름 = x['클래스'] or x['아이디'] or x['태그']
            막음.append('%s — `%s` 가 본문을 덮습니다 (%d×%d · %s)'
                        % (짧, 이름, x['폭'], x['높이'], x['자리']))

    mustmeasure.있어야한다(range(잰쪽), '잰 쪽', 최소=10, 어디=NEW)
    print('  쪽 %d개를 그려 봤습니다 (%s)'
          % (잰쪽, '전수' if 전부 else '표본 — 전수는 --all'))
    print()

    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:4]:
            print('  ~ %s' % t)
        print()
    if 받아들이기:
        os.makedirs(os.path.dirname(기준길), exist_ok=True)
        _io.write(기준길, json.dumps({
            '_무엇인가': ('본문 위에 올라앉은 것의 기준선입니다. 여기 있는 '
                          '것은 **새로 생긴 것이 아니라는 뜻**일 뿐입니다.'),
            '_왜쌓아두나': ('히어로 배경(`g-hero-bg`·`g-hero-shade`)처럼 '
                            '**깔린 것**도 크고 `absolute` 라 걸립니다. '
                            '그 위에 글이 올라가므로 덮는 것이 아닙니다. '
                            '`elementFromPoint` 로 가려 보았더니 화면 아래에 '
                            '있는 **진짜 덮개까지 놓쳐** 되돌렸습니다 — '
                            '구별하지 못하는 꾀는 두지 않습니다.'),
            '_어떻게줄이나': '고친 뒤 여기서 그 줄을 지웁니다.',
            '알던것': sorted(막음),
        }, ensure_ascii=False, indent=1))
        print('  · 기준선에 %d곳을 적었습니다 — %s'
              % (len(막음), os.path.relpath(기준길, ROOT)))
        return 0

    새것 = [t for t in 막음 if t not in 알던것]
    고쳐진것 = 알던것 - set(막음)
    if 고쳐진것 and not 새것:
        print('  · 고쳐진 곳 %d곳 — `--받아들이기` 로 기준을 조이세요'
              % len(고쳐진것))
        print()
    if 새것:
        print('  **새로 생긴** 손볼 곳 %d가지' % len(새것))
        for t in 새것[:12]:
            print('  ✗ %s' % t)
        print()
        print('  **화면 밖으로 안 나간다고 괜찮은 것이 아닙니다.**')
        print('  화면 **안**에서 본문 위에 올라앉으면 손님은 아무것도')
        print('  못 읽습니다. 숨겨 두어야 할 것이 펼쳐졌는지 보세요.')
        return 1
    print('  · 본문 위에 올라앉은 것이 새로 생기지 않았습니다'
          ' (쌓인 것 %d곳)' % len(알던것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
