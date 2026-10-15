# -*- coding: utf-8 -*-
"""받은 **부품 사진**을 자리에 넣습니다 (2026-10-15 주인 지시 사이클).

  주인 — 「낚시용품 빨리 하나씩 한페이지씩」

★ 왜 도구로 만드나
  26장을 한 장씩 넣습니다. 손으로 하면 **같은 실수를 26번**
  할 수 있습니다. 실제로 01 막대찌에서 한 번 틀렸습니다 —
  `site/img/` 에 두었는데 그곳은 `.gitignore` 가 무시하는
  **생성물 자리**라 저장소에 안 올라갑니다. 깨끗한 자리에서
  다시 만들면 그림만 사라집니다.
  그 교훈을 코드에 담아 **다음 25장은 안 틀리게** 합니다.

★ 하는 일
  ① 받은 PNG 를 읽어 **크기·순백 바탕**을 봅니다
  ② `data/img/rig/parts/<부품>.webp` 로 줄여 넣습니다
     — 표시 118px 의 2.7배인 **320px**. 레티나에서도 또렷합니다
  ③ **원본은 건드리지 않습니다** (받은 자리에 그대로)
  ④ 부품 이름이 **자료에 정말 있는지** 봅니다 — 없으면 멈춥니다
  ⑤ 이미 있으면 덮어쓰기 전에 **묻습니다**(`--덮기` 없으면 멈춤)
     [[dont-overwrite-existing-file]]

★ **그림 안은 못 봅니다.** 이름이 맞아도 다른 물건일 수 있습니다 —
  01~26 가운데 04 편대·15 면사매듭이 그랬습니다. 눈으로 보는
  일은 사람이 합니다 [[machine-check-is-not-design]].

쓰는 법
    python -m engine.adopt_part_image "G:/…/02_고리봉돌.png" 고리봉돌
    python -m engine.adopt_part_image "…/02_고리봉돌.png" 고리봉돌 --덮기
    python -m engine.adopt_part_image --목록          (무엇이 들어왔나)
"""
import argparse
import io
import json
import os
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
칸 = os.path.join(뿌리, 'data', 'img', 'rig', 'parts')
낼크기 = 320          # 표시 118px · 모바일 86px → 2.7배
품질 = 88


def 부품표():
    """부품 이름 → **영문 사진 이름**. 자료가 짝을 들고 있습니다.

    ★ 파일 이름을 **영문**으로 두는 까닭 (2026-10-15 총감독 결정)
      한글 파일 이름은 FTP 로 올릴 때 깨질 위험이 있습니다. 쪽에서는
      브라우저가 알아서 인코딩해 로컬에서는 잘 되지만, 서버로 가는
      길에 조용히 망가지면 **그림만 안 뜹니다.**
      짝은 `rigs.json` 의 「사진」 칸 **한 곳에만** 둡니다.
    """
    길 = os.path.join(뿌리, 'data', 'raw', 'rigs.json')
    d = json.load(io.open(길, encoding='utf-8'))['부품']
    return {k: (v.get('사진') or '') for k, v in d.items()}


def 부품들():
    return list(부품표().keys())


def 목록내기():
    것 = sorted(os.listdir(칸)) if os.path.isdir(칸) else []
    표 = 부품표()
    모두 = list(표.keys())
    파일들 = [os.path.splitext(x)[0] for x in 것 if x.endswith('.webp')]
    # 파일은 영문, 부품은 한글입니다 — 자료의 짝으로 맞댑니다
    든것 = [b for b in 모두 if 표.get(b) and 표[b] in 파일들]
    print('부품 사진이 들어온 자리 — %s' % os.path.relpath(칸, 뿌리))
    print('=' * 60)
    print('  자료의 부품 %d가지 · 사진이 온 것 %d가지'
          % (len(모두), len(든것)))
    print()
    for b in 모두:
        있 = b in 든것
        크 = ''
        if 있:
            p = os.path.join(칸, 표[b] + '.webp')
            크 = ' %-20s %.1fKB' % (표[b] + '.webp',
                                    os.path.getsize(p) / 1024.0)
        print('  %s %-14s%s' % ('✓' if 있 else '·', b, 크))
    쓴파일 = {표[b] for b in 든것}
    덤 = [x for x in 파일들 if x not in 쓴파일]
    if 덤:
        print()
        print('  ★ 자료에 없는 이름의 사진 %d장 — 쪽에 안 나옵니다' % len(덤))
        for x in 덤:
            print('      %s' % x)
    print('-' * 60)
    print('[한 줄 요약] 사진이 온 부품 %d / %d가지' % (len(든것), len(모두)))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument('원본', nargs='?')
    p.add_argument('부품', nargs='?')
    p.add_argument('--덮기', action='store_true')
    p.add_argument('--목록', action='store_true')
    a = p.parse_args()

    if a.목록 or not a.원본:
        return 목록내기()
    if not a.부품:
        print('★ 어느 부품인지 알려 주십시오 (두 번째 값)')
        return 1

    표 = 부품표()
    모두 = list(표.keys())
    if a.부품 not in 모두:
        print('★ 「%s」는 자료에 없는 부품입니다 — 넣어도 쪽에 안 나옵니다'
              % a.부품)
        가까운 = [b for b in 모두 if a.부품 in b or b in a.부품]
        if 가까운:
            print('   비슷한 것: %s' % ' · '.join(가까운))
        return 1

    if not os.path.isfile(a.원본):
        print('★ 받은 그림이 없습니다 — %s' % a.원본)
        return 1

    영 = 표.get(a.부품)
    if not 영:
        print('★ 「%s」에 사진 이름(영문)이 자료에 없습니다 — '
              'rigs.json 의 「사진」 칸을 먼저 채우십시오' % a.부품)
        return 1
    목적 = os.path.join(칸, '%s.webp' % 영)
    if os.path.isfile(목적) and not a.덮기:
        print('★ 이미 있습니다 — %s' % os.path.relpath(목적, 뿌리))
        print('   덮어쓰려면 --덮기 를 붙이십시오')
        return 1

    try:
        from PIL import Image
    except ImportError:
        print('★ Pillow 가 없어 못 바꿉니다 — 재지 못했습니다')
        return 4             # [[clean-python-has-no-packages]]

    im = Image.open(a.원본).convert('RGB')
    w, h = im.size
    귀 = [im.getpixel(xy) for xy in ((2, 2), (w - 3, 2),
                                     (2, h - 3), (w - 3, h - 3))]
    순백 = all(all(c >= 250 for c in px) for px in 귀)

    os.makedirs(칸, exist_ok=True)
    im.resize((낼크기, 낼크기), Image.LANCZOS).save(
        목적, 'WEBP', quality=품질, method=6)

    print('부품 사진을 넣었습니다 — %s (%s.webp)' % (a.부품, 영))
    print('  받은 것  %dx%d · %.0fKB'
          % (w, h, os.path.getsize(a.원본) / 1024.0))
    print('  넣은 것  %dx%d · %.1fKB  →  %s'
          % (낼크기, 낼크기, os.path.getsize(목적) / 1024.0,
             os.path.relpath(목적, 뿌리).replace('\\', '/')))
    print('  네 귀가 순백인가: %s' % ('예' if 순백 else '★ 아니오 — 봐 주십시오'))
    if w != h:
        print('  ★ 가로세로가 다릅니다(%dx%d) — 늘어나 보일 수 있습니다'
              % (w, h))
    print('  ★ 원본은 그대로 둡니다 — 덮지 않았습니다')
    print('  ★ 다음: python -m engine.build 로 쪽을 다시 만듭니다')
    print('  ★ **그림 안은 이 도구가 못 봅니다.** 이름이 맞아도 다른')
    print('    물건일 수 있습니다 — 눈으로 보아 주십시오')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
