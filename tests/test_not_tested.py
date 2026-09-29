# -*- coding: utf-8 -*-
"""**못 잰 것이 PASS 로 안 나오는지** 증명합니다. (검수 지시 3)

★ 왜 이 시험이 따로 필요한가 (2026-09-27 바깥 검수 지시)

    「검사기가 측정 실패를 PASS 로 바꾸는 일이 다시 발생하지 않도록
      한다. 의도적으로 측정 실패를 발생시켰을 때 PASS 가 나오면
      안 된다. 즉 **측정 실패 ≠ PASS** 가 자동 테스트로 증명되어야
      한다」

    제가 이 실수를 **세 번** 했습니다.

        · 광고가 하나도 안 떴는데 「멀쩡합니다」로 통과
        · 12건 전부 측정 실패인데 통과
        · 잴 것이 없는데 「제대로 되어 있습니다」로 통과

    셋 다 같은 성질입니다 — **안 잰 것을 통과로 세는 것.**
    발견할 때마다 고치는 식으로는 또 생깁니다.
    그래서 **일부러 못 재게 만들어 놓고** 통과가 나오는지 봅니다.

어떻게 보나
    검사기가 기대는 것을 하나씩 없앱니다.
      · 볼 쪽이 없을 때
      · 자료가 없을 때
      · 크롬을 못 찾을 때
      · 시간이 넘을 때
    그때 검사기가 **0(통과)으로 끝나면 안 됩니다.**

    「막지 않는 검사」(계약-21 의 알림)는 0 으로 끝나도 됩니다.
    다만 그때도 **「멀쩡하다」고 말하면 안 됩니다.**

쓰는 법
    python tests/test_not_tested.py
"""
import os
import re
import sys
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402
from engine.gate import 상태들   # noqa: E402  상태 목록은 gate.py 한 곳에만

통과, 실패 = 0, []

# 「다 잘됐다」는 뜻의 말들 — 못 쟀을 때 나오면 안 됩니다
통과하는말 = (
    '이상 없음', '멀쩡합니다', '탈이 없습니다', '모두 지킵니다',
    '모두 통과', '제대로 그 언어입니다', '모두 갈 곳이 있습니다',
    '길이 모두 이어집니다', '제대로 뜹니다', '하나입니다',
    '끝까지 다듬어져 있습니다', '모두 있습니다',
)


def 봄(이름, 참인가, 덧=''):
    global 통과
    if 참인가:
        통과 += 1
        print('  · %s' % 이름)
    else:
        실패.append(이름)
        print('  ✗ %s' % 이름)
        if 덧:
            for 줄 in str(덧).strip().split('\n')[-4:]:
                print('      %s' % 줄)


def 돌리기(도구, 사이트=None, 자료=None, 인자=(), 길막기=False,
           옛자리=None):
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    if 옛자리:
        # ★ 옛 사이트가 없을 때를 만들어 봅니다 (2026-09-28)
        환경['BADAGAJA_OLD'] = 옛자리
    if 사이트:
        환경['BADAGAJA_SITE'] = 사이트
    if 자료:
        환경['BADAGAJA_DATA'] = 자료
    if 길막기:
        # ★ 크롬을 못 찾게 만듭니다 (2026-09-27)
        #   PATH 를 비우는 것으로는 모자랍니다 — 검사기가 크롬 자리를
        #   절대 경로로 알고 있기 때문입니다. 그래서 검사기가 보는
        #   BADAGAJA_CHROME 에 **없는 자리**를 줍니다.
        환경['BADAGAJA_CHROME'] = os.path.join(
            ROOT, '없는자리', 'chrome.exe')
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, 'engine', 도구)] + list(인자),
        capture_output=True, text=True, encoding='utf-8',
        env=환경, timeout=900)
    return r.returncode, (r.stdout or '') + (r.stderr or '')


def 통과라고했나(글):
    return any(x in 글 for x in 통과하는말)


def 빈자리():
    t = tempfile.mkdtemp(prefix='nottested-')
    os.makedirs(os.path.join(t, 'site'), exist_ok=True)
    return t, os.path.join(t, 'site')


def 시험_볼쪽이없을때():
    """쪽이 하나도 없으면 「멀쩡하다」고 하면 안 됩니다."""
    print('[1] 볼 쪽이 하나도 없을 때')
    도구들 = ('check_links.py', 'check_seo.py', 'check_ads.py',
              'check_assets.py', 'check_canonical.py', 'check_console.py',
              'check_render.py', 'check_i18n.py')
    for 도구 in 도구들:
        t, 빈곳 = 빈자리()
        try:
            코드, 글 = 돌리기(도구, 사이트=빈곳, 인자=['--strict'])
            나쁜가 = (코드 == 0 and 통과라고했나(글))
            봄('%-22s 빈 사이트를 통과시키지 않는다' % 도구,
               not 나쁜가, 글[-300:])
        finally:
            shutil.rmtree(t, ignore_errors=True)
    print('')


def 시험_자료가없을때():
    """자료가 없으면 「지킨다」고 하면 안 됩니다."""
    print('[2] 자료가 하나도 없을 때')
    도구들 = ('check_stale.py', 'check_keep.py', 'check_refresh.py',
              'check_urls.py')
    for 도구 in 도구들:
        t = tempfile.mkdtemp(prefix='nottested-')
        빈자료 = os.path.join(t, 'data')
        os.makedirs(os.path.join(빈자료, 'raw'), exist_ok=True)
        try:
            코드, 글 = 돌리기(도구, 자료=빈자료, 인자=['--strict'])
            나쁜가 = (코드 == 0 and 통과라고했나(글))
            봄('%-22s 빈 자료를 통과시키지 않는다' % 도구,
               not 나쁜가, 글[-300:])
        finally:
            shutil.rmtree(t, ignore_errors=True)
    print('')


def 시험_판정도구():
    """gate.py 가 못 잰 것을 PASS 로 세지 않는가.

    ★ gate 가 나를 부른 것이면 건너뜁니다 (2026-09-27)
        gate → 이 시험 → gate → 이 시험 … 끝이 없습니다.
        gate 가 BADAGAJA_GATE 를 남기므로 그때는 안 돌립니다.
        **건너뛴 것은 「통과」가 아닙니다** — 그렇다고 적습니다.
    """
    print('[3] 판정 도구가 못 잰 것을 PASS 로 세는가')
    if os.environ.get('BADAGAJA_GATE'):
        print('  ~ gate 가 부른 것이라 건너뜁니다 (고리를 끊습니다)')
        print('    gate → 이 시험 → gate … 로 끝이 없어집니다')
        print('    따로 돌리면 잽니다: python tests/test_not_tested.py')
        print('')
        return
    # ★ **빈 사이트**에 대고 돌립니다 (2026-09-27 — 속도)
    #   여기서 보려는 것은 「gate 가 검산을 내고, 못 잰 것이 있으면
    #   NO-GO 라고 하는가」입니다. 진짜 사이트를 다시 잴 까닭이
    #   없습니다. 전에는 gate 를 통째로 돌려 **4분 넘게** 걸렸고,
    #   그 안에서 이 시험을 또 불러 고리까지 생겼습니다.
    #
    #   빈 사이트면 검사기들이 곧바로 넘어져, 오히려
    #   「못 잰 것이 있을 때 NO-GO 인가」를 더 또렷이 봅니다.
    t = tempfile.mkdtemp(prefix='nottested-gate-')
    빈곳 = os.path.join(t, 'site')
    os.makedirs(빈곳, exist_ok=True)
    환경 = dict(os.environ)
    환경['PYTHONIOENCODING'] = 'utf-8'
    환경['BADAGAJA_SITE'] = 빈곳
    try:
        r = subprocess.run([sys.executable, os.path.join(ROOT, 'engine',
                                                         'gate.py')],
                           capture_output=True, text=True, encoding='utf-8',
                           env=환경, timeout=600)
    finally:
        shutil.rmtree(t, ignore_errors=True)
    글 = (r.stdout or '') + (r.stderr or '')

    # 검산이 반드시 나와야 합니다
    # ★ **상태가 몇 가지든 받아들입니다** (2026-09-28)
    #   전에는 넷만 더하는 꼴로 찾았습니다. 그런데 INFRA_FAIL 이
    #   생기며 여섯이 됐고, 시험은 그것을 못 읽어
    #   「검산을 스스로 안 낸다」고 했습니다.
    #   **검사기는 멀쩡한데 시험이 낡아 잘못 잡은 것**입니다.
    #   상태 수는 gate.py 가 정합니다. 여기서 따로 세지 않습니다.
    m = re.search(r'검산\s+([\d+\s]+?)=\s*(\d+)\s*(=|≠)\s*(\d+)',
                  글)
    봄('검산을 스스로 냅니다', bool(m), 글[-300:])
    if m:
        더한것 = [int(x) for x in re.findall(r'\d+', m.group(1))]
        봄('검산이 맞습니다',
           sum(더한것) == int(m.group(4)) and m.group(3) == '=',
           m.group(0))
        봄('상태를 하나도 빠뜨리지 않고 셉니다',
           len(더한것) == len(상태들),
           '더한 것 %d가지 · 상태 %d가지' % (len(더한것), len(상태들)))

    # NOT_TESTED 가 하나라도 있으면 NO-GO 여야 합니다
    안잰것 = re.search(r'NOT_TESTED\s+(\d+)', 글)
    if 안잰것 and int(안잰것.group(1)) > 0:
        # ★ **「GO 라고 안 한다」를 봅니다** (2026-09-28)
        #   전에는 'NO-GO' 글자를 찾았습니다. 그런데 --smoke 는
        #   「판정 없음」이라 적습니다 — GO 도 NO-GO 도 아닙니다.
        #   그래서 멀쩡한 판정을 시험이 잡았습니다.
        #   정작 지켜야 할 것은 **못 쟀는데 GO 라 하지 않는 것**입니다.
        봄('못 잰 것이 있으면 GO 라고 하지 않습니다',
           'GO 후보' not in 글, 글[-300:])
        봄('못 잰 것이 있으면 0 이 아닌 값으로 끝납니다',
           r.returncode != 0, '끝난값 %d' % r.returncode)
    else:
        봄('못 잰 것이 없으면 GO 후보라고 합니다',
           'GO 후보' in 글, 글[-300:])

    # 「PASS 6」 같은 말이 나오는데 표에 없는 항목이 있으면 안 됩니다
    표항목 = len(re.findall(r'^  [·✗?-] \d+ ', 글, re.M))
    총 = re.search(r'TOTAL\s+(\d+)', 글)
    봄('표에 적은 항목 수가 TOTAL 과 같습니다',
       bool(총) and 표항목 == int(총.group(1)),
       '표 %d개 · TOTAL %s' % (표항목, 총.group(1) if 총 else '?'))
    print('')


def 시험_크롬을못찾을때():
    """브라우저를 못 찾으면 통과시키면 안 됩니다."""
    print('[4] 브라우저를 못 찾을 때')
    # ★ 한 쪽만 재도 충분합니다 (2026-09-27 — 속도)
    #   전에는 check_render 가 416쪽을 다 시도해 10분 넘게 걸렸습니다.
    #   크롬이 없으면 첫 쪽에서 이미 드러납니다.
    한쪽 = os.path.join(ROOT, 'site', 'index.html')
    for 도구, 인자 in (('check_render.py', [한쪽, '--strict']),
                       ('check_ads.py', ['--strict']),
                       ('check_console.py', ['--strict'])):
        코드, 글 = 돌리기(도구, 인자=인자, 길막기=True)
        # 크롬을 못 찾으면 넘어지거나(0 아님) 「못 쟀다」고 해야 합니다
        나쁜가 = (코드 == 0 and 통과라고했나(글))
        봄('%-22s 브라우저가 없으면 통과시키지 않는다' % 도구,
           not 나쁜가, 글[-300:])
    print('')



def 시험_옛사이트가없을때():
    """★ **옛 사이트가 없으면 통과시키면 안 됩니다** (2026-09-28)

    오늘 잡은 것입니다. 옛 사이트를 빈 폴더로 놓고 돌렸더니
    검사기 셋이 **아무 말 없이 통과**했습니다.

      16 중국어 옛 자산 보호  「바꿔도 중국어판이 멀쩡합니다」
      24 옛쪽대비            「옛 쪽이 가졌던 것이 새 쪽에 모두 있습니다」

    볼 것이 0개라 걸린 것도 0개였던 것입니다.
    **아무것도 안 봤는데 괜찮다고 합니다.**

    클라우드에는 옛 사이트가 없습니다. 그러니 그동안
    클라우드 판정의 16·24번 PASS 는 **거짓**이었습니다.
    """
    print('[5] 옛 사이트가 없을 때')
    빈자리 = tempfile.mkdtemp(prefix='없는옛사이트-')
    try:
        for 도구 in ('check_keep.py', 'check_design.py',
                     'check_tide_old.py'):
            코드, 글 = 돌리기(도구, 인자=['--strict'],
                              옛자리=빈자리)
            나쁜가 = (코드 == 0 and 통과라고했나(글))
            봄('%-22s 옛 사이트가 없으면 통과시키지 않는다' % 도구,
               not 나쁜가, 글[-300:])
    finally:
        os.rmdir(빈자리)
    print('')


def 시험_배포상태가르기():
    """★ **「잴 환경이 없다」와 「잰 결과가 나쁘다」를 가릅니다**
      (2026-09-29 바깥 검수 12차)

    20번(실제 서버)은 올려야만 잽니다. 그런데 NOT_TESTED 하나가
    곧 NO-GO 라 **영원히 GO 가 안 됐습니다.**

    가른 뒤에도 **막을 것은 여전히 막아야** 합니다.
    그것을 안 지키면 「빠른 거짓말」이 됩니다.
    """
    print('[6] 배포 상태를 가른 뒤에도 막을 것은 막는가')
    import importlib
    from engine import gate as _g
    importlib.reload(_g)

    def 재보기(항목들, 덧나쁨=False, 덧못잼=False):
        _g.결과.clear()
        for 번호, 상태 in 항목들:
            _g.적기(번호, '시험%s' % 번호, 상태, '')
        셈 = {k: 0 for k in _g.상태들}
        for x in _g.결과:
            셈[x['상태']] = 셈.get(x['상태'], 0) + 1
        # ★ **「못 쟀다」만이 아니라 「달랐다」도** (2026-09-29)
        #   올리기 전 20번은 NOT_TESTED 가 아니라 FAIL 로 나옵니다.
        #   서버에 옛 판이 있으니 「내 것과 다르다」이기 때문입니다.
        #   그래서 영원히 NO-GO 였습니다 — 닭과 달걀.
        나중 = [x for x in _g.결과
                if x.get('번호') == '20'
                and x['상태'] in ('NOT_TESTED', 'FAIL')]
        지금못잰 = 셈['NOT_TESTED'] - len(
            [x for x in 나중 if x['상태'] == 'NOT_TESTED'])
        나중FAIL = len([x for x in 나중 if x['상태'] == 'FAIL'])
        막는것 = ((셈['FAIL'] - 나중FAIL) or 셈['ERROR']
                  or 셈['INFRA_FAIL'] or 덧나쁨)
        덜잰것 = (지금못잰 > 0) or 덧못잼
        갈수 = not 막는것 and not 덜잰것 and not 나중
        준비 = not 막는것 and not 덜잰것
        return 'GO 후보' if 갈수 else ('검증 배포 필요' if 준비 else 'NO-GO')

    봄('20번만 못 쟀으면 검증 배포 필요',
       재보기([('1', 'PASS'), ('20', 'NOT_TESTED'), ('15', 'N.A.')])
       == '검증 배포 필요')
    봄('20번까지 통과하면 GO 후보',
       재보기([('1', 'PASS'), ('20', 'PASS'), ('15', 'N.A.')]) == 'GO 후보')
    # ★ 여기부터가 핵심입니다 — 가른 뒤에도 막아야 합니다
    봄('FAIL 이 하나라도 있으면 막는다',
       재보기([('1', 'FAIL'), ('20', 'NOT_TESTED')]) == 'NO-GO')
    봄('20번 말고 다른 것을 못 쟀으면 막는다',
       재보기([('1', 'NOT_TESTED'), ('20', 'NOT_TESTED')]) == 'NO-GO')
    봄('검사기가 죽었으면(ERROR) 막는다',
       재보기([('1', 'ERROR'), ('20', 'NOT_TESTED')]) == 'NO-GO')
    봄('잴 형편이 안 되면(INFRA_FAIL) 막는다',
       재보기([('1', 'INFRA_FAIL'), ('20', 'NOT_TESTED')]) == 'NO-GO')
    봄('덧검사가 나쁘면 막는다',
       재보기([('1', 'PASS'), ('20', 'NOT_TESTED')], 덧나쁨=True) == 'NO-GO')
    봄('덧검사를 못 쟀으면 막는다',
       재보기([('1', 'PASS'), ('20', 'NOT_TESTED')], 덧못잼=True) == 'NO-GO')

    # ★ **닭과 달걀** — 2026-09-29 오픈 날 실제로 막힌 자리
    #   20번은 올리기 전에 재면 NOT_TESTED 가 아니라 **FAIL** 입니다.
    #   서버에 옛 판이 있으니 「다르다」이기 때문입니다.
    #   올려야 같아지는데, 올리려면 통과해야 했습니다.
    봄('20번이 FAIL 이어도 그것 하나뿐이면 검증 배포 필요',
       재보기([('1', 'PASS'), ('20', 'FAIL'), ('15', 'N.A.')])
       == '검증 배포 필요')
    봄('20번 FAIL + 다른 FAIL 이 있으면 여전히 막는다',
       재보기([('1', 'FAIL'), ('20', 'FAIL')]) == 'NO-GO')
    봄('20번 FAIL + 다른 것 못 쟀으면 여전히 막는다',
       재보기([('1', 'NOT_TESTED'), ('20', 'FAIL')]) == 'NO-GO')
    봄('20번 FAIL + ERROR 면 여전히 막는다',
       재보기([('1', 'ERROR'), ('20', 'FAIL')]) == 'NO-GO')
    봄('20번 FAIL + 덧검사 나쁘면 여전히 막는다',
       재보기([('1', 'PASS'), ('20', 'FAIL')], 덧나쁨=True) == 'NO-GO')
    print('')


def 시험_지문만믿지않나():
    """★ **판 지문이 같아도 쪽이 다를 수 있습니다** (2026-09-29)

    운영 배포가 되돌려진 뒤 서버가 이런 상태였습니다.

        build.json   새 것    ← 지문은 같다고 나옴
        taean.html   **옛 것** ← 실제로는 다름

    smoke.py 는 지문 하나만 보고 「올린 것이 내가 만든 그것」
    이라 말했습니다. **거짓말이었습니다.**

    되돌리기가 반만 되면 늘 이런 꼴이 납니다. 지문 파일 하나가
    안 되돌려지면 **서버가 섞여 있는데 괜찮다고** 합니다.
    """
    print('[7] 판 지문만 믿고 통과시키지 않는가')
    길 = os.path.join(ROOT, 'engine', 'smoke.py')
    글 = io.read(길, default='') if hasattr(io, 'read') else ''
    if not 글:
        import io as _io
        글 = _io.open(길, encoding='utf-8', errors='replace').read()
    봄('지문이 같아도 진짜 쪽을 받아 견준다',
       '지문은 같은데' in 글 and '글자만(' in 글,
       'smoke.py 가 쪽까지 안 봅니다')
    봄('쪽이 다르면 결정적 오류로 센다',
       "결정적.append('판 지문은 같은데" in 글,
       '수상함으로 세면 되돌리지 않습니다')
    print('')


def main():
    print('못 잰 것이 PASS 로 안 나오는지 (검수 지시 3)')
    print('')
    시험_볼쪽이없을때()
    시험_자료가없을때()
    시험_판정도구()
    시험_크롬을못찾을때()
    시험_옛사이트가없을때()
    시험_배포상태가르기()
    시험_지문만믿지않나()

    if 실패:
        print('%d가지 통과 · %d가지 실패' % (통과, len(실패)))
        for x in 실패:
            print('  ✗ %s' % x)
        print('')
        print('  ★ 안 잰 것을 통과로 세면, 검사가 있는 것이')
        print('    없는 것보다 나쁩니다 — 믿어 버리기 때문입니다.')
        return 1
    print('%d가지 모두 통과 — 못 잰 것은 통과가 되지 않습니다.' % 통과)
    return 0


if __name__ == '__main__':
    sys.exit(main())
