# -*- coding: utf-8 -*-
"""어종 쪽이 **최신 채비 자산**을 가리키는가 (2026-10-08).

★ 왜 만드나 — 주인이 잡으셨습니다

    「**새로운 채비사진이 있는데 왜 구형을 사용하려는거야?**」

  `data/img/rig/` 에 새 채비 사진 32장(16종 × PC·모바일)이 있고
  `/rig/` 16쪽은 그것을 씁니다. 그런데 **어종 쪽 18개는 하나도
  안 쓰고** 옛 SVG 채비도를 그리고 있었습니다.

  저는 어종 쪽끼리만 견주어 「같은 생성기에서 나오니 구버전
  혼용 0」이라 결론냈고, 그 뒤 **구버전 SVG 의 글자 겹침을
  정성껏 고치고** 있었습니다. 기준을 절반만 적용한 탓입니다.

★ 바깥 검수가 정한 **판정 기준**

    「파일명이나 만든 날짜만으로 구버전을 판정하지 마세요.
      최신 기준은 **현재 /rig/ 에서 실제 서비스 중인 채비 체계와,
      그 채비를 만드는 현재 generator/data 를 SSOT** 로 봅니다」
    판정 우선순위 —
      현재 /rig/ 서비스 내용 > 현재 generator/data > 파일명·날짜

★ 보는 것 **다섯** (바깥 검수가 적어 준 그대로)

    ① 어종의 `rig_id` 가 **실제 있는** 채비인가
    ② PC 사진이 그 `rig_id` 의 공식 자산인가
    ③ 모바일 사진이 그 `rig_id` 의 공식 자산인가
    ④ 「채비 자세히」 링크가 **같은 `rig_id`** 의 `/rig/` 쪽인가
    ⑤ 옛 SVG 채비도 참조가 남아 있지 않은가

  곁들여 「크게 보기」가 있는지도 봅니다 — 바깥 검수가
  「hover 전용 금지·늘 보이게」로 못박은 단추입니다.

쓰는 법
    python engine/check_rigref.py
    python engine/check_rigref.py --strict
"""
import io as _io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io, rigref    # noqa: E402

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

막음, 알림 = [], []                 # 계약-21

# 옛 SVG 채비도의 자취 — 이것이 어종 쪽에 남아 있으면 구버전입니다
옛자취 = ('class="rig-fig"', 'rig-part-label', '채비도-svg')


def 카드들(글):
    return re.findall(r'<section class="fish-rig"[^>]*>.*?</section>',
                      글, re.S)


def main():
    엄격 = '--strict' in sys.argv
    from engine.data import 자료
    d = 자료()
    채비자료 = d.채비자료

    본쪽 = 0
    카드있는쪽 = 0
    쓰인채비 = {}

    for 길 in io.쪽들(NEW):
        짧 = os.path.relpath(길, NEW).replace(os.sep, '/')
        if '/fish/' not in ('/' + 짧):
            continue
        try:
            글 = _io.open(길, encoding='utf-8', errors='replace').read()
        except OSError:
            continue
        본쪽 += 1

        # ── ⑤ 옛 SVG 채비도가 남았는가
        for 자취 in 옛자취:
            if 자취 in 글:
                막음.append('%s — 옛 채비도 자취가 남았습니다 (%s)'
                            % (짧, 자취))

        것들 = 카드들(글)
        if not 것들:
            # 채비가 없는 어종도 있습니다(해루질 갈래). 막지 않고 셉니다.
            continue
        카드있는쪽 += 1
        for 카드 in 것들:
            m = re.search(r'data-rig="([^"]+)"', 카드)
            rid = m.group(1) if m else ''
            쓰인채비[rid] = 쓰인채비.get(rid, 0) + 1

            # ── ① 그 채비가 실제 있는가
            참 = rigref.채비(rid, 채비자료)
            if not 참:
                막음.append('%s — 모르는 채비입니다 (%s)' % (짧, rid or '빈값'))
                continue

            # ── ②③ PC·모바일 사진이 그 채비의 공식 자산인가
            pc = re.search(r'<img[^>]+src="([^"]+)"', 카드)
            mo = re.search(r'<source[^>]+srcset="([^"]+)"', 카드)
            for 무엇, 찾은, 참값 in (('PC', pc, 참['PC사진']),
                                     ('모바일', mo, 참['모바일사진'])):
                if not 찾은:
                    막음.append('%s — %s 사진이 없습니다 (%s)'
                                % (짧, 무엇, rid))
                    continue
                끝 = 찾은.group(1).split('/')[-1]
                if 끝 != 참값.split('/')[-1]:
                    막음.append(
                        '%s — %s 사진이 다른 채비를 가리킵니다'
                        ' (%s ↔ %s)' % (짧, 무엇, 끝, 참값.split('/')[-1]))

            # ── ④ 「자세히」 링크가 같은 채비인가
            링 = re.search(r'class="rig-go-btn" href="([^"]+)"', 카드)
            if not 링:
                막음.append('%s — 채비 자세히 링크가 없습니다 (%s)'
                            % (짧, rid))
            else:
                끝 = 링.group(1).split('/')[-1].split('?')[0]
                바름 = 참['상세'].split('/')[-1]
                if 끝 != 바름:
                    막음.append(
                        '%s — 사진과 링크가 **다른 채비**입니다'
                        ' (사진 %s · 링크 %s)' % (짧, rid, 끝))

            # ── 곁들여: 「크게 보기」
            if 'class="rig-zoom"' not in 카드:
                막음.append('%s — 「크게 보기」가 없습니다 (%s)'
                            % (짧, rid))

    print()
    print('  어종 쪽이 최신 채비 자산을 가리키는가')
    print()
    print('  어종 쪽 %d개 · 추천 채비 카드가 있는 쪽 %d개 · 쓰인 채비 %d갈래'
          % (본쪽, 카드있는쪽, len(쓰인채비)))
    if 쓰인채비:
        차례 = sorted(쓰인채비.items(), key=lambda t: (-t[1], t[0]))
        print('    %s' % ' · '.join('%s %d' % (k, v) for k, v in 차례[:8]))
    if not 본쪽:
        print()
        print('  □ 어종 쪽을 하나도 못 찾았습니다 — 못 쟀습니다')
        return 4 if 엄격 else 0
    if not 카드있는쪽:
        print()
        print('  ✗ **추천 채비 카드가 한 쪽에도 없습니다.**')
        print('    어종 쪽이 새 채비 사진을 안 쓰고 있습니다.')
        return 1

    print()
    if 막음:
        print('  손볼 곳 %d가지' % len(막음))
        for t in 막음[:12]:
            print('  ✗ %s' % t)
        if len(막음) > 12:
            print('  … 그 밖 %d가지' % (len(막음) - 12))
        print()
        print('  **자산은 `engine/rigref.py` 한 곳에서만 받습니다.**')
        print('  rig_id 하나가 PC 사진·모바일 사진·상세 주소를 모두')
        print('  정합니다. 두 곳에서 따로 지으면 반드시 어긋납니다.')
        return 1
    if 알림:
        print('  살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for t in 알림[:6]:
            print('  ! %s' % t)
    print('  · 채비·PC 사진·모바일 사진·상세 링크가 모두 같은 채비를')
    print('    가리키고, 옛 채비도 자취가 없습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
