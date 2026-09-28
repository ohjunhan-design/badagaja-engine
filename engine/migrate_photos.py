# -*- coding: utf-8 -*-
"""옛 사이트의 사진 자료를 새 틀로 옮깁니다.

★ 왜 생겼나 (2026-09-27 주인 지시 「사진 넣어야해」)

    새 틀로 만든 416쪽에 **사진이 한 장도 없었습니다.**
    옛 사이트는 500장을 씁니다. 바다 사이트에서 바다 사진이
    없으면 첫인상이 통째로 달라집니다.

    게다가 `build.py` 가 대표 사진 주소를 **자료를 안 보고
    지어내고** 있었습니다.

        build.py 가 만든 것   img/taean/hero.jpg        ← 없는 파일
        실제 파일             img/coast/taean-hero.jpg  ← 있는 파일

    그래서 공유 미리보기(og:image) 52갈래가 깨져 있었습니다.
    카톡·네이버로 나눠도 그림이 안 떴을 것입니다.

무엇을 옮기나
    옛 저장소 data/ 의 네 갈래를 한 파일로 모읍니다.

        coast-photos.json        충남·전북·전남 등 해안 권역
        jeju-photos.json         제주
        jeju-spot-photos.json    제주 명소
        species-photos.json      어종

★ **파일이 실제로 있는 것만** 옮깁니다
    자료에 적혀 있어도 파일이 없으면 안 옮깁니다. 없는 사진을
    가리키면 깨진 그림이 나옵니다. 적힌 것과 있는 것은 다릅니다.

★ 촬영자·이용허락은 **자료에 적힌 값 그대로** 옮깁니다 (주인 규칙 5)
    한 글자도 고치거나 채워 넣지 않습니다. 빈 칸은 빈 칸으로 둡니다.

★ 두 번 돌려도 결과가 같아야 합니다 (계약-18)
    차례를 정해 놓고 씁니다.

쓰는 법
    python engine/migrate_photos.py            무엇이 옮겨질지 봅니다
    python engine/migrate_photos.py --write    data/raw/photos.json 을 씁니다
"""
import os
import sys
import json
import datetime
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

OLD = os.environ.get('BADAGAJA_OLD', r'D:\바다가자\badagaja-site')
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

갈래들 = [
    ('data/coast-photos.json', '해안 권역'),
    ('data/jeju-photos.json', '제주'),
    ('data/jeju-spot-photos.json', '제주 명소'),
    ('data/species-photos.json', '어종'),
]

# 자료에서 그대로 가져오는 칸들 — 새 이름으로 옮겨 적습니다
#
# ★ 갈래마다 칸 이름이 다릅니다 (2026-09-27 에 겪었습니다)
#     해안·제주   use · region · spot · title · credit
#     어종        section · slug · name · sci · author · note
#
#   처음에는 'credit' 만 보다가 어종 사진 35장의 촬영자를 모두
#   빈 칸으로 만들었습니다. 규칙 5(촬영자는 자료가 준 값만 적는다)를
#   지키려다 **있는 값을 버리는** 셈이었습니다. 둘 다 봅니다.
칸옮김 = [
    (('use',), '쓰임'),
    (('region', 'section'), '권역'),
    (('spot', 'slug'), '명소'),
    (('title', 'name'), '제목'),
    (('file',), '파일'),
    (('credit', 'author'), '촬영자'),
    (('license',), '이용허락'),
    (('page',), '출처주소'),
    (('sci',), '학명'),
    (('note',), '메모'),
]

def 그림크기(길):
    """사진의 가로·세로. 파일 앞부분만 읽어 잽니다.

    못 재면 (None, None) 입니다 — **짐작해 적지 않습니다.**
    """
    try:
        with open(길, 'rb') as f:
            앞 = f.read(32)
            if 앞[:8] == b'\x89PNG\r\n\x1a\n':
                return (int.from_bytes(앞[16:20], 'big'),
                        int.from_bytes(앞[20:24], 'big'))
            if 앞[:2] == b'\xff\xd8':          # JPEG
                f.seek(2)
                while True:
                    표 = f.read(1)
                    if not 표:
                        return (None, None)
                    if 표 != b'\xff':
                        continue
                    종류 = f.read(1)
                    while 종류 == b'\xff':
                        종류 = f.read(1)
                    if not 종류:
                        return (None, None)
                    n = 종류[0]
                    # 크기가 적혀 있는 토막들 (SOF0~SOF15, 일부 제외)
                    if 0xC0 <= n <= 0xCF and n not in (0xC4, 0xC8, 0xCC):
                        f.read(3)               # 길이 2 + 정밀도 1
                        높 = int.from_bytes(f.read(2), 'big')
                        넓 = int.from_bytes(f.read(2), 'big')
                        return (넓, 높)
                    길이 = int.from_bytes(f.read(2), 'big')
                    if 길이 < 2:
                        return (None, None)
                    f.seek(길이 - 2, 1)
            if 앞[:4] == b'RIFF' and 앞[8:12] == b'WEBP':
                f.seek(0)
                온것 = f.read(40)
                if 온것[12:16] == b'VP8X':
                    넓 = int.from_bytes(온것[24:27], 'little') + 1
                    높 = int.from_bytes(온것[27:30], 'little') + 1
                    return (넓, 높)
                return (None, None)
    except OSError:
        pass
    return (None, None)


막음, 알림 = [], []


def 모으기():
    """네 갈래를 모읍니다. **파일이 있는 것만** 남깁니다."""
    나옴 = []
    잰것 = []
    for 상대, 이름 in 갈래들:
        p = os.path.join(OLD, 상대.replace('/', os.sep))
        if not os.path.isfile(p):
            알림.append('%s 가 없습니다' % 상대)
            잰것.append((이름, 상대, 0, 0))
            continue
        d = io.read_json(p, default=None)
        것들 = d.get('items') if isinstance(d, dict) and 'items' in d else d
        if isinstance(것들, dict):
            것들 = list(것들.values())
        것들 = [x for x in (것들 or []) if isinstance(x, dict)]
        살아있는것 = 0
        for x in 것들:
            파일 = x.get('file')
            if not 파일:
                continue
            실제 = os.path.join(OLD, 파일.replace('/', os.sep))
            if not os.path.isfile(실제):
                continue        # 적혀 있어도 파일이 없으면 안 옮깁니다
            한장 = {}
            for 옛칸들, 새칸 in 칸옮김:
                for 옛칸 in 옛칸들:
                    값 = x.get(옛칸)
                    if 값 not in (None, ''):
                        한장[새칸] = 값
                        break
            한장['크기'] = os.path.getsize(실제)
            넓, 높 = 그림크기(실제)
            if 넓 and 높:
                한장['가로'] = 넓
                한장['세로'] = 높
            나옴.append(한장)
            살아있는것 += 1
        잰것.append((이름, 상대, len(것들), 살아있는것))
    # 차례를 못 박습니다 — 두 번 돌려도 같아야 합니다 (계약-18)
    나옴.sort(key=lambda x: (x.get('파일', ''), x.get('쓰임', '')))
    return 나옴, 잰것


def main():
    쓰기 = '--write' in sys.argv
    사진들, 잰것 = 모으기()

    print('옛 사이트 사진을 새 틀로 옮기기 (주인 지시 2026-09-27)')
    print('  옛 저장소  %s' % OLD)
    print('')

    print('[1] 네 갈래에서 무엇이 나왔나')
    print('  %-12s %-30s %6s %6s' % ('갈래', '파일', '적힌것', '있는것'))
    print('  ' + '─' * 60)
    for 이름, 상대, 적힌, 있는 in 잰것:
        표 = '·' if 적힌 == 있는 else '~'
        print('  %s %-10s %-30s %6d %6d' % (표, 이름, 상대, 적힌, 있는))
    print('  ' + '─' * 60)
    print('  %-12s %-30s %6d %6d'
          % ('합계', '', sum(x[2] for x in 잰것),
             sum(x[3] for x in 잰것)))
    빠진것 = sum(x[2] for x in 잰것) - sum(x[3] for x in 잰것)
    if 빠진것:
        알림.append('자료에 적혔지만 파일이 없는 사진 %d장' % 빠진것)
        print('  ~ 적혔지만 파일이 없는 것 %d장 — 안 옮깁니다' % 빠진것)
    print('')

    # ── 2. 대표 사진이 권역마다 있는가
    print('[2] 대표 사진(히어로)이 권역마다 있는가')
    히어로 = [x for x in 사진들
              if str(x.get('쓰임', '')).startswith('hero')]
    권역별 = collections.defaultdict(list)
    for x in 히어로:
        if x.get('권역'):
            권역별[x['권역']].append(x)
    from engine import data as _data
    try:
        d = _data.자료()
        필요한권역 = [x['id'] for x in d.권역들]
    except Exception:          # noqa: BLE001  자료를 못 읽어도 나머지는 봅니다
        필요한권역 = []
        알림.append('권역 자료를 못 읽었습니다')
    print('      대표 사진 %d장 · 권역 %d곳' % (len(히어로), len(권역별)))
    if 필요한권역:
        없는권역 = [x for x in 필요한권역 if x not in 권역별]
        print('      새 틀 권역 %d곳 · 대표 사진이 없는 곳 %d곳'
              % (len(필요한권역), len(없는권역)))
        if 없는권역:
            막음.append('대표 사진이 없는 권역 %d곳' % len(없는권역))
            print('  ✗ %s' % ' · '.join(없는권역[:8]))
        else:
            print('  · 모든 권역에 대표 사진이 있습니다')
    print('')

    # ── 3. 이용허락이 적혀 있는가 (주인 규칙 5)
    print('[3] 촬영자·이용허락이 적혀 있는가 (주인 규칙 5)')
    촬영자없음 = [x for x in 사진들 if not x.get('촬영자')]
    허락없음 = [x for x in 사진들 if not x.get('이용허락')]
    print('      촬영자가 빈 것 %d장 · 이용허락이 빈 것 %d장'
          % (len(촬영자없음), len(허락없음)))
    if 촬영자없음 or 허락없음:
        알림.append('촬영자·이용허락이 빈 사진이 있습니다')
        for x in (촬영자없음 + 허락없음)[:5]:
            print('      ~ %s' % x.get('파일'))
        print('      ★ 빈 칸은 **빈 칸으로 둡니다.** 지어내지 않습니다.')
    else:
        print('  · 모두 적혀 있습니다')
    print('')

    # ── 3.5 가로·세로를 쟀는가 (계약-14 · 주인 규칙 28)
    print('[3.5] 사진 크기를 쟀는가')
    못잰것 = [x for x in 사진들 if not (x.get('가로') and x.get('세로'))]
    print('      잰 것 %d장 · 못 잰 것 %d장'
          % (len(사진들) - len(못잰것), len(못잰것)))
    if 못잰것:
        알림.append('가로·세로를 못 잰 사진 %d장' % len(못잰것))
        for x in 못잰것[:5]:
            print('      ~ %s' % x.get('파일'))
    # og:image 로 쓰는 대표 사진은 가이드를 지켜야 합니다
    나쁜비율 = []
    for x in 히어로:
        넓, 높 = x.get('가로'), x.get('세로')
        if not (넓 and 높):
            continue
        if 넓 < 150 or 높 < 150:
            나쁜비율.append('%s — %dx%d (150 보다 작습니다)'
                            % (x.get('파일'), 넓, 높))
        elif 넓 / float(높) > 3 or 높 / float(넓) > 3:
            나쁜비율.append('%s — %dx%d (3:1 을 넘습니다)'
                            % (x.get('파일'), 넓, 높))
    if 나쁜비율:
        막음.append('og:image 가이드를 어기는 대표 사진 %d장' % len(나쁜비율))
        print('  ✗ og:image 가이드를 어기는 것 %d장' % len(나쁜비율))
        for x in 나쁜비율[:5]:
            print('      %s' % x)
    else:
        print('  · 대표 사진이 모두 150px 넘고 3:1 안입니다 (주인 규칙 28)')
    print('')

    # ── 4. 이용허락 갈래
    print('[4] 이용허락 갈래')
    갈 = collections.Counter(x.get('이용허락', '(없음)') for x in 사진들)
    for k, v in 갈.most_common():
        print('      %-22s %4d장' % (k, v))
    print('      ★ 쪽에는 촬영자만 적습니다. 이용허락 종류는')
    print('        photos.html 에만 둡니다 (주인 규칙 6).')
    print('')

    if 쓰기:
        나갈파일 = os.path.join(DATA, 'raw', 'photos.json')
        io.write_json(나갈파일, {
            '_설명': ('옛 사이트에서 옮겨 온 사진 자료. '
                      'engine/migrate_photos.py --write 가 만듭니다 — '
                      '손으로 고치지 마세요'),
            '_왜': ('2026-09-27 주인 지시. 새 틀 416쪽에 사진이 한 장도 '
                    '없었고, build.py 가 대표 사진 주소를 자료를 안 보고 '
                    '지어내 og:image 52갈래가 깨져 있었습니다'),
            '_규칙': [
                '파일이 실제로 있는 것만 옮깁니다',
                '촬영자·이용허락은 자료에 적힌 값 그대로입니다 (주인 규칙 5)',
                '쪽에는 촬영자만 적고 이용허락 종류는 photos.html 에만 (규칙 6)',
                '인물 단체사진은 쓰지 않습니다 (규칙 2)',
                '대표 사진은 바다가 주제인 사진이어야 합니다 (규칙 3)',
            ],
            '_옮긴날': datetime.date.today().isoformat(),
            '_어디서': [x[1] for x in 갈래들],
            '사진': 사진들,
        })
        print('썼습니다: data/raw/photos.json (%d장)' % len(사진들))
        print('')

    if 알림:
        print('살펴볼 것 %d가지' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        return 1 if '--strict' in sys.argv else 0
    print('사진 %d장을 옮길 수 있습니다 (대표 사진 %d권역).'
          % (len(사진들), len(권역별)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
