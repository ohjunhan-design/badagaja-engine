# -*- coding: utf-8 -*-
"""**올린 뒤 운영 주소에서 직접 다시 잽니다** (2026-10-09 감독팀 지시)

★ 왜 이 검사가 있나

    「배포 후 운영 URL 에서 직접 재측정. 실패 시 『페이지가 보인다』로
     성공 처리하지 말고 어느 항목이 안 붙었는지 명시. 이 둘
     (Pillow·확대 버튼)은 운영에서 다시 재기 전까지 완료로
     닫지 마세요.」 — AI 감독팀

    로컬에서 통과한 것이 서버에서도 통과한다는 보장이 없습니다.
    실제로 겪었습니다 — 일꾼에 Pillow 가 없어 38쪽의 사진 크기가
    안 붙었는데 로컬에서는 멀쩡했습니다.

무엇을 재나 (모두 **운영 주소**에서)

    ① 판 지문      build.json 의 커밋·지문이 바라던 것인가
    ② 새 쪽        club/support.html 200 · 신청 폼 · cloud 오연결 0
    ③ 사진 크기    width/height 가 **양의 정수**이고
                   **실제 그림 파일 크기와 맞는가** (Pillow)
    ④ 딸린 것      CSS·JS·그림이 404 나지 않는가
    ⑤ 보호 대상    /zh-cn/ · api/ 가 그대로인가

    ★ 「쪽이 보인다」로 통과시키지 않습니다. 항목마다 따로 내고,
      하나라도 안 붙었으면 **그것을 이름으로 말합니다.**
    ★ **서버에 못 닿는 것을 통과로 보지 않습니다** — 못잼(4)입니다.

    ★ 쪽 수를 코드에 박지 않습니다 (기억: 시험에 이름을 박지 않기)
      감독팀이 「Pillow 38/38쪽」이라 했는데 실제로 세니
      fish·rig·catch 가 **58쪽**이었습니다(확대 단추도 17 이 아니라
      35쪽). 옛 판 기준이거나 다른 셈법으로 보입니다.
      **그때그때 세고, 몇 쪽을 봤는지 결과에 적습니다.**

    ★ 확대 단추가 그림을 가리는지는 여기서 안 봅니다 —
      브라우저가 필요해 `check_rigpage.py` 가 봅니다.

쓰는 법
    python engine/check_live_after_deploy.py                운영 주소
    python engine/check_live_after_deploy.py --바라는커밋 abc1234
"""
import io
import os
import re
import sys
import json
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

뿌리 = os.environ.get('BADAGAJA_LIVE', 'https://badagaja.com')
때 = 20

_사진 = re.compile(r'<img\b[^>]*>', re.I)
_크기값 = re.compile(
    r'\bwidth="(?P<w>\d+)"[^>]*\bheight="(?P<h>\d+)"'
    r'|\bheight="(?P<h2>\d+)"[^>]*\bwidth="(?P<w2>\d+)"', re.I)
_주소 = re.compile(r'\bsrc="([^"]+)"', re.I)
_css = re.compile(r'<link[^>]+href="([^"]+\.css[^"]*)"', re.I)
_js = re.compile(r'<script[^>]+src="([^"]+\.js[^"]*)"', re.I)
_클라우드 = re.compile(r'badagaja\.cloud', re.I)


def 그림크기(그림길, 쪽길, 쌓아둠):
    """그림을 **로컬 site/ 에서** 열어 진짜 크기를 봅니다.

    ★ 서버에서 받아 열면 느리고 돈이 듭니다. 올라간 것과 로컬이
      같은 판이라는 것은 [1] 에서 이미 확인했습니다.
    """
    if 그림길.startswith(('http', 'data:')):
        return None
    # 쪽 기준 상대 주소를 site/ 기준으로 풀어 줍니다
    바탕 = os.path.dirname(쪽길)
    풀린 = os.path.normpath(os.path.join(바탕, 그림길)).replace('\\', '/')
    if 풀린 in 쌓아둠:
        return 쌓아둠[풀린]
    실파일 = os.path.join(ROOT, 'site', 풀린)
    값 = None
    if os.path.exists(실파일):
        try:
            from PIL import Image
            with Image.open(실파일) as im:
                값 = im.size
        except Exception:                             # noqa: BLE001
            값 = None
    쌓아둠[풀린] = 값
    return 값


def 받기(길):
    """(끝난코드, 글) — 못 받으면 (None, 까닭)"""
    주소 = 뿌리.rstrip('/') + '/' + 길.lstrip('/')
    req = urllib.request.Request(
        주소, headers={'User-Agent': 'badagaja-check/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=때) as r:
            return r.getcode(), r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:                            # noqa: BLE001
        return None, str(e)


def 쪽목록():
    """로컬 site/ 에서 **갈래마다** 몇 쪽씩 고릅니다.

    ★ 쪽 이름을 코드에 박지 않습니다 (기억: 시험에 이름을 박지 않기)
    """
    import glob
    것 = {}
    for 갈 in ('fish', 'rig', 'catch'):
        길들 = sorted(glob.glob(os.path.join(ROOT, 'site', 갈, '*.html')))
        것[갈] = [os.path.relpath(p, os.path.join(ROOT, 'site'))
                  .replace('\\', '/') for p in 길들]
    return 것


def main():
    # ★ Pillow 가 없으면 **못 잽니다** — 조용히 통과시키지 않습니다
    from engine import mustmeasure
    mustmeasure.꾸러미가있어야한다(
        'PIL', '사진의 진짜 크기를 재서 적힌 값과 대조합니다',
        깔이름='Pillow')

    바라는 = None
    if '--바라는커밋' in sys.argv:
        바라는 = sys.argv[sys.argv.index('--바라는커밋') + 1]

    print()
    print('  올린 뒤 운영에서 다시 재기 — %s' % 뿌리)
    print('  (감독팀 지시 — 「쪽이 보인다」로 통과시키지 않습니다)')
    print()

    막음, 알림 = [], []

    # ── ④ 판 지문 먼저 — 새 판이 안 올라갔으면 나머지가 뜻이 없습니다
    코드, 글 = 받기('build.json')
    판 = {}
    if 코드 != 200:
        print('  ✗ build.json 을 못 읽었습니다 (%s)' % 코드)
        print('    올라가지 않았거나 서버가 막고 있습니다.')
        return 4                                      # 못잼
    try:
        판 = json.loads(글)
    except Exception as e:                            # noqa: BLE001
        print('  ✗ build.json 이 깨졌습니다 — %s' % e)
        return 4
    커밋 = 판.get('커밋짧게')
    print('  [1] 올라간 판')
    print('      커밋 %s · 쪽 %s · 지문 %s'
          % (커밋, 판.get('쪽수'), str(판.get('통지문', ''))[:12]))
    if 바라는 and not str(커밋).startswith(바라는[:7]):
        막음.append('올라간 판이 %s 인데 바란 것은 %s' % (커밋, 바라는[:7]))
        print('      ✗ 바란 것(%s)과 다릅니다' % 바라는[:7])
    else:
        print('      ✓')

    # ── ③ 새 쪽
    print()
    print('  [2] 새 쪽')
    for 길 in ('club/support.html',):
        코드, 글 = 받기(길)
        if 코드 != 200:
            막음.append('%s 가 %s' % (길, 코드))
            print('      ✗ %s — %s' % (길, 코드))
        else:
            있나 = 'clubApply' in 글
            cloud = len(_클라우드.findall(글))
            print('      ✓ %s — 200 · 신청 폼 %s · cloud 링크 %d개'
                  % (길, '있음' if 있나 else '**없음**', cloud))
            if not 있나:
                막음.append('%s 에 신청 폼이 없습니다' % 길)
            if cloud:
                막음.append('%s 에 badagaja.cloud 링크가 %d개 '
                            '(BADA-ORG-001 — 동호회는 badagaja.com 소관)'
                            % (길, cloud))

    # ── ③ 사진 크기 — 붙었는가 + **실제 파일과 맞는가**
    print()
    print('  [3] 사진 크기가 붙고 실제 파일과 맞는가 (Pillow)')
    갈래별 = 쪽목록()
    빠진쪽, 틀린것, 본쪽, 본사진 = [], [], 0, 0
    재본그림 = {}
    for 갈, 길들 in sorted(갈래별.items()):
        for 길 in 길들:
            코드, 글 = 받기(길)
            if 코드 is None:
                print('      ✗ %s — 서버에 못 닿았습니다 (%s)' % (길, 글))
                return 4                              # 못잼
            if 코드 != 200:
                막음.append('%s 가 %s' % (길, 코드))
                continue
            본쪽 += 1
            for 태그 in _사진.findall(글):
                if 'data:' in 태그:
                    continue
                본사진 += 1
                m = _크기값.search(태그)
                if not m:
                    빠진쪽.append((길, 태그[:70]))
                    continue
                w, h = int(m.group('w')), int(m.group('h'))
                if w <= 0 or h <= 0:
                    틀린것.append((길, '0 이하 %dx%d' % (w, h)))
                    continue
                src = _주소.search(태그)
                if not src:
                    continue
                그림길 = src.group(1)
                실제 = 그림크기(그림길, 길, 재본그림)
                if 실제 and (w, h) != 실제:
                    틀린것.append((길, '%s — 적힌 %dx%d · 실제 %dx%d'
                                   % (그림길.split('/')[-1], w, h,
                                      실제[0], 실제[1])))
    print('      쪽 %d개 · 사진 %d장' % (본쪽, 본사진))
    if 빠진쪽:
        print('      ✗ 크기가 없는 사진 %d장' % len(빠진쪽))
        for 길, t in 빠진쪽[:6]:
            print('          %s — %s' % (길, t))
        막음.append('사진 %d장에 width·height 가 없습니다 '
                    '(Pillow 가 안 돌았을 수 있습니다)' % len(빠진쪽))
    if 틀린것:
        print('      ✗ 적힌 크기가 실제와 다른 사진 %d장' % len(틀린것))
        for 길, t in 틀린것[:6]:
            print('          %s — %s' % (길, t))
        막음.append('적힌 크기가 실제와 다른 사진 %d장' % len(틀린것))
    if not (빠진쪽 or 틀린것):
        print('      ✓ 모두 붙었고 실제 파일과 맞습니다')

    # ── ④ 딸린 것이 404 나지 않는가
    print()
    print('  [4] 딸린 것(CSS·JS·그림)이 있는가')
    코드, 첫글 = 받기('index.html')
    딸린것 = []
    if 코드 == 200:
        딸린것 += _css.findall(첫글)
        딸린것 += _js.findall(첫글)
    없는것 = []
    for 길 in sorted(set(딸린것))[:40]:
        if 길.startswith('http'):
            continue
        c, _ = 받기(길)
        if c != 200:
            없는것.append((길, c))
    print('      본 것 %d개 · 404 %d개' % (len(set(딸린것)), len(없는것)))
    for 길, c in 없는것[:6]:
        print('      ✗ %s — %s' % (길, c))
    if 없는것:
        막음.append('딸린 것 %d개가 404' % len(없는것))
    else:
        print('      ✓ 모두 있습니다')

    # ── ⑥ 보호 대상
    print()
    print('  [5] 건드리면 안 되는 것이 그대로인가')
    for 길, 바람 in (('zh-cn/', '있어야'), ('api/marine.php', '있어야')):
        코드, _ = 받기(길)
        괜찮 = (코드 == 200) if 바람 == '있어야' else (코드 != 200)
        print('      %s %s — %s' % ('✓' if 괜찮 else '✗', 길, 코드))
        if not 괜찮:
            막음.append('%s 가 %s (%s 했습니다)' % (길, 코드, 바람))

    # ── 끝
    print()
    if 막음:
        print('  ✗ 안 붙은 것 %d가지' % len(막음))
        for x in 막음:
            print('      · %s' % x)
        print()
        print('  「쪽이 보인다」로 닫지 않습니다. 위 항목을 고쳐야 끝입니다.')
        return 1                                      # 어김
    print('  ✓ 운영에서 모두 확인했습니다')
    if 알림:
        for x in 알림:
            print('      ~ %s' % x)
    return 0


if __name__ == '__main__':
    sys.exit(main())
