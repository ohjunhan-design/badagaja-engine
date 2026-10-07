# -*- coding: utf-8 -*-
"""**`origin` 이 대장 저장소를 가리키는가** (2026-10-07 바깥 검수 설계).

★ 왜 만들었나
  주인 —
    「지피티가 자꾸 **옛판을 본다**고 하는데 그건 **구조적인 문제**가
      있다는 소리야 … **잔재가 많이 남아 있다**는 소리야」

  잔재 하나를 찾았습니다. 깃 원격 이름이 **거꾸로** 붙어 있었습니다.

      origin  badagaja-2nd      **2026-09-28 에 멈춤**   ← 이름이 origin
      engine  badagaja-engine   **지금 대장**

  누구나 `origin` 을 대장으로 봅니다. 보면 **9일 전 판**이 나옵니다.
  바깥 검수가 「옛판을 본다」고 한 일의 뿌리 가운데 하나입니다.

★ 바깥 검수 —
    「README 경고만으로는 부족합니다. 누군가 저장소를 **자동으로 읽거나**,
      도구가 **기본 remote 를 따라가거나**, 사람이 **습관적으로 origin 을
      보면** 다시 옛판을 기준으로 판단할 수 있습니다」

    「빌드/배포 전에 origin URL 을 읽어서 **현재 대장 저장소가 아니면
      경고 또는 FAIL** 시키는 게 좋습니다」

★ 지금은 **알림**입니다 (계약-21)
  막음으로 두면 **지금 당장 배포가 멈춥니다** — 아직 이름을 못 바꿨고,
  바꾸는 것은 주인 권한입니다. 고칠 수 없는 것으로 막으면 안 됩니다.
  이름을 바로잡은 뒤 **막음으로 올립니다** (아래 `막음으로` 참고).

  깃허브 액션에서는 `actions/checkout` 이 `origin` 을 대장으로 만들므로
  **언제나 통과**합니다. 혼동은 **사람 컴퓨터에서** 생기고, 이 검사는
  바로 그 자리를 봅니다.

검사 등급 (계약-21)
  막음 — 대장 저장소를 가리키는 원격이 **하나도 없습니다**. 올릴 곳이 없습니다
  알림 — 대장은 있으나 그 이름이 `origin` 이 아닙니다
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ 대장 저장소 — **한 곳에만 적습니다** (주인 규칙 29 의 정신)
대장 = 'ohjunhan-design/badagaja-engine'

# ★ 이름을 바로잡으면 이것을 True 로 올립니다
#     git remote rename origin old-2nd-stopped
#     git remote rename engine origin
막음으로 = False

막음, 알림 = [], []


def _원격들():
    """{이름: 주소} — `git remote -v` 를 읽습니다."""
    try:
        r = subprocess.run(['git', 'remote', '-v'], cwd=ROOT,
                           capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode != 0:
        return None
    것 = {}
    for 줄 in (r.stdout or '').splitlines():
        조각 = 줄.split()
        if len(조각) >= 2 and '(push)' in 줄:
            것[조각[0]] = 조각[1]
    return 것


def _소유(주소):
    """주소에서 `소유자/저장소` 를 뽑습니다. 호스트 별칭도 견딥니다.

    SSH 설정으로 호스트를 갈라 쓰면 주소가 이렇게 생깁니다 —
        git@badagaja-engine.github.com:ohjunhan-design/badagaja-engine.git
    호스트는 **별칭**이라 믿을 수 없으므로 **뒤쪽 두 토막**만 봅니다.
    """
    s = re.sub(r'\.git$', '', (주소 or '').strip())
    s = re.sub(r'^[a-z+]+://', '', s)
    s = re.sub(r'^[^@]+@', '', s)
    토막 = re.split(r'[:/]', s)
    토막 = [x for x in 토막 if x]
    return '/'.join(토막[-2:]) if len(토막) >= 2 else ''


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print('`origin` 이 **대장 저장소**를 가리키는가')
    print('      대장 — %s' % 대장)

    원 = _원격들()
    if 원 is None:
        print('')
        print('  ~ git 을 읽을 수 없습니다 — 건너뜁니다')
        return 0
    if not 원:
        print('')
        print('  ~ 원격이 없습니다 — 건너뜁니다')
        return 0

    print('')
    print('[1] 원격 목록')
    맞는것 = []
    for 이름 in sorted(원):
        s = _소유(원[이름])
        맞 = (s.lower() == 대장.lower())
        if 맞:
            맞는것.append(이름)
        print('      %-18s %-34s %s' % (이름, s or '?', '← 대장' if 맞 else ''))

    print('')
    print('[2] 대장을 가리키는 원격이 있는가')
    if not 맞는것:
        막음.append('대장 저장소를 가리키는 원격이 없습니다')
        print('  ✗ 하나도 없습니다 — **올릴 곳이 없습니다**')
        print('      → git remote add origin git@github.com:%s.git' % 대장)
    else:
        print('  · 있습니다 — %s' % ' · '.join(맞는것))

    print('')
    print('[3] 그 이름이 `origin` 인가')
    if 맞는것 and 'origin' not in 맞는것:
        쪽 = '막음' if 막음으로 else '알림'
        (막음 if 막음으로 else 알림).append(
            '`origin` 이 대장이 아닙니다 (대장은 `%s`)' % 맞는것[0])
        print('  %s `origin` 은 **%s** 를 가리킵니다'
              % ('✗' if 막음으로 else '~', _소유(원.get('origin', '')) or '없음'))
        print('      대장은 `%s` 라는 이름에 붙어 있습니다.' % 맞는것[0])
        print('      → **보통 `origin` 이 대장입니다.** 거꾸로면 사람도 도구도')
        print('        습관적으로 옛 것을 봅니다 (등급 %s).' % 쪽)
        print('      고치려면 —')
        print('        git remote rename origin old-2nd-stopped')
        print('        git remote rename %s origin' % 맞는것[0])
        print('        그 뒤 이 파일의 `막음으로` 를 True 로 올립니다.')
    elif 맞는것:
        print('  · `origin` 이 대장을 가리킵니다')

    print('')
    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  ★ **누가 보든 새 판을 보고 판단해야 합니다** (2026-10-07 주인 지시).')
        return 1
    print('원격 짜임이 헷갈리지 않습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
