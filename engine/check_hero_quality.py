# -*- coding: utf-8 -*-
"""권역 **대표 사진 품질**을 세 단계로 나눕니다 (2026-10-02).

★ 왜 만들었나
  바깥 검수 — 「전국 적용 후에는 모든 57개를 같은 사진/텍스트
  조건이라고 생각하면 안 됩니다. 긴 지역명, 사진 비율, 포인트 수,
  어종 수, 금어기 문장 길이가 달라집니다」

  「사진 품질 점검 목록도 같이 만들어 주세요. 57권역을
  **좋음 / 보통 / 교체 필요** 세 단계로만 분류하면 됩니다.
  교체 필요 사진은 **클로드가 생성하지 말고** 저에게 넘기세요」

★ 제가 **그림의 아름다움을 재지 않습니다.** 그건 사람 눈의 일입니다
  (주인 규칙 6-2). 여기서는 **기계가 잴 수 있는 것**만 봅니다 —

    · 사진이 **있는가**                     없으면 교체 필요
    · 가로세로 비율                         히어로는 가로가 길어야 합니다
    · 그림 크기(픽셀)                       작으면 늘려 흐려집니다
    · 파일 크기                             너무 작으면 뭉개진 그림
    · 촬영자가 적혀 있는가                   주인 규칙 5

★ 흐릿함·구도·바다다움은 **지피티가 봅니다.** 저는 목록만 냅니다.

쓰는 법
  python engine/check_hero_quality.py          # 표
  python engine/check_hero_quality.py --목록   # 교체 필요만
"""
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

막음, 알림 = [], []        # 계약-21 — 모듈 수준에 둡니다

# 히어로에 **알맞은 비율** — 사진 안에 글자를 얹으므로 가로가 길어야
# 합니다. 세로로 긴 사진은 글자가 하늘이나 바다를 가립니다.
좋은비 = (1.3, 2.4)        # 가로/세로
작은폭 = 1000              # 이보다 좁으면 PC 에서 늘려 흐려집니다
작은파일 = 60 * 1024       # 60KB 밑이면 뭉개졌을 가능성


def 재기():
    from engine.data import 자료
    d = 자료()
    끝 = []
    for r in d.권역들:
        권역 = r['id']
        이름 = r['이름'].get('ko') if isinstance(r['이름'], dict) else r['이름']
        사진 = d.히어로(권역) or {}
        파일 = 사진.get('파일')
        # ★ 시험이 **딴 자리를 대고** 돌릴 수 있어야 합니다 (계약-28).
        #   진짜 site/ 를 건드리지 않고 사본으로 망가뜨려 봅니다.
        사이트뿌리 = os.environ.get('BADAGAJA_SITE') or os.path.join(여기, 'site')
        길 = os.path.join(사이트뿌리, 파일) if 파일 else None
        한 = {'권역': 권역, '이름': 이름, '파일': 파일 or '',
              '촬영자': 사진.get('촬영자') or '', '탈': []}
        if not 파일:
            한['등급'] = '교체 필요'
            한['탈'].append('대표 사진이 없습니다')
            끝.append(한); continue
        if not (길 and os.path.isfile(길)):
            한['등급'] = '교체 필요'
            한['탈'].append('파일이 그 자리에 없습니다')
            끝.append(한); continue

        크기 = os.path.getsize(길)
        한['파일크기'] = 크기
        try:
            from PIL import Image
            with Image.open(길) as im:
                w, h = im.size
        except Exception:                      # noqa: BLE001
            w = h = 0
        한['가로'], 한['세로'] = w, h
        비 = (w / h) if h else 0
        한['비율'] = round(비, 2)

        if not 한['촬영자']:
            한['탈'].append('촬영자가 안 적혀 있습니다')
        if w and w < 작은폭:
            한['탈'].append('가로 %dpx — %d 보다 좁아 늘리면 흐려집니다'
                            % (w, 작은폭))
        if 비 and 비 < 좋은비[0]:
            한['탈'].append('세로로 깁니다 (%.2f) — 글자가 사진을 가립니다'
                            % 비)
        if 비 and 비 > 좋은비[1]:
            한['탈'].append('너무 납작합니다 (%.2f)' % 비)
        if 크기 < 작은파일:
            한['탈'].append('%dKB — 뭉개졌을 수 있습니다' % (크기 // 1024))

        한['등급'] = ('좋음' if not 한['탈']
                      else ('교체 필요' if len(한['탈']) >= 2 else '보통'))
        끝.append(한)
    return 끝


def main():
    목록만 = '--목록' in sys.argv
    것들 = 재기()
    셈 = {'좋음': 0, '보통': 0, '교체 필요': 0}
    for x in 것들:
        셈[x['등급']] = 셈.get(x['등급'], 0) + 1

    if not 목록만:
        print()
        print('  권역 대표 사진 — %d곳' % len(것들))
        print('  좋음 %d · 보통 %d · 교체 필요 %d'
              % (셈['좋음'], 셈['보통'], 셈['교체 필요']))
        print()
        print('  %-12s %-10s %-9s %8s  %s'
              % ('권역', '이름', '등급', '크기', '본 것'))
        print('  ' + '-' * 76)
        차례 = {'교체 필요': 0, '보통': 1, '좋음': 2}
        for x in sorted(것들, key=lambda v: (차례[v['등급']], v['권역'])):
            크 = ('%dx%d' % (x.get('가로', 0), x.get('세로', 0))
                  if x.get('가로') else '—')
            print('  %-12s %-10s %-9s %8s  %s'
                  % (x['권역'], x['이름'][:9], x['등급'], 크,
                     ' · '.join(x['탈']) or '이상 없음'))
        print()

    # 교체 필요 목록은 **따로 파일로** — 바깥 검수에 넘길 것입니다
    바꿀것 = [x for x in 것들 if x['등급'] == '교체 필요']
    낼 = os.path.join(여기, 'docs', '사진-교체필요.json')
    from engine import io as _io
    _io.write(낼, json.dumps(
        {'잰날': '2026-10-02', '모두': len(것들), '셈': 셈,
         '교체필요': 바꿀것}, ensure_ascii=False, indent=1))
    print('  교체 필요 %d곳 → docs/사진-교체필요.json' % len(바꿀것))
    print('  ★ 교체 사진은 **제가 만들지 않습니다.** 바깥 검수에 넘깁니다')

    # ── 등급 가르기 (계약-21) ──────────────────────────────
    #
    # ★ **막는 것** — 대표 사진이 아예 없거나 파일이 그 자리에 없는 곳.
    #   권역 쪽에 사진이 빠지면 배포를 막습니다 (주인 규칙 6-1).
    #
    # ★ **알리는 것** — 좁거나 뭉개졌거나 세로로 긴 것.
    #   손님이 보기에 아쉬울 뿐 쪽이 깨지지는 않고, 고치는 일(새 사진)은
    #   제 손에 있지 않습니다. 목록만 내고 사람이 정합니다.
    for x in 것들:
        없음 = [t for t in x['탈']
                if '없습니다' in t or '자리에 없' in t]
        if 없음:
            막음.append('%s — %s' % (x['이름'], 없음[0]))
        elif x['등급'] == '교체 필요':
            알림.append('%s — %s' % (x['이름'], ' · '.join(x['탈'])))

    print('')
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:10]:
            print('  ✗ %s' % t)
        print('  **권역 쪽에는 대표 사진이 반드시 들어갑니다** (주인 규칙 6-1)')
        return 1
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:10]:
            print('  ! %s' % t)
    else:
        print('  사진이 다 있고 쓸 만합니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
