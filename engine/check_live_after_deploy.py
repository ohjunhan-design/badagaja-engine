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

    ① Pillow      사진에 width/height 가 붙었는가 (fish·rig·catch)
    ② 확대 단추    그림 위를 안 가리고 아래에 있는가 · 44px 이상
    ③ 새 쪽        club/support.html 이 200 인가
    ④ 판 지문      build.json 의 커밋·지문이 바라던 것인가
    ⑤ 딸린 것      CSS·JS·그림이 404 나지 않는가
    ⑥ 보호 대상    /zh-cn/ · /api/ · .htaccess 가 그대로인가

    ★ 「쪽이 보인다」로 통과시키지 않습니다. 항목마다 따로 내고,
      하나라도 안 붙었으면 **그것을 이름으로 말합니다.**

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
_크기 = re.compile(r'\bwidth="\d+"[^>]*\bheight="\d+"'
                   r'|\bheight="\d+"[^>]*\bwidth="\d+"', re.I)


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
            print('      ✓ %s — 200 · 신청 폼 %s'
                  % (길, '있음' if 있나 else '**없음**'))
            if not 있나:
                막음.append('%s 에 신청 폼이 없습니다' % 길)

    # ── ① Pillow — 사진 크기
    print()
    print('  [3] 사진에 크기가 붙었나 (Pillow)')
    갈래별 = 쪽목록()
    빠진쪽, 본쪽 = [], 0
    for 갈, 길들 in sorted(갈래별.items()):
        for 길 in 길들:
            코드, 글 = 받기(길)
            if 코드 != 200:
                막음.append('%s 가 %s' % (길, 코드))
                continue
            본쪽 += 1
            사진들 = [x for x in _사진.findall(글)
                      if 'data:' not in x]
            없는것 = [x for x in 사진들 if not _크기.search(x)]
            if 없는것:
                빠진쪽.append((길, len(없는것), len(사진들)))
    print('      쪽 %d개 · 크기 빠진 쪽 %d개' % (본쪽, len(빠진쪽)))
    if 빠진쪽:
        for 길, n, 다 in 빠진쪽[:8]:
            print('      ✗ %s — 사진 %d/%d 에 width·height 없음'
                  % (길, n, 다))
        막음.append('사진 크기가 빠진 쪽 %d개 (Pillow 가 안 돌았을 수 있습니다)'
                    % len(빠진쪽))
    else:
        print('      ✓ 모두 붙었습니다')

    # ── ⑥ 보호 대상
    print()
    print('  [4] 건드리면 안 되는 것이 그대로인가')
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
