# -*- coding: utf-8 -*-
"""중국어 번역 자료를 옛 사이트에서 옮겨 옵니다.

왜 이 도구가 필요한가
    옛 사이트는 중국어 낱말표를 zh-cn/i18n/ 에 잘 모아 두었습니다.
    어종 105가지, 일반 낱말 661개, 먹거리·명소 347개 — 사람이
    하나씩 고른 값입니다. **다시 만들 수 없습니다.**

    그런데 읽는 곳이 다섯 군데로 흩어져 있었습니다
    (build-zh-points.ps1 · build-zh-regions.ps1 · zh-coast.py …).
    새 틀에서는 **자료 한 곳**에 두고 build.py 만 읽습니다 (계약-11).

무엇을 옮기나
    species.json       어종 105가지 (중국 본토에서 부르는 이름)
    home-data.json     지형·일반 낱말 661개
    point.json         등급·방법·시즌·경고
    point-words.json   방법·시즌 문장
    region.json        먹거리·명소 설명 347개
    village-exp.json   어촌 체험 이름
    rules.json         금어기 쪽 문구
    coast-zh.json      묶음·권역 이름과 교통

    제주 전용(jeju-*.json)·축제(festival-live.json)·요금 감시
    (price-watch.json)·사진(spot-images.json)은 **안 옮깁니다.**
    새 틀에 아직 그 쪽이 없습니다. 생기면 그때 옮깁니다.

★ 옮기기만 하고 **번역하지 않습니다.**
    없는 낱말을 지어내면 틀린 중국어가 조용히 섞입니다.
    없으면 없다고 두고, check_i18n.py 가 얼마나 비었는지 알려 줍니다.

쓰는 법
    python engine/migrate_zh.py            보여만 줍니다
    python engine/migrate_zh.py --write    data/raw/zh.json 에 씁니다
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 옛 파일 → 새 자료의 칸 이름
옮길것 = [
    ('species.json', '어종'),
    ('home-data.json', '낱말'),
    ('point.json', '포인트'),
    ('point-words.json', '포인트문장'),
    ('region.json', '권역낱말'),
    ('village-exp.json', '어촌체험'),
    ('rules.json', '금어기'),
    ('coast-zh.json', '묶음'),
]


def 설명빼기(x):
    """_설명 같은 메모는 자료에 안 넣습니다 (주인 규칙 11).

    근거·메모는 data-private/ 에 두고 웹에 내지 않습니다.
    여기 남겨 두면 ads-data 처럼 밖으로 나갈 수 있습니다.
    """
    if isinstance(x, dict):
        return dict((k, 설명빼기(v)) for k, v in x.items()
                    if not k.startswith('_'))
    if isinstance(x, list):
        return [설명빼기(v) for v in x]
    return x


def 세기(x):
    if isinstance(x, dict):
        return sum(세기(v) for v in x.values()) or len(x)
    if isinstance(x, list):
        return len(x)
    return 1


def main():
    쓰기 = '--write' in sys.argv
    바탕 = os.path.join(OLD, 'zh-cn', 'i18n')
    if not os.path.isdir(바탕):
        print('옛 사이트의 번역 자료를 못 찾았습니다: %s' % 바탕)
        return 1

    print('중국어 번역 자료를 옮깁니다')
    print('  옛 자리: %s' % 바탕)
    print('')

    나옴 = {}
    탈 = []
    for 파일, 칸 in 옮길것:
        p = os.path.join(바탕, 파일)
        if not os.path.exists(p):
            탈.append('%s 가 없습니다' % 파일)
            continue
        d = io.read_json(p, default=None)
        if d is None:
            탈.append('%s 를 못 읽었습니다' % 파일)
            continue
        깨끗 = 설명빼기(d)
        나옴[칸] = 깨끗
        print('  %-20s → %-10s 낱말 %d개' % (파일, 칸, 세기(깨끗)))

    print('')
    if 탈:
        print('★ 살펴볼 것 %d건' % len(탈))
        for x in 탈:
            print('    %s' % x)
        print('')

    # 어종은 자주 쓰므로 간단한 표도 함께 만듭니다 (한국어 → 중국어)
    어종표 = {}
    for 이름, v in (나옴.get('어종') or {}).items():
        if isinstance(v, dict) and v.get('cn'):
            어종표[이름] = v['cn']
    print('  어종 한국어 → 중국어 %d가지' % len(어종표))
    보기 = list(어종표.items())[:4]
    for k, v in 보기:
        print('      %-14s %s' % (k, v))
    print('')

    if not 쓰기:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
        return 0

    io.write_json(os.path.join(DATA, 'raw', 'zh.json'), {
        '_설명': '중국어 낱말표. 옛 사이트 zh-cn/i18n/ 에서 옮겼습니다. '
                 '사람이 하나씩 고른 값이라 다시 만들 수 없습니다',
        '_옮긴곳': 'zh-cn/i18n/ (파일 %d개)' % len(나옴),
        '_고칠때': '새 낱말은 여기 더합니다. 지어내지 말고 확인한 것만 적습니다',
        '어종표': 어종표,
        '표': 나옴,
    })
    print('자료에 썼습니다: data/raw/zh.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
