# -*- coding: utf-8 -*-
"""자료가 언제 갱신됐는지, 기한이 지나지 않았는지 봅니다. (주인 규칙 30)

왜
    「갱신은 data/refresh-plan.json(갱신 대장) 한곳에서 봅니다.
      무엇을 얼마나 자주 갱신하는지, 어디서 왔는지, 자동인지 손인지를
      한 파일에 적습니다. 새 자료를 넣으면 대장에도 한 줄 더합니다」
                                          (주인 규칙 30, 2026-09-26)

    자료가 늘수록 「언제 무엇을 갱신해야 하는지」가 도구와 일꾼에
    흩어집니다. 한곳에 모으고 여기서 봅니다.

★ 마지막 갱신일은 **git 기록에서 읽습니다.** 손으로 안 적습니다.
    손으로 적으면 고치는 것을 잊고, 그러면 대장이 거짓이 됩니다.

★ 막지 않습니다 (계약-21)
    자료가 좀 낡았다고 배포를 멈출 일은 아닙니다. 알려만 줍니다.
    다만 **정직하게** 알립니다 — 쪽에 「○○년 ○월 기준」을 밝히는 것과
    짝을 이룹니다.

쓰는 법
    python engine/check_refresh.py
    python engine/check_refresh.py --strict    기한 지난 것이 있으면 1
"""
import os
import sys
import glob
import datetime
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

막음, 알림 = [], []


def _진짜길(무늬):
    """대장에 적힌 'data/raw/...' 를 실제 자리로 바꿉니다.

    ★ 자료가 딴 자리(시험용 사본)에 있어도 돌아야 합니다 (2026-09-27)
      전에는 ROOT 만 붙여, 사본이 다른 드라이브에 있으면
      os.path.relpath 가 넘어졌습니다.
    """
    if 무늬.startswith('data/'):
        return os.path.join(DATA, 무늬[len('data/'):].replace('/', os.sep))
    return os.path.join(ROOT, 무늬)


def 마지막손댄날(길들):
    """그 파일들을 마지막으로 고친 날 — **git 기록에서** 읽습니다."""
    가장최근 = None
    for 무늬 in 길들:
        for p in glob.glob(_진짜길(무늬)):
            try:
                r = subprocess.run(
                    ['git', 'log', '-1', '--format=%cI', '--', p],
                    cwd=ROOT, capture_output=True, text=True, timeout=30)
            except OSError:
                continue
            s = (r.stdout or '').strip()
            if not s:
                continue
            try:
                날 = datetime.datetime.fromisoformat(s).date()
            except ValueError:
                continue
            if 가장최근 is None or 날 > 가장최근:
                가장최근 = 날
    if 가장최근 is None:
        # ★ git 을 못 읽으면 파일 시각으로 떨어집니다 (2026-09-27)
        #   자료를 내려받은 사본이나 git 밖에서도 재야 합니다.
        #   git 이 있으면 git 이 이깁니다 — 파일 시각은 옮기기만 해도
        #   바뀌어 미덥지 않기 때문입니다.
        for 무늬 in 길들:
            for p2 in glob.glob(_진짜길(무늬)):
                try:
                    날 = datetime.date.fromtimestamp(os.path.getmtime(p2))
                except OSError:
                    continue
                if 가장최근 is None or 날 > 가장최근:
                    가장최근 = 날
    return 가장최근


def main():
    자리 = os.path.join(DATA, 'raw', 'refresh-plan.json')
    대장 = io.read_json(자리, default=None)
    if 대장 is None:
        print('갱신 대장이 없습니다: data/raw/refresh-plan.json')
        print('  주인 규칙 30 — 갱신은 대장 한곳에서 봅니다.')
        return 1

    것들 = [x for x in (대장.get('자료') or []) if not str(
        x.get('key', '')).startswith('_')]
    오늘 = datetime.date.today()

    print('자료 갱신 대장 (주인 규칙 30)')
    print('  적힌 자료 %d갈래' % len(것들))
    print('')
    print('  %-16s %-6s %-6s %-12s %s'
          % ('자료', '주기', '방법', '마지막 갱신', '지난 날'))

    지난것, 모르는것 = [], []
    for x in 것들:
        파일 = x.get('파일') or []
        날 = 마지막손댄날(파일) if 파일 else None
        지남 = (오늘 - 날).days if 날 else None
        기한 = x.get('유효기간일')
        표 = ' '
        # ★ 「기한 is not None」 입니다 (2026-09-27 시험이 잡음)
        #   「if 기한」 으로 두었더니 기한이 0 일 때 건너뛰었습니다.
        #   0 은 「기한 없음」이 아니라 「오늘까지」입니다.
        #
        # ★ **>= 입니다** (2026-09-28 뮤테이션이 잡음)
        #   주석에는 「오늘까지」라 적어 두고 코드는 > 라서
        #   하루를 더 봐주고 있었습니다. 글과 코드가 달랐습니다.
        #   기한 0 이면 오늘(지남 0) 이미 지난 것입니다.
        #   기한 180 이면 180일째에 알립니다 — 넘긴 뒤가 아니라
        #   넘기는 날 알려야 갱신할 틈이 있습니다.
        if 기한 is not None and 지남 is not None and 지남 >= 기한:
            표 = '~'
            지난것.append((x['이름'], 지남, 기한))
        elif 파일 and 날 is None:
            표 = '?'
            모르는것.append(x['이름'])
        print('  %s %-14s %-6s %-6s %-12s %s'
              % (표, x['이름'], x.get('주기', '?'), x.get('방법', '?'),
                 날.isoformat() if 날 else ('실시간' if not 파일 else '모름'),
                 ('%d일' % 지남) if 지남 is not None else '-'))
    print('')

    # 대장에 안 적힌 자료가 있나 — 적지 않으면 잊힙니다
    적힌파일 = set()
    for x in 것들:
        for 무늬 in (x.get('파일') or []):
            for p in glob.glob(_진짜길(무늬)):
                적힌파일.add(os.path.relpath(p, DATA).replace(os.sep, '/'))
    있는파일 = set()
    for p in glob.glob(os.path.join(DATA, 'raw', '**', '*.json'),
                       recursive=True):
        길 = os.path.relpath(p, DATA).replace(os.sep, '/')
        # 대장 자신은 셈에서 뺍니다 — 대장이 대장을 적을 까닭이 없습니다
        if 길.endswith('refresh-plan.json'):
            continue
        있는파일.add(길)
    안적힌것 = sorted(있는파일 - 적힌파일)

    # ★ 적은 길이 아무것도 못 가리키면 — 적어도 안 적은 것과 같습니다
    #   (2026-09-27 — 'raw/…' 와 'data/raw/…' 를 헷갈려 겪었습니다)
    헛길 = []
    for x in 것들:
        for 무늬 in (x.get('파일') or []):
            if not glob.glob(_진짜길(무늬)):
                헛길.append('%s — %s' % (x['이름'], 무늬))
    print('[0] 대장에 적은 길이 진짜 파일을 가리키는가')
    if 헛길:
        막음.append('아무것도 안 가리키는 길 %d개' % len(헛길))
        print('  ✗ %d개 — **적어 놓고도 안 적은 것과 같습니다**' % len(헛길))
        for x in 헛길:
            print('      %s' % x)
        print('      → 다른 줄들처럼 data/raw/… 로 적었는지 보세요.')
    else:
        print('  · 적은 길이 모두 진짜 파일을 가리킵니다')
    print('')

    print('[1] 대장에 안 적힌 자료')
    if 안적힌것:
        알림.append('대장에 안 적힌 자료 %d개' % len(안적힌것))
        print('  ~ %d개 — 적지 않으면 갱신을 잊습니다' % len(안적힌것))
        for x in 안적힌것[:6]:
            print('      %s' % x)
        if len(안적힌것) > 6:
            print('      … 그 밖 %d개' % (len(안적힌것) - 6))
    else:
        print('  · 자료가 모두 대장에 있습니다')
    print('')

    print('[2] 기한이 지난 자료')
    if 지난것:
        알림.append('기한 지난 자료 %d갈래' % len(지난것))
        print('  ~ %d갈래' % len(지난것))
        for 이름, 지남, 기한 in 지난것:
            print('      %-16s %d일 지남 (기한 %d일)' % (이름, 지남, 기한))
    else:
        print('  · 기한을 넘긴 자료가 없습니다')
    if 모르는것:
        print('  ~ 갱신일을 못 읽은 자료 %d갈래: %s'
              % (len(모르는것), ' · '.join(모르는것[:4])))
        print('    (아직 커밋 안 한 파일일 수 있습니다)')
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (배포를 막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ~ %s' % x)
        print('')
        print('  3,603곳을 매달 다시 확인할 수는 없습니다. 그러나')
        print('  **언제 것인지 밝히면 최신이 아니어도 정직합니다.**')
        return 1 if '--strict' in sys.argv else 0
    print('갱신이 제때 되고 있습니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
