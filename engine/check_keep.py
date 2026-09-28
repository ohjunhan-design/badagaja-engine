# -*- coding: utf-8 -*-
"""바꿀 때 **지우면 안 되는 것**이 지켜지는지 봅니다. (계약-18)

★ 왜 이 검사가 필요한가 (2026-09-27)

    중국어판 190쪽은 그대로 두기로 했습니다(주인 결정).
    그런데 「쪽을 그대로 둔다」는 것으로는 모자랍니다.

        중국어 쪽 182곳이 옛 css/style.css 를 씁니다.
        새 틀은 그 파일을 안 만듭니다 (assets/css/site.css 를 씁니다).

    한국어 쪽을 새것으로 바꾸면서 옛 css 를 지우면,
    **중국어판 190쪽의 디자인이 통째로 깨집니다.**
    쪽은 그대로 있는데 글자만 남은 화면이 됩니다.

    「그대로 둔다」는 그 쪽이 **쓰는 것까지** 둔다는 뜻입니다.

무엇을 보나
    1. 옛 중국어 쪽이 거는 링크가 전환 뒤에도 살아 있는가
    2. 새로 잰 값이 자료(keep.json)에 적은 것과 맞는가
       — 자료가 낡으면 검사가 헛돕니다
    3. 새 틀이 만드는 것과 남길 것이 겹치지 않는가

★ 이 도구는 **읽기만 합니다** (계약-09)

쓰는 법
    python engine/check_keep.py
    python engine/check_keep.py --strict
"""
import os
import re
import sys
import glob
import posixpath
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []


def 있는것(뿌리):
    나옴 = set()
    for p in glob.glob(os.path.join(뿌리, '**', '*'), recursive=True):
        if os.path.isfile(p):
            나옴.add(os.path.relpath(p, 뿌리).replace(os.sep, '/'))
    return 나옴


def 중국어가쓰는것():
    """옛 중국어 쪽이 **중국어 폴더 밖**으로 거는 링크를 셉니다."""
    옛것 = 있는것(OLD)
    쪽들 = sorted(glob.glob(os.path.join(OLD, 'zh-cn', '**', '*.html'),
                            recursive=True))
    셈 = collections.Counter()
    어디서 = {}
    for p in 쪽들:
        여기 = os.path.relpath(p, OLD).replace(os.sep, '/')
        s = io.read(p, default='')
        for m in re.finditer(
                r'href="(?!https?:|mailto:|tel:|#|//|data:|javascript:)'
                r'([^"#?]*)', s):
            길 = m.group(1).strip()
            if not 길:
                continue
            간곳 = posixpath.normpath(
                posixpath.join(posixpath.dirname(여기), 길))
            if 길.endswith('/') or 길 in ('.', './'):
                간곳 = posixpath.join(간곳.rstrip('/.'),
                                      'index.html').lstrip('/')
            elif 간곳 not in 옛것 and (간곳 + '/index.html') in 옛것:
                간곳 = 간곳 + '/index.html'
            if 간곳.startswith('zh-cn/'):
                continue
            셈[간곳] += 1
            어디서.setdefault(간곳, 여기)
    return 셈, 어디서, len(쪽들)


def 남기기로한것(d):
    """keep.json 의 「남길것」. 폴더는 / 로 끝냅니다."""
    return list((d.get('남길것') or {}).items())


def 덮이나(길, 남길것):
    for 자리, _ in 남길것:
        if 자리.endswith('/'):
            if 길.startswith(자리):
                return 자리
        elif 길 == 자리:
            return 자리
    return None


def main():
    자료 = io.꼭읽기json(os.path.join(DATA, 'raw', 'keep.json'))
    if not 자료:
        print('data/raw/keep.json 이 없습니다 — 무엇을 남길지 적어 두세요.')
        return 1

    남길것 = 남기기로한것(자료)
    print('바꿀 때 지우면 안 되는 것 (계약-18)')
    print('  남기기로 한 것 %d갈래' % len(남길것))
    print('')

    셈, 어디서, 쪽수 = 중국어가쓰는것()
    새것 = 있는것(NEW)

    # ── 1. 중국어 쪽이 거는 링크가 전환 뒤에도 사는가
    print('[1] 옛 중국어 쪽 %d개가 거는 링크' % 쪽수)
    print('      중국어 폴더 밖으로 %d갈래' % len(셈))
    산것, 지켜진것, 죽은것 = [], [], []
    for 간곳, 수 in 셈.items():
        if 간곳 in 새것:
            산것.append((간곳, 수))
        elif 덮이나(간곳, 남길것):
            지켜진것.append((간곳, 수))
        else:
            죽은것.append((간곳, 수))
    print('      새 틀이 그대로 만듦      %4d갈래' % len(산것))
    print('      남기기로 적어 둠        %4d갈래' % len(지켜진것))
    print('      갈 곳이 없음           %4d갈래' % len(죽은것))
    if 죽은것:
        죽은것.sort(key=lambda x: -x[1])
        막음.append('중국어 쪽이 쓰는데 남기지도 만들지도 않는 것 %d갈래'
                    % len(죽은것))
        print('  ✗ 중국어판이 쓰는데 사라질 것 %d갈래' % len(죽은것))
        for 간곳, 수 in 죽은것[:8]:
            print('      %-42s %4d곳   보기: %s'
                  % (간곳, 수, 어디서.get(간곳, '?')))
        print('      → data/raw/keep.json 의 「남길것」에 적거나,')
        print('        새 틀이 만들도록 하세요.')
    else:
        print('  · 중국어판이 쓰는 것이 모두 살아남습니다')
    print('')

    # ── 2. 자료에 적은 값이 지금 잰 값과 맞는가
    print('[2] 자료에 적은 값이 지금과 맞는가')
    적은것 = dict((k, v) for k, v in
                  (자료.get('중국어가쓰는것') or {}).items()
                  if not k.startswith('_'))
    지금것 = dict((k, v) for k, v in 셈.items() if k not in 새것)
    어긋 = []
    for k, v in sorted(적은것.items()):
        if 지금것.get(k) != v:
            어긋.append('%s — 적은 값 %s · 지금 %s'
                        % (k, v, 지금것.get(k, '없음')))
    for k in sorted(지금것):
        if k not in 적은것:
            어긋.append('%s — 새로 생겼는데 자료에 없습니다 (%d곳)'
                        % (k, 지금것[k]))
    print('      자료에 적은 것 %d갈래 · 지금 잰 것 %d갈래'
          % (len(적은것), len(지금것)))
    if 어긋:
        알림.append('자료에 적은 값이 %d갈래 어긋납니다' % len(어긋))
        print('  ~ 자료가 낡았습니다 %d건' % len(어긋))
        for x in 어긋[:5]:
            print('      %s' % x)
        print('      → keep.json 의 「중국어가쓰는것」을 고쳐 주세요.')
        print('        (막지는 않습니다 — 값이 달라도 [1] 이 진짜 검사입니다)')
    else:
        print('  · 자료가 지금과 같습니다')
    print('')

    # ── 3. 새 틀이 만드는 것과 남길 것이 겹치나
    print('[3] 새 틀이 만드는 것과 남길 것이 겹치나')
    겹침 = []
    for 길 in sorted(새것):
        자리 = 덮이나(길, 남길것)
        if 자리 and not 자리.endswith('/'):
            겹침.append('%s (남길 것으로도 적혀 있습니다)' % 길)
    if 겹침:
        알림.append('새 틀이 만드는데 남길 것으로도 적힌 것 %d개' % len(겹침))
        print('  ~ %d개 — 새 틀이 덮어씁니다' % len(겹침))
        for x in 겹침[:4]:
            print('      %s' % x)
    else:
        print('  · 겹치지 않습니다')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 「쪽을 그대로 둔다」는 그 쪽이 **쓰는 것까지** 둔다는 뜻입니다.')
        return 1 if '--strict' in sys.argv else 0
    print('바꿔도 중국어판이 멀쩡합니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
