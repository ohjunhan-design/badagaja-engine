# -*- coding: utf-8 -*-
"""바깥 검수에 줄 **소스 꾸러미**를 묶습니다.

★ 왜 만드나 (2026-10-01)
  바깥 검수자(챗지피티)가 소스를 못 보면 짐작으로 묻습니다.
  오늘만 해도 「규정이 박힌 쪽 3곳」이 실은 36곳이었고,
  어종 아이디가 두 벌이라는 것도 소스를 봤으면 바로 알았을
  일입니다. 제가 세어 옮겨 적는 데서 샙니다.

  더 나쁜 일도 있었습니다 — 검수자가 **옛 사본**을 보고
  「239MB · _stage 80MB · 차림표 두 체계」라 했는데 실제
  배포본은 107.6MB · _stage 없음 · 한 체계였습니다.
  둘 다 틀리지 않았습니다. **본 것이 달랐을 뿐**입니다.

★ 무엇을 빼나 — 뺄 것을 먼저 정합니다 (넣을 것보다 중요)
  · `data-private/` — 조사해 모은 남의 자료, 광고 설정 (주인 규칙 11)
  · `oldsite/` — 옛 사이트. 이것 때문에 검수자가 헷갈렸습니다
  · `site/` — 생성물. 자료에서 언제든 다시 만듭니다
  · `.git/` — 이력
  · 사진 93MB — 꾸러미가 못 올라갈 만큼 커집니다

★ 묶기 전에 **비밀값이 섞였는지 봅니다**
  한 번 밖으로 나간 것은 되돌릴 수 없습니다. 찾으면 **멈춥니다.**

쓰는 법
    python engine/export_review.py
    python engine/export_review.py --force   # 비밀값 경고를 넘김 (사람이 보고 나서만)
"""
import io
import os
import re
import sys
import json
import zipfile
import datetime

뿌리 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 넣을 자리 ────────────────────────────────────────
넣을폴더 = ['engine', 'template', 'docs', 'tests', '.github',
            'data/raw']
넣을파일 = ['check', 'check.cmd', 'README.md', 'requirements.txt',
            'site/build.json']
# assets 는 차림표·셈본만 (사진은 뺍니다)
넣을확장 = ('.css', '.js', '.json', '.svg')

# ── 뺄 자리 — 이름이 하나라도 걸리면 안 넣습니다 ────
뺄자리 = ('data-private', 'oldsite', '__pycache__', '.git',
          'node_modules', 'tests/out', '.tmp', 'release',
          'data/cache')

# ── 비밀값으로 보이는 꼴 ─────────────────────────────
#   찾으면 멈춥니다. 한 번 나간 것은 못 거둡니다.
비밀꼴 = [
    ('애드센스 게시자', re.compile(r'ca-pub-\d{10,}')),
    ('비밀번호',       re.compile(r'(?i)(password|passwd|비밀번호)'
                                  r'\s*[:=]\s*["\']?[^\s"\',}]{4,}')),
    ('비밀키',         re.compile(r'(?i)(secret|api[_-]?key|token|'
                                  r'access[_-]?key)\s*[:=]\s*'
                                  r'["\']?[A-Za-z0-9_\-]{12,}')),
    ('FTP 주소',       re.compile(r'(?i)ftp://[^\s"\']+:[^\s"\']+@')),
    ('개인 메일',      re.compile(r'[A-Za-z0-9._%+-]+@'
                                  r'(?:gmail|naver|daum|hanmail)\.[a-z]+')),
]
# 이것들은 비밀이 아닙니다 — 보기·설명·빈 칸
봐줄것 = re.compile(r'(?i)(example|sample|your[_-]|xxx|보기|예시|'
                    r'\{\{|\$\{|os\.environ|secrets\.|placeholder)')

# ★ **이미 사이트에 공개한 것**은 비밀이 아닙니다 (2026-10-01)
#   badagaja.com/robots.txt 와 llms.txt 에 문의처로 적혀 있습니다.
#   이것이 매번 걸리면 경고가 무뎌져 **진짜 비밀이 묻힙니다.**
#   새로 더할 때는 **정말 공개된 것인지 서버에서 확인하고** 적습니다.
이미공개 = (
    'ohjunhan@gmail.com',      # robots.txt·llms.txt 의 문의처
)


def 넣나(상대):
    """이 파일을 꾸러미에 넣을지."""
    길 = 상대.replace(os.sep, '/')
    for 뺄 in 뺄자리:
        if 길 == 뺄 or 길.startswith(뺄 + '/') or ('/' + 뺄 + '/') in 길:
            return False
    if 길 in 넣을파일:
        return True
    for 폴더 in 넣을폴더:
        if 길.startswith(폴더 + '/'):
            return not 길.endswith('.pyc')
    if 길.startswith('assets/'):
        return 길.endswith(넣을확장)
    return False


def 모으기():
    """★ **넣을 폴더만** 훑습니다 (2026-10-01).

    처음에는 저장소 전체를 `os.walk` 했는데 2분이 넘어도 안 끝났습니다.
    `site/` 와 `assets/img/` 에 사진이 수만 장 있어 그것까지 다 훑고
    하나하나 「넣을까」를 물었기 때문입니다.
    **안 넣을 것은 아예 열어 보지 않습니다.**
    """
    것들 = []
    훑을곳 = 넣을폴더 + ['assets']
    for 폴더 in 훑을곳:
        밑 = os.path.join(뿌리, 폴더.replace('/', os.sep))
        if not os.path.isdir(밑):
            continue
        for 안, 폴더들, 파일들 in os.walk(밑):
            폴더들[:] = [d for d in 폴더들
                         if d not in ('.git', '__pycache__', 'node_modules',
                                      'out', 'img', 'photo', 'images')]
            for 이름 in 파일들:
                길 = os.path.join(안, 이름)
                상대 = os.path.relpath(길, 뿌리)
                if 넣나(상대):
                    것들.append((상대.replace(os.sep, '/'), 길))
    for 상대 in 넣을파일:
        길 = os.path.join(뿌리, 상대.replace('/', os.sep))
        if os.path.isfile(길):
            것들.append((상대, 길))
    것들 = sorted(set(것들))
    return 것들


# ★ **싼 검사를 먼저** 합니다 (2026-10-01)
#   큰 자료(4MB json)에 복잡한 정규식을 돌리면 몇 분이 걸립니다.
#   이 낱말이 아예 없으면 정규식을 돌릴 까닭이 없습니다.
#   거의 모든 파일이 여기서 걸러져 몇 초에 끝납니다.
싼낱말 = ('pub-', 'ftp://', 'password', 'passwd', '비밀번호',
          'secret', 'token', 'api_key', 'apikey', 'api-key',
          'access_key', '@gmail', '@naver', '@daum', '@hanmail')


def 비밀찾기(것들):
    """묶기 전에 **비밀값이 섞였는지** 봅니다."""
    걸린것 = []
    for 상대, 길 in 것들:
        try:
            글 = io.open(길, encoding='utf-8', errors='replace').read()
        except Exception:
            continue
        낮은글 = 글.lower()
        if not any(낱 in 낮은글 for 낱 in 싼낱말):
            continue                      # 낱말조차 없으면 볼 것 없습니다
        for 이름, 꼴 in 비밀꼴:
            for m in 꼴.finditer(글):
                앞뒤 = 글[max(0, m.start() - 60):m.end() + 60]
                if 봐줄것.search(앞뒤):
                    continue
                if any(것 in m.group(0) for 것 in 이미공개):
                    continue
                줄번호 = 글.count(chr(10), 0, m.start()) + 1
                걸린것.append((이름, 상대, 줄번호, m.group(0)[:50]))
    return 걸린것


def 하기(강제=False):
    것들 = 모으기()
    합 = sum(os.path.getsize(p) for _, p in 것들)
    print('넣을 파일 %d개 · %.1fMB' % (len(것들), 합 / 1048576.0))

    걸린것 = 비밀찾기(것들)
    if 걸린것:
        print()
        print('★ 비밀값으로 보이는 것 %d곳' % len(걸린것))
        for 이름, 상대, 줄, 글 in 걸린것[:20]:
            print('    %-14s %s:%d  %s' % (이름, 상대, 줄, 글))
        if not 강제:
            print()
            print('멈춥니다. 한 번 밖으로 나간 것은 되돌릴 수 없습니다.')
            print('사람이 보고 괜찮으면 --force 를 붙여 다시 돌리십시오.')
            return 1
        print('  (--force 로 넘깁니다)')

    날 = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    낼자리 = os.path.join(뿌리, 'tests', 'out')
    if not os.path.isdir(낼자리):
        os.makedirs(낼자리)
    낼곳 = os.path.join(낼자리, '바다가자-검수용-%s.zip' % 날)

    # 판 지문을 꾸러미 맨 앞에 넣습니다 — 어느 판인지 바로 압니다
    한줄 = '(판 지문 없음)'
    p = os.path.join(뿌리, 'site', 'build.json')
    if os.path.isfile(p):
        try:
            한줄 = json.load(io.open(p, encoding='utf-8'))['_한줄']
        except Exception:
            pass
    머리 = chr(10).join([
        한줄,
        '',
        '이 꾸러미는 바깥 검수용입니다.',
        '',
        '넣은 것 — 생성기(engine) · 틀(template) · 자료 원본(data/raw)',
        '          · 문서(docs) · 시험(tests) · 워크플로(.github)',
        '          · 차림표와 셈본(assets 의 css·js)',
        '',
        '뺀 것  — data-private(조사 자료·광고 설정) · oldsite(옛 사이트)',
        '          · site(생성물) · .git · 사진',
        '',
        '사진을 뺐으므로 디자인을 눈으로 보는 검수에는 한계가 있습니다.',
        '화면이 필요하면 badagaja.com 을 직접 보십시오.',
        '',
        '파일 %d개 · %.1fMB' % (len(것들), 합 / 1048576.0),
    ])

    with zipfile.ZipFile(낼곳, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('0-먼저읽어주세요.txt', 머리.encode('utf-8'))
        for 상대, 길 in 것들:
            z.write(길, 상대)
    print()
    print('묶었습니다 — %s' % 낼곳)
    print('  %.1fMB → %.1fMB'
          % (합 / 1048576.0, os.path.getsize(낼곳) / 1048576.0))
    return 0


if __name__ == '__main__':
    sys.exit(하기('--force' in sys.argv))
