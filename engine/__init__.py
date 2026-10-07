# -*- coding: utf-8 -*-
"""엔진 꾸러미 — **한글을 낼 수 있게 먼저 맞춥니다.**

★ 왜 여기서 (2026-10-07)
  주인 컴퓨터(윈도)의 기본 콘솔은 **cp949** 입니다. 검사기가 「—」나
  「✗」를 내는 순간 `UnicodeEncodeError` 로 **통째로 죽습니다.**

      File "engine/check_photos.py", line 130, in main
      UnicodeEncodeError: 'cp949' codec can't encode character '—'

  재 보니 `main()` 이 있는 파일 **65개 가운데 대부분**이 인코딩을
  안 맞추고 있었습니다. 그런데 **깃허브(우분투)는 UTF-8 이 기본**이라
  거기서는 멀쩡히 돕니다. 즉 **주인 컴퓨터에서만** 죽습니다.
  판정은 통과하는데 사람이 손으로 돌리면 죽는 것입니다.

  65곳에 같은 두 줄을 넣는 대신 **여기 한 곳**에서 맞춥니다.
  모든 검사기가 `from engine import …` 로 이 꾸러미를 거칩니다.

★ 사람이 이미 정해 두었으면 **건드리지 않습니다**
  `PYTHONIOENCODING` 을 손으로 준 경우, 파이프로 넘기는 경우에는
  그쪽 뜻을 따릅니다.
"""
import os
import sys


def _한글낼수있게():
    """표준 출력이 한글을 못 내면 **UTF-8 로 맞춥니다.**"""
    if os.environ.get('PYTHONIOENCODING'):
        return                       # 사람이 정했으면 그대로 둡니다
    for 흐름 in (sys.stdout, sys.stderr):
        고치기 = getattr(흐름, 'reconfigure', None)
        if 고치기 is None:
            continue                 # 파이프로 바꿔치기한 경우
        이름 = (getattr(흐름, 'encoding', '') or '').lower()
        if 'utf-8' in 이름 or 'utf8' in 이름:
            continue
        try:
            고치기(encoding='utf-8', errors='replace')
        except (OSError, ValueError):
            pass                     # 못 바꿔도 그냥 갑니다


_한글낼수있게()
