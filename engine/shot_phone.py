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
    # ★ **주소 조각(#…)을 떼어 둡니다** (2026-10-08)
    #   `쪽.html#yeosu-f-001` 을 그대로 abspath 에 넣으면 조각까지
    #   파일 이름으로 쳐서 **없는 파일**이 되고, 회색 빈 칸이
    #   찍힙니다. 조각은 주소 뒤에 다시 붙입니다 — 쪽이 그것을
    #   읽어 그 포인트를 열어 줍니다.
    # ★ **공개 주소도 받습니다 — 다만 badagaja.com 은 안 됩니다**
    #   (2026-10-08)
    #
    #   물때·지도처럼 바깥에서 오는 것은 로컬 파일로 찍으면 늘
    #   비어 있어, 공개 쪽을 iframe 에 넣어 보았습니다.
    #   **빈 칸만 찍혔습니다.** 서버가 `X-Frame-Options: SAMEORIGIN`
    #   을 보내기 때문입니다 — `file://` 래퍼와 출처가 다릅니다.
    #
    #   그 설정은 **올바른 것이라 바꾸지 않습니다.** 공개 쪽을
    #   휴대폰 폭으로 보려면 크롬 창을 줄여 찍습니다(500px 까지만
    #   줄어듭니다). 같은 출처에 래퍼를 둘 수 있게 되면 이 길이
    #   다시 쓸모 있어 남겨 둡니다.
    # ★ 낼 곳은 **절대 경로**로 바꿉니다 (2026-10-09)
    #   크롬은 자기 작업 폴더를 기준으로 삼아, 상대 경로를 주면
    #   엉뚱한 데 쓰거나 폴더가 없어 **아무 말 없이 안 씁니다.**
    #   「못 찍었습니다」만 나오고 까닭을 알 수 없었습니다.
    낼곳 = os.path.abspath(낼곳)
    os.makedirs(os.path.dirname(낼곳) or '.', exist_ok=True)

    낮은것 = (쪽길 or '').lower()
    if 낮은것.startswith('http://') or 낮은것.startswith('https://'):
        주소 = 쪽길
        집 = tempfile.mkdtemp(prefix='bada-shot-')
        래퍼 = os.path.join(집, 'wrap.html')
        _io.write(래퍼, 틀 % {'w': 폭, 'h': 높이, 'url': 주소})
        깃발 = machine.크롬앞머리() + [
            '--hide-scrollbars', '--force-device-scale-factor=1',
            '--window-size=%d,%d' % (max(폭, 520), 높이),
            # 바깥에서 받아 오므로 넉넉히 기다립니다
            # ★ 긴 쪽(5,000px 넘는 것)은 12초로 모자랍니다 —
            #   2026-10-09 운영 첫 쪽을 찍었더니 **빈 화면**이
            #   나왔습니다. 쪽 높이에 맞춰 늘립니다.
            '--virtual-time-budget=%d' % max(12000, 높이 * 6),
            '--screenshot=%s' % 낼곳,
            'file:///' + urllib.parse.quote(래퍼.replace('\\', '/'),
                                            safe='/:'),
        ]
        subprocess.run(깃발, capture_output=True, timeout=180)
        return _정말찍혔나(낼곳)

    조각 = ''
    if '#' in 쪽길:
        쪽길, 뒤 = 쪽길.split('#', 1)
        조각 = '#' + 뒤
    # ★ 물음표(?point=…)도 같습니다 — 파일 이름에 섞이면 못 찾습니다
    if '?' in 쪽길:
        쪽길, 뒤 = 쪽길.split('?', 1)
        조각 = '?' + 뒤 + 조각
    쪽길 = os.path.abspath(쪽길)
    주소 = 'file:///' + urllib.parse.quote(
        쪽길.replace('\\', '/'), safe='/:') + 조각
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
    return _정말찍혔나(낼곳)


def _정말찍혔나(낼곳):
    """파일이 생겼다고 **찍힌 것이 아닙니다.**

    ★ 2026-10-09 — 공개 서버를 찍었더니 **통째로 회색**이었습니다.
      `X-Frame-Options: SAMEORIGIN` 이 iframe 을 막습니다.
      그런데 도구는 「찍었습니다」라고 했습니다. 그 말을 믿고
      빈 그림을 주인께 보낼 뻔했습니다.

      파일이 있는지가 아니라 **그림에 내용이 있는지**를 봅니다.
    """
    if not os.path.exists(낼곳):
        return False
    try:
        from PIL import Image
        with Image.open(낼곳) as im:
            작 = im.convert('RGB').resize((20, 60))
            색 = set(작.getpixel((x, y))
                     for y in range(60) for x in range(20))
        # ★ 색 **가짓수**로는 못 가립니다 — 빈 쪽도 회색 음영이
        #   열 가지쯤 나옵니다. **색이 있는가**를 봅니다:
        #   R·G·B 가 서로 다른 점(= 회색이 아닌 점)이 있는지.
        색있음 = sum(1 for r, g, b in 색
                     if max(r, g, b) - min(r, g, b) > 12)
        if 색있음 < 2:
            print('✗ 빈 그림입니다 (회색뿐 — 색 %d가지, 유채색 %d가지).'
                  % (len(색), 색있음))
            print('  공개 서버는 X-Frame-Options 로 iframe 을 막습니다 —')
            print('  이 도구는 **로컬 서버 전용**입니다.')
            print('  공개 쪽은 크롬 탭으로 직접 찍으세요.')
            return False
    except ImportError:
        pass          # Pillow 가 없으면 못 봅니다 — 막지는 않습니다
    return True



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
