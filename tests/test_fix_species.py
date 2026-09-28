# -*- coding: utf-8 -*-
"""어종 아이디 도구가 몇 번을 돌려도 안전한지 봅니다.  (계약-26)

왜 이 시험이 있나
    2026-09-26 — fix_species.py 를 두 번 돌렸더니 자료가 망가졌습니다.
      1회차: '감성돔' → 'gamseongdom'        (맞음)
      2회차: 'gamseongdom' 을 **새 어종 이름**으로 읽고 'etc-001' 을 덧씌움
      그 뒤 쓰기 루프는 그마저 못 찾아 대상을 통째로 비웠습니다

    개수(104가지·13,250건)는 두 번 다 같았습니다. **수가 맞아도 내용은 틀릴 수
    있습니다.** 그래서 수가 아니라 값 자체를 견줍니다.

쓰는 법
    python tests/test_fix_species.py
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

통과, 실패 = 0, []


def 봄(이름, 참인가, 덧붙임=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s %s' % (이름, 덧붙임))


def 자료찍기(폴더):
    """포인트 파일들의 알맹이를 한 덩이로 — 값끼리 견주려고"""
    나옴 = {}
    바닥 = os.path.join(폴더, 'points')
    for f in sorted(os.listdir(바닥)):
        나옴[f] = io.read(os.path.join(바닥, f))
    s = os.path.join(폴더, 'species.json')
    if os.path.exists(s):
        나옴['species.json'] = io.read(s)
    return 나옴


def 돌리기(일터):
    """일터의 자료로 fix_species.py --write 를 한 번.

    BADAGAJA_DATA 로 자리를 옮깁니다 — 시험이 진짜 자료를 덮어쓰면 안 됩니다.
    """
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_DATA'] = os.path.join(일터, 'data')
    return subprocess.run(
        [sys.executable, os.path.join(ROOT, 'engine', 'fix_species.py'), '--write'],
        env=환경, capture_output=True, text=True, encoding='utf-8')


def main():
    print('어종 아이디 도구 시험')
    print('')

    바탕 = os.path.join(ROOT, 'data', 'raw', 'points')
    if not os.path.isdir(바탕):
        print('  자료가 아직 없습니다 — migrate.py 를 먼저 돌리세요')
        return 0

    일터 = tempfile.mkdtemp(prefix='species-test-')
    try:
        # 지금 자료를 그대로 베껴 시험합니다 (진짜 자료는 안 건드립니다)
        shutil.copytree(os.path.join(ROOT, 'data', 'raw'),
                        os.path.join(일터, 'data', 'raw'))
        # 이 도구는 자기가 이미 붙인 아이디를 되돌릴 줄 알아야 합니다.
        # 그것을 보려면 species.json 이 있는 채로 시작합니다.

        한번 = 돌리기(일터)
        봄('한 번 돌면 끝난다', 한번.returncode == 0, 한번.stderr[-200:])
        첫판 = 자료찍기(os.path.join(일터, 'data', 'raw'))

        두번 = 돌리기(일터)
        봄('두 번째도 끝난다', 두번.returncode == 0, 두번.stderr[-200:])
        둘째판 = 자료찍기(os.path.join(일터, 'data', 'raw'))

        다른것 = [k for k in 첫판 if 첫판[k] != 둘째판.get(k)]
        봄('두 번 돌려도 자료가 똑같다 (계약-26)', not 다른것, ' · '.join(다른것[:3]))

        # 대상이 비어 버리지 않았는가 — 옛 사고가 이렇게 났습니다
        빈것 = 0
        있는것 = 0
        for f in sorted(os.listdir(os.path.join(일터, 'data', 'raw', 'points'))):
            d = io.read_json(os.path.join(일터, 'data', 'raw', 'points', f), default={})
            for x in d.get('포인트', []):
                if x.get('대상'):
                    있는것 += 1
                else:
                    빈것 += 1
        봄('대상이 통째로 비지 않았다', 있는것 > 2000, '대상 있는 곳 %d' % 있는것)

        # etc-001 같은 순번 아이디가 남아 있으면 안 됩니다
        sp = io.read_json(os.path.join(일터, 'data', 'raw', 'species.json'), default={})
        순번 = [x['id'] for x in sp.get('어종', []) if x['id'].startswith('etc-')]
        봄('순번 아이디가 없다', not 순번, ' · '.join(순번[:3]))

        # 어종 이름이 한글인가 — 아이디를 이름 자리에 넣은 것이 그때 사고였습니다
        로마자 = [x['id'] for x in sp.get('어종', [])
                  if (x.get('이름') or {}).get('ko', '').isascii()]
        봄('어종 이름이 한글이다', not 로마자, ' · '.join(로마자[:3]))

        # 포인트가 가리키는 아이디가 실제로 있는가
        있는아이디 = set(x['id'] for x in sp.get('어종', []))
        끊김 = []
        for f in sorted(os.listdir(os.path.join(일터, 'data', 'raw', 'points'))):
            d = io.read_json(os.path.join(일터, 'data', 'raw', 'points', f), default={})
            for x in d.get('포인트', []):
                for s in (x.get('대상') or []):
                    if s not in 있는아이디:
                        끊김.append('%s → %s' % (x['id'], s))
        봄('없는 어종을 가리키지 않는다', not 끊김, ' · '.join(끊김[:3]))
    finally:
        shutil.rmtree(일터, ignore_errors=True)

    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패: %s' % (통과, len(실패), ' · '.join(실패)))
        return 1
    print('%d가지 모두 통과했습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
