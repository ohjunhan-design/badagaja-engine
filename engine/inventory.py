# -*- coding: utf-8 -*-
"""쪽 인벤토리 — **438쪽이 각자 왜 있어야 하는지 셉니다** (2026-10-01).

★ 왜 만드나
  바깥 검수 요청 —
  「쪽 갈래별로 쪽 수 / 고유 내용 / 되풀이 비율 / 답 묶음 / 구조화 자료 /
    색인 상태 / 광고·제휴 자리 / 안쪽 링크 / 얇은 쪽 위험을 보고 싶습니다.
    A/B/C 로 점수 매기지 말고 **근거가 있는 상태 분류**를 해 주세요」

★ 되풀이 비율을 **짐작하지 않고 셉니다** (주인 규칙 29 · 계약-11)
  같은 갈래 쪽들을 줄 단위로 모아, **그 갈래의 절반 넘는 쪽에 똑같이
  나오는 줄**을 되풀이로 봅니다. 되풀이 글자 / 본문 전체 글자 = 되풀이 비율.
  틀(머리글·바닥글·차림표)은 본문에서 먼저 뺍니다.

  이렇게 세면 「이 쪽에만 있는 글이 몇 자인가」가 나옵니다.
  구글이 말하는 **얇은 쪽**은 글이 적은 쪽이 아니라
  **다른 쪽과 같은 글만 있는 쪽**입니다.

★ 상태 세 가지 — 점수가 아니라 **까닭이 붙은 분류**
  · 고유 가치 충분 — 이 쪽에만 있는 글이 넉넉하고 답 묶음이 있음
  · 보강 필요 — 고유 글이 모자라거나 답 묶음·구조화 자료가 빠짐
  · 색인 제외 검토 — 고유 글이 거의 없어 다른 쪽과 구별되지 않음

  어느 쪽이든 **왜 그렇게 봤는지**를 함께 적습니다.
"""
import json
import os
import re
import sys
from collections import Counter

곳 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
쪽밭 = os.path.join(곳, 'site')
sys.path.insert(0, 곳)

from engine import io as _io   # 쓰기는 io.write 를 지납니다 (계약-13)  # noqa: E402

# ── 본문만 남기기 ────────────────────────────────────
_버릴칸 = re.compile(
    r'<(script|style|nav|header|footer|svg|template)\b[^>]*>.*?</\1>',
    re.S | re.I)
_주석 = re.compile(r'<!--.*?-->', re.S)
_태그 = re.compile(r'<[^>]+>')
_빈칸 = re.compile(r'[ \t ]+')


def 본문글(html):
    """틀을 뺀 본문 글. **머리글·바닥글·차림표는 세지 않습니다.**"""
    몸 = html
    꼬리 = 몸.find('<main')
    if 꼬리 >= 0:
        끝 = 몸.find('</main>', 꼬리)
        몸 = 몸[꼬리:끝 if 끝 > 0 else len(몸)]
    몸 = _주석.sub(' ', 몸)
    몸 = _버릴칸.sub(' ', 몸)
    몸 = _태그.sub('\n', 몸)
    줄들 = []
    for 줄 in 몸.split('\n'):
        줄 = _빈칸.sub(' ', 줄).strip()
        if len(줄) >= 2:
            줄들.append(줄)
    return 줄들


# ── 쪽 하나 재기 ─────────────────────────────────────
def 쪽재기(길, 상대):
    html = open(길, encoding='utf-8').read()
    줄들 = 본문글(html)
    낮 = html.lower()
    제목 = re.search(r'<title>(.*?)</title>', html, re.S)
    설명 = re.search(r'name="description"\s+content="(.*?)"', html, re.S)
    정식 = re.search(r'rel="canonical"\s+href="(.*?)"', html, re.S)
    로봇 = re.search(r'name="robots"\s+content="(.*?)"', html, re.S)
    구조 = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
    # 안쪽 링크 — 같은 집 주소만, 자기 자신·앵커 제외
    링크 = set()
    for 주 in re.findall(r'href="([^"]+)"', html):
        if 주.startswith('#') or '://' in 주 and 'badagaja.com' not in 주:
            continue
        if 주.endswith('.css') or 주.endswith('.js') or 주.endswith('.xml'):
            continue
        주 = 주.split('#')[0].split('?')[0]
        if 주 and '.html' in 주:
            링크.add(주)
    return {
        '쪽': 상대,
        '바이트': len(html),
        '줄들': 줄들,
        '글자': sum(len(x) for x in 줄들),
        '제목': (제목.group(1).strip() if 제목 else ''),
        '설명': (설명.group(1).strip() if 설명 else ''),
        '정식주소': (정식.group(1) if 정식 else ''),
        '로봇': (로봇.group(1) if 로봇 else ''),
        '구조화': sorted(set(구조)),
        '답묶음': ('class="answer' in html or 'answer-block' in 낮),
        '사진': bool(re.search(r'<img\b', html)) or 'og:image' in html,
        '안쪽링크': len(링크),
        '광고자리': len(re.findall(r'data-ad-slot|class="ad-|adsbygoogle', html)),
        '제휴자리': len(re.findall(r'data-aff|제휴|쿠팡', html)),
    }


def 갈래(상대):
    칸 = 상대.replace('\\', '/').split('/')
    if len(칸) == 1:
        이름 = 칸[0]
        if 이름 == 'index.html':
            return '맨위/첫쪽'
        if 이름 in ('rule.html', 'gear.html'):
            return '맨위/묶음'
        return '권역/상세'
    if len(칸) == 2:
        return 칸[0] + '/묶음' if 칸[1] == 'index.html' else 칸[0]
    return 칸[0] + '/' + 칸[1]


# ── 되풀이 비율 ──────────────────────────────────────
def 되풀이재기(쪽들):
    """갈래 안 **절반 넘는 쪽에 똑같이 나오는 줄**을 되풀이로 봅니다."""
    셈 = Counter()
    for p in 쪽들:
        for 줄 in set(p['줄들']):
            셈[줄] += 1
    문턱 = max(2, len(쪽들) // 2)
    되풀이줄 = {줄 for 줄, n in 셈.items() if n >= 문턱}
    for p in 쪽들:
        되 = sum(len(x) for x in p['줄들'] if x in 되풀이줄)
        p['되풀이글자'] = 되
        p['고유글자'] = p['글자'] - 되
        p['되풀이비율'] = (되 / p['글자']) if p['글자'] else 1.0
    return 되풀이줄


# ── 상태 분류 — 점수가 아니라 까닭 ───────────────────
#  ★ **기능으로 답하는 쪽**은 글자 수로 재지 않습니다 (2026-10-01)
#    바깥 검수 지적 —
#    「tide는 300자의 정확한 실시간 결과가 2,000자의 설명보다
#      가치 있을 수 있습니다. **왜 이 URL이 존재하는가?** 에
#      실제 기능으로 답하는지가 기준입니다」
#
#    맞습니다. 물때 쪽은 읽는 쪽이 아니라 **보고 나가는 쪽**입니다.
#    길잡이·묶음 쪽도 글을 읽히려고 있는 것이 아니라
#    **고르게 하려고** 있습니다. 글자 수로 재면 엉뚱한 답이 나옵니다.
기능쪽 = ('tide/묶음', 'guide/묶음')


def 상태(p, 갈래이름=''):
    """**고유 가치 충분 / 보강 필요 / 색인 제외 검토** + 까닭.

    ★ 처음 판정이 틀렸습니다 — **답 묶음 없음을 보강 필요로 세었습니다**
      (2026-10-01 바깥 검수)

      「답 묶음 없음 = 보강 필요로 판정하면 안 됩니다. Answer Block 은
        SEO/AEO 를 위한 **수단**이지 쪽 품질의 필수조건이 아닙니다.
        festival 은 이미 고유글자 평균 886자, 되풀이 21%, 고유 소개·
        프로그램·교통·주의사항·주변 바다가 있다면, 197쪽 전부를
        자동으로 보강 필요로 분류할 근거가 부족합니다」

      그 말이 맞습니다. 제 첫 판정은 **267쪽을 「보강 필요」로 몰았고
      그 이유가 사실상 하나(답 묶음 없음)뿐**이었습니다. 그것은
      품질 판정이 아니라 **제 작업 진행률**을 적은 것입니다.

      그래서 **갈랐습니다** —
      · 품질 판정에는 **독립 가치·되풀이·정보량·찾아갈 길**만 씁니다
      · 답 묶음·광고 자리는 **따로 셉니다** (품질 판정에서 뺍니다)
    """
    까닭 = []
    고유 = p['고유글자']
    되 = p['되풀이비율']
    기능 = 갈래이름 in 기능쪽 or 갈래이름.endswith('/묶음')

    # ── 색인 제외 검토 — **다른 쪽과 구별되지 않을 때만**
    if 되 >= 0.7:
        까닭.append('되풀이 %.0f%% — 본문 대부분이 같은 갈래 다른 쪽과 같음'
                    % (100 * 되))
        return '색인 제외 검토', 까닭
    if not 기능 and 고유 < 150:
        까닭.append('이 쪽에만 있는 글 %d자 — 같은 갈래 다른 쪽과 구별되지 않음'
                    % 고유)
        return '색인 제외 검토', 까닭

    # ── 보강 필요 — **근거가 있을 때만**
    if 기능:
        # 기능쪽은 **일을 하는가**로 봅니다
        if p['안쪽링크'] < 8:
            까닭.append('고르게 하는 쪽인데 나갈 길이 %d개뿐'
                        % p['안쪽링크'])
        if not p['사진']:
            까닭.append('사진 없음 (주인 규칙 6-1)')
        if not p['설명']:
            까닭.append('설명 없음')
    else:
        if 고유 < 400:
            까닭.append('이 쪽에만 있는 글 %d자 (400자 미만)' % 고유)
        if 되 >= 0.5:
            까닭.append('되풀이 %.0f%% (절반 넘음)' % (100 * 되))
        if not p['사진']:
            까닭.append('사진 없음 (주인 규칙 6-1)')
        if p['안쪽링크'] < 3:
            까닭.append('안쪽 링크 %d개 — 다음으로 갈 길이 거의 없음'
                        % p['안쪽링크'])
        if not p['설명']:
            까닭.append('설명 없음')
    if 까닭:
        return '보강 필요', 까닭
    근 = ['이 쪽에만 있는 글 %d자' % 고유, '되풀이 %.0f%%' % (100 * 되),
          '안쪽 링크 %d개' % p['안쪽링크']]
    if p['구조화']:
        근.append('구조화 자료 ' + '·'.join(p['구조화'][:3]))
    return '고유 가치 충분', [' · '.join(근)]


def 모으기():
    묶 = {}
    for 뿌리, _, 파일들 in os.walk(쪽밭):
        for 이름 in 파일들:
            if not 이름.endswith('.html'):
                continue
            길 = os.path.join(뿌리, 이름)
            상대 = os.path.relpath(길, 쪽밭).replace('\\', '/')
            p = 쪽재기(길, 상대)
            묶.setdefault(갈래(상대), []).append(p)
    for 이름, 쪽들 in 묶.items():
        되풀이재기(쪽들)
        for p in 쪽들:
            p['상태'], p['까닭'] = 상태(p, 이름)
    return 묶


def 적기(묶, 낼곳):
    줄 = []
    쓰 = 줄.append
    전체 = sum(len(v) for v in 묶.values())
    쓰('# 438쪽 인벤토리 — 쪽 갈래별 고유 가치')
    쓰('')
    쓰('모두 %d쪽. 갈래 %d가지.' % (전체, len(묶)))
    쓰('')
    쓰('되풀이 비율은 **같은 갈래 절반 넘는 쪽에 똑같이 나오는 줄**의 글자 비율입니다.')
    쓰('틀(머리글·바닥글·차림표)은 세기 전에 뺐습니다.')
    쓰('')
    쓰('## 갈래별 요약')
    쓰('')
    쓰('| 갈래 | 쪽 수 | 평균 고유 글자 | 평균 되풀이 | 답묶음 | 구조화 | 사진 | 안쪽링크 | 광고자리 |')
    쓰('|---|---|---|---|---|---|---|---|---|')
    차례 = sorted(묶.items(), key=lambda x: -len(x[1]))
    for 이름, 쪽들 in 차례:
        n = len(쪽들)
        쓰('| %s | %d | %d | %.0f%% | %d/%d | %d/%d | %d/%d | %.0f | %d/%d |' % (
            이름, n,
            sum(p['고유글자'] for p in 쪽들) // n,
            100 * sum(p['되풀이비율'] for p in 쪽들) / n,
            sum(1 for p in 쪽들 if p['답묶음']), n,
            sum(1 for p in 쪽들 if p['구조화']), n,
            sum(1 for p in 쪽들 if p['사진']), n,
            sum(p['안쪽링크'] for p in 쪽들) / n,
            sum(1 for p in 쪽들 if p['광고자리']), n))
    쓰('')
    쓰('## 쪽 품질 — 점수가 아니라 까닭')
    쓰('')
    쓰('★ **답 묶음·광고 자리는 품질 판정에서 뺐습니다.**')
    쓰('  답 묶음은 검색·AI 노출을 위한 **수단**이지 쪽 품질의 조건이')
    쓰('  아닙니다. 처음에는 섞어 세어 267쪽이 「보강 필요」로 나왔는데,')
    쓰('  그 까닭이 사실상 하나(답 묶음 없음)뿐이었습니다. 그것은 품질이')
    쓰('  아니라 **제 작업 진행률**이었습니다. 아래에 따로 적습니다.')
    쓰('')
    셈 = Counter(p['상태'] for 쪽들 in 묶.values() for p in 쪽들)
    for 이름 in ('고유 가치 충분', '보강 필요', '색인 제외 검토'):
        쓰('- **%s** — %d쪽' % (이름, 셈.get(이름, 0)))
    쓰('')
    쓰('## 따로 세는 것 — 작업 진행률')
    쓰('')
    모두 = [p for 쪽들 in 묶.values() for p in 쪽들]
    쓰('- 답 묶음 있는 쪽 — %d / %d쪽'
       % (sum(1 for p in 모두 if p['답묶음']), 전체))
    쓰('- 광고 자리 있는 쪽 — %d / %d쪽'
       % (sum(1 for p in 모두 if p['광고자리']), 전체))
    쓰('- 구조화 자료 있는 쪽 — %d / %d쪽'
       % (sum(1 for p in 모두 if p['구조화']), 전체))
    쓰('')
    for 이름, 쪽들 in 차례:
        쓰('### %s (%d쪽)' % (이름, len(쪽들)))
        쓰('')
        갈셈 = Counter(p['상태'] for p in 쪽들)
        쓰('상태: ' + ' · '.join('%s %d' % (k, v) for k, v in 갈셈.items()))
        쓰('')
        까닭셈 = Counter()
        for p in 쪽들:
            for c in p['까닭']:
                까닭셈[re.sub(r'\d+', 'N', c)] += 1
        for c, n in 까닭셈.most_common(8):
            쓰('- %s — %d쪽' % (c, n))
        쓰('')
        얇 = sorted(쪽들, key=lambda p: p['고유글자'])[:3]
        쓰('가장 얇은 쪽: ' + ' · '.join(
            '%s(고유 %d자)' % (p['쪽'], p['고유글자']) for p in 얇))
        쓰('')
    _io.write(낼곳, '\n'.join(줄) + '\n')
    return 전체


def main():
    묶 = 모으기()
    낼 = os.path.join(곳, 'docs', '인벤토리.md')
    전체 = 적기(묶, 낼)
    셈 = Counter(p['상태'] for 쪽들 in 묶.values() for p in 쪽들)
    묶음자료 = {이름: [{k: v for k, v in p.items() if k != '줄들'} for p in 쪽들]
                for 이름, 쪽들 in 묶.items()}
    _io.write_json(os.path.join(곳, 'docs', '인벤토리.json'), 묶음자료)
    print('%d쪽 · 갈래 %d가지 → docs/인벤토리.md' % (전체, len(묶)))
    for 이름 in ('고유 가치 충분', '보강 필요', '색인 제외 검토'):
        print('  %s %d쪽' % (이름, 셈.get(이름, 0)))


if __name__ == '__main__':
    main()
