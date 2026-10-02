# -*- coding: utf-8 -*-
"""지피티 시안에서 **해루질 준비물 자료**를 꺼내 옮깁니다 (2026-10-02).

★ 왜 만드나
  주인 지적 — 첫 쪽 「초보자를 위한 해루질 준비물」과 「해루질
  대상 17가지」가 **같은 곳(catch)** 으로 갔습니다.
  「준비물에서는 페이지를 만들더라도 **준비물만 보이게** 만들어.
    제품특성 언제 사용하는지 등을 설명하면 더 좋고」

  지피티 — 「catch/basics.html 은 초보 교육 쪽이고 **준비물만
  보고 싶다**는 질문과 역할이 다릅니다. 새 쪽을 catch/gear.html
  로 분리하세요」 역할 셋을 가릅니다 —
      gear   = 무엇을 챙길까
      basics = 어떻게 시작할까
      catch  = 무엇을 대상으로 하나

★ 한 번만 돌리는 도구입니다. 옮긴 뒤에는 자료가 대장입니다.

★ 지킨 것
  · 제품명·쇼핑몰 **없습니다** (주인 규칙 12)
  · 조개의 **식용 여부는 적지 않습니다** (주인 규칙)
  · 갈퀴·호미는 **지역 규정 확인**을 반드시 밝힙니다
  · 사진 대신 **선그림**을 씁니다. 제품 사진은 저작권이 걸립니다
"""
import io
import json
import os
import re
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

시안 = os.path.join(여기, 'docs', 'catch-gear-prototype.html')
낼곳 = os.path.join(여기, 'data', 'raw', 'gear-catch.json')


def 꺼내기():
    글 = io.open(시안, encoding='utf-8').read()
    i = 글.find('id="gear"')
    if i < 0:
        raise SystemExit('★ 시안에서 준비물 칸을 못 찾았습니다')
    토막 = 글[i:]

    것들 = []
    본 = re.compile(
        r'<div class="gear-icon">(.*?)</div>.*?'
        r'<h3>(.*?)</h3>.*?class="badge[^"]*">(.*?)</span>.*?'
        r'class="gear-one">(.*?)</p>.*?'
        r'<b>이럴 때</b><span>(.*?)</span>.*?'
        r'<b>볼 특징</b><span>(.*?)</span>', re.S)
    for m in 본.finditer(토막):
        그림, 이름, 배지, 한줄, 언제, 특징 = [x.strip() for x in m.groups()]
        # 선그림은 <svg ...>…</svg> 알맹이만 남깁니다
        안 = re.search(r'<svg[^>]*>(.*?)</svg>', 그림, re.S)
        것들.append({
            'id': {'장화': 'boots', '장갑': 'gloves', '망': 'net',
                   '헤드랜턴': 'headlamp', '갈퀴': 'rake',
                   '호미': 'hoe', '구명조끼': 'lifevest'}.get(이름, 이름),
            '이름': 이름,
            '갈래': 배지,
            '한줄': re.sub(r'<[^>]+>', '', 한줄),
            '이럴때': 언제,
            '볼특징': 특징,
            '그림': (안.group(1).strip() if 안 else ''),
        })

    # 상황 묶음 — 시안의 「상황부터 고르세요」
    상황 = []
    for m in re.finditer(
            r'<article class="purpose ([a-z]+)"><strong>(.*?)</strong>'
            r'<span>(.*?)</span>', 글, re.S):
        상황.append({'반': m.group(1), '제목': m.group(2).strip(),
                     '글': re.sub(r'<[^>]+>', '', m.group(3)).strip()})
    return 것들, 상황


def main():
    것들, 상황 = 꺼내기()
    if len(것들) < 5:
        raise SystemExit('★ %d가지만 찾았습니다 — 시안을 확인하세요' % len(것들))

    자료 = {
        '_설명': ('해루질 준비물. 지피티 시안 docs/catch-gear-prototype.html '
                  '에서 옮겼습니다(2026-10-02). 제품명·쇼핑몰은 적지 '
                  '않습니다. 갈퀴·호미는 지역 규정 확인을 밝힙니다.'),
        '제목': '해루질 준비물',
        '_짧은제목': '준비물',
        '소개': ('준비물 이름만 늘어놓지 않고, 왜 필요한지 · 언제 쓰는지 · '
                 '어떤 특징을 보면 되는지만 적습니다. 특정 제품이나 '
                 '가게로 연결하지 않습니다.'),
        '상황': 상황,
        '준비물': 것들,
    }
    from engine import io as _io
    _io.write(낼곳, json.dumps(자료, ensure_ascii=False, indent=1))
    print('준비물 %d가지 · 상황 %d갈래 → %s'
          % (len(것들), len(상황), os.path.relpath(낼곳, 여기)))
    for x in 것들:
        print('  · %-6s %-8s %s' % (x['이름'], x['갈래'], x['이럴때'][:34]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
