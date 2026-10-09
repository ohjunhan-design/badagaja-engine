# -*- coding: utf-8 -*-
"""**운영에 올라간 채비 쪽의 확대 단추를 잽니다** (2026-10-09)

★ 왜 이 검사가 있나

    감독팀 지시 — 「확대 버튼 34/34(17쪽×PC·모바일, 넘침·가림 0).
    **운영에서 다시 재기 전까지 완료로 닫지 마세요.**」

    `check_rigpage.py` 는 **로컬 `site/`** 를 봅니다. 로컬이
    통과해도 서버에 제대로 올라갔다는 보장이 없습니다 —
    실제로 Pillow 가 일꾼에 없어 38쪽의 사진 크기가 안 붙은
    적이 있습니다.

어떻게 재나

    **운영에서 받아 로컬에 두고, 그것을 그려 봅니다.**

    서버 쪽을 iframe 에 넣으면 `X-Frame-Options: SAMEORIGIN`
    이 막습니다(2026-10-09에 겪었습니다). 그래서 쪽과 딸린 것
    (CSS·그림)을 **받아서** 로컬에 펼친 뒤 `check_rigpage` 와
    똑같은 방식으로 잽니다.

    받은 것이 서버 그대로이므로 **운영을 잰 것**입니다.

쓰는 법
    python engine/check_live_rigpage.py
    python engine/check_live_rigpage.py --쪽 rig/bottom.html
"""
import io
import os
import re
import sys
import json
import shutil
import tempfile
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import mustmeasure           # noqa: E402
from engine import check_rigpage as RP   # noqa: E402

뿌리 = os.environ.get('BADAGAJA_LIVE', 'https://badagaja.com')
때 = 25

_딸린것 = re.compile(
    r'(?:href|src)="([^"]+\.(?:css|js|jpg|jpeg|png|webp|svg)[^"]*)"', re.I)


def 받기(길):
    """운영에서 바이트를 받습니다. 못 받으면 None"""
    주소 = 뿌리.rstrip('/') + '/' + 길.lstrip('/')
    req = urllib.request.Request(
        주소, headers={'User-Agent': 'badagaja-rigcheck/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=때) as r:
            return r.read()
    except Exception:                                 # noqa: BLE001
        return None


def 펼치기(집, 쪽길):
    """쪽과 딸린 것을 **운영에서 받아** 집에 펼칩니다.

    돌려주는 것 — (펼친 쪽의 자리, 못 받은 것 목록)
    """
    몸 = 받기(쪽길)
    if 몸 is None:
        return None, ['쪽 자체를 못 받았습니다']
    글 = 몸.decode('utf-8', 'replace')

    쪽자리 = os.path.join(집, 쪽길.replace('/', os.sep))
    os.makedirs(os.path.dirname(쪽자리), exist_ok=True)
    io.open(쪽자리, 'w', encoding='utf-8', newline='').write(글)

    바탕 = os.path.dirname(쪽길)
    못받음 = []
    받은것 = set()
    for 주소 in _딸린것.findall(글):
        깨끗 = 주소.split('?')[0].split('#')[0]
        if 깨끗.startswith(('http', 'data:', '//')):
            continue
        풀린 = os.path.normpath(
            os.path.join(바탕, 깨끗)).replace('\\', '/')
        if 풀린 in 받은것:
            continue
        받은것.add(풀린)
        자료 = 받기(풀린)
        if 자료 is None:
            못받음.append(풀린)
            continue
        낼곳 = os.path.join(집, 풀린.replace('/', os.sep))
        os.makedirs(os.path.dirname(낼곳), exist_ok=True)
        io.open(낼곳, 'wb').write(자료)
    return 쪽자리, 못받음


def 한쪽재기(쪽길, 폭, 높이=2200):
    """운영에서 받아 펼친 뒤 `check_rigpage` 와 같은 방식으로 잽니다"""
    집 = tempfile.mkdtemp(prefix='badagaja-live-rig-')
    try:
        쪽자리, 못받음 = 펼치기(집, 쪽길)
        if 쪽자리 is None:
            raise RuntimeError('운영에서 쪽을 못 받았습니다 — %s' % 쪽길)
        # ★ **재는 스크립트를 심어야 결과가 나옵니다** —
        #   이것을 빠뜨려 「크롬이 결과를 안 돌려줬습니다」가 났습니다.
        #   check_rigpage 가 쓰는 그 스크립트를 그대로 씁니다
        #   (같은 것을 두 곳에 두지 않습니다).
        글 = io.open(쪽자리, encoding='utf-8').read()
        글 = 글.replace(
            '</body>',
            RP.재는스크립트.replace('__최대폭__', str(RP.최대그림폭))
            + '</body>')
        io.open(쪽자리, 'w', encoding='utf-8', newline='').write(글)

        틀 = os.path.join(집, '틀.html')
        io.open(틀, 'w', encoding='utf-8', newline='').write(
            RP.R.틀쪽.replace('__쪽__', RP.R._틀에서부를길(집, 쪽자리))
                     .replace('__폭__', str(폭))
                     .replace('__높이__', str(높이)))

        import subprocess
        from engine import machine
        나옴 = subprocess.run(
            machine.크롬앞머리() + [
                '--hide-scrollbars',
                '--window-size=%d,%d' % (폭 + 40, 높이 + 60),
                '--virtual-time-budget=3000',
                '--allow-file-access-from-files',
                '--host-resolver-rules=MAP * 127.0.0.1:1',
                '--dump-dom', 'file:///' + 틀.replace('\\', '/')],
            capture_output=True, text=True, encoding='utf-8',
            errors='replace', timeout=120)
        m = re.search(r'id="__잰결과__"[^>]*>(.*?)</div>', 나옴.stdout, re.S)
        if not m:
            raise RuntimeError('크롬이 결과를 안 돌려줬습니다')
        import html as _h
        잰것 = json.loads(_h.unescape(m.group(1)))
        잰것['_못받은것'] = 못받음
        return 잰것
    finally:
        shutil.rmtree(집, ignore_errors=True)


def 채비쪽들():
    """**로컬 자료에서** 목록을 얻고, 재는 것은 운영입니다.

    ★ 이름을 코드에 박지 않습니다 (기억: 시험에 이름을 박지 않기)
    ★ `RP.채비쪽들()` 은 **절대 경로**를 줍니다. 운영 주소로
      쓰려면 `site/` 기준 상대 주소여야 합니다 — 이것을 안 바꿔
      「드라이브 경로를 못 받았습니다」가 났습니다.
    """
    바탕 = os.path.join(ROOT, "site")
    나옴 = []
    for p in RP.채비쪽들():
        if os.path.isabs(p):
            p = os.path.relpath(p, 바탕)
        나옴.append(p.replace(chr(92), "/"))
    return 나옴


def main():
    하나 = None
    if '--쪽' in sys.argv:
        하나 = sys.argv[sys.argv.index('--쪽') + 1]

    print()
    print('  운영 채비 쪽의 확대 단추 — %s' % 뿌리)
    print('  (감독팀 지시 — 운영에서 다시 재기 전까지 완료로 닫지 않습니다)')
    print()

    쪽들 = [하나] if 하나 else 채비쪽들()
    mustmeasure.있어야한다(쪽들, '채비 쪽', 최소=1,
                          어디=os.path.join(ROOT, 'site'))

    막음, 본것 = [], 0
    for 쪽길 in 쪽들:
        for 폭, 이름 in ((1280, 'PC'), (390, '휴대폰')):
            try:
                잰것 = 한쪽재기(쪽길, 폭)
            except Exception as e:                    # noqa: BLE001
                print('  ✗ %s %s — 못 쟀습니다: %s' % (쪽길, 이름, e))
                return 4                              # 못잼
            본것 += 1
            탈 = []
            if 잰것.get('처음에보임'):
                탈.append('확대 칸이 처음부터 보임')
            cta = 잰것.get('확대단추') or {}
            if not cta.get('보임'):
                탈.append('「크게 보기」가 안 보임')
            elif (cta.get('높이') or 0) < 44:
                탈.append('「크게 보기」가 %spx (44 넘어야)' % cta.get('높이'))
            if 잰것.get('가로넘침'):
                탈.append('가로 넘침 %d개' % 잰것['가로넘침'])
            if 잰것.get('덮는것'):
                탈.append('그림을 덮는 것 %d개' % len(잰것['덮는것']))
            if 잰것.get('_못받은것'):
                탈.append('딸린 것 %d개를 운영에서 못 받음'
                          % len(잰것['_못받은것']))
            if 탈:
                막음.append((쪽길, 이름, 탈))
                print('  ✗ %-22s %-4s %s' % (쪽길, 이름, ' · '.join(탈)))

    print()
    print('  쪽 %d개 × 두 폭 = **%d번** 운영에서 받아 그려 봤습니다'
          % (len(쪽들), 본것))
    if 막음:
        print('  ✗ 탈이 난 것 %d번' % len(막음))
        return 1                                      # 어김
    print('  ✓ %d/%d 모두 괜찮습니다 — 초기 숨김 · 확대 단추 44px ·'
          ' 넘침 0 · 가림 0' % (본것, 본것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
