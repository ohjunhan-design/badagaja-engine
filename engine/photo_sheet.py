# -*- coding: utf-8 -*-
"""명소 사진을 **한 장에 모아** 눈으로 훑게 합니다 (2026-10-09)

★ 왜 이것을 만드나

  여행 쪽에서 「대천해수욕장」 사진을 찾았습니다 — 화면의 3분의 2가
  스카이바이크 철골이고 바다는 귀퉁이에만 있었습니다.
  자료에는 제목이 「대천해수욕장」으로 **정확히** 적혀 있습니다.
  한국관광공사가 붙인 이름입니다. **이름으로는 못 가립니다.**

  색으로 가려 보려고 검사기를 만들었다가 **버렸습니다.**
  61장이 걸렸는데 대부분 어종 사진과 노을 사진이었고, 정작
  문제의 대천 사진은 **안 걸렸습니다**(하늘이 넓어서).
  구별하지 못하는 검사는 두지 않습니다.

  주인 규칙 6-2 그대로입니다 — **기계가 재는 것과 사람이 보는
  것은 다릅니다.** 이것은 가리는 도구가 아니라 **보여 드리는
  도구**입니다. 사진을 모아 한 장으로 붙이면 주인이 한눈에
  훑어 「이건 아니다」를 고르실 수 있습니다.

쓰는 법 — `python engine/photo_sheet.py [쓰임] [한줄개수]`
  쓰임은 자료의 `쓰임` 값(spot·hero·species 등), 없으면 spot.
"""
import io
import json
import os
import sys

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
sys.path.insert(0, 여기)

import mustmeasure   # noqa: E402

칸폭, 칸높 = 260, 190       # 한 칸 크기
글높 = 26                   # 이름을 적을 띠


def main():
    mustmeasure.꾸러미가있어야한다(
        'PIL', '사진을 모아 한 장으로 붙입니다.', 깔이름='Pillow')
    from PIL import Image, ImageDraw, ImageFont

    쓰임 = sys.argv[1] if len(sys.argv) > 1 else 'spot'
    한줄 = int(sys.argv[2]) if len(sys.argv) > 2 else 6

    자료길 = os.path.join(뿌리, 'data', 'raw', 'photos.json')
    자료 = json.load(io.open(자료길, encoding='utf-8'))
    모두 = 자료.get('사진') if isinstance(자료, dict) else 자료
    것들 = [x for x in 모두 if (x.get('쓰임') or '') == 쓰임]
    mustmeasure.있어야한다(
        것들, '「%s」 사진' % 쓰임, 최소=5, 어디=자료길)

    글꼴 = None
    for 후보 in (r'C:\Windows\Fonts\malgun.ttf',
                 r'C:\Windows\Fonts\MALGUN.TTF'):
        if os.path.exists(후보):
            글꼴 = ImageFont.truetype(후보, 13)
            break

    줄수 = (len(것들) + 한줄 - 1) // 한줄
    장 = Image.new('RGB', (한줄 * 칸폭, 줄수 * (칸높 + 글높)), '#ffffff')
    그리개 = ImageDraw.Draw(장)

    붙임, 못읽음 = 0, []
    for i, x in enumerate(것들):
        쪽길 = x.get('파일') or ''
        실길 = os.path.join(뿌리, 'site', *쪽길.split('/'))
        if not os.path.exists(실길):
            실길 = os.path.join(뿌리, *쪽길.split('/'))
        칸x = (i % 한줄) * 칸폭
        칸y = (i // 한줄) * (칸높 + 글높)
        try:
            with Image.open(실길) as im:
                im = im.convert('RGB')
                비 = max(칸폭 / im.width, 칸높 / im.height)
                im = im.resize((max(1, int(im.width * 비)),
                                max(1, int(im.height * 비))))
                왼 = max(0, (im.width - 칸폭) // 2)
                위 = max(0, (im.height - 칸높) // 2)
                장.paste(im.crop((왼, 위, 왼 + 칸폭, 위 + 칸높)),
                         (칸x, 칸y))
            붙임 += 1
        except Exception:                             # noqa: BLE001
            못읽음.append(쪽길)
            그리개.rectangle([칸x, 칸y, 칸x + 칸폭, 칸y + 칸높],
                           fill='#eeeeee')
        이름 = (x.get('명소') or x.get('제목') or '?')[:18]
        그리개.rectangle([칸x, 칸y + 칸높, 칸x + 칸폭, 칸y + 칸높 + 글높],
                       fill='#1b3a33')
        그리개.text((칸x + 6, 칸y + 칸높 + 6), 이름,
                  fill='#ffffff', font=글꼴)
        그리개.rectangle([칸x, 칸y, 칸x + 칸폭 - 1, 칸y + 칸높 + 글높 - 1],
                       outline='#ffffff', width=2)

    mustmeasure.있어야한다(range(붙임), '붙인 사진', 최소=5, 어디=자료길)

    낼곳 = os.path.join(뿌리, 'docs', '사진-%s-대조표.jpg' % 쓰임)
    os.makedirs(os.path.dirname(낼곳), exist_ok=True)
    장.save(낼곳, 'JPEG', quality=88)
    print()
    print('  「%s」 사진 %d장을 한 장에 붙였습니다 (%d줄 × %d칸)'
          % (쓰임, 붙임, 줄수, 한줄))
    if 못읽음:
        print('  못 읽은 것 %d장' % len(못읽음))
    print('  → %s' % os.path.relpath(낼곳, 뿌리))
    print()
    print('  ★ 이름으로는 못 가립니다 — 「대천해수욕장」이라 적힌')
    print('    사진이 스카이바이크 철골이었습니다. 눈으로 봅니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
