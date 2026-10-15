# -*- coding: utf-8 -*-
"""**받는 것이 늘면 개인정보 방침에도 있어야 합니다** (2026-10-15 P0-3).

★ 왜 만드나
  동호회 접수를 켜면 **새 개인정보를 받기 시작합니다.**
  그런데 `privacy.html` 은 손으로 쓰는 쪽이라, 기능을 켜고
  방침 고치는 것을 **잊기 쉽습니다.** 잊으면 법에 어긋납니다
  (개인정보 보호법 제30조 — 처리 항목·목적·보유 기간을 알림).

  사람 기억에 맡기지 않습니다. **받는 자리가 생기면 검사기가
  방침을 봅니다.** [[promise-must-be-kept]]

★ 어떻게 가리나 — **받는 자리가 있는가**로 봅니다
  쪽 이름이나 폴더로 짐작하지 않습니다 [[page-kind-from-page]].
      · `api/club-apply.php` 가 있으면   → 동호회 접수를 받습니다
      · 쪽에 `<form ... method="post">` 가 있으면 → 무언가 받습니다
  받는 자리가 **없으면 아무것도 요구하지 않습니다.**

★ 지금 상태 (2026-10-15)
  접수는 **아직 안 켰습니다.** 그래서 이 검사기는 지금 통과합니다.
  켜는 날 **저절로** 방침을 묻습니다 — 그것이 이 파일의 쓸모입니다.

★ 이미 적혀 있는 것 — 다시 묻지 않습니다
  운영 `privacy.html` 에 접속 기록(IP·시각·브라우저)은 **이미
  적혀 있습니다.** 확인했습니다. 그러므로 이 검사기가 보는 것은
  **새로 받기 시작하는 것**뿐입니다.

쓰는 법
    python -m engine.check_privacy_sync
    python -m engine.check_privacy_sync --strict
"""
import argparse
import io
import os
import re
import sys

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 받는 자리 → 방침에 **반드시 있어야 할 말**
#   (한 자리에 여럿이면 모두 있어야 합니다)
받는자리 = [
    {
        '무엇': '동호회 접수',
        '자리': ['api/club-apply.php', 'site/api/club-apply.php'],
        '있어야': ['동호회'],
        '왜': '동호회 이름·지역·연락처를 새로 받습니다',
    },
]


def 글만(h):
    """태그를 걷어 본문만. 태그 안 글자에 속지 않으려고."""
    h = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', h)
    h = re.sub(r'<[^>]+>', ' ', h)
    return re.sub(r'\s+', ' ', h)


def 방침읽기():
    길 = os.path.join(뿌리, 'site', 'privacy.html')
    if not os.path.isfile(길):
        return None, '%s 가 없습니다' % 길
    return 글만(io.open(길, encoding='utf-8').read()), None


def 폼있는쪽():
    """`method="post"` 인 폼을 가진 쪽. 받는 자리입니다."""
    칸 = os.path.join(뿌리, 'site')
    것 = []
    for 뿌, _, 들 in os.walk(칸):
        for n in 들:
            if not n.endswith('.html'):
                continue
            길 = os.path.join(뿌, n)
            try:
                s = io.open(길, encoding='utf-8', errors='ignore').read()
            except OSError:
                continue
            if re.search(r'(?is)<form[^>]*method\s*=\s*["\']?post', s):
                것.append(os.path.relpath(길, 뿌리).replace('\\', '/'))
    return sorted(것)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--strict', action='store_true')
    # ★ 켜졌다 **치고** 봅니다 — 시험용입니다.
    #   설계가 「로컬에도 api/ 를 만들지 않는다」고 정했으므로
    #   (실수로 올라갈 수 있습니다) 파일을 만들어 시험할 수
    #   없습니다. 그러면 **검사기가 정말 잡는지 모릅니다** —
    #   [[mutation-must-really-break]]. 그래서 이 길을 둡니다.
    p.add_argument('--켜졌다치고', action='store_true',
                   help='받는 자리가 다 있다고 치고 봅니다 (시험용)')
    a = p.parse_args()

    방침, 탈 = 방침읽기()
    if 방침 is None:
        print('★ 방침을 못 읽었습니다 — %s' % 탈)
        return 1

    막음, 알림 = [], []
    켜진것 = []

    for 것 in 받는자리:
        있는자리 = [z for z in 것['자리']
                    if os.path.exists(os.path.join(뿌리, z))]
        if not 있는자리 and a.켜졌다치고:
            있는자리 = [것['자리'][0] + ' (켜졌다 치고)']
        if not 있는자리:
            continue                      # 아직 안 켰습니다
        켜진것.append((것['무엇'], 있는자리[0]))
        빠진말 = [m for m in 것['있어야'] if m not in 방침]
        if 빠진말:
            막음.append('%s 를 켰는데(%s) 방침에 「%s」가 없습니다 — %s'
                        % (것['무엇'], 있는자리[0],
                           '」·「'.join(빠진말), 것['왜']))

    폼들 = 폼있는쪽()
    if 폼들:
        알림.append('보내는 폼이 있는 쪽 %d장 — 무엇을 받는지 '
                    '방침과 맞는지 보십시오' % len(폼들))

    print('받는 것이 방침에 적혀 있는가')
    print('=' * 72)
    print('  방침 본문 %d자 · 받는 자리 %d가지를 봤습니다'
          % (len(방침), len(받는자리)))
    print()
    if 켜진것:
        print('  켜져 있는 것')
        for 무, 자 in 켜진것:
            print('      %-12s %s' % (무, 자))
    else:
        print('  · 아직 **아무것도 안 켰습니다** — 요구할 것이 없습니다')
        print('    (켜는 날 이 검사기가 저절로 방침을 묻습니다)')
    if 폼들:
        print('  ~ 보내는 폼이 있는 쪽 %d장' % len(폼들))
        for z in 폼들[:6]:
            print('      %s' % z)

    print()
    if 막음:
        print('  ✗ 방침에 빠진 것 %d가지' % len(막음))
        for m in 막음:
            print('      %s' % m)
    else:
        print('  ✓ 받는 것과 방침이 **어긋나지 않습니다**')
    if 알림:
        for m in 알림:
            print('  ~ %s' % m)

    print('-' * 72)
    print('[한 줄 요약] 켜진 접수 %d가지 · 방침에 빠진 것 %d가지 · '
          '폼 있는 쪽 %d장' % (len(켜진것), len(막음), len(폼들)))
    if 막음:
        return 2 if a.strict else 1
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
