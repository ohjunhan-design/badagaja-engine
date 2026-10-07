# -*- coding: utf-8 -*-
"""되돌릴 것을 **정말 다 받았는가** (2026-10-07 바깥 검수 순서 ②).

★ 왜 생겼나
  되돌리기 코드가 `mirror -R _before/ /www/` 입니다 — **`--delete` 가
  없습니다.** 새 판에만 있던 파일이 되돌린 뒤에도 서버에 남습니다.

      바깥 검수 — 「지금 발견한 구멍은 **실제 구멍**입니다.
        현재 rollback 은 **『파일을 덮어쓰는 복원』**이지
        **『정확히 이전 판으로 되돌리는 복원』**은 아닙니다.
        다만 `--delete` 는 **칼이 큰 만큼**, 먼저 **백업 완전성 +
        삭제 계획을 증명하고** 넣는 것이 맞습니다」

★ 가장 무서운 것은 **`.htaccess`** 입니다
  `ftp:list-options -a` 가 없으면 lftp 는 점으로 시작하는 파일을
  **아예 못 봅니다.** 그 상태로 `--delete` 를 넣으면 `.htaccess` 가
  지워지고 **사이트가 통째로 500** 이 됩니다 (주인 규칙 27 — 두 번 겪음).

★ 이 글의 셈은 **순수함수**입니다 — `tests/` 가 가짜 목록으로 잽니다.
  서버에 붙지 않고도 「무엇이 지워질지」를 미리 잴 수 있어야 합니다.

쓰는 법
    python engine/check_backup.py          _server.list 와 _before/ 를 견줍니다
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ **지워지면 안 되는 것** — 하나라도 삭제 목록에 들면 멈춥니다
#   서버에만 있고 저장소에는 없는 것들입니다.
건드리면안될것 = (
    '.htaccess',        # 없으면 사이트가 500 입니다
    'api/',             # 옛 사이트와 함께 쓰는 자리
    'zh-cn/',           # 중국어판
    '.well-known/',     # 인증서·소유 확인
    'favicon.ico',
)

# ★ 백업에서 일부러 뺀 것 — 지울 것에서도 빼야 합니다
#   백업에 없다고 지우면 **검증판 자리가 통째로 사라집니다.**
백업에서뺀것 = ('_stage/',)


def 길다듬기(줄, 뿌리='/www/'):
    """lftp `find` 가 낸 줄 → `_before/` 기준의 상대 경로."""
    s = (줄 or '').strip()
    if not s:
        return None
    if s.startswith(뿌리):
        s = s[len(뿌리):]
    # ★ **lstrip 은 문자 집합을 벗깁니다** (2026-10-07 — 시험이 잡음)
    #   `s.lstrip('./')` 는 `.htaccess` 에서 **점까지 벗겨**
    #   `htaccess` 로 만듭니다. 그러면 백업에 `.htaccess` 가 있어도
    #   **없는 것으로 세어** 지울 목록에 넣습니다 — 사이트가 500 입니다.
    #   하필 가장 위험한 파일이 점으로 시작합니다.
    if s.startswith('./'):
        s = s[2:]
    s = s.lstrip('/')
    return s or None


def 뺄것인가(길, 뺀것=백업에서뺀것):
    return any(길 == x.rstrip('/') or 길.startswith(x) for x in 뺀것)


def 견주기(서버것들, 받은것들, 뺀것=백업에서뺀것):
    """서버에 있는데 **안 받은 것**과, 받았는데 서버에 없는 것.

    돌려주는 것: (못받은것, 더받은것) — 둘 다 정렬된 목록입니다.
    """
    서버 = set(x for x in 서버것들 if x and not 뺄것인가(x, 뺀것))
    받은 = set(x for x in 받은것들 if x and not 뺄것인가(x, 뺀것))
    return sorted(서버 - 받은), sorted(받은 - 서버)


def 지울것(지금서버것들, 되돌릴것들, 뺀것=백업에서뺀것):
    """`--delete` 를 붙이면 **무엇이 지워질지**.

    ★ 올리기 전에 이것을 보고 멈출 수 있어야 합니다.
      바깥 검수 순서 ⑦ — 「삭제 예정 경로 위험검사」
    """
    지금 = set(x for x in 지금서버것들 if x and not 뺄것인가(x, 뺀것))
    되돌릴 = set(x for x in 되돌릴것들 if x)
    return sorted(지금 - 되돌릴)


def 위험한가(지울것들, 안될것=건드리면안될것):
    """지울 목록에 **건드리면 안 되는 것**이 섞였나 → 섞인 것 목록."""
    걸린것 = []
    for 길 in 지울것들:
        for 안될 in 안될것:
            if 길 == 안될 or 길.startswith(안될.rstrip('/') + '/') \
               or (안될.endswith('/') and 길.startswith(안될)):
                걸린것.append((길, 안될))
                break
    return 걸린것


def lftp계획읽기(줄들, 뿌리='/www/'):
    """`lftp mirror --dry-run` 이 낸 글에서 **지우겠다는 것**만 뽑습니다.

    ★ 이것은 **교차검증용**입니다 — 판정의 근거가 아닙니다.
      바깥 검수 — 「저는 `lftp --dry-run` **출력 문자열 자체를
      안전판정의 유일한 근거로 쓰지는 않겠습니다.** 이미 오늘
      `s.lstrip('./')` 같은 작은 문자열 처리 하나가 `.htaccess` 를
      망가뜨렸습니다. 판정은 **경로 집합 계산**을 기준으로 하고,
      `lftp --dry-run` 은 **우리 계산이 맞는지** 확인하는 교차검증으로」
    """
    것 = []
    for 줄 in 줄들:
        s = (줄 or '').strip()
        if not s:
            continue
        낮은 = s.lower()
        if not (낮은.startswith('rm ') or 낮은.startswith('rmdir ')
                or 'remove' in 낮은[:12]):
            continue
        몫 = s.split(None, 1)
        if len(몫) < 2:
            continue
        길 = 길다듬기(몫[1].strip().strip('"').strip("'"), 뿌리)
        if 길:
            것.append(길)
    return sorted(set(것))

def _받은것읽기(밭):
    것 = []
    for 터, _, 파일들 in os.walk(밭):
        for 이름 in 파일들:
            길 = os.path.relpath(os.path.join(터, 이름), 밭)
            것.append(길.replace(os.sep, '/'))
    return 것


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    엄격 = '--strict' in sys.argv
    import io as _io

    밭 = os.path.join(ROOT, '_before')
    # ★ **올린 뒤의** 서버 목록이 있으면 그것으로 **삭제 계획**까지 냅니다
    #   바깥 검수 — 「백업 단계 직후 dry-run 은 **반만 맞습니다.**
    #   그 시점에는 서버와 `_before` 가 사실상 같은 상태라서,
    #   **새 배포가 추가한 파일을 삭제하는 실제 rollback 상황을
    #   재현하지 못합니다.** … 가장 좋은 위치는 **업로드가 끝난
    #   직후 → post-deploy 검사 전**입니다」
    뒤목록 = os.path.join(ROOT, '_server-after.list')
    앞목록 = os.path.join(ROOT, '_server.list')

    막음, 알림 = [], []
    print('되돌릴 것을 **정말 다 받았는가** (바깥 검수 순서 ②⑥⑦)')

    if not os.path.isdir(밭):
        print('  □ 받아 둔 것이 없습니다 — **잰 것이 아닙니다.**')
        print('    러너에서 lftp 로 받은 뒤에 돕니다.')
        return 2 if 엄격 else 0
    받은 = _받은것읽기(밭)

    # ── ① 점으로 시작하는 파일을 받았는가
    숨은것 = [x for x in 받은 if os.path.basename(x).startswith('.')]
    print('  받은 것 %d개 · 그중 점으로 시작하는 것 %d개'
          % (len(받은), len(숨은것)))
    for x in 숨은것[:5]:
        print('      %s' % x)
    if not 숨은것:
        막음.append('점으로 시작하는 파일을 **하나도 못 받았습니다** '
                    '— ftp:list-options -a 를 보십시오')

    # ── ② 서버 목록과 견주기
    if os.path.exists(앞목록):
        서버 = [x for x in (길다듬기(l) for l in
                            _io.open(앞목록, encoding='utf-8',
                                     errors='replace')) if x]
        못받은, 더받은 = 견주기(서버, 받은)
        print('  서버 %d · 받은 것 %d' % (len(서버), len(받은)))
        if 못받은:
            막음.append('서버에 있는데 **안 받은 것** %d개 '
                        '— 이대로는 되돌려도 그 판이 아닙니다' % len(못받은))
            for x in 못받은[:8]:
                print('      ✗ %s' % x)
        else:
            print('  · 서버에 있는 것을 다 받았습니다')
        if 더받은:
            알림.append('받았는데 서버 목록에 없는 것 %d개' % len(더받은))
    else:
        알림.append('서버 목록(_server.list)이 없어 **완전성은 못 쟀습니다**')

    # ── ③ 되돌릴 때 **무엇이 지워질지** + 위험검사
    if os.path.exists(뒤목록):
        뒤서버 = [x for x in (길다듬기(l) for l in
                              _io.open(뒤목록, encoding='utf-8',
                                       errors='replace')) if x]
        지울 = 지울것(뒤서버, 받은)
        print('')
        print('  되돌리면 지워질 것 %d개' % len(지울))
        for x in 지울[:10]:
            print('      %s' % x)
        걸린 = 위험한가(지울)
        if 걸린:
            막음.append('**지우면 안 되는 것**이 삭제 목록에 %d개' % len(걸린))
            for 길, 안될 in 걸린[:6]:
                print('      ✗ %-40s (%s)' % (길, 안될))
        else:
            print('  · 지우면 안 되는 것은 섞여 있지 않습니다')

        # ★ **교차검증** — lftp 가 하려는 일과 내 셈이 같은가
        계획길 = os.path.join(ROOT, 'rollback-plan.txt')
        if os.path.exists(계획길):
            lftp것 = lftp계획읽기(_io.open(계획길, encoding='utf-8',
                                          errors='replace'))
            다름 = sorted(set(지울) ^ set(lftp것))
            print('  lftp 가 지우겠다는 것 %d개' % len(lftp것))
            if 다름:
                알림.append('내 셈과 lftp 가 **다릅니다** %d개 '
                            '— 둘 중 하나가 틀렸습니다' % len(다름))
                for x in 다름[:6]:
                    print('      ~ %s' % x)
            else:
                print('  · 내 셈과 lftp 가 **같습니다**')
    else:
        알림.append('올린 뒤 서버 목록이 없어 **삭제 계획은 못 쟀습니다**')

    print('')
    for x in 알림:
        print('  ~ %s' % x)
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **되돌릴 수 없는 백업은 백업이 아닙니다.**')
        # ★ 바깥 검수 — 「**절대로 『경고만 하고 계속』하지 마세요.**
        #   --delete 를 실제로 쓸 수 있게 되는 순간부터는 이 검사가
        #   **칼집 역할**을 해야 합니다」
        return 1 if 엄격 else 0
    print('되돌릴 것을 다 받았고, 지울 것에 위험이 없습니다.')
    print('  ※ 실제 되돌리기에는 **아직 --delete 를 안 넣었습니다.**')
    return 0

if __name__ == '__main__':
    sys.exit(main())
