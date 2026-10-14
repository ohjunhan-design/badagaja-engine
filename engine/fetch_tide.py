# -*- coding: utf-8 -*-
"""물때를 **미리 받아 파일로 저장합니다** (2026-10-14 주인 의견 · 총감독 지휘)

★ 왜 만드나
  손님이 올 때마다 서버가 정부 API 를 **하루치씩 30번** 부르는
  구조였습니다. 재어 보니 정부 API 는 건강할 때 **70ms** 인데
  **간헐적으로 응답이 아예 없거나 오류**가 납니다. 그걸 손님이
  그대로 맞아, 강화에서 **32초**를 기다린 손님이 있었습니다.

  간조·만조는 **천문 계산값**이라 내년 시각도 이미 정해져 있습니다.
  날씨처럼 자주 받을 까닭이 없습니다. 그래서 **미리 받아 두고**
  손님은 그 파일만 읽게 합니다.

★ 여기서 하는 일
  · 57권역에 대해 서버의 미리받기 통로를 불러 **30일치**를 받습니다
  · **빈 날이 있으면 다시 받습니다** — 아무도 안 기다리므로
    끈질기게 해도 됩니다(손님이 기다릴 때는 두 번이 한계였습니다)
  · **날짜가 모두 찬 것만** 파일을 바꿉니다.
    일부만 찼으면 **옛 파일을 그대로 둡니다** — 반쪽짜리로
    덮어쓰면 어제까지 멀쩡하던 것이 나빠집니다.

★ 쓰는 법
    python -m engine.fetch_tide                # 전부
    python -m engine.fetch_tide --권역 taean   # 한 곳만
    python -m engine.fetch_tide --날수 14      # 일수 바꾸기
    python -m engine.fetch_tide --확인         # 받지 않고 지금 상태만

  ★ 관리용 암호는 환경변수 **`BADAGAJA_TIDE_ADMIN`** 으로만
    받습니다. **없으면 오류로 끝냅니다** — 코드에 기본값을
    두지 않습니다(이 저장소는 공개입니다).
    이 암호는 정부 열쇠가 아니라 호출 한도를 지키는 문지기이지만,
    드러나면 **누구든 정부 호출을 태울 수** 있습니다.
"""
import argparse
import datetime
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request

여기 = os.path.dirname(os.path.abspath(__file__))
뿌리 = os.path.dirname(여기)
낼곳 = os.path.join(뿌리, 'data', 'tide')

통로 = 'https://badagaja.com/api/tide-cache2.php'
# ★ **관리용 암호는 코드에 두지 않습니다** (2026-10-14 보안 조치)
#   전에는 기본값으로 박아 두었는데, 이 저장소는 **공개**라
#   그대로 드러났습니다. 그 암호로는 간격을 건너뛰고 정부 API
#   호출을 태울 수 있었습니다.
#   ★ 기본값을 두지 않습니다. 없으면 **오류로 끝냅니다** —
#     조용히 안 되는 것보다 크게 멈추는 편이 낫습니다.
암호 = os.environ.get('BADAGAJA_TIDE_ADMIN', '')

기본날수 = 30
한번에기다릴초 = 200        # ★ 재어 보니 같은 주소가 **1.97초~133초** 로
                            #   들쑥날쑥합니다. 아무도 안 기다리므로
                            #   넉넉히 줍니다.
권역사이쉼 = 1.2            # 정부 API 를 몰아치지 않습니다
재시도 = 0                  # ★ 다시 안 합니다 — **합치기**가 맡습니다.
                            #   지금 정부가 느려 구간당 90초입니다.
                            #   한 회차를 짧게 끝내고 **여러 회차**로
                            #   채우는 편이 전체로는 빠릅니다.
재시도쉼 = 5.0


def 권역목록():
    """생성기가 쓰는 **같은 자료**에서 셉니다 (규칙 29)."""
    sys.path.insert(0, 뿌리)
    from engine import build
    d = build.자료()
    것 = []
    for r in d.권역들:
        이름 = (r.get('이름') or {}).get('ko') or r['id']
        것.append((r['id'], 이름))
    return 것


구간크기 = 20          # 한 요청에 이만큼씩 — 90초 상한에 안 걸리게


def 한번받기(권역, 날수, 부터=0):
    주소 = '%s?region=%s&days=%d&t=%s' % (통로, 권역, 날수, 암호)
    if 부터 > 0:
        주소 += '&from=%d' % 부터
    요청 = urllib.request.Request(
        주소, headers={'User-Agent': 'badagaja-prefetch/1.0'})
    t0 = time.time()
    try:
        몸 = urllib.request.urlopen(
            요청, timeout=한번에기다릴초).read().decode('utf-8', 'replace')
    except Exception as e:
        return None, time.time() - t0, '못 받음(%s)' % type(e).__name__
    try:
        d = json.loads(몸)
    except Exception:
        return None, time.time() - t0, '글이 깨졌습니다'
    return d, time.time() - t0, None


def 빈날세기(d, 날수):
    날 = d.get('days') or []
    빈 = [x.get('date') for x in 날 if not (x.get('events') or [])]
    return 날, 빈


def 날짜키(x):
    return x.get('date') or ''


def 합치기(옛자료, 새자료):
    """★ **조석은 변하지 않습니다** — 그래서 합쳐도 됩니다.

    10/19 의 간조·만조는 어제 받든 오늘 받든 **같은 값**입니다.
    그러니 한 번만 성공하면 그 날은 영영 채워진 것입니다.

    정부 API 가 들쑥날쑥해서 받을 때마다 **다른 날이 빕니다.**
    한 번에 다 채우려 하면 오래 걸리고 그래도 못 채웁니다.
    대신 **채워진 것만 모아 두면** 몇 번에 걸쳐 저절로 다 찹니다.

    ★ **차례도 함께 합칩니다** (2026-10-14 고침)
      전에는 새로 받은 것의 차례만 썼습니다. 그래서 60일을 달라
      했는데 서버가 상한에 걸려 20일만 주면, 이미 있던 30일이
      **20일로 줄었습니다.** 옛 차례를 먼저 두고 새 날짜를 뒤에
      더하면 **늘기만 하고 줄지 않습니다.**

    돌려주는 것: (날짜→날 사전, 날짜 차례 목록)
    """
    모음 = {}
    차례 = []
    for 묶음 in (옛자료, 새자료):
        if not 묶음:
            continue
        for x in (묶음.get('days') or []):
            키 = 날짜키(x)
            if not 키:
                continue
            찬것 = bool(x.get('events'))
            if 키 not in 모음:
                모음[키] = x
                차례.append(키)
            elif 찬것 and not 모음[키].get('events'):
                모음[키] = x
    return 모음, 차례


def 차례대로(모음, 차례, 새자료, 날수):
    """오늘부터 날수만큼 줄 세웁니다.

    ★ **오늘은 새로 받은 것의 첫 날**입니다 — 서버는 늘 오늘부터
      만들어 줍니다. 그 앞(지난 날)은 버립니다.
    """
    첫 = None
    for x in (새자료.get('days') or []):
        첫 = 날짜키(x)
        break
    자리 = 0
    if 첫 and 첫 in 차례:
        자리 = 차례.index(첫)
    줄 = []
    for 키 in 차례[자리:자리 + 날수]:
        if 키 in 모음:
            줄.append(모음[키])
    return 줄


def 옛파일읽기(권역):
    """이미 받아 둔 것을 읽습니다 — **합치기의 바탕**입니다."""
    p = os.path.join(낼곳, '%s.json' % 권역)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(io.open(p, encoding='utf-8'))
    except Exception:
        return None


def 한권역(권역, 이름, 날수, 조용히=False):
    """★ **구간으로 나눠** 받아 날짜로 합칩니다.

    60일을 한 번에 달라 하면 서버가 90초 상한에 걸려 앞쪽
    20~30일만 줍니다. 그리고 서버는 **늘 오늘부터** 세므로
    여러 번 받아도 **뒷날이 영영 안 옵니다.**
    그래서 0~19 · 20~39 · 40~59 로 나눠 받습니다.

    돌려주는 것: (저장할 자료, 말, 빈 날 + 모자란 날)
    """
    옛 = 옛파일읽기(권역)
    쌓임 = None
    기준 = None          # 날짜 차례의 바탕 — 첫 구간(오늘부터)
    말들 = []

    부터목록 = list(range(0, 날수, 구간크기))
    for 부터 in 부터목록:
        이구간 = min(구간크기, 날수 - 부터)
        for 차 in range(1 + 재시도):
            d, 초, 탈 = 한번받기(권역, 부터 + 이구간, 부터)
            if 탈:
                말들.append('%d~ %s(%.0f초)' % (부터, 탈, 초))
                if 차 < 재시도:
                    time.sleep(재시도쉼)
                continue
            받은 = d.get('days') or []
            빈이구간 = sum(1 for x in 받은 if not x.get('events'))
            말들.append('%d~ %d일(빈%d,%.0f초)'
                        % (부터, len(받은), 빈이구간, 초))
            if 부터 == 0:
                기준 = d
            if 쌓임 is None:
                바탕 = 옛
            else:
                바탕 = 쌓임
            모음, 날차례 = 합치기(바탕, d)
            if 기준 is None:
                기준 = d
            줄 = 차례대로(모음, 날차례, 기준, 날수)
            쌓임 = dict(기준)
            쌓임['days'] = 줄
            if 빈이구간 == 0 and len(받은) >= 이구간:
                break      # 이 구간은 다 찼습니다
            if 차 < 재시도:
                time.sleep(재시도쉼)
        time.sleep(0.8)    # 구간 사이에도 조금 쉽니다

    if 쌓임 is None:
        return None, ' · '.join(말들) + ' → **못 받음, 안 바꿈**', -1

    빈 = [날짜키(x) for x in 쌓임['days'] if not x.get('events')]
    모자람 = 날수 - len(쌓임['days'])
    꼬리 = ''
    if 모자람 > 0:
        꼬리 = ' · **%d일 모자람**' % 모자람
    if not 빈 and 모자람 <= 0:
        return 쌓임, ' · '.join(말들) + ' → **다 참**', 0
    return (쌓임,
            ' · '.join(말들) + ' → 빈 %d%s' % (len(빈), 꼬리),
            len(빈) + max(0, 모자람))


def 서울오늘():
    """한국 날짜의 `달/일` 키.

    ★ 윈도는 이미 한국 시간입니다. `TZ=` 를 주면 아홉 시간
      빠져 **어제가 오늘이 됩니다.** 그래서 그냥 씁니다.
    """
    t = datetime.datetime.now()
    return '%d/%d' % (t.month, t.day)


def 남은날세기(자료):
    """오늘부터 **이어지는** 날이 며칠인가. 오늘이 없으면 0."""
    날들 = (자료 or {}).get('days') or []
    키들 = [날짜키(x) for x in 날들]
    오늘 = 서울오늘()
    if 오늘 not in 키들:
        return 0
    return len(날들) - 키들.index(오늘)


def 저장(권역, d):
    """★ 다 찬 것만 여기까지 옵니다.

    ★ **날 수가 줄면 쓰지 않습니다** (2026-10-14 감독실 승인)

      겪은 일: `data/tide/` 의 samcheok·ulleung 이 **30일 → 14일**로
      덮여 있었고, 조금 뒤 gangneung·gwgoseong 은 **50일 → 14일**
      이었습니다. 구간 받기가 일부만 성공하면 짧은 것이 그대로
      쓰입니다. 조용히 덮으니 아무도 모릅니다.

      조석은 변하지 않으므로 **긴 것이 언제나 낫습니다.**
      줄어드는 쓰기는 **잃는 일**이지 고치는 일이 아닙니다.
      그래서 **거부하고 까닭을 말합니다** — 조용히 지나가면
      다음에 또 당합니다.
    """
    os.makedirs(낼곳, exist_ok=True)
    p = os.path.join(낼곳, '%s.json' % 권역)
    글 = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    옛 = None
    옛자료 = None
    if os.path.isfile(p):
        옛 = io.open(p, encoding='utf-8').read()
        try:
            옛자료 = json.loads(옛)
        except Exception:
            옛자료 = None          # 깨진 파일은 덮어도 됩니다
    if 옛 == 글:
        return '같습니다'

    if 옛자료 is not None:
        옛남 = 남은날세기(옛자료)
        새남 = 남은날세기(d)
        if 새남 < 옛남:
            return ('★ 쓰지 않았습니다 — 날이 줄어듭니다 '
                    '(지금 %d일 → 쓸 것 %d일). 조석은 변하지 않으니 '
                    '긴 것이 낫습니다' % (옛남, 새남))

    io.open(p, 'w', encoding='utf-8', newline='\n').write(글)
    return '새로 썼습니다' if 옛 is None else '바꿨습니다'


def 지금상태(것, 날수):
    print('지금 저장된 것 (%s)' % 낼곳)
    있 = 0
    for 권역, 이름 in 것:
        p = os.path.join(낼곳, '%s.json' % 권역)
        if not os.path.isfile(p):
            print('   %-12s **없습니다**' % 이름)
            continue
        있 += 1
        d = json.load(io.open(p, encoding='utf-8'))
        날, 빈 = 빈날세기(d, 날수)
        첫 = (날[0].get('date') if 날 else '-')
        끝 = (날[-1].get('date') if 날 else '-')
        print('   %-12s %2d일 (%s~%s) · 빈 날 %d개 · %.1fKB'
              % (이름, len(날), 첫, 끝, len(빈),
                 os.path.getsize(p) / 1024.0))
    print('\n%d곳 중 **%d곳**이 저장되어 있습니다' % (len(것), 있))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--권역', default='')
    p.add_argument('--날수', type=int, default=기본날수)
    p.add_argument('--확인', action='store_true')
    a = p.parse_args()

    if not 암호:
        print('관리용 암호가 없습니다.')
        print('환경변수 **BADAGAJA_TIDE_ADMIN** 에 넣고 다시 하십시오.')
        print('(암호는 저장소에 두지 않습니다 — 감독실 작업 폴더에')
        print(' 있습니다. 코드·문서·메시지에 적지 마십시오)')
        return 2

    것 = 권역목록()
    if a.권역:
        것 = [x for x in 것 if x[0] == a.권역]
        if not 것:
            print('그런 권역이 없습니다: %s' % a.권역)
            return 1

    if a.확인:
        지금상태(것, a.날수)
        return 0

    print('물때를 미리 받습니다 — %d곳 × %d일' % (len(것), a.날수))
    print('통로 %s' % 통로)
    print('(빈 날이 있으면 최대 %d번 더 해 봅니다)\n' % 재시도)

    다찬곳 = 0
    남은빈날 = 0
    못받은곳 = []
    바뀐것 = 0
    시작 = time.time()
    for i, (권역, 이름) in enumerate(것, 1):
        d, 말, 빈수 = 한권역(권역, 이름, a.날수)
        if d is not None:
            어찌 = 저장(권역, d)
            if 어찌 != '같습니다':
                바뀐것 += 1
            if 빈수 == 0:
                다찬곳 += 1
            else:
                남은빈날 += 빈수
            print('%3d/%d %-12s %s · %s' % (i, len(것), 이름, 말, 어찌))
        else:
            못받은곳.append((이름, 말))
            print('%3d/%d %-12s %s' % (i, len(것), 이름, 말))
        if i < len(것):
            time.sleep(권역사이쉼)

    걸린 = time.time() - 시작
    print('')
    print('-' * 56)
    print('%d일이 **다 찬 곳 %d/%d** · 파일이 바뀐 곳 %d · %.1f분'
          % (a.날수, 다찬곳, len(것), 바뀐것, 걸린 / 60.0))
    if 남은빈날:
        print('아직 빈 날 모두 %d개 — **다음 번에 채워집니다**'
              % 남은빈날)
        print('  조석은 변하지 않으므로 한 번만 성공하면 그 날은 끝입니다')
    if 못받은곳:
        print('')
        print('한 번도 못 받은 곳 %d곳 — **옛 파일 그대로 둡니다**'
              % len(못받은곳))
        for 이름, 말 in 못받은곳:
            print('   %-12s %s' % (이름, 말))
    print('')
    print('※ 못 채워도 손님 화면은 멀쩡합니다 — 옛 파일이 있고,')
    print('  그것도 없으면 지금까지 쓰던 길로 갑니다.')
    return 1 if (못받은곳 and len(못받은곳) == len(것)) else 0

if __name__ == '__main__':
    sys.exit(main())
