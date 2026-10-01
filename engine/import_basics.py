# -*- coding: utf-8 -*-
"""옛 쪽의 **왕초보 그림 강의**를 자료로 옮깁니다 (2026-10-01).

★ 왜 — 권역 57쪽이 거는데 **새 사이트에 없었습니다**

      fish/basics.html   「바다낚시 처음이라면」  57곳이 걸림
      catch/basics.html  「해루질 처음이라면」    57곳이 걸림

  권역 쪽 57개 전부에 「처음이신가요」 칸이 있고 거기서 이 둘을
  가리킵니다. **초보자가 가장 먼저 누르는 링크**인데, 새 사이트에
  파일이 없어 서버에 남은 **옛 디자인 쪽**으로 떨어지고 있었습니다.

  `data/raw/keep.json` 에 「새 틀은 아직 안 만듭니다」라고 제가
  적어 두어, 검사기가 **일부러 남긴 것**으로 보고 통과시켰습니다.
  미뤄도 된다고 본 판단이 틀렸습니다 — 광고 심사가 보는 것은
  **사이트가 하나로 이어져 있는가**입니다.

★ 내용은 좋습니다. 버리지 않고 **자료로 옮깁니다.**
  낚싯대 이름 · 릴 · 매듭 · 던지기 · 챔질 · 뜰채 · 쓰레기.
  그림 7장이 번호 순서로 이어지는 **고유한 안내**입니다.
  새로 쓰면 더 나빠집니다. 뜻은 그대로 두고 **자리만** 옮깁니다.

★ 어종 차례와 **섞지 않습니다**
  `lessons.json` 의 `차례` 에는 어종 35가지가 들어 있습니다.
  기초 강의는 어종이 아니므로 `기초` 라는 다른 칸에 둡니다.
  섞으면 어종 목록에 「낚싯대 이름부터」가 끼어듭니다.

★ 한 번만 돌리는 도구입니다
  옮긴 뒤에는 자료가 대장이고, 옛 쪽은 보지 않습니다.
"""
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
옛집 = os.path.join(os.path.dirname(여기), 'badagaja-site')
자료길 = os.path.join(여기, 'data', 'raw', 'lessons.json')

_카드 = re.compile(
    r'<figure class="ls-card">\s*(.*?)\s*</figure>', re.S)
_svg = re.compile(r'<svg\b.*?</svg>', re.S)
_캡 = re.compile(r'<figcaption>(.*?)</figcaption>', re.S)
_제목 = re.compile(r'<b>(?:<i class="ls-no">\d+</i>)?(.*?)</b>', re.S)
_속 = re.compile(r'<span>(.*?)</span>', re.S)
_겉svg = re.compile(r'^<svg[^>]*>|</svg>$', re.S)
_머리 = re.compile(r'<p class="ls-kicker">(.*?)</p>\s*'
                   r'<h2>(.*?)</h2>\s*<p class="ls-lede">(.*?)</p>', re.S)


def _글만(s):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', s)).strip()


def 뽑기(쪽길):
    """한 쪽에서 강의 카드들을 뽑습니다."""
    with io.open(쪽길, encoding='utf-8') as f:
        s = f.read()
    머리 = _머리.search(s)
    카드들 = []
    for 속 in _카드.findall(s):
        그림 = _svg.search(속)
        캡 = _캡.search(속)
        if not (그림 and 캡):
            continue
        제목 = _제목.search(캡.group(1))
        글 = _속.search(캡.group(1))
        # ★ SVG **겉껍데기는 벗깁니다** — 새 사이트가 제 틀로 감쌉니다
        #   (`차례` 자료의 그림도 알맹이만 들어 있습니다)
        알맹이 = _겉svg.sub('', 그림.group(0)).strip()
        카드들.append({
            '제목': _글만(제목.group(1)) if 제목 else '',
            '그림': 알맹이,
            # ★ **굵게는 살립니다** (메모: 굵게 표시는 모든 칸에)
            #   esc() 를 쓰는 자리라 `<b>` 를 떼면 뜻이 흐려집니다.
            #   별표(**)로 두면 그대로 글자가 되어 보입니다.
            '글': re.sub(r'\s+', ' ',
                         re.sub(r'</?b>', '**', 글.group(1))).strip()
            if 글 else '',
        })
    return {
        '꼬리말': _글만(머리.group(1)) if 머리 else '',
        '제목': _글만(머리.group(2)) if 머리 else '',
        '소개': re.sub(r'\s+', ' ',
                       re.sub(r'</?b>', '**', 머리.group(3))).strip()
        if 머리 else '',
        '단계': 카드들,
    }


def main():
    할것 = [
        ('낚시', os.path.join(옛집, 'fish', 'basics.html')),
        ('해루질', os.path.join(옛집, 'catch', 'basics.html')),
    ]
    with io.open(자료길, encoding='utf-8') as f:
        자료 = json.load(f)
    기초 = 자료.get('기초') or {}
    for 이름, 길 in 할것:
        if not os.path.exists(길):
            print('  ! 옛 쪽을 못 찾았습니다 — %s' % 길)
            continue
        것 = 뽑기(길)
        if not 것['단계']:
            print('  ! %s — 카드를 못 뽑았습니다' % 이름)
            continue
        기초[이름] = 것
        print('  %s — 「%s」 그림 %d장'
              % (이름, 것['제목'], len(것['단계'])))
    자료['기초'] = 기초
    자료.setdefault(
        '_기초',
        '왕초보 그림 강의. 어종 차례(차례)와 섞지 않습니다 — '
        '어종이 아니라 「낚싯대 다루는 법」처럼 모두에게 같은 것입니다. '
        'engine/import_basics.py 가 옛 쪽에서 옮겨 왔습니다')
    with io.open(자료길, 'w', encoding='utf-8') as f:
        json.dump(자료, f, ensure_ascii=False, indent=1)
    print('  → data/raw/lessons.json 의 「기초」 에 넣었습니다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
