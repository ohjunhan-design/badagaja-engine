# -*- coding: utf-8 -*-
"""휴대폰 폭으로 **진짜** 찍습니다 (2026-10-01).

★ 겪은 일 — 그림을 믿고 없는 잘못을 고쳤습니다

  `chrome --headless --window-size=390,2600 --screenshot` 으로 찍고
  「글자가 오른쪽으로 잘린다」고 판단해 차림표를 고쳤습니다.

  **거짓이었습니다.** 윈도 크롬은 창을 **500px 아래로 줄이지
  못합니다.** 390 을 줘도 **1009px 로 그린 다음 왼쪽 390px 만
  잘라낸 그림**을 줍니다. 그러니 잘린 것처럼 보일 수밖에 없습니다.

  같은 쪽을 `check_mobile.py` 로 재니 「화면 밖으로 나가는 것이
  없습니다」였고, 몸 너비가 **1009px** 로 찍혀 있었습니다.
  검사기가 맞고 제 눈이 틀렸습니다.

★ 그래서 **iframe 에 넣어** 찍습니다
  창은 넓게 두고, 그 안에 390px 짜리 틀을 만들어 쪽을 넣습니다.
  틀 안쪽은 진짜 390px 이므로 반응형이 제대로 걸립니다.

★ 규칙 6-2 — 기계가 잰 것과 눈으로 본 것을 **갈라서** 말합니다
  이 도구는 **눈으로 보기 위한 것**입니다. 넘침을 재는 일은
  `check_mobile.py` 가 합니다. 둘을 섞지 않습니다.
"""
import os
import sys
import subprocess
import tempfile
import urllib.parse

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import machine   # noqa: E402
from engine import io as _io   # 쓰기는 io.write 로 (계약-13)   # noqa: E402

틀 = """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
 html,body{margin:0;padding:0;background:#fff}
 iframe{display:block;width:%(w)dpx;height:%(h)dpx;border:0}
</style></head><body>
<iframe src="%(url)s" scrolling="no"></iframe>
</body></html>"""


def 찍기(쪽길, 낼곳, 폭=390, 높이=2600):
    """쪽 하나를 **진짜 `폭`px** 로 찍습니다."""
    쪽길 = os.path.abspath(쪽길)
    주소 = 'file:///' + urllib.parse.quote(
        쪽길.replace('\\', '/'), safe='/:')
    집 = tempfile.mkdtemp(prefix='bada-shot-')
    래퍼 = os.path.join(집, 'wrap.html')
    _io.write(래퍼, 틀 % {'w': 폭, 'h': 높이, 'url': 주소})
    깃발 = machine.크롬앞머리() + [
        '--hide-scrollbars', '--force-device-scale-factor=1',
        '--window-size=%d,%d' % (max(폭, 520), 높이),
        '--virtual-time-budget=4000',
        '--screenshot=%s' % 낼곳,
        'file:///' + urllib.parse.quote(래퍼.replace('\\', '/'), safe='/:'),
    ]
    subprocess.run(깃발, capture_output=True, timeout=120)
    return os.path.exists(낼곳)


def main():
    if len(sys.argv) < 3:
        print('쓰는 법: python engine/shot_phone.py <쪽.html> <낼그림.png> '
              '[폭] [높이]')
        return 2
    폭 = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    높이 = int(sys.argv[4]) if len(sys.argv) > 4 else 2600
    됐나 = 찍기(sys.argv[1], sys.argv[2], 폭, 높이)
    print('%s — %dx%d' % ('찍었습니다' if 됐나 else '못 찍었습니다',
                          폭, 높이))
    return 0 if 됐나 else 1


if __name__ == '__main__':
    sys.exit(main())
