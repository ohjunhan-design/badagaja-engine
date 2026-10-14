# -*- coding: utf-8 -*-
"""PHP 를 **올리기 전에** 눈에 띄는 잘못을 잡습니다 (2026-10-14).

★ 왜 만들었나 — 제가 500 을 냈습니다

  차단기 사유 글을 이렇게 썼습니다.

      sprintf(
          '%s %d~%d 를 받았는데 %d일이 **모두 비어** 왔습니다 — '
          '정부가 거부하는 것으로 봅니다',
          ...)

  **파이썬 습관**입니다. 파이썬은 나란한 문자열을 저절로 잇지만
  **PHP 는 잇지 않습니다.** 사이에 `.` 이 있어야 합니다. 없으면
      syntax error, unexpected single-quoted string …, expecting ")"
  가 나고 **사이트가 500** 입니다. 감독실이 새 이름으로 먼저
  올려 잡아냈고, ` .` 한 글자를 더해 고쳤습니다.

  제 컴퓨터에 PHP 가 없어 `php -l` 을 못 돌립니다. 그렇다고
  **서버에 올려 봐야 아는 것**으로 두면 또 500 을 냅니다.
  그래서 **올리기 전에 기계가 봅니다.**

★ 보는 것
  ① **나란한 문자열 리터럴** — PHP 가 못 잇는 자리
  ② 괄호 · 중괄호 · 대괄호 짝
  ③ 닫히지 않은 따옴표
  ④ BOM · CRLF (`.htaccess` 때 배운 것과 같은 뿌리)

★ 보지 못하는 것
  이것은 **PHP 파서가 아닙니다.** 변수 오타, 없는 함수, 논리
  잘못은 못 봅니다. 「여기까지는 기계가 봤다」일 뿐이고,
  **서버에 올린 뒤 응답 코드를 보는 일은 그대로 해야 합니다.**

쓰는 법
    python -m engine.php_lint <파일.php> [...]
    from engine.php_lint import 재기
"""
import io
import os
import sys


def 걷어내기(글):
    """문자열과 주석을 **같은 길이의 공백**으로 바꿉니다.

    길이를 지키므로 줄 번호와 자리가 그대로 남습니다.
    돌려주는 것: (걷어낸 글, 탈 목록)
    """
    남 = []
    탈 = []
    i = 0
    n = len(글)
    줄 = 1
    while i < n:
        c = 글[i]
        if c == '\n':
            줄 += 1
            남.append(c)
            i += 1
            continue
        # 주석 — // # /* */
        if 글.startswith('//', i) or c == '#':
            끝 = 글.find('\n', i)
            끝 = n if 끝 < 0 else 끝
            남.append(' ' * (끝 - i))
            i = 끝
            continue
        if 글.startswith('/*', i):
            끝 = 글.find('*/', i + 2)
            if 끝 < 0:
                탈.append('%d줄 — 주석 `/*` 가 닫히지 않았습니다' % 줄)
                남.append(' ' * (n - i))
                break
            끝 += 2
            남.append(''.join(' ' if x != '\n' else '\n'
                              for x in 글[i:끝]))
            줄 += 글.count('\n', i, 끝)
            i = 끝
            continue
        # 문자열 — ' 또는 "
        if c in ('"', "'"):
            시작줄 = 줄
            j = i + 1
            닫힘 = False
            while j < n:
                if 글[j] == '\\':
                    j += 2
                    continue
                if 글[j] == '\n':
                    줄 += 1
                if 글[j] == c:
                    닫힘 = True
                    break
                j += 1
            if not 닫힘:
                탈.append('%d줄 — 따옴표 %s 가 닫히지 않았습니다'
                          % (시작줄, c))
                남.append(' ' * (n - i))
                break
            # ★ **따옴표 자체는 남깁니다** — ① 검사가 이것을 봅니다
            속 = 글[i + 1:j]
            남.append(c + ''.join(' ' if x != '\n' else '\n' for x in 속) + c)
            i = j + 1
            continue
        남.append(c)
        i += 1
    return ''.join(남), 탈


def 재기(길):
    """한 PHP 파일을 봅니다. 돌려주는 것은 탈 목록(빈 목록이면 성함)."""
    with open(길, 'rb') as f:
        덩이 = f.read()
    탈 = []
    if 덩이[:3] == b'\xef\xbb\xbf':
        탈.append('맨 앞에 BOM 이 있습니다 — 아파치가 그대로 500 을 냅니다')
    if b'\r' in 덩이:
        탈.append('CRLF 줄바꿈이 섞여 있습니다')
    글 = 덩이.decode('utf-8', 'replace')

    걷, 탈2 = 걷어내기(글)
    탈 += 탈2

    # ── ① 나란한 문자열 리터럴 ──────────────────────────
    #
    #   파이썬은 잇지만 **PHP 는 못 잇습니다.** 사이에 `.` 이
    #   있어야 합니다. 이것이 제가 낸 500 의 까닭입니다.
    줄들 = 걷.split('\n')
    for 번호, 줄 in enumerate(줄들, 1):
        벗 = 줄.rstrip()
        if not 벗:
            continue
        if 벗[-1] not in ('"', "'"):
            continue
        # 다음 줄의 첫 글자
        for 뒤번호 in range(번호, len(줄들)):
            뒤 = 줄들[뒤번호].strip()
            if 뒤:
                break
        else:
            continue
        if 뒤 and 뒤[0] in ('"', "'"):
            탈.append('%d줄 — 문자열 둘이 나란합니다. **PHP 는 저절로 '
                      '잇지 않습니다** — 줄 끝에 ` .` 이 있어야 합니다'
                      % 번호)

    # ── ② 짝 맞추기 ────────────────────────────────────
    for 열, 닫, 이름 in (('(', ')', '괄호'),
                         ('{', '}', '중괄호'),
                         ('[', ']', '대괄호')):
        a, b = 걷.count(열), 걷.count(닫)
        if a != b:
            탈.append('%s 짝이 안 맞습니다 — %s %d개 · %s %d개'
                      % (이름, 열, a, 닫, b))
    return 탈


def main(인자):
    if not 인자:
        print('쓰는 법: python -m engine.php_lint <파일.php> [...]')
        return 2
    모두성함 = True
    못읽음 = 0
    for 길 in 인자:
        if not os.path.isfile(길):
            print('%-44s ✗ 파일이 없습니다' % os.path.basename(길))
            못읽음 += 1
            모두성함 = False
            continue
        탈 = 재기(길)
        if 탈:
            모두성함 = False
            print('%-44s ✗ %d가지' % (os.path.basename(길), len(탈)))
            for x in 탈:
                print('    · %s' % x)
        else:
            print('%-44s 성합니다' % os.path.basename(길))
    print()
    if 못읽음:
        print('[한 줄 요약] 못 읽은 파일이 %d개 있습니다' % 못읽음)
        return 4
    if not 모두성함:
        print('[한 줄 요약] ✗ 올리지 마십시오 — 올리면 500 이 납니다')
        return 1
    print('[한 줄 요약] 눈에 띄는 잘못이 없습니다 '
          '(★ 이것은 PHP 파서가 아닙니다 — 올린 뒤 응답 코드를 '
          '꼭 보십시오)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
