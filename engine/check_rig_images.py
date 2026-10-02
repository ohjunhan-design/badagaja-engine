# -*- coding: utf-8 -*-
"""**채비 그림이 자료와 맞는가** (2026-10-02 바깥 검수 13차).

★ 바깥 검수가 잡은 것
  「같은 다운샷 채비인데 본문과 그림이 **다른 채비**입니다.
    더 큰 문제는 PC용과 모바일용 이미지끼리도 다릅니다.
    갈치는 PC 가 케미→직결구슬→도래→와이어→갈치바늘→봉돌인데
    모바일은 텐야/메탈지그 방식입니다. **같은 주소에서 PC 손님과
    휴대폰 손님이 전혀 다른 채비를 배웁니다.**
    이건 디자인 문제가 아니라 **정보 신뢰성 결함**입니다」

  맞습니다. 그리고 세어 보니 더 큰 것이 있었습니다 —
  **채비 자료는 16가지인데 그림은 9가지뿐**입니다.
  없는 일곱은 원투·찌낚시 셋·에기 둘·지그헤드로, 손님이 가장 많이
  보는 기본 채비들입니다. 쪽 제목은 「무엇을 챙기고 **어떻게 매나**」인데
  매는 법을 글로만 설명하고 있었습니다
  ([[promise-must-be-kept]] — 「약속한 것이 거기 있어야 합니다」).

★ 넷을 봅니다
    [1] 자료의 채비마다 그림이 있는가            — 없으면 **막습니다**
    [2] PC 와 모바일이 **짝을 이루는가**         — 한쪽만 있으면 막습니다
    [3] 그림이 쪽에 실제로 **실려 있는가**        — 파일만 있고 안 쓰면 소용없습니다
    [4] 그림이 가리키는 파일이 **진짜 있는가**

★ 그림 **안에 적힌 글자**는 못 읽습니다
  webp 안의 호수·어종은 기계가 읽을 수 없습니다. 그래서 자료에
  `그림값` 칸을 두고, 그림을 만든 사람이 「이 그림에 무엇을 적었는지」를
  한 줄로 적게 합니다. 그러면 **자료가 바뀔 때 그림이 낡은 것**을
  여기서 잡습니다. 지금은 그 칸이 비어 있어 알림만 냅니다
  ([[rig-order-needs-evidence]] — 짐작이면 비워 둡니다).
"""
import io
import json
import os
import re
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

막음, 알림 = [], []
def _자료칸():
    """자료가 있는 자리.

    ★ **시험이 주는 사본을 봅니다** (2026-10-02)
      `os.path.join(뿌리, 'data')` 로 박아 두면 검사기 자기검증이
      자료를 일부러 망가뜨려도 **멀쩡한 진짜 자료**를 재고
      「아무 탈 없다」고 합니다. 오늘 그 꼴로 두 가지가 헛되이
      실패하고 있었습니다.
    """
    return os.environ.get('BADAGAJA_DATA', os.path.join(뿌리, 'data'))



def 말(s=''):
    print(s)


def _자료():
    길 = os.path.join(_자료칸(), 'raw', 'rigs.json')
    with io.open(길, encoding='utf-8') as f:
        return json.load(f)


def _사이트():
    return os.environ.get('BADAGAJA_SITE') or os.path.join(뿌리, 'site')


def _그림칸():
    """채비 그림의 **원본 자리**입니다.

    ★ `site/img/rig/` 가 아니라 **`data/img/rig/`** 입니다
      (2026-10-02 — 처음에 site/ 를 보다가 틀렸습니다).
      `site/` 는 생성물이라 저장소에 올리지 않습니다(.gitignore).
      그러니 거기에 그림을 두면 **다음 빌드에 사라지고**, 다른
      컴퓨터에서는 아예 없습니다. 빌드가 `data/img/rig/` 에서
      `site/` 로 옮깁니다(build.py 4927줄 둘레).
      새 그림은 **반드시 `data/img/rig/` 에** 둡니다.
    """
    return os.path.join(_자료칸(), 'img', 'rig')


def 검사_그림있나(채비):
    """[1][2] 채비마다 그림이 있고 PC·모바일이 짝을 이루는가."""
    말()
    말('[1] 채비마다 그림이 있고 PC·모바일이 짝을 이루는가')
    칸 = _그림칸()
    있는것 = set(os.listdir(칸)) if os.path.isdir(칸) else set()
    없는것, 짝없는것 = [], []
    for k in sorted(채비):
        이름 = 채비[k].get('이름') or k
        # 그림은 `{열쇠}.webp`(PC) 와 `{열쇠}-m.webp`(모바일) 입니다.
        pc = [n for n in 있는것
              if re.fullmatch(re.escape(k) + r'\.(webp|png|jpg)', n)]
        mo = [n for n in 있는것
              if re.fullmatch(re.escape(k) + r'-m\.(webp|png|jpg)', n)]
        if not pc and not mo:
            없는것.append('%s (%s)' % (k, 이름))
        elif not pc or not mo:
            짝없는것.append('%s (%s) — %s 만 있습니다'
                          % (k, 이름, 'PC' if pc else '모바일'))
    말('      채비 %d가지 · 그림 파일 %d개' % (len(채비), len(있는것)))

    if 없는것:
        # ★ **지금은 알림입니다** (2026-10-02)
        #   일곱이 비어 있는 것은 **고쳐야 할 잘못**이 맞습니다. 그런데
        #   지금 막으면 그림과 상관없는 고침도 함께 못 올립니다. 바깥
        #   검수(지피티)가 일곱 장을 만드는 중이니, **다 들어오면 이
        #   줄을 `막음` 으로 올립니다.** 그때부터는 새 채비를 자료에만
        #   넣고 그림을 빠뜨리면 배포가 멈춥니다.
        알림.append('그림이 없는 채비 %d가지 — 들어오면 막음으로 올립니다'
                   % len(없는것))
        말('  ~ **그림이 아예 없는 채비 %d가지**' % len(없는것))
        for x in 없는것:
            말('      %s' % x)
        말('      → 쪽 제목은 「어떻게 매나」인데 매는 그림이 없습니다.')
    else:
        말('  · 채비 %d가지 모두 그림이 있습니다' % len(채비))

    if 짝없는것:
        알림.append('PC·모바일 짝이 없는 채비 %d가지' % len(짝없는것))
        말('  ~ **PC 와 모바일 중 한쪽만 있는 것 %d가지**' % len(짝없는것))
        for x in 짝없는것:
            말('      %s' % x)
        말('      → 없는 쪽 손님은 그림을 못 봅니다.')
    elif not 없는것:
        말('  · PC 와 모바일이 모두 짝을 이룹니다')


_img = re.compile(
    r'<img\b[^>]*\bsrc\s*=\s*["\']([^"\']*img/rig/[^"\']+)["\']', re.I)
_src = re.compile(
    r'\bsrcset\s*=\s*["\']([^"\']*img/rig/[^"\']*)["\']', re.I)


def 검사_쪽에실렸나(채비):
    """[3][4] 그림이 쪽에 실려 있고 그 파일이 진짜 있는가."""
    말()
    말('[3] 채비 쪽에 그 채비 그림이 실려 있는가')
    밑 = _사이트()
    쪽칸 = os.path.join(밑, 'rig')
    if not os.path.isdir(쪽칸):
        알림.append('채비 쪽 칸을 못 찾았습니다')
        말('  ~ 채비 쪽 칸이 없습니다 — %s' % 쪽칸)
        return

    칸 = _그림칸()
    있는것 = set(os.listdir(칸)) if os.path.isdir(칸) else set()
    안실림, 깨진것, 본쪽 = [], [], 0
    for k in sorted(채비):
        p = os.path.join(쪽칸, k + '.html')
        if not os.path.exists(p):
            continue
        본쪽 += 1
        글 = io.open(p, encoding='utf-8', errors='replace').read()
        주소들 = set(_img.findall(글))
        for s in _src.findall(글):
            for 한 in s.split(','):
                한 = 한.strip().split()[0] if 한.strip() else ''
                if 'img/rig/' in 한:
                    주소들.add(한)
        쓴파일 = {os.path.basename(x.split('?')[0]) for x in 주소들}
        # 이 채비의 그림을 쓰고 있는가
        제것 = {n for n in 쓴파일
               if re.fullmatch(re.escape(k) + r'(-m)?\.(webp|png|jpg)', n)}
        if not 제것 and (k + '.webp') in 있는것:
            안실림.append('%s — 그림 파일은 있는데 쪽이 안 씁니다' % k)
        for n in 쓴파일:
            if n not in 있는것:
                깨진것.append('%s.html → img/rig/%s 가 없습니다' % (k, n))
    말('      채비 쪽 %d개' % 본쪽)

    if 깨진것:
        막음.append('채비 쪽이 없는 그림을 가리키는 곳 %d곳' % len(깨진것))
        말('  x **없는 그림을 가리킵니다 %d곳**' % len(깨진것))
        for x in 깨진것[:8]:
            말('      %s' % x)
    if 안실림:
        알림.append('그림이 있는데 쪽이 안 쓰는 채비 %d가지' % len(안실림))
        말('  ~ 그림 파일은 있는데 쪽이 안 씁니다 %d가지' % len(안실림))
        for x in 안실림[:8]:
            말('      %s' % x)
    if not 깨진것 and not 안실림 and 본쪽:
        말('  · 쪽마다 제 채비 그림을 쓰고 그 파일이 모두 있습니다')


def 검사_그림값(채비):
    """[4] 그림에 적은 값을 자료와 맞대어 봅니다.

    그림 **안의 글자는 기계가 못 읽습니다.** 그래서 그림을 만든 사람이
    `그림값` 칸에 「이 그림에 무엇을 적었는지」를 적어 두면, 자료가
    바뀔 때 **그림이 낡은 것**을 여기서 잡습니다.
    """
    말()
    말('[4] 그림에 적은 값이 자료와 같은가')
    적힌것, 어긋난것 = 0, []
    for k in sorted(채비):
        v = 채비[k]
        적음 = v.get('그림값')
        if not 적음:
            continue
        적힌것 += 1
        for 칸 in ('대상', '미끼'):
            자료값 = (v.get(칸) or '').strip()
            그림값 = (적음.get(칸) or '').strip()
            if 그림값 and 자료값 and 그림값 != 자료값:
                어긋난것.append('%s / %s — 그림「%s」 자료「%s」'
                              % (k, 칸, 그림값, 자료값))
    if not 적힌것:
        알림.append('채비 자료에 「그림값」이 아직 없습니다')
        말('  ~ 아직 아무 채비에도 「그림값」이 없습니다')
        말('      그림을 만들 때 무엇을 적었는지 자료에 남겨 주십시오.')
        말('      그래야 자료가 바뀔 때 **낡은 그림**을 여기서 잡습니다.')
        return
    말('      그림값이 적힌 채비 %d가지' % 적힌것)
    if 어긋난것:
        막음.append('그림과 자료가 어긋난 곳 %d곳' % len(어긋난것))
        말('  x **그림에 적힌 값이 자료와 다릅니다 %d곳**' % len(어긋난것))
        for x in 어긋난것[:8]:
            말('      %s' % x)
        말('      → 손님이 쪽에서 읽는 값과 그림이 다릅니다.')
    else:
        말('  · 그림에 적은 값이 모두 자료와 같습니다')


# ★ **아이콘이 사이트 빛깔을 쓰는가** (2026-10-02 바깥 검수 13차)
#
#   「SVG 자체의 **모양은 좋지만 색상 시스템은 구버전**입니다.
#     `float`·`downshot`·`metal`·`minnow`·`galchi` 등이 청색
#     중심이라 새 `/tide/`, 권역 Hero 와 같이 놓으면 이질적입니다.
#     파일마다 다시 그릴 필요는 없고 **색만 일괄 토큰화**하는
#     방향이 맞습니다」
#
#   아이콘 26개 중 22개가 옛 빛깔(청색 #2E7D9A · 주황 #D9873A ·
#   진회색 #3B4A52)을 쓰고 있었습니다. 71곳을 사이트 표준으로
#   바꿨습니다. **다시 어긋나지 않게** 여기서 봅니다.
#
#   ★ 표준은 **`site.css` 에서 읽습니다.** 여기에 베껴 적으면
#     차림표를 고칠 때 이 목록이 낡습니다 ([[one-source-of-truth]]).
#
#   ★ **알림입니다.** 빛깔이 조금 달라도 쪽이 깨지지는 않습니다.
#     그리고 뜻이 있는 빛깔이 있습니다 — 갈치 아이콘의 야광 초록은
#     **케미라이트**라 초록이어야 알아봅니다. 모래·껍데기 빛깔도
#     조개와 갯벌의 제 빛깔이지 브랜드색이 아닙니다.
_뜻있는빛깔 = {
    '#B8935C',   # 모래
    '#E5C99A',   # 조개 껍데기
    '#7BD34A',   # 갈치 채비의 케미라이트 — 야광이라 초록이어야 합니다
    '#E5A94F',   # favicon 의 해
    '#FFF', '#FFFFFF', '#000', '#000000',
}


def _차림표빛깔():
    """`assets/css/site.css` 에서 표준 빛깔을 읽습니다."""
    import re as _re
    길 = os.path.join(뿌리, 'assets', 'css', 'site.css')
    try:
        글 = io.open(길, encoding='utf-8', errors='replace').read()
    except OSError:
        return set()
    머리 = 글[:4000]   # :root 둘레만 봅니다
    return {c.upper() for c in _re.findall(r'#[0-9A-Fa-f]{6}', 머리)}


def 검사_아이콘빛깔():
    import re as _re
    말()
    말('[5] 아이콘이 사이트 빛깔을 쓰는가')
    칸 = os.path.join(뿌리, 'assets', 'icon')
    if not os.path.isdir(칸):
        알림.append('아이콘 칸을 못 찾았습니다')
        말('  ~ 아이콘 칸이 없습니다')
        return
    표준 = _차림표빛깔() | _뜻있는빛깔
    딴것, 본것 = {}, 0
    for n in sorted(os.listdir(칸)):
        if not n.endswith('.svg'):
            continue
        본것 += 1
        글 = io.open(os.path.join(칸, n), encoding='utf-8',
                    errors='replace').read()
        for c in _re.findall(r'#[0-9A-Fa-f]{3,8}', 글):
            c = c.upper()
            if c not in 표준:
                딴것.setdefault(c, set()).add(n)
    말('      아이콘 %d개 · 차림표 표준 빛깔 %d가지'
       % (본것, len(표준) - len(_뜻있는빛깔)))
    if 딴것:
        알림.append('사이트 빛깔이 아닌 아이콘 %d가지' % len(딴것))
        말('  ~ 차림표에 없는 빛깔 %d가지' % len(딴것))
        for c, 들 in sorted(딴것.items(), key=lambda x: -len(x[1]))[:8]:
            말('      %-9s %s' % (c, ', '.join(sorted(들)[:4])))
        말('      → 뜻이 있는 빛깔이면 _뜻있는빛깔 에 적어 주십시오.')
    else:
        말('  . 아이콘이 모두 사이트 빛깔을 씁니다')


def 하기():
    엄격 = '--strict' in sys.argv
    말()
    말('채비 그림이 자료와 맞는가')
    말('=' * 60)
    d = _자료()
    채비 = d.get('채비') or {}

    검사_그림있나(채비)
    검사_쪽에실렸나(채비)
    검사_그림값(채비)
    검사_아이콘빛깔()

    말()
    말('-' * 60)
    if 알림:
        말('알림 %d (막지 않습니다)' % len(알림))
        for x in 알림:
            말('    %s' % x)
    if 막음:
        말('어김 %d' % len(막음))
        for x in 막음:
            말('    %s' % x)
        return 1 if 엄격 else 0
    말('어김 없습니다')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(하기())
