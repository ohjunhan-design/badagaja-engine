# -*- coding: utf-8 -*-
"""**검사기가 정말 살아 있는가** — 일부러 망가뜨린 표본으로 잽니다.

★ 왜 만들었나 (2026-09-28 바깥 검수 6차 지시)

    바깥 검수가 이렇게 말했습니다.

        검사기 → 검사기 자체가 고장 → 뮤테이션 테스트도 고장
        이면 전부 PASS 가 될 수 있습니다.

    **제가 겪은 그대로입니다.** 2026-09-27 에 이런 일이 있었습니다.

        _re.sub(r'<img\x08[^>]*>', ...)
                     ↑ 진짜 백스페이스 문자

    `\\b`(단어 경계)를 쓰려다 역슬래시가 먹혀 제어문자가 박혔습니다.
    눈에는 `<img[^>]*>` 로 보입니다. 그래서 **망가뜨리는 시험이
    아무것도 안 망가뜨렸고**, 저는 한 시간을 헤맸습니다.

    이번에는 시험이 **FAIL 쪽으로** 죽어서 알아챘습니다.
    만약 **PASS 쪽으로** 죽었다면 영영 몰랐을 것입니다.

    그리고 곧바로 전부터 있던 같은 사고를 찾았습니다 —
    `check_contracts.py` 의 계약-09 조건이 똑같이 죽어 있었고,
    **그동안 아무것도 안 보면서 「지킴」으로 세어지고** 있었습니다.

★ 뮤테이션 시험과 무엇이 다른가

    뮤테이션 시험   그 자리에서 **망가뜨려** 봅니다
                    → 망가뜨리는 코드가 죽으면 조용히 통과합니다
    카나리          **이미 망가진 표본**이 저장소에 있습니다
                    → 표본은 안 바뀌므로 죽을 수가 없습니다

    탄광의 카나리와 같습니다. 새가 살아 있으면 공기가 좋은 것이고,
    새가 죽으면 나와야 합니다. **여기서는 반대로** — 검사기가
    카나리를 못 잡으면 그 검사기가 죽은 것입니다.

★ 규칙
    tests/canary/ 의 쪽들은 **일부러 망가져 있습니다. 고치지 마세요.**
    검사기는 저마다 제 카나리를 **반드시 잡아야** 합니다.
    하나라도 통과시키면 그 검사기는 죽은 것입니다.

쓰는 법
    python engine/check_canary.py
    python engine/check_canary.py --strict
"""
import os
import sys
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

카나리뿌리 = os.path.join(ROOT, 'tests', 'canary')
NEW = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))

# 검사 등급 (계약-21)
막음 = []
알림 = []


# ── 카나리 목록 ────────────────────────────────────────────
#
#   (이름, 검사기, 이 쪽에 넣을 탈, 잡았다고 볼 말)
#
#   ★ 「잡았다고 볼 말」을 적어 두는 것이 중요합니다.
#     그냥 끝난값만 보면, 검사기가 **딴 까닭으로** 실패해도
#     「잡았다」고 세어집니다. 무엇을 잡았는지까지 봅니다.
카나리들 = [
    ('빈링크', 'check_golden.py',
     '눌러도 아무 데도 안 가는 링크',
     '빈 링크'),
    ('링크안링크', 'check_golden.py',
     '<a> 안에 <a> — 브라우저가 제멋대로 고쳐 짭니다',
     '링크 안에 링크'),
    ('보이는것없음', 'check_golden.py',
     '사진도 그림도 없는 쪽 (주인 규칙 6-1)',
     '보이는 것이 하나도 없음'),
    ('알트없음', 'check_golden.py',
     'alt 없는 사진 — 눈이 불편한 분이 못 읽습니다',
     'alt 없는 사진'),
]


def 카나리자리(이름):
    return os.path.join(카나리뿌리, 이름)


def 돌리기(도구, 사이트):
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_SITE'] = 사이트
    길 = os.path.join(ROOT, 'engine', 도구)
    try:
        r = subprocess.run([sys.executable, 길], capture_output=True,
                           text=True, encoding='utf-8', errors='replace',
                           env=환경, timeout=600)
    except (OSError, subprocess.SubprocessError) as e:
        return None, '못 돌렸습니다: %s' % e
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def 한마리보기(이름, 도구, 무슨탈, 잡을말):
    자리 = 카나리자리(이름)
    if not os.path.isdir(자리):
        막음.append('%s — 카나리 쪽이 없습니다' % 이름)
        print('  ✗ %-14s 카나리가 없습니다 (%s)' % (이름, 자리))
        return

    # ★ 카나리를 **건드리지 않습니다** — 사본에 대고 잽니다 (계약-09)
    t = tempfile.mkdtemp(prefix='canary-')
    try:
        사본 = os.path.join(t, 'site')
        shutil.copytree(자리, 사본)
        코드, 글 = 돌리기(도구, 사본)
        if 코드 is None:
            막음.append('%s — 검사기를 못 돌렸습니다' % 이름)
            print('  ✗ %-14s 검사기를 못 돌렸습니다' % 이름)
            return
        # ★ **`✗` 가 붙은 줄에서만** 찾습니다 (2026-09-28)
        #
        #   전에는 글 어디에든 그 말이 보이면 「잡았다」고 했습니다.
        #   그런데 검사기의 **통과 문구**에 검사 항목 이름이
        #   나열돼 있습니다.
        #
        #       · 모두 지켰습니다
        #           링크 안 링크 · 단추 안 단추 · 빈 쪽 · alt 없는 사진 · 빈 링크
        #
        #   그래서 카나리를 **고쳐 놓아도** 「잡았다」가 나왔습니다.
        #   글자로 판정하면 이렇게 엉뚱한 데서 걸립니다.
        #   그래서 **탈이 하나라도 났을 때만**(✗ 가 있을 때만) 찾습니다.
        #   카나리를 고쳐 놓으면 검사기가 ✗ 를 안 내므로 못 잡은 것이
        #   드러납니다. (✗ 는 요약 줄에만 붙고 자세한 줄에는 없어서,
        #    ✗ 줄 안에서만 찾으면 이번엔 너무 엄격해집니다)
        잡았나 = (코드 != 0) and ('✗' in 글) and (잡을말 in 글)
        if 잡았나:
            print('  · %-14s %-34s 잡았습니다' % (이름, 무슨탈[:34]))
        else:
            # ★ 못 잡았으면 **그 검사기가 죽은 것**입니다
            막음.append('%s — %s 가 못 잡았습니다' % (이름, 도구))
            print('  ✗ %-14s %-34s **못 잡았습니다**'
                  % (이름, 무슨탈[:34]))
            print('      끝난값 %s · 「%s」 가 안 나왔습니다'
                  % (코드, 잡을말))
            print('      → %s 가 죽었거나, 카나리가 고쳐졌습니다' % 도구)
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 진짜쪽은통과하나():
    """★ 반대쪽도 봅니다 — **멀쩡한 쪽을 FAIL 로 내면** 그것도 고장입니다.

    카나리만 보면 「무조건 FAIL 내는 검사기」가 만점을 받습니다.
    그것은 검사기가 아니라 빨간불 기계입니다.
    """
    print('[2] 멀쩡한 쪽은 통과시키는가')
    if not os.path.isdir(NEW):
        print('  ~ site/ 가 없어 못 쟀습니다 — 먼저 build.py 로 만드세요')
        알림.append('멀쩡한 쪽으로는 못 쟀습니다')
        return
    도구들 = sorted(set(x[1] for x in 카나리들))
    for 도구 in 도구들:
        코드, 글 = 돌리기(도구, NEW)
        if 코드 is None:
            막음.append('%s — 진짜 쪽에서 못 돌렸습니다' % 도구)
            print('  ✗ %-22s 못 돌렸습니다' % 도구)
        elif 코드 == 1:
            # 1 = 막음. 멀쩡한 쪽에서 막으면 헛것입니다
            막음.append('%s — 멀쩡한 쪽을 막았습니다' % 도구)
            print('  ✗ %-22s 멀쩡한 쪽을 **막았습니다** (헛불)' % 도구)
        else:
            print('  · %-22s 멀쩡한 쪽은 통과시킵니다' % 도구)


def main():
    print('검사기가 정말 살아 있는가 — 카나리 (바깥 검수 6차)')
    print('  일부러 망가뜨린 표본을 **반드시 잡아야** 합니다.')
    print('  못 잡으면 그 검사기는 죽은 것입니다.')
    print('')

    print('[1] 망가진 표본을 잡는가')
    if not os.path.isdir(카나리뿌리):
        print('  ✗ tests/canary/ 가 없습니다')
        print('     python engine/make_canary.py 로 만드세요')
        return 1
    for 이름, 도구, 무슨탈, 잡을말 in 카나리들:
        한마리보기(이름, 도구, 무슨탈, 잡을말)
    print('')

    진짜쪽은통과하나()
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
    if 막음:
        print('✗ 죽은 검사기가 있습니다 %d건' % len(막음))
        for x in 막음:
            print('    %s' % x)
        print('')
        print('  **있는 줄 알았던 검사가 아무것도 안 보고 있었습니다.**')
        print('  없으면 조심이라도 하는데, 있으면 믿어 버립니다.')
        return 1
    print('검사기 %d가지가 모두 살아 있습니다.' % len(카나리들))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
