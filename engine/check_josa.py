# -*- coding: utf-8 -*-
"""**조사가 앞말에 붙어 있는가** (2026-10-09)

★ 왜 이 검사가 있나

    공개판에서 쪽 18개에 이런 글이 있었습니다.

        「원투 채비 를 부품마다 이름과 호수까지…」
        「우럭 · 붕장어 · 도다리 · 노래미 · 광어 로 노립니다」
        「미끼는 갯지렁이 · 오징어살 · 새우 를 씁니다」

    한국어 조사는 **앞말에 붙여 씁니다.** 떨어져 있으면
    사람 눈에 바로 걸립니다. 받침도 안 가려 「볼락 로」
    (→ 볼락으로)·「오징어살 를」(→ 오징어살을)이 되었습니다.

    더 나쁜 것은 **문장에 조사를 붙인 것**입니다.

        「미끼는 안 씁니다 — 메탈지그 자체가 미끼입니다 를 씁니다.」

    까닭은 하나였습니다 — `engine/korean.py` 에 `조사()` 가
    이미 있는데 **채비 쪽에서만 손으로 붙였습니다.**
    같은 일을 두 곳에서 따로 하면 반드시 어긋납니다.

무엇을 재나

    ① 한글 뒤 **빈칸 + 조사**가 있는가 (를·을·과·와·로·으로)
       → 있으면 **막습니다.** 거짓 양성이 거의 없습니다 —
         이 여섯은 홀로 쓰이지 않는 말입니다.
    ② 그 조사 앞이 **문장**인가 (…니다 / 없음)
       → 비문입니다. 함께 막습니다.

    ★ 「이·가」는 보지 않습니다 — 「이 사람」·「가 보자」처럼
      홀로 쓰여 거짓 양성이 납니다. 못 잡는 것이 있어도
      **틀리게 잡는 것보다 낫습니다.**

쓰는 법
    python engine/check_josa.py          전수 (빠릅니다 — 글만 봅니다)
"""
import io
import os
import re
import sys
import glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 홀로 쓰이지 않는 조사만 봅니다
# ★ 「와」는 **뺍니다** (2026-10-09 — 처음 돌려 걸러낸 것)
#   「꿀빵을 사 와 함께 먹는」 은 「사다 + 오다」 활용이라
#   띄어 쓰는 것이 **맞습니다.** 조사 「와」와 겹칩니다.
#   그리고 「와」는 받침 없는 말 뒤에만 와서, 떨어뜨려 쓰는
#   잘못이 애초에 드뭅니다. 틀리게 잡는 것보다 놓치는 쪽이 낫습니다.
조사들 = ('으로', '를', '을', '과', '로')

_군더더기 = re.compile(
    r'<(script|style)\b[^>]*>.*?</\1>|<!--.*?-->', re.S | re.I)
# ★ 인라인 태그는 **빈 글자**로 지웁니다 (2026-10-09)
#   빈칸으로 바꾸면 `<b>해감</b>을` 이 「해감 을」이 되어
#   **없는 잘못 98군데**가 나옵니다. 처음 돌렸을 때 그랬습니다.
#   블록 태그는 빈칸으로 — 안 그러면 두 문단이 붙습니다.
_속태그 = re.compile(
    r'</?(b|strong|em|i|u|s|span|a|small|code|sub|sup|mark|'
    r'abbr|time|label|bdi|q|cite|var|kbd|samp|ruby|rt|rp|wbr)'
    r'(\s[^>]*)?>', re.I)
_태그 = re.compile(r'<[^>]+>')
_빈칸 = re.compile(r'[ \t ]+')

# 한글 뒤 빈칸 + 조사 + (글 끝이거나 한글이 아닌 것)
_떨어진조사 = re.compile(
    '(?<=[가-힣])[  ]('
    + '|'.join(조사들)
    + ')(?=[ .,!?·—…)\\]」』]|$)')

_문장끝 = re.compile(r'(니다|없음|하세요|습니다)[  ]*$')


def 글만(s):
    """태그를 걷어내고 본문 글만 남깁니다"""
    s = _군더더기.sub(' ', s)
    s = _속태그.sub('', s)          # 먼저 — 붙여 쓴 글을 안 끊습니다
    s = _태그.sub(' ', s)
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&')
          .replace('&lt;', '<').replace('&gt;', '>')
          .replace('&quot;', '"').replace('&#39;', "'"))
    return _빈칸.sub(' ', s)


def 쪽하나(길):
    """떨어진 조사를 모두 돌려줍니다"""
    try:
        s = io.open(길, encoding='utf-8').read()
    except Exception as e:
        return [('읽기 실패', str(e), False)]
    글 = 글만(s)
    나옴 = []
    for m in _떨어진조사.finditer(글):
        앞 = 글[max(0, m.start() - 26):m.start() + 1]
        뒤 = 글[m.end():m.end() + 14]
        비문 = bool(_문장끝.search(앞))
        나옴.append((('%s%s%s' % (앞, m.group(0), 뒤)).strip(),
                     m.group(1), 비문))
    return 나옴


def 쪽들():
    것 = sorted(glob.glob(os.path.join(NEW, '**', '*.html'), recursive=True))
    return [p for p in 것 if os.path.basename(p) != '404.html']


def main():
    것들 = 쪽들()
    if not 것들:
        print('✗ 쪽이 없습니다 — 먼저 build 를 돌리세요')
        return 4          # 못잼 (계약)

    걸린쪽, 모두, 비문수 = [], 0, 0
    for p in 것들:
        나옴 = 쪽하나(p)
        if 나옴:
            걸린쪽.append((os.path.relpath(p, NEW).replace('\\', '/'), 나옴))
            모두 += len(나옴)
            비문수 += sum(1 for _, _, 비 in 나옴 if 비)

    print('조사 붙여쓰기 — 쪽 %d개를 봤습니다' % len(것들))
    if not 걸린쪽:
        print('  ✓ 떨어진 조사 0')
        return 0

    print('  ✗ 떨어진 조사 %d군데 · 쪽 %d개 (그중 비문 %d)'
          % (모두, len(걸린쪽), 비문수))
    for 길, 나옴 in 걸린쪽[:14]:
        print('    %s' % 길)
        for 글, 자, 비 in 나옴[:3]:
            print('      %s「 %s」 … %s' % ('비문 ' if 비 else '', 자, 글))
    if len(걸린쪽) > 14:
        print('    … 그 밖에 %d쪽' % (len(걸린쪽) - 14))
    print('  → 조사는 engine/korean.py 의 조사() 로 붙입니다.'
          ' 손으로 빈칸을 두지 않습니다.')
    return 1              # 어김 (계약)


if __name__ == '__main__':
    sys.exit(main())
