# -*- coding: utf-8 -*-
"""어종 안내를 손보다 **있던 것을 잃지 않았는지** 봅니다.

★ 2026-09-30 — 자료를 늘리다 오히려 **지웠습니다**

    주인 지시 20 「어종별 채비법과 잡는방법 미끼 등등 전수해서 데이터 확보해」
    를 하면서 지식백과 자료로 어종 칸을 다시 썼습니다.
    그런데 **덮어쓰는 바람에 원래 있던 것이 사라졌습니다.**

      · 우럭 — 「봉돌을 맨 아래 달고 바늘 두 개를 다는 바닥 채비」가
                통째로 없어지고 루어 이야기만 남았습니다.
                그러면서 쪽에 붙는 채비도는 그대로 **원투 채비도**여서,
                글과 그림이 서로 다른 말을 하고 있었습니다
      · 볼락 — 「민장대에 구슬찌」가 사라졌습니다
      · 숭어 — **「훌치기는 지역에 따라 금지」** 가 사라졌습니다.
                규정에 관한 말이라 없어지면 손님이 다칠 수 있습니다

    `check_golden.py` 는 **쪽의 글자 수와 링크 수**를 봅니다.
    글을 늘리면서 딴것을 지우면 합계는 오히려 늘어나 **안 걸립니다.**
    그래서 **낱말 단위**로 따로 봅니다.

무엇을 보나
    이전 판(git HEAD)의 어종 안내에 있던 **뜻이 큰 낱말**이
    지금 판의 그 어종 어딘가에 남아 있는가.
    칸이 바뀐 것은 잘못이 아닙니다 — 채비에 있던 「미노우」를
    미끼로 옮긴 것처럼요. 그래서 **쪽 전체를 하나로 합쳐** 봅니다.

    처음 만드는 어종(이전 판에 없던 것)은 볼 것이 없으니 건너뜁니다.
"""
import io
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
자료 = os.path.join(ROOT, 'data', 'raw', 'guide.json')

# 사라지면 안 되는 말 — 채비 갈래·미끼·규정처럼 **뜻이 큰 것**만 봅니다.
#   흔한 말(「좋습니다」 같은)까지 보면 글을 다듬을 때마다 걸려
#   검사기가 도리어 걸림돌이 됩니다.
지킬말 = (
    # 채비 갈래
    '원투', '바닥 채비', '다운샷', '민장대', '구슬찌', '전유동', '반유동',
    '처넣기', '맥낚시', '찌낚시', '던질', '카드', '어피', '훌치기', '에깅',
    # 미끼·루어
    '루어', '지그헤드', '미노우', '바이브', '웜', '크릴', '갯지렁이',
    '떡밥', '밑밥', '집어제', '홍합', '깐새우', '전갱이', '새우', '게',
    # 규정·안전
    '금지', '금어기', '놓아주',
)

칸들 = ('채비', '미끼', '어디서', '언제', '귀띔', '한줄', '먹는법', '손질법')


def 모두(x):
    """한 어종의 글을 모두 이어 붙입니다 (칸이 바뀐 것은 잘못이 아닙니다)."""
    조각 = [(x.get(k) or {}).get('ko') or '' for k in 칸들]
    조각 += [(it.get('ko') or '') for it in (x.get('이렇게') or [])]
    return ' '.join(조각)


def 이전판():
    """git HEAD 의 guide.json 을 읽습니다. 못 읽으면 None."""
    난 = subprocess.run(['git', 'show', 'HEAD:data/raw/guide.json'],
                        cwd=ROOT, capture_output=True)
    if 난.returncode != 0 or not 난.stdout:
        return None
    try:
        return json.loads(난.stdout.decode('utf-8'))['어종']
    except Exception:
        return None


# 검사 등급 (계약-21)
#   막음 — 있던 말이 사라졌습니다. 고쳐야 합니다
#   알림 — 잴 수 없었습니다. 막지는 않습니다
막음, 알림 = [], []


def main():
    엄격 = '--strict' in sys.argv
    print('어종 안내를 손보다 있던 것을 잃지 않았는가')

    옛것 = 이전판()
    if 옛것 is None:
        알림.append('이전 판을 못 읽었습니다 — 견줄 것이 없습니다')
        print('  ~ 이전 판을 못 읽었습니다 (git 기록이 없거나 첫 커밋입니다)')
        print('     — 견줄 것이 없어 건너뜁니다.')
        print('')
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ! %s' % x)
        return 0

    지금 = json.load(io.open(자료, encoding='utf-8'))['어종']
    옛 = {x['이름']['ko']: x for x in 옛것}
    print('  어종 %d가지 · 지킬 말 %d개' % (len(지금), len(지킬말)))
    print('')

    잃은것 = []
    본것 = 0
    for x in 지금:
        이름 = x['이름']['ko']
        o = 옛.get(이름)
        if not o:
            continue                      # 새로 만든 어종
        본것 += 1
        a, b = 모두(o), 모두(x)
        빠진 = [w for w in 지킬말 if w in a and w not in b]
        if 빠진:
            잃은것.append((이름, 빠진))

    if 잃은것:
        for 이름, 빠진 in 잃은것:
            막음.append('%s — %s' % (이름, ' · '.join(빠진)))
        print('  ✗ 있던 말이 사라진 어종 %d가지' % len(잃은것))
        for 이름, 빠진 in 잃은것:
            print('      %-8s %s' % (이름, ' · '.join(빠진)))
    else:
        print('  · 어종 %d가지에서 있던 말이 하나도 안 사라졌습니다' % 본것)
    print('')

    if 알림:
        print('살펴볼 것 %d가지 (막지 않습니다)' % len(알림))
        for x in 알림:
            print('  ! %s' % x)
        print('')
    if 막음:
        print('손볼 곳 %d가지' % len(막음))
        for x in 막음:
            print('  ✗ %s' % x)
        print('')
        print('  **늘리려다 지운 것이 아닌지 보세요.**')
        print('  덮어쓰지 말고, 옛 뜻을 품은 채 늘립니다.')
        print('  정말 빼는 것이 맞다면 이 파일의 `지킬말` 에서 빼세요.')
        return 1 if 엄격 else 0
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
