# -*- coding: utf-8 -*-
"""검사 — **차림표에 없는 이름을 쓰고 있지 않은가** (2026-10-01).

★ 오늘 하루에 **세 번** 당했습니다
      `--brand`      없는 색 이름 → 단추가 기본 파랑으로 (어제)
      `.tbl`         없는 표 이름 → 표가 꾸며지지 않음
      `.ls-basic`    없는 띠 이름 → 글이 서로 붙어 보임

  없는 이름을 써도 **오류가 안 납니다. 조용히 버려집니다.**
  그래서 쪽은 만들어지고 검사도 통과하는데, 사람 눈에만 이상합니다
  (주인 규칙 6-2 — 기계가 통과한 것과 사람이 보는 것은 다릅니다).

★ 무엇을 보나
  쪽이 쓰는 `class="…"` 이름 가운데, 차림표(site.css)에도 없고
  쪽 안 `<style>` 에도 없는 것을 찾습니다.

★ 알림입니다. 막지 않습니다.
  뜻만 담고 꾸밈이 없는 이름(`wrap`·`serif` 같은 것)도 있고,
  자바스크립트만 보는 이름도 있어서 **다 잘못은 아닙니다.**
  다만 **새로 생긴 것**은 사람이 한 번 봐야 합니다.
"""
import os
import re
import sys
from collections import Counter

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# ★ **시험이 주는 사본을 봅니다** (2026-10-02 판정 [2])
#   전에는 `os.path.join(여기, 'site')` 로 **늘 진짜 site/ 만**
#   봤습니다. 검사기 자기검증이 사본을 만들어 일부러 깨뜨린 뒤
#   `BADAGAJA_SITE` 로 가리켜 주는데, 이 검사기는 그것을 안 보고
#   멀쩡한 진짜 쪽을 재고 「아무 탈 없다」고 했습니다.
#   그래서 **「검사기가 못 잡는다」로 두 가지가 헛되이 실패**하고
#   있었습니다. 다른 검사기들은 모두 환경값을 봅니다.
쪽밭 = os.environ.get('BADAGAJA_SITE', os.path.join(여기, 'site'))
차림표 = os.path.join(여기, 'assets', 'css', 'site.css')

# ★ 꾸밈이 없어도 되는 이름 — **알면서 두는 것**입니다
봐준다 = {
    'wrap', 'serif', 'long', 'notice', 'lead', 'kicker',
    'section', 'grid', 'dots', 'o',
}


# ── 검사 등급 (계약-21) ──────────────────────────────
#   막는 것과 알리는 것을 **따로 모읍니다.** 한 덩이로 두면
#   나중에 「이건 알림만」 하고 싶을 때 검사기를 통째로
#   고쳐야 합니다.
막음, 알림 = [], []


def 차림표이름들():
    이름 = set()
    for 길 in (차림표,):
        if not os.path.exists(길):
            continue
        글 = open(길, encoding='utf-8').read()
        글 = re.sub(r'/\*.*?\*/', ' ', 글, flags=re.S)
        for m in re.finditer(r'\.([A-Za-z_][\w-]*)', 글):
            온것 = m.group(1)
            이름.add(온것)
            # ★ **변형 이름의 바탕도 있는 것으로 봅니다** (2026-10-01)
            #   차림표에 `.firsttime--btn` 만 있고 `.firsttime` 은
            #   없었는데, 쪽은 `class="firsttime firsttime--btn"` 으로
            #   **둘을 함께** 씁니다. 바탕 이름을 없다고 세면
            #   잘 나오는 칸을 「꾸밈 없음」으로 잘못 알립니다.
            #   실제로 처음 돌렸을 때 권역 57쪽의 「처음이신가요」 칸을
            #   그렇게 잘못 잡았습니다 (화면을 찍어 보니 멀쩡했습니다).
            if '--' in 온것:
                이름.add(온것.split('--')[0])
    return 이름


def 쪽이름들():
    씀 = Counter()
    어디 = {}
    집스타일 = {}
    for 뿌리, _, 파일들 in os.walk(쪽밭):
        for 파일 in 파일들:
            if not 파일.endswith('.html'):
                continue
            # ★ 다른 검사기가 쓰는 **임시 파일**은 건너뜁니다 (2026-10-01)
            if 파일.startswith('__'):
                continue
            길 = os.path.join(뿌리, 파일)
            상대 = os.path.relpath(길, 쪽밭).replace('\\', '/')
            try:
                글 = open(길, encoding='utf-8').read()
            except OSError:
                continue          # 읽는 사이에 사라졌으면 넘어갑니다
            # 쪽 안 <style> 에 적힌 이름은 **있는 것으로 봅니다**
            안쪽 = set()
            for st in re.findall(r'<style\b[^>]*>(.*?)</style>', 글, re.S):
                for m in re.finditer(r'\.([A-Za-z_][\w-]*)', st):
                    안쪽.add(m.group(1))
            집스타일[상대] = 안쪽
            # ★ SVG 안 class 는 보지 않습니다 — 그림 제 안에서 씁니다
            몸 = re.sub(r'<svg\b.*?</svg>', ' ', 글, flags=re.S)
            for m in re.finditer(r'class="([^"]*)"', 몸):
                for 이름 in m.group(1).split():
                    if not 이름 or '{' in 이름:
                        continue
                    씀[이름] += 1
                    어디.setdefault(이름, set()).add(상대)
    return 씀, 어디, 집스타일


def main():
    있는것 = 차림표이름들()
    씀, 어디, 집스타일 = 쪽이름들()
    없는것 = []
    for 이름, 수 in 씀.items():
        if 이름 in 있는것 or 이름 in 봐준다:
            continue
        쪽들 = 어디[이름]
        # 쪽 안 <style> 에 있으면 넘어갑니다
        if all(이름 in 집스타일.get(p, set()) for p in 쪽들):
            continue
        없는것.append((이름, 수, sorted(쪽들)))
    if not 없는것:
        print('[통과] 차림표에 없는 이름을 쓰는 곳이 없습니다.')
        return 0
    # ★ 등급을 **둘로 나눕니다** (계약-21)
    #   지금은 전부 알림입니다 — 꾸밈이 없어도 되는 이름이 섞여
    #   있어 막으면 거짓 경보로 배포가 멈춥니다.
    알림 = list(없는것)
    if 막음:
        pass
    if 알림:
        pass
    없는것.sort(key=lambda t: -t[1])
    print('[알림] 차림표에 없는 이름 %d가지 (막지 않습니다)' % len(없는것))
    print('  없는 이름은 **오류 없이 조용히 버려집니다.**')
    print('  꾸밈이 필요 없는 것이면 engine/check_css_names.py 의')
    print('  `봐준다` 에 적어 두세요.')
    print()
    # ★ **안 보여 준 것이 몇인지 밝힙니다** (2026-10-02)
    #   스무 가지만 내고 나머지는 말없이 묻었습니다. 89가지 중
    #   69가지가 조용히 사라진 셈입니다. 그래서 검사기 자기검증이
    #   「못 잡는다」고 했습니다 — 잡기는 잡았는데 **출력에
    #   안 나왔을** 뿐이었습니다.
    #   잡은 것을 안 보여 주면 **못 잡은 것과 같습니다.**
    #   `--list` 를 붙이면 전부 냅니다.
    낼수 = len(없는것) if '--list' in sys.argv else 20
    for 이름, 수, 쪽들 in 없는것[:낼수]:
        # ★ **「곳」이 무엇인지 밝힙니다** (2026-10-01 바깥 검수)
        #   「27곳이 27개의 실제 DOM 사용 횟수인지, 27페이지인지
        #     검사 메시지에서 명확하게 표현하면 더 좋습니다.
        #     검사 결과 문구가 **실제 검사 범위를 과장하지 않는다**는
        #     것과 같은 원칙입니다」
        print('  .%-22s 쓴 곳 %d번 · %d쪽 — %s'
              % (이름, 수, len(쪽들), 쪽들[0]))
    if len(없는것) > 낼수:
        print()
        print('  … 그 밖 %d가지. 전부 보려면 --list 를 붙이세요.'
              % (len(없는것) - 낼수))
    return 0


if __name__ == '__main__':
    sys.exit(main())
