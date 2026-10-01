# -*- coding: utf-8 -*-
"""올린 것이 **내가 만든 바로 그것인지** 증명할 지문을 만듭니다.

★ 왜 생겼나 (2026-09-27 바깥 검수 3차)

      「check_deployed.py 에는 하나 더 넣는 것을 권합니다 — 배포 버전
        식별자. 그러면 내 PC 의 commit abc123 과 서버의 abc123 을
        직접 비교할 수 있습니다. 파일 하나만 달라도 SHA-256 으로
        잡히게 하면 더 좋습니다. **「서버가 내 것과 같다」라는 검사를
        진짜 증명 가능한 검사로 만드는 방법**입니다」

    지금까지는 몇 쪽만 골라 글자를 견주었습니다. 고른 쪽이 같으면
    나머지도 같으려니 했습니다. 그것은 짐작입니다.

무엇을 만드나
    site/build.json 한 파일입니다.

        커밋      지금 git 커밋 (짧게 7자 + 온전한 40자)
        쪽수      만든 쪽 수
        통지문    site/ 밑 **모든 파일**의 SHA-256 을 합쳐 낸 지문
        파일      파일마다의 SHA-256 (여기서 하나만 달라도 갈립니다)

★ 만든 시각은 **일부러 안 넣습니다** (계약-07)
    자료를 안 고쳤으면 다시 만들어도 결과가 같아야 합니다.
    시각을 넣으면 돌릴 때마다 달라져 멱등성 검사가 깨집니다.
    「언제 만들었나」는 git 기록이 압니다 (주인 규칙 30).

★ build.json 자신은 지문에서 뺍니다
    제 지문을 제 안에 담을 수는 없습니다.

쓰는 법
    python engine/build_id.py            site/build.json 을 만듭니다
    python engine/build_id.py --보기     지금 판을 보여 줍니다
"""
import os
import sys
import glob
import hashlib
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

SITE = os.environ.get('BADAGAJA_SITE', os.path.join(ROOT, 'site'))
판이름 = 'build.json'


def 지금커밋():
    """git 이 아는 지금 커밋. 없으면 None — **모른다고 적습니다.**"""
    try:
        r = subprocess.run(['git', 'rev-parse', 'HEAD'],
                           cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', timeout=30)
        if r.returncode == 0 and (r.stdout or '').strip():
            return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def 파일들(뿌리=None):
    뿌리 = 뿌리 or SITE
    나옴 = []
    for p in glob.glob(os.path.join(뿌리, '**', '*'), recursive=True):
        if not os.path.isfile(p):
            continue
        키 = os.path.relpath(p, 뿌리).replace(os.sep, '/')
        if 키 == 판이름:        # 제 지문을 제 안에 담을 수는 없습니다
            continue
        나옴.append((키, p))
    return sorted(나옴)


def 지문들(뿌리=None):
    나옴 = {}
    for 키, p in 파일들(뿌리):
        with open(p, 'rb') as f:
            나옴[키] = hashlib.sha256(f.read()).hexdigest()
    return 나옴


def 통지문(것들):
    """파일 지문들을 합쳐 낸 하나의 지문. 차례가 정해져 있어야 합니다."""
    h = hashlib.sha256()
    for 키 in sorted(것들):
        h.update(키.encode('utf-8'))
        h.update(b'\x00')
        h.update(것들[키].encode('ascii'))
        h.update(b'\n')
    return h.hexdigest()


def 커밋날짜():
    """지금 커밋의 날짜 (YYYY-MM-DD).

    ★ **만든 시각 대신 커밋 날짜**를 씁니다 (2026-10-01).
      시각을 넣으면 돌릴 때마다 달라져 멱등성 검사가 깨집니다
      (계약-07). 커밋 날짜는 git 이 아는 값이라 다시 만들어도
      같고, 「언제 것인가」도 알 수 있습니다.
    """
    try:
        r = subprocess.run(
            ['git', 'log', '-1', '--format=%cs'],
            cwd=ROOT, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=20)
        return (r.stdout or "").strip() or None
    except Exception:
        return None


배포판 = 1          # 판 지문의 꼴이 바뀌면 올립니다


def 만들기(뿌리=None):
    뿌리 = 뿌리 or SITE
    것들 = 지문들(뿌리)
    커밋 = 지금커밋()
    날짜 = 커밋날짜()
    쪽수 = sum(1 for k in 것들 if k.endswith('.html'))
    통 = 통지문(것들)
    # ★ **한 줄 요약** (2026-10-01 지피티 제안)
    #   바깥에서 검수할 때 이 한 줄만 보면 같은 판인지 압니다.
    #   오늘 지피티가 옛 사본을 보고 「239MB·_stage 80MB」라
    #   했는데 실제 배포본은 107.6MB·_stage 없음이었습니다.
    #   둘 다 틀리지 않았습니다 — **본 것이 달랐을 뿐**입니다.
    한줄 = ('바다가자 판 %s · %s · %d쪽 · %d파일 · %s'
            % (커밋[:7] if 커밋 else '(모름)', 날짜 or '(모름)',
               쪽수, len(것들), 통[:8]))
    판 = {
        '_한줄': 한줄,
        '_무엇인가': '이 판이 무엇인지 증명하는 지문입니다. '
                     'engine/build_id.py 가 만듭니다. 손으로 고치지 마세요.',
        '_왜있나': '올린 것이 내가 만든 바로 그것인지 서버에서 확인하려고. '
                   'engine/check_deployed.py --net 이 견줍니다.',
        '커밋': 커밋 or '(모름)',
        '커밋짧게': (커밋[:7] if 커밋 else '(모름)'),
        '커밋날짜': 날짜 or '(모름)',
        '배포판': 배포판,
        '쪽수': 쪽수,
        '파일수': len(것들),
        '통지문': 통,
        '파일': 것들,
    }
    io.write_json(os.path.join(뿌리, 판이름), 판)
    return 판


def 읽기(뿌리=None):
    return io.read_json(os.path.join(뿌리 or SITE, 판이름), default=None)


def main():
    if '--보기' in sys.argv:
        판 = 읽기()
        if not 판:
            print('아직 판이 없습니다. python engine/build_id.py 로 만듭니다.')
            return 1
    else:
        판 = 만들기()
        print('판 지문을 만들었습니다: site/%s' % 판이름)
    print('')
    print('  커밋    %s' % 판.get('커밋짧게'))
    print('  쪽 수   %d' % 판.get('쪽수', 0))
    print('  파일 수 %d' % 판.get('파일수', 0))
    print('  통지문  %s' % 판.get('통지문', '')[:32])
    if 판.get('커밋') == '(모름)':
        print('')
        print('  ~ git 커밋을 못 읽었습니다 — 서버와 견줄 때 커밋은 못 씁니다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
