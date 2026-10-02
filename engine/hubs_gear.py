# -*- coding: utf-8 -*-
"""해루질 준비물 쪽 — `catch/gear.html` (2026-10-02).

★ 왜 따로 만드나
  주인 지적 — 첫 쪽에서 「초보자를 위한 해루질 준비물」과
  「해루질 대상 17가지」가 **같은 곳으로** 갔습니다.

  지피티 — 「catch/basics.html 은 초보 교육 쪽이고, **준비물만
  보고 싶다**는 질문과 역할이 다릅니다」 셋을 가릅니다 —
      gear   = 무엇을 챙길까
      basics = 어떻게 시작할까
      catch  = 무엇을 대상으로 하나

★ 겉모습은 지피티 시안 `docs/catch-gear-prototype.html` 그대로입니다.

★ 지킨 것
  · 제품명·쇼핑몰 **없습니다** (주인 규칙 12)
  · 조개의 **식용 여부는 적지 않습니다**
  · 갈퀴·호미는 **지역 규정 확인**을 밝힙니다
  · 사진 대신 **선그림** — 제품 사진은 저작권이 걸립니다
"""
import os
import sys

여기 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 여기)

from engine import template, url                     # noqa: E402
from engine.hubs import esc, 칸, _바탕값              # noqa: E402
from engine import io as _io                         # noqa: E402

자료길 = os.path.join(여기, 'data', 'raw', 'gear-catch.json')


def 있나():
    return os.path.isfile(자료길)


def _그림(속):
    if not 속:
        return ''
    return ('<svg viewBox="0 0 64 64" aria-hidden="true" fill="none" '
            'stroke="currentColor" stroke-width="2.4" '
            'stroke-linecap="round" stroke-linejoin="round">%s</svg>' % 속)


def 준비물쪽(d, 언어='ko'):
    것 = _io.read_json(자료길, default=None)
    if not 것 or not (것.get('준비물') or []):
        return None, None

    쪽길 = 'catch/gear.html'

    # ── 머리 — 대표 준비물 여섯을 작은 그림으로
    작은것 = []
    # ★ **일곱 개를 다 보입니다** (2026-10-02 바깥 검수)
    #   「7가지라고 하는데 상단 대표 아이콘은 6개뿐입니다.
    #     **구명조끼가 빠져** 있습니다. 안전 장비가 빠진 상태라
    #     시각적으로도, 의미상으로도 어색합니다」
    #   모바일에서는 두세 줄로 쌓지 않고 **가로로 밉니다.**
    for x in 것['준비물']:
        작은것.append(
            '<div class="kit-mini">%s<b>%s</b><span>%s</span></div>'
            % (_그림(x.get('그림')), esc(x['이름']),
               esc((x.get('이럴때') or '').split(',')[0].strip()[:8])))

    # ── 상황부터 고르기
    상황칸 = ''
    if 것.get('상황'):
        줄 = ''.join(
            '<article class="purpose purpose--%s"><strong>%s</strong>'
            '<span>%s</span></article>'
            % (esc(s.get('반') or 'core'), esc(s['제목']), esc(s['글']))
            for s in 것['상황'])
        상황칸 = '<div class="purpose-grid">%s</div>' % 줄

    # ── 준비물 카드
    카드 = []
    for x in 것['준비물']:
        카드.append(
            '<article class="gear-card">'
            '<div class="gear-icon">%s</div>'
            '<div class="gear-in">'
            '<div class="gear-title"><h3>%s</h3>'
            '<span class="gear-badge">%s</span></div>'
            '<p class="gear-one">%s</p>'
            '<div class="gear-specs">'
            '<div class="gear-spec"><b>이럴 때</b><span>%s</span></div>'
            '<div class="gear-spec"><b>볼 특징</b><span>%s</span></div>'
            '</div></div></article>'
            % (_그림(x.get('그림')), esc(x['이름']), esc(x.get('갈래') or ''),
               esc(x.get('한줄') or ''), esc(x.get('이럴때') or ''),
               esc(x.get('볼특징') or '')))

    # ★ **규정 확인을 반드시 밝힙니다** (지피티 지시 · 주인 규칙)
    규정 = ('<div class="warn-box"><h3>갈퀴·호미는 지역 규정을 먼저 봅니다</h3>'
            '<p>마을어장과 어촌계 구역에서는 도구를 쓰는 것 자체가 '
            '금지된 곳이 있습니다. 같은 갯벌이라도 구역마다 다르므로 '
            '가기 전에 그곳 규정을 반드시 확인하세요. '
            '<a href="%s">금어기·크기·마을어장 보기</a></p>'
            '<p class="warn-small">잡을 수 있는 크기와 철도 함께 봅니다. '
            '여기서는 어떤 도구가 어떤 때 쓰이는지만 설명합니다.</p>'
            '</div>' % esc(url.rel(쪽길, url.rule(언어))))

    칸들 = []
    if 상황칸:
        칸들.append(칸('상황부터 고르세요', '%d갈래' % len(것['상황']),
                       '<p class="lead">같은 준비물도 쓰는 때가 '
                       '다릅니다.</p>' + 상황칸, 흰=False))
    칸들.append(칸('해루질 준비물 %d가지' % len(것['준비물']),
                   '기능과 쓰는 때',
                   '<p class="lead">제품 이름이 아니라 **무엇을 왜 쓰는지**를 '
                   '적습니다.</p>'.replace('**', '')
                   + '<div class="gear-grid">%s</div>' % ''.join(카드)
                   + 규정, 흰=True))

    값 = _바탕값(
        d, 쪽길, 언어,
        제목='해루질 준비물 — 무엇을 왜 챙기나 | %s' % d.사이트['이름']['ko'],
        짧은제목='해루질 준비물',
        설명='해루질에 챙길 것 %d가지를 왜 쓰는지·언제 쓰는지·무엇을 '
             '보고 고르는지로 설명합니다. 특정 제품이나 가게로 '
             '연결하지 않습니다.' % len(것['준비물']),
        머리말='해루질 처음 준비한다면',
        큰제목='무엇을 챙겨야 할까요',
        소개글=것.get('소개') or '',
        한줄='%d가지' % len(것['준비물']),
        갈래칸='<div class="hero-kit">%s</div>' % ''.join(작은것)
               + ''.join(칸들),
        꼬리안내='준비물은 바다와 자리에 따라 다릅니다. 갯바위·테트라포드'
                 '에서는 구명조끼를 먼저 챙기세요.',
        이름표글='%d가지' % len(것['준비물']),
        _og갈래='catch')
    return 쪽길, template.그리기('rig-parts.html', 값)
