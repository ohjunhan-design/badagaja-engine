# -*- coding: utf-8 -*-
"""남기기로 한 옛 쪽마다 **최종 주소·canonical·내부 링크**를 재어 적습니다.

★ 왜 생겼나 (2026-09-27 바깥 검수 3차·4차)

      「keep.json 11개와 아직 안 만든 12개는 반드시
        왜 유지하는가 / 최종 URL / canonical / 내부 링크 여부 /
        검색 노출 의도를 기록해두는 걸 권합니다」

      (4차) 「왜 유지하는가·최종 URL·canonical·내부 링크는 지금,
             검색 노출 의도는 배포 후에 해도 됩니다」

    까닭이 있습니다. 옛 쪽을 서버에 그대로 남기면, 같은 주제의
    새 쪽이 나중에 생겼을 때 **둘이 함께 검색에 잡힙니다.**
    그때 어느 쪽이 대표인지 정해 두지 않으면 서로 깎아먹습니다.

★ 적는 것이 아니라 **재는** 것입니다 (주인 규칙 29)
    canonical 은 옛 쪽 파일에서 읽습니다. 내부 링크는 새 쪽 416개와
    옛 중국어 쪽 190개를 뒤져 셉니다. 손으로 적으면 반드시 틀립니다.

쓰는 법
    python engine/keep_detail.py            재어 보여 줍니다
    python engine/keep_detail.py --write    keep.json 에 적습니다
"""
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))
뿌리주소 = 'https://badagaja.com'

막음, 알림 = [], []


def 옛쪽의canonical(길):
    """옛 파일이 스스로 밝힌 대표 주소. 없으면 None — **지어내지 않습니다.**"""
    p = os.path.join(OLD, 길.replace('/', os.sep))
    if not os.path.isfile(p):
        return None
    s = io.read(p, default='')
    m = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', s, re.I)
    if not m:
        return None
    m2 = re.search(r'href=["\']([^"\']+)["\']', m.group(0), re.I)
    return m2.group(1) if m2 else None


def 최종주소(길):
    """그 쪽이 실제로 살 주소. index.html 은 폴더 주소로 넘어갑니다."""
    if 길.endswith('/'):
        return 뿌리주소 + '/' + 길
    if 길.endswith('/index.html'):
        return 뿌리주소 + '/' + 길[:-len('index.html')]
    if 길 == 'index.html':
        return 뿌리주소 + '/'
    return 뿌리주소 + '/' + 길


def 가리키는쪽세기(길):
    """그 쪽을 가리키는 쪽이 몇인가 — 새 틀과 옛 중국어판을 따로 셉니다."""
    이름 = 길.rstrip('/')
    새것, 옛중국어 = 0, 0
    꼴 = re.compile(r'(?:href|src)=["\'][^"\']*' + re.escape(이름))
    for p in glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True):
        if 꼴.search(io.read(p, default='')):
            새것 += 1
    zh = os.path.join(OLD, 'zh-cn')
    if os.path.isdir(zh):
        for p in glob.glob(os.path.join(zh, '**', '*.html'), recursive=True):
            if 꼴.search(io.read(p, default='')):
                옛중국어 += 1
    return 새것, 옛중국어


def main():
    쓰기 = '--write' in sys.argv
    표 = io.read_json(os.path.join(DATA, 'raw', 'keep.json'), default=None)
    if not 표:
        print('keep.json 이 없습니다')
        return 1
    남길것 = 표.get('남길것') or {}
    넘김표 = io.꼭읽기json(os.path.join(DATA, 'raw', 'url-map.json')) or {}
    아직 = (넘김표.get('아직_안_만듦') or {}).get('쪽') or []

    볼것 = [x for x in 남길것 if not x.startswith('_')]
    볼것 += [x for x in 아직 if x not in 볼것]
    볼것 = sorted(볼것)

    print('남기는 옛 쪽마다 — 최종 주소 · canonical · 내부 링크')
    print('  (바깥 검수 3차·4차 지시. 재서 적습니다 — 손으로 안 적습니다)')
    print('')

    잰것 = {}
    쪽인것 = [x for x in 볼것 if x.endswith('.html')]
    폴더인것 = [x for x in 볼것 if not x.endswith('.html')]

    print('  %-42s %-5s %-5s %s' % ('옛 쪽', '새틀', '중국어', 'canonical'))
    print('  ' + '─' * 84)
    canonical없음 = []
    for 길 in 쪽인것:
        c = 옛쪽의canonical(길)
        새것, 옛중국어 = 가리키는쪽세기(길)
        잰것[길] = {
            '최종주소': 최종주소(길),
            'canonical': c or '(쪽에 안 적혀 있습니다)',
            '가리키는_새쪽': 새것,
            '가리키는_옛중국어쪽': 옛중국어,
        }
        if not c:
            canonical없음.append(길)
        print('  %-42s %5d %5d  %s'
              % (길, 새것, 옛중국어, (c or '✗ 없음')[:34]))
    print('')

    if 폴더인것:
        print('  폴더·설정 (쪽이 아니라 canonical 이 없는 것이 맞습니다)')
        for 길 in 폴더인것:
            새것, 옛중국어 = 가리키는쪽세기(길)
            잰것[길] = {
                '최종주소': 최종주소(길),
                'canonical': '(쪽이 아닙니다)',
                '가리키는_새쪽': 새것,
                '가리키는_옛중국어쪽': 옛중국어,
            }
            print('      %-38s 새틀 %d · 중국어 %d' % (길, 새것, 옛중국어))
        print('')

    # ── canonical 이 없는 쪽 — 나중에 새 쪽이 생기면 겹칩니다
    print('[1] canonical 이 적혀 있는가')
    if canonical없음:
        알림.append('canonical 이 없는 옛 쪽 %d개' % len(canonical없음))
        print('  ~ %d개 — 지금은 새 쪽이 없어 겹치지 않습니다.' % len(canonical없음))
        print('    그러나 **새 틀로 같은 쪽을 만들면 그때 겹칩니다.**')
        print('    만들 때 옛 쪽에 새 주소를 가리키는 canonical 을 넣거나,')
        print('    301 로 넘겨야 합니다.')
        for x in canonical없음[:8]:
            print('      %s' % x)
    else:
        print('  · 모두 적혀 있습니다')
    print('')

    # ── 새 틀이 가리키는데 아직 안 만든 쪽 — 옛것이 받아 줍니다
    print('[2] 새 틀이 가리키는데 아직 안 만든 쪽')
    가리켜지는것 = [(k, v) for k, v in 잰것.items()
                    if v['가리키는_새쪽'] > 0 and k in 아직]
    if 가리켜지는것:
        print('  %d개 — 옛 쪽이 서버에 남아 404 는 안 납니다' % len(가리켜지는것))
        for k, v in sorted(가리켜지는것):
            print('      %-30s 새 틀 %d쪽이 가리킴 → %s'
                  % (k, v['가리키는_새쪽'], v['최종주소']))
        print('      ★ 이것은 **일부러 그렇게 한 것**입니다.')
        print('        새 틀로 만들면 url-map.json 의 「아직_안_만듦」과')
        print('        keep.json 에서 함께 빼야 합니다.')
    else:
        print('  · 없습니다')
    print('')

    if 쓰기:
        표['잰것'] = {
            '_설명': ('남기는 옛 쪽마다 최종 주소·canonical·내부 링크 수. '
                      'engine/keep_detail.py --write 가 재서 적습니다 — '
                      '손으로 고치지 마세요 (주인 규칙 29)'),
            '_왜': ('바깥 검수 3차·4차 — 옛 쪽을 남기면 나중에 같은 주제의 '
                    '새 쪽이 생겼을 때 둘이 함께 검색에 잡힙니다. '
                    '그때 어느 쪽이 대표인지 미리 정해 둡니다'),
            '_검색노출의도': ('배포 뒤에 채웁니다 (4차 검수 판단). '
                              '먼저 서버에서 실제로 어떻게 잡히는지 보고 정합니다'),
            '쪽': 잰것,
        }
        io.write_json(os.path.join(DATA, 'raw', 'keep.json'), 표)
        print('keep.json 에 적었습니다 (%d쪽)' % len(잰것))
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
        return 1 if '--strict' in sys.argv else 0
    print('남기는 옛 쪽 %d개를 모두 재어 적었습니다.' % len(잰것))
    return 0


if __name__ == '__main__':
    sys.exit(main())
