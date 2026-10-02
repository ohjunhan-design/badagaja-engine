# -*- coding: utf-8 -*-
"""**새 채비 그림을 받아 자리에 넣습니다** (2026-10-02).

★ 왜 만드나
  바깥 검수(지피티)가 채비 그림을 한 장씩 만들어 저장소에 올립니다.
  들어온 그림마다 ① 자리가 맞는지 ② 크기가 다른 그림과 어울리는지
  ③ 쪽이 거는 이름과 같은지를 **손으로 보면 빠뜨립니다.**

★ 쓰는 법
      python engine/adopt_rig_image.py bottom
      python engine/adopt_rig_image.py --all

  `data/img/rig/` 에 있는 새 그림을 보고
    · png 로 올라왔으면 **webp 로 바꿉니다** (쪽이 webp 를 겁니다)
    · 가로세로를 재어 다른 그림과 견줍니다
    · PC·모바일 짝이 맞는지 봅니다
    · `rigs.json` 의 「그림값」 칸이 비었으면 알려 줍니다

★ 그림 **안의 글자는 못 읽습니다.** 그것은 검사기가 아니라
  `rigs.json` 의 「그림값」 칸이 맡습니다 (check_rig_images [4]).
"""
import io
import json
import os
import struct
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
칸 = os.path.join(뿌리, 'data', 'img', 'rig')


def 말(s=''):
    print(s)


def _크기(길):
    """webp·png 의 가로세로. 바깥 꾸러미 없이 머리만 읽습니다."""
    try:
        with io.open(길, 'rb') as f:
            b = f.read(40)
    except OSError:
        return None, None
    if b[:8] == b'\x89PNG\r\n\x1a\n':
        return struct.unpack('>II', b[16:24])
    if b[:4] == b'RIFF' and b[8:12] == b'WEBP':
        꼴 = b[12:16]
        if 꼴 == b'VP8X':
            return (int.from_bytes(b[24:27], 'little') + 1,
                    int.from_bytes(b[27:30], 'little') + 1)
        if 꼴 == b'VP8 ':
            return (struct.unpack('<H', b[26:28])[0] & 0x3fff,
                    struct.unpack('<H', b[28:30])[0] & 0x3fff)
        if 꼴 == b'VP8L':
            n = int.from_bytes(b[21:25], 'little')
            return ((n & 0x3fff) + 1, ((n >> 14) & 0x3fff) + 1)
    return None, None


def _webp로(png길):
    """png 를 webp 로 바꿉니다. Pillow 가 없으면 건너뜁니다."""
    try:
        from PIL import Image
    except ImportError:
        return None, 'Pillow 가 없습니다 (pip install pillow)'
    webp길 = os.path.splitext(png길)[0] + '.webp'
    try:
        with Image.open(png길) as im:
            im.save(webp길, 'WEBP', quality=88, method=6)
    except Exception as e:
        return None, str(e)[:60]
    return webp길, None


def _자료():
    길 = os.path.join(뿌리, 'data', 'raw', 'rigs.json')
    with io.open(길, encoding='utf-8') as f:
        return json.load(f)


def 보기(열쇠, 채비):
    """채비 하나의 그림 두 장을 보고 손봅니다."""
    이름 = (채비.get(열쇠) or {}).get('이름') or 열쇠
    말()
    말('  %s (%s)' % (열쇠, 이름))
    탈 = 0
    for 꼬리, 무엇 in (('', 'PC'), ('-m', '모바일')):
        webp = os.path.join(칸, '%s%s.webp' % (열쇠, 꼬리))
        png = os.path.join(칸, '%s%s.png' % (열쇠, 꼬리))
        길 = None
        if os.path.exists(webp):
            길 = webp
        elif os.path.exists(png):
            말('      %s — png 로 왔습니다. webp 로 바꿉니다' % 무엇)
            새, 탈말 = _webp로(png)
            if 새:
                길 = 새
                말('          %s 로 바꿨습니다 (%d KB)'
                   % (os.path.basename(새), os.path.getsize(새) // 1024))
            else:
                말('      ✗ %s — 못 바꿨습니다: %s' % (무엇, 탈말))
                탈 += 1
                continue
        if not 길:
            말('      ✗ %s 그림이 없습니다' % 무엇)
            탈 += 1
            continue
        w, h = _크기(길)
        크 = os.path.getsize(길) // 1024
        모양 = ''
        if w and h:
            세로냐 = (h > w)
            맞냐 = (세로냐 == (꼬리 == '-m'))
            모양 = '%dx%d %s' % (w, h, '세로' if 세로냐 else '가로')
            if not 맞냐:
                모양 += '  ✗ **방향이 뒤집혔습니다**'
                탈 += 1
        말('      · %-5s %-24s %4d KB' % (무엇, 모양, 크))
        if 크 > 500:
            말('          ~ 500KB 가 넘습니다. 다른 그림은 250~400KB 입니다')
    if not (채비.get(열쇠) or {}).get('그림값'):
        말('      ~ rigs.json 에 「그림값」이 비었습니다 —'
           ' 그림에 적은 대상·미끼를 적어 두면')
        말('        자료가 바뀔 때 판정이 낡은 그림을 잡습니다')
    return 탈


def main():
    것 = _자료().get('채비') or {}
    인자 = [x for x in sys.argv[1:] if not x.startswith('--')]
    모두 = '--all' in sys.argv
    볼것 = sorted(것) if 모두 or not 인자 else 인자
    말()
    말('  새 채비 그림을 받습니다 — %s' % 칸)
    탈 = 0
    for k in 볼것:
        if k not in 것:
            말('  ✗ %s — rigs.json 에 없는 채비입니다' % k)
            탈 += 1
            continue
        탈 += 보기(k, 것)
    말()
    if 탈:
        말('  ✗ 손봐야 할 것 %d가지' % 탈)
        return 1
    말('  · 모두 제자리에 있습니다')
    말('    이제 `python engine/build.py` 로 쪽에 겁니다.')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
