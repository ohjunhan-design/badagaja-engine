# -*- coding: utf-8 -*-
"""옛 **물때표 보는 법**을 자료로 옮깁니다 (2026-10-01).

★ 왜 — 이 사이트의 **핵심 주제**인데 새 틀에 없었습니다
  물때는 바다가자닷컴의 뼈대입니다. 「해루질은 물이 빠져야 하고
  낚시는 물이 흘러야 한다」는 것이 사이트 전체의 전제입니다.
  그 전제를 **설명하는 유일한 쪽**이 옛 디자인으로 남아 있었습니다.

★ `tide/index.html` 과 **역할이 다릅니다. 합치지 않습니다.**
  바깥 검수 지적 —
  「tide 는 300자의 정확한 실시간 결과가 2,000자 설명보다 가치
    있을 수 있습니다. **왜 이 URL 이 존재하는가?** 에 실제 기능으로
    답하는지가 기준입니다」

  그 말대로입니다.
      tide/      **오늘 물때가 몇 시인가** — 보고 바로 나가는 쪽
      muldae     **물때표를 어떻게 읽는가** — 한 번 배우는 쪽
  둘을 합치면 둘 다 나빠집니다.

★ 아홉 절 · 그림 12장을 그대로 옮깁니다
  1 물때란 · 2 사리와 조금 · 3 들물과 날물 · 4 하루 두 번 ·
  5 물때표 한 칸 읽기 · 6 해루질은 언제 · 7 낚시는 언제 ·
  8 바다마다 다릅니다 · 9 안전

  글이 좋습니다. 새로 쓰면 더 나빠집니다.
"""
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
옛쪽 = os.path.join(os.path.dirname(여기), 'badagaja-site', 'muldae.html')
낼곳 = os.path.join(여기, 'data', 'raw', 'muldae.json')

_겉svg = re.compile(r'^<svg[^>]*>|</svg>$', re.S)


def _깨끗이(s):
    """`<b class="k">` 같은 꾸밈은 **별표로** 바꿉니다.

    새 틀은 글을 esc() 로 내보내므로 태그를 그대로 두면 글자로
    보입니다. 굵게는 뜻을 담고 있으니 버리지 않고 `**…**` 로
    옮깁니다 (낚시 기초를 옮길 때와 같은 방식).
    """
    s = re.sub(r'<b[^>]*>', '**', s)
    s = s.replace('</b>', '**')
    s = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def 뽑기():
    with io.open(옛쪽, encoding='utf-8') as f:
        s = f.read()
    몸 = s[s.find('<main'):s.find('</main>')] or s

    머리 = re.search(r'<h1>(.*?)</h1>\s*<p class="lede">(.*?)</p>', 몸, re.S)
    # ★ 소개에서 **링크를 뺍니다** (2026-10-01)
    #   옛 소개 끝에 「왕초보 낚시 기초 바로가기 →」 가 붙어 있어
    #   글자만 남으니 「…보세요.왕초보 낚시 기초 바로가기 →」 가
    #   되었습니다. 새 쪽에는 그 길이 아래 카드로 따로 있습니다.
    소개 = 머리.group(2) if 머리 else ''
    소개 = re.sub(r'<a\b.*?</a>', '', 소개, flags=re.S)

    # ── 절 나누기 — `<h2 id="…">` 부터 다음 h2 앞까지
    절들 = []
    자리 = [(m.start(), m.group(1), _깨끗이(m.group(2)))
            for m in re.finditer(
                r'<h2 id="([^"]+)"[^>]*>(?:<span class="n">\d+</span>)?'
                r'(.*?)</h2>', 몸, re.S)]
    for i, (시작, 아이디, 제목) in enumerate(자리):
        끝 = 자리[i + 1][0] if i + 1 < len(자리) else len(몸)
        속 = 몸[시작:끝]
        # ★ **그림을 먼저 들어냅니다** (2026-10-01에 겪은 일)
        #   그냥 `<p>…</p>` 를 긁었더니 2번 절 본문이 이렇게 나왔습니다 —
        #     「갯벌 높이 사리 무렵 갯벌이 넓게 드러남 갯벌 높이 조금
        #      무렵 갯벌이 거의 안 드러남 같은 갯벌이라도…」
        #   앞쪽 절반은 **그림 안에 적힌 글자**입니다. 닫히지 않은
        #   `<p>` 가 있어 다음 `</p>` 까지 먹으면서 그림이 통째로
        #   딸려 들어온 것입니다. 그림을 먼저 빼면 섞일 수 없습니다.
        글칸 = re.sub(r'<svg\b.*?</svg>', ' ', 속, flags=re.S)
        글들 = [_깨끗이(x)
                for x in re.findall(r'<p[^>]*>(.*?)</p>', 글칸, re.S)]
        # ★ 2번 절처럼 **`<p>` 가 아닌 설명**도 있습니다
        #   「사리 — 물이 가장 많이 빠지는 때」는 `<div class="mf-two">`
        #   안의 `<b>`+`<span>` 입니다. 못 가져오면 절이 통째로 빕니다.
        for b, sp in re.findall(r'<b>(.*?)</b>\s*<span>(.*?)</span>',
                                글칸, re.S):
            글들.append('**%s** %s' % (_깨끗이(b), _깨끗이(sp)))
        글들 = [x for x in 글들 if len(x) > 10]
        그림들 = []
        for g in re.finditer(r'<svg\b.*?</svg>', 속, re.S):
            이름 = re.search(r'aria-label="([^"]*)"', g.group(0))
            보기 = re.search(r'viewBox="([^"]*)"', g.group(0))
            그림들.append({
                '설명': 이름.group(1) if 이름 else '',
                '보기칸': 보기.group(1) if 보기 else '0 0 480 244',
                '속': _겉svg.sub('', g.group(0)).strip(),
            })
        표 = re.search(r'<table\b.*?</table>', 속, re.S)
        절들.append({
            'id': 아이디, '제목': 제목,
            '글': 글들, '그림': 그림들,
            '표': 표.group(0) if 표 else '',
        })
    return {
        '_설명': '물때표 보는 법. engine/import_muldae.py 가 옛 쪽에서 '
                 '옮겨 왔습니다. tide/ 는 「오늘 몇 시인가」, 이 쪽은 '
                 '「어떻게 읽는가」 — 역할이 다릅니다',
        '제목': _깨끗이(머리.group(1)) if 머리 else '물때표 보는 법',
        '소개': _깨끗이(소개),
        '절': 절들,
    }


def main():
    if not os.path.exists(옛쪽):
        print('  ! 옛 쪽을 못 찾았습니다 — %s' % 옛쪽)
        return 1
    것 = 뽑기()
    with io.open(낼곳, 'w', encoding='utf-8') as f:
        json.dump(것, f, ensure_ascii=False, indent=1)
    print('  「%s」 — 절 %d개 · 그림 %d장'
          % (것['제목'], len(것['절']),
             sum(len(x['그림']) for x in 것['절'])))
    for x in 것['절']:
        print('   %-10s %-22s 글 %d · 그림 %d%s'
              % (x['id'], x['제목'], len(x['글']), len(x['그림']),
                 ' · 표' if x['표'] else ''))
    print('  → data/raw/muldae.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
