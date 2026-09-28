# -*- coding: utf-8 -*-
"""옛 사이트에서 **검사에 필요한 것만** 떠서 저장소에 둡니다.

★ 왜 만들었나 (2026-09-28)

    옛 사이트를 빈 폴더로 놓고 검사기를 돌려 봤더니 셋이
    **아무 말 없이 통과**했습니다. 볼 것이 0개라 걸린 것도
    0개였던 것입니다.

        16 중국어 옛 자산 보호  「바꿔도 중국어판이 멀쩡합니다」
        24 옛쪽대비            「옛 쪽이 가졌던 것이 모두 있습니다」

    클라우드에는 옛 사이트가 없습니다. 그러니 그동안 그
    두 항목의 PASS 는 **재지 않고 통과시킨 것**이었습니다.

    못 잰 것을 통과로 세지 않게 고쳤더니, 이번에는 클라우드에서
    영영 GO 가 안 나오게 됐습니다. 그래서 옛 쪽을 저장소에 둡니다.

★ 무엇을 뜨나

    html · css · js 만 뜹니다. 23MB 남짓입니다.

    사진은 안 뜹니다. check_keep 이 보는 것은 href 가 가리키는
    곳이고, 사진은 src 라 안 봅니다. 79MB 를 아낍니다.

    data-private/ 는 **절대 안 뜹니다** (주인 규칙 11).
    api/ 도 안 뜹니다 — 열쇠가 들어 있을 수 있습니다.

★ 왜 도구로 만드나 (주인 규칙 26)

    손으로 복사하면 다음에 못 되풀이합니다.
    자료가 바뀌면 이 도구를 다시 돌리면 됩니다.

쓰는 법
    python engine/make_oldsite.py            떠 옵니다
    python engine/make_oldsite.py --check    지금 것이 옛 것과 같은지만 봅니다
"""
import os
import re
import sys
import shutil
import hashlib
import io as io2

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 옛 사이트가 있는 자리 (내 컴퓨터)
옛뿌리 = os.environ.get('BADAGAJA_OLD_SRC', r'D:\바다가자\badagaja-site')
# 저장소 안에 둘 자리
둘자리 = os.path.join(ROOT, 'oldsite')

뜰꼬리 = ('.html', '.css', '.js')

# ★ 이 칸들은 **절대 안 뜹니다**
#   data-private — 근거 자료는 웹에 안 냅니다 (주인 규칙 11)
#   api          — 열쇠가 들어 있을 수 있습니다
#   .git         — 저장소 안의 저장소
안뜰칸 = {'.git', 'data-private', 'api', 'node_modules',
          '_stage', '.claude', '.github', 'oldsite'}


# ★ **개인 휴대전화는 가리고 뜹니다** (2026-09-28)
#
#   옛 쪽에 「시기·요금은 마을에 확인 · 문의 010-XXXX-XXXX」 가
#   29곳 있습니다. 마을 갯벌체험장 문의처입니다.
#
#   이미 웹에 있는 것이지만, **저장소 기록은 지워도 남습니다.**
#   공개 저장소에 넣으면 영영 남습니다.
#
#   검사기는 쪽 구조와 href 만 봅니다. 번호를 가려도 재는 데
#   지장이 없습니다. 그러니 가리고 뜹니다.
전화무늬 = re.compile(r'(?<![0-9])01[016789](?:[-. ]\d{3,4}[-. ]\d{4}'
                      r'|\d{7,8})(?![0-9])')


def 전화가리기(글):
    새글, 셈 = 전화무늬.subn('010-****-****', 글)
    return 새글, 셈


def 지문(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for 덩이 in iter(lambda: f.read(65536), b''):
            h.update(덩이)
    return h.hexdigest()[:16]


def 뜰것들(뿌리):
    """뜰 파일을 (상대길, 온길) 로 돌려줍니다."""
    끝 = []
    for 여기, 칸들, 파일들 in os.walk(뿌리):
        칸들[:] = [c for c in 칸들 if c not in 안뜰칸]
        for f in sorted(파일들):
            if not f.endswith(뜰꼬리):
                continue
            온길 = os.path.join(여기, f)
            상대 = os.path.relpath(온길, 뿌리).replace(os.sep, '/')
            끝.append((상대, 온길))
    return sorted(끝)


def main():
    볼까만 = '--check' in sys.argv

    if not os.path.isdir(옛뿌리):
        print('옛 사이트가 없습니다: %s' % 옛뿌리)
        print('  BADAGAJA_OLD_SRC 로 자리를 알려 주세요.')
        print('  (클라우드에서는 뜰 수 없습니다 — 이미 뜬 것을 씁니다)')
        return 2

    가린것 = [0]
    것들 = 뜰것들(옛뿌리)
    if not 것들:
        print('뜰 것이 없습니다: %s' % 옛뿌리)
        return 1

    크기 = sum(os.path.getsize(p) for _, p in 것들)
    print('옛 사이트에서 뜰 것')
    print('  %s' % 옛뿌리)
    print('  파일 %d개 · %.1f MB' % (len(것들), 크기 / 1048576))
    print('')

    if 볼까만:
        같음, 다름, 없음 = 0, [], []
        for 상대, 온길 in 것들:
            여기 = os.path.join(둘자리, 상대.replace('/', os.sep))
            if not os.path.exists(여기):
                없음.append(상대)
            elif 지문(여기) == 지문(온길):
                같음 += 1
            else:
                다름.append(상대)
        print('  같음 %d · 다름 %d · 아직 안 뜬 것 %d'
              % (같음, len(다름), len(없음)))
        for x in (다름 + 없음)[:8]:
            print('      %s' % x)
        return 0 if not (다름 or 없음) else 1

    if os.path.isdir(둘자리):
        shutil.rmtree(둘자리)
    for 상대, 온길 in 것들:
        여기 = os.path.join(둘자리, 상대.replace('/', os.sep))
        os.makedirs(os.path.dirname(여기), exist_ok=True)
        if 상대.endswith('.html'):
            글 = io2.open(온길, encoding='utf-8', errors='replace').read()
            글, 가린수 = 전화가리기(글)
            가린것[0] += 가린수
            io2.open(여기, 'w', encoding='utf-8', newline='').write(글)
        else:
            shutil.copy2(온길, 여기)

    # 뜬 것을 한 줄로 적어 둡니다 — 나중에 견주려고
    쪽수 = sum(1 for 상대, _ in 것들 if 상대.endswith('.html'))
    중국어 = sum(1 for 상대, _ in 것들 if 상대.startswith('zh-cn/'))
    print('  떴습니다 → %s' % 둘자리)
    print('  쪽 %d장 (그중 중국어 %d장)' % (쪽수, 중국어))
    print('  개인 휴대전화 %d곳을 가렸습니다' % 가린것[0])
    print('')
    print('  ★ 사진은 안 떴습니다 — check_keep 은 href 만 봅니다.')
    print('    data-private·api 도 안 떴습니다 (주인 규칙 11).')
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
