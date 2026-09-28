# -*- coding: utf-8 -*-
"""이관 도구를 **두 번 돌려도 같은지** 봅니다.

★ 왜 이 시험이 필요한가 (2026-09-26 바깥 검수 요구)

    「다섯 이관 도구의 멱등성을 전수 시험해야 합니다」

    이관 도구는 옛 사이트에서 자료를 캐 data/raw/ 에 씁니다.
    자료가 매달 갱신되니 **여러 번 돌게 됩니다.** 그때 결과가
    조금씩 달라지면, 500여 쪽이 조금씩 흔들립니다.

    실제로 겪었습니다. fix_species 를 두 번 돌리니 자료가 망가졌는데,
    개수는 두 번 다 같아서(104가지·13,250건) 한동안 몰랐습니다.
    **개수만 보면 못 잡습니다. 내용을 통째로 견줘야 합니다.**

무엇을 보나
    1. 도구마다 — 두 번 돌려 나온 파일이 바이트까지 같은가
    2. 차례 전체 — 여덟을 순서대로 두 번 돌려도 같은가
    3. 서로 덮는가 — 뒤 도구가 앞 도구의 결과를 지우지 않는가
       (migrate 가 fix_species 가 고친 것을 되돌리면 큰일입니다)

어떻게 보나
    진짜 data/ 는 **한 글자도 안 건드립니다.** 임시 자리에 베껴
    거기에 대고 돌립니다. BADAGAJA_DATA 로 자리를 옮깁니다.

쓰는 법
    python tests/test_idempotent.py
    python tests/test_idempotent.py --fast    빠른 것만
"""
import io as _io
import os
import sys
import shutil
import hashlib
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

# ★ 차례를 **베껴 적지 않습니다** — engine/refresh.py 에서 읽습니다
#   (2026-09-28 바깥 검수 6차 「Single Source of Truth」)
#
#   전에는 여기에 같은 목록을 따로 적어 두었습니다. 그런데
#   **refresh.py 의 것과 달랐습니다.**
#
#       refresh    … migrate_photos · migrate_home · migrate_map · fix_species
#       이 시험    … migrate_photos · migrate_map · fix_species
#                      (migrate_home 이 빠지고 fix_species 자리가 다름)
#
#   그래서 시험은 **실제와 다른 차례**를 재고 있었습니다.
#   「refresh 로 제자리에 돌아오는가」를 묻는 시험인데, 정작
#   refresh 가 무엇을 하는지 모르고 있었습니다.
#
#   이제 읽어 씁니다. refresh 에 한 줄 더하면 시험도 저절로 따라옵니다.
from engine.refresh import 차례   # noqa: E402

느린것 = ('migrate.py', 'extract_jeonnam.py')

통과, 실패 = 0, []


못잼 = []


def 옛저장소():
    """옛 사이트 자리. 없으면 None."""
    자리 = os.environ.get('BADAGAJA_OLD')
    if not 자리:
        # 기본 자리를 봅니다 — engine/io.py 와 같은 자리여야 합니다
        자리 = os.path.join(os.path.dirname(ROOT), 'badagaja-site')
    return 자리 if os.path.isdir(자리) else None


def 옛것쓰나(도구):
    """★ **글자가 아니라 재료로 판정합니다** (2026-09-28)

    처음에는 실패한 글에서 「옛 저장소」 같은 말을 찾아 가렸습니다.
    5개는 가려졌는데 6개가 새어 나갔습니다 — 도구마다 죽는 말이
    달랐기 때문입니다. **글자로 판정하면 늘 어딘가 샙니다.**
    (오늘만 세 번째 같은 잘못입니다)

    그 도구가 옛 저장소를 **읽는 도구인가**를 소스에서 보고,
    옛 저장소가 **정말 그 자리에 있는가**를 봅니다.
    둘 다 사실이면 잴 수 있고, 아니면 못 잽니다.
    """
    길 = os.path.join(ROOT, 'engine', 도구)
    try:
        글 = _읽기(길)
    except OSError:
        return False
    return 'BADAGAJA_OLD' in 글


def _읽기(길):
    import io as _i
    with _i.open(길, encoding='utf-8') as f:
        return f.read()


def 재료가없나(글):
    """★ **못 잰 것과 어긴 것은 다릅니다** (2026-09-28)

    클라우드 판정에서 18번이 FAIL 로 나왔습니다. 그런데 까닭은
    「자료가 흔들린다」가 아니라 **「잴 재료가 없다」** 였습니다.

        migrate.py 는 옛 저장소(BADAGAJA_OLD)에서 자료를 옮깁니다.
        클라우드에는 옛 저장소가 없습니다. 그러니 못 돕니다.

    이것을 FAIL 로 세면 두 가지를 잃습니다.
      · 진짜 FAIL 이 파묻힙니다 — 11개가 빨갛게 서 있으면
        그중 하나가 진짜라도 눈에 안 들어옵니다
      · 「고칠 것이 있다」고 잘못 알려 줍니다. 고칠 것이 없습니다.

    바깥 검수가 말한 「NOT_TESTED 자기기만」의 **반대쪽**입니다.
    못 쟀으면서 「괜찮다」고 하는 것도 나쁘지만,
    못 쟀으면서 「틀렸다」고 하는 것도 판정을 못 믿게 만듭니다.
    """
    표 = ('BADAGAJA_OLD', '옛 저장소', '옛 사이트', 'FileNotFoundError',
          '못 찾았습니다', '없습니다 —', 'No such file')
    return any(x in (글 or '') for x in 표)


def 못쟀다(이름, 까닭):
    못잼.append(이름)
    print('  ~ %s — 못 쟀습니다 (%s)' % (이름, 까닭))


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s' % 이름)
        if 덧:
            for 줄 in str(덧).split('\n')[:6]:
                print('      %s' % 줄)


def 지문(뿌리):
    """그 자리 밑 모든 파일의 내용 지문. 이름과 내용을 함께 봅니다."""
    나옴 = {}
    for r, _, fs in os.walk(뿌리):
        for f in fs:
            p = os.path.join(r, f)
            키 = os.path.relpath(p, 뿌리).replace(os.sep, '/')
            with open(p, 'rb') as fh:
                나옴[키] = hashlib.sha256(fh.read()).hexdigest()
    return 나옴


def 견주기(앞, 뒤):
    """두 지문의 차이를 사람이 읽는 말로"""
    생김 = sorted(set(뒤) - set(앞))
    사라짐 = sorted(set(앞) - set(뒤))
    바뀜 = sorted(k for k in set(앞) & set(뒤) if 앞[k] != 뒤[k])
    말 = []
    if 생김:
        말.append('새로 생김 %d개: %s' % (len(생김), ' · '.join(생김[:3])))
    if 사라짐:
        말.append('사라짐 %d개: %s' % (len(사라짐), ' · '.join(사라짐[:3])))
    if 바뀜:
        말.append('내용이 바뀜 %d개: %s' % (len(바뀜), ' · '.join(바뀜[:3])))
    return 말


def 돌리기(도구, 자료, 인자=()):
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_DATA'] = 자료
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'engine', 도구)] + list(인자),
        capture_output=True, text=True, encoding='utf-8',
        env=환경, timeout=1800)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def 자료사본():
    t = tempfile.mkdtemp(prefix='idem-')
    사본 = os.path.join(t, 'data')
    shutil.copytree(os.path.join(ROOT, 'data'), 사본)
    return t, 사본


def 시험_하나씩(빠르게):
    print('[1] 도구마다 두 번 돌려 같은가')
    for 도구, 인자, 설명 in 차례:
        if 빠르게 and 도구 in 느린것:
            print('  ~ %-26s 건너뜀 (--fast)' % 도구)
            continue
        if 옛것쓰나(도구) and not 옛저장소():
            못쟀다(도구, '옛 저장소가 없습니다')
            continue
        t, 자료 = 자료사본()
        try:
            코드, 글 = 돌리기(도구, 자료, 인자)
            if 코드 != 0:
                if 재료가없나(글):
                    못쟀다(도구, '옛 저장소가 없습니다')
                else:
                    봄('%s — 한 번째가 실패' % 도구, False, 글[-500:])
                continue
            앞 = 지문(자료)
            코드, 글 = 돌리기(도구, 자료, 인자)
            if 코드 != 0:
                봄('%s — 두 번째가 실패' % 도구, False, 글[-500:])
                continue
            뒤 = 지문(자료)
            차 = 견주기(앞, 뒤)
            봄('%-26s %s' % (도구, 설명), not 차, '\n'.join(차))
        finally:
            shutil.rmtree(t, ignore_errors=True)


def 시험_차례(빠르게):
    print('[2] 차례 전체를 두 번 돌려 같은가')
    if 빠르게:
        print('  ~ 건너뜀 (--fast)')
        return
    # ★ 차례는 이관 도구부터 돕니다 — 옛 저장소가 없으면 통째로 못 잽니다
    if not 옛저장소():
        못쟀다('차례 전체', '옛 저장소가 없습니다')
        return
    t, 자료 = 자료사본()
    try:
        for 회 in (1, 2):
            for 도구, 인자, _ in 차례:
                코드, 글 = 돌리기(도구, 자료, 인자)
                if 코드 != 0:
                    봄('차례 %d회 — %s 가 실패' % (회, 도구), False, 글[-400:])
                    return
            if 회 == 1:
                앞 = 지문(자료)
        뒤 = 지문(자료)
        차 = 견주기(앞, 뒤)
        봄('여덟 도구를 차례대로 두 번', not 차, '\n'.join(차))
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 시험_되돌림(빠르게):
    """★ 가장 무서운 것 — 앞 도구가 뒤 도구의 결과를 지우는가

    migrate 는 포인트를 캐 씁니다. fix_species 는 그 파일을 열어
    어종 이름을 아이디로 바꿉니다. **같은 파일입니다.**

    자료를 갱신하려고 migrate 를 다시 돌리면, fix_species 가
    해 둔 일이 통째로 날아갑니다. 그런데 파일 개수도 포인트 수도
    그대로라 개수를 세는 검사는 아무것도 못 잡습니다.

    막는 것은 두 겹입니다 (2026-09-26)
        engine/refresh.py     차례를 한 곳에 묶습니다
        engine/check_stale.py 어중간한 자료를 잡습니다

    여기서는 **둘 다 제 몫을 하는지** 봅니다. 일부러 되돌려 놓고,
    검사가 잡는지 · refresh 로 제자리에 오는지 확인합니다.
    """
    print('[3] 앞 도구가 뒤 도구의 일을 되돌리는가 — 검사가 잡는가')
    if 빠르게:
        print('  ~ 건너뜀 (--fast)')
        return
    # ★ 차례는 이관 도구부터 돕니다 — 옛 저장소가 없으면 통째로 못 잽니다
    if not 옛저장소():
        못쟀다('차례 전체', '옛 저장소가 없습니다')
        return
    t, 자료 = 자료사본()
    try:
        for 도구, 인자, _ in 차례:
            코드, 글 = 돌리기(도구, 자료, 인자)
            if 코드 != 0:
                봄('차례를 못 돌렸습니다 — %s' % 도구, False, 글[-400:])
                return
        다끝남 = 지문(자료)

        # (가) 다 끝난 자료는 「어중간하지 않다」고 나와야 합니다
        코드, 글 = 돌리기('check_stale.py', 자료)
        봄('차례를 다 돌린 자료는 어중간하지 않다',
           '자료가 끝까지 다듬어져 있습니다' in 글, 글[-400:])

        # (나) 자료 갱신하듯 migrate 만 다시 돌립니다 — 되돌아갑니다
        코드, 글 = 돌리기('migrate.py', 자료, ('--write',))
        되돌아감 = 지문(자료)
        차 = 견주기(다끝남, 되돌아감)
        봄('migrate 만 돌리면 뒤 도구의 일이 날아간다 (그래서 위험합니다)',
           bool(차), '되돌아가지 않았습니다 — 시험이 낡았을 수 있습니다')

        # (다) ★ 핵심 — 되돌아간 것을 검사가 반드시 잡아야 합니다
        코드, 글 = 돌리기('check_stale.py', 자료, ('--strict',))
        봄('되돌아간 자료를 check_stale 이 잡는다',
           코드 != 0 and '자료가 어중간합니다' in 글, 글[-500:])

        # (라) refresh 로 차례 전체를 돌리면 제자리로 돌아와야 합니다
        코드, 글 = 돌리기('refresh.py', 자료, ('--write',))
        고침 = 지문(자료)
        차2 = 견주기(다끝남, 고침)
        봄('refresh --write 로 제자리로 돌아온다', not 차2, '\n'.join(차2))
    finally:
        shutil.rmtree(t, ignore_errors=True)


def 시험_집차림표():
    """migrate_home.py — 첫 화면 차림표도 두 번 돌려 같은가 (계약-26)

    ★ 이 도구만 data/ 가 아니라 assets/css/ 에 씁니다.
      자리가 다르다고 시험에서 빼면 약속이 헐거워집니다.
      자리에 맞는 시험을 따로 만듭니다.
    """
    print('[4] migrate_home.py — 첫 화면 차림표')
    t = tempfile.mkdtemp(prefix='idem-home-')
    try:
        사본 = os.path.join(t, 'assets')
        shutil.copytree(os.path.join(ROOT, 'assets'), 사본)
        환경 = dict(os.environ)
        환경['PYTHONIOENCODING'] = 'utf-8'
        환경['BADAGAJA_ASSETS'] = 사본

        def 한번():
            r = subprocess.run(
                [sys.executable,
                 os.path.join(ROOT, 'engine', 'migrate_home.py'), '--write'],
                capture_output=True, text=True, encoding='utf-8',
                env=환경, timeout=600)
            return r.returncode, (r.stdout or '') + (r.stderr or '')

        코드, 글 = 한번()
        if 코드 != 0:
            if 재료가없나(글):
                못쟀다('migrate_home.py', '옛 저장소가 없습니다')
            else:
                봄('migrate_home.py — 한 번째가 실패', False, 글[-400:])
            return
        나온것 = os.path.join(사본, 'css', 'home.css')
        if not os.path.exists(나온것):
            봄('migrate_home.py — 차림표를 안 만들었습니다', False)
            return
        with _io.open(나온것, encoding='utf-8') as f:
            앞 = f.read()
        코드, 글 = 한번()
        if 코드 != 0:
            봄('migrate_home.py — 두 번째가 실패', False, 글[-400:])
            return
        with _io.open(나온것, encoding='utf-8') as f:
            뒤 = f.read()
        봄('migrate_home.py — 두 번 돌려도 바이트까지 같다', 앞 == 뒤,
           '앞 %d자 · 뒤 %d자' % (len(앞), len(뒤)))
        # 옛 차림표가 통째로 들어갔는가
        봄('옛 첫 화면 차림표가 들어 있다',
           '.g-hero' in 뒤 and '.hm-r' in 뒤 and '.sc-pill' in 뒤,
           뒤[:200])
    finally:
        shutil.rmtree(t, ignore_errors=True)   # 계약-17 예외 — 방금 만든 것


def main():
    빠르게 = '--fast' in sys.argv
    print('이관 도구가 두 번 돌려도 같은가')
    print('  진짜 data/ 는 안 건드립니다 — 임시 사본에 대고 돌립니다')
    print('')
    시험_하나씩(빠르게)
    print('')
    시험_차례(빠르게)
    print('')
    시험_되돌림(빠르게)
    print('')
    시험_집차림표()
    print('')
    if 실패:
        print('%d가지 통과 · %d가지 실패%s'
              % (통과, len(실패),
                 ' · %d가지 못 쟀습니다' % len(못잼) if 못잼 else ''))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  자료가 매달 갱신됩니다. 돌릴 때마다 결과가 달라지면')
        print('  500여 쪽이 조금씩 흔들립니다.')
        return 1

    # ★ **못 쟀으면 「통과」라고 하지 않습니다** (2026-09-28)
    #
    #   옛 저장소(BADAGAJA_OLD)가 없으면 이관 도구가 못 돕니다.
    #   클라우드에는 옛 저장소가 없습니다.
    #
    #   전에는 이것을 FAIL 로 셌습니다. 그래서 클라우드 판정에서
    #   18번이 빨갛게 섰고, 저는 「자료가 흔들리나」 하고 한참을
    #   엉뚱한 데서 찾았습니다. 잴 재료가 없었을 뿐입니다.
    #
    #   그렇다고 PASS 로 넘기면 더 나쁩니다 — **안 잰 것을 잰
    #   것처럼** 세게 됩니다. 끝난값 2 를 내면 판정이 이것을
    #   NOT_TESTED 로 읽고, NOT_TESTED 는 NO-GO 입니다.
    #   「몰라서 못 간다」와 「틀려서 못 간다」는 다릅니다.
    if 못잼:
        print('%d가지 통과 · **%d가지는 못 쟀습니다**' % (통과, len(못잼)))
        for x in 못잼:
            print('  ~ %s' % x)
        print('')
        print('  옛 저장소가 있어야 이관 도구를 돌릴 수 있습니다.')
        print('  BADAGAJA_OLD 를 가리키게 하고 다시 재세요.')
        print('  **못 쟀을 뿐이지 틀린 것이 아닙니다. 그러나')
        print('    못 쟀으면 「괜찮다」고도 말하지 않습니다.**')
        return 2

    print('%d가지 모두 통과 — 몇 번을 돌려도 같습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
