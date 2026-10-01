# -*- coding: utf-8 -*-
"""어종·해루질 대상 **아이콘 15가지**를 그립니다.

★ 왜 (2026-09-28)

    주인 지적으로 목록 쪽 맨 위의 큰 덮개 그림을 뺐더니,
    `check_photos` 가 바로 잡았습니다.

        ✗ 2쪽에 그림이 하나도 없습니다
            catch/index.html · fish/index.html
        → 글만 있는 쪽에는 손님이 머물지 않습니다 (주인 규칙 6-1)

    **큰 그림을 빼는 것과 아무것도 안 보이는 것은 다릅니다.**
    옛 쪽도 카드마다 작은 그림이 있었습니다.

    자료(`data/raw/guide/`)에 이미 `그림` 칸이 있습니다 —
    35가지 대상 전부에 이름이 적혀 있는데(shell · crab · float …)
    정작 그 그림이 없었습니다. 여기서 만듭니다.

★ 사진이 아니라 **그린 그림**입니다
    주인 규칙 5 — 사진의 촬영자는 API 가 준 값만 적습니다.
    이건 사진이 아니라 제가 그린 것이라 촬영자가 없습니다.
    `assets/icon/` 에 따로 두어 사진과 섞이지 않게 합니다.

쓰는 법
    python engine/make_icons.py            무엇을 그릴지 봅니다
    python engine/make_icons.py --write    그립니다
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

ASSETS = os.environ.get('BADAGAJA_ASSETS', os.path.join(ROOT, 'assets'))

# 색 — 사이트 차림표와 같은 결로
바다 = '#2E7D9A'
연한바다 = '#BFDCE6'
모래 = '#E5C99A'
진한모래 = '#B8935C'
잉크 = '#3B4A52'
주황 = '#D9873A'

틀 = ('<svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" '
      'role="img" aria-label="%s">%s</svg>')


# ── 그림 15가지 ────────────────────────────────────────────
#
#   ★ 알아볼 수 있을 만큼만 단순하게 그립니다.
#     카드 안에서 28px 로 작게 나오므로 자잘한 선은 뭉개집니다.
그림들 = {
    'shell': ('조개', (
        '<path d="M24 38 C10 30 8 18 24 10 C40 18 38 30 24 38Z" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<path d="M24 11 V37 M16 14 L20 36 M32 14 L28 36" '
        'stroke="%s" stroke-width="1.6" fill="none" stroke-linecap="round"/>'
        % (모래, 진한모래, 진한모래))),

    'razor': ('맛조개', (
        '<rect x="20" y="8" width="8" height="32" rx="4" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<path d="M24 11 V37" stroke="%s" stroke-width="1.4"/>'
        % (모래, 진한모래, 진한모래))),

    'snail': ('고둥', (
        '<path d="M28 12 C16 12 12 22 18 30 C22 36 32 36 34 28" '
        'fill="none" stroke="%s" stroke-width="3.4" stroke-linecap="round"/>'
        '<circle cx="26" cy="24" r="5" fill="%s"/>'
        % (진한모래, 모래))),

    'abalone': ('전복', (
        '<ellipse cx="24" cy="24" rx="15" ry="11" '
        'fill="%s" stroke="%s" stroke-width="2"/>'
        '<circle cx="17" cy="21" r="1.7" fill="%s"/>'
        '<circle cx="22" cy="19" r="1.7" fill="%s"/>'
        '<circle cx="27" cy="19" r="1.7" fill="%s"/>'
        % (잉크, 바다, 연한바다, 연한바다, 연한바다))),

    'crab': ('게', (
        '<ellipse cx="24" cy="26" rx="11" ry="8" fill="%s"/>'
        '<path d="M13 22 L7 16 M35 22 L41 16" stroke="%s" '
        'stroke-width="3" stroke-linecap="round"/>'
        '<path d="M15 32 L10 37 M33 32 L38 37 M20 34 L18 39 M28 34 L30 39" '
        'stroke="%s" stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="20" cy="23" r="1.7" fill="#fff"/>'
        '<circle cx="28" cy="23" r="1.7" fill="#fff"/>'
        % (주황, 주황, 주황))),

    'octopus': ('문어·낙지', (
        '<path d="M24 10 C32 10 36 16 36 22 L36 26 L12 26 L12 22 '
        'C12 16 16 10 24 10Z" fill="%s"/>'
        '<path d="M14 27 C12 33 10 36 8 38 M20 27 C19 34 18 37 17 40 '
        'M28 27 C29 34 30 37 31 40 M34 27 C36 33 38 36 40 38" '
        'stroke="%s" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        '<circle cx="20" cy="20" r="1.8" fill="#fff"/>'
        '<circle cx="28" cy="20" r="1.8" fill="#fff"/>'
        % (주황, 주황))),

    'worm': ('갯지렁이', (
        '<path d="M8 30 C14 20 20 38 26 26 C31 16 37 32 42 24" '
        'stroke="%s" stroke-width="4" fill="none" stroke-linecap="round"/>'
        % 주황)),

    'fish': ('물고기', (
        '<path d="M8 24 C14 15 28 15 36 24 C28 33 14 33 8 24Z" fill="%s"/>'
        '<path d="M36 24 L43 18 L43 30Z" fill="%s"/>'
        '<circle cx="16" cy="22" r="2" fill="#fff"/>'
        % (바다, 바다))),

    'rock': ('갯바위', (
        '<path d="M6 38 L16 18 L24 30 L32 14 L42 38Z" '
        'fill="%s" stroke="%s" stroke-width="1.6"/>'
        '<path d="M6 38 H42" stroke="%s" stroke-width="2.6" '
        'stroke-linecap="round"/>'
        % (잉크, 잉크, 바다))),

    # ── 채비 ──────────────────────────────────────────────
    'float': ('찌 채비', (
        '<path d="M24 6 V20" stroke="%s" stroke-width="2"/>'
        '<path d="M24 20 C29 24 29 31 24 35 C19 31 19 24 24 20Z" fill="%s"/>'
        '<path d="M24 35 V42" stroke="%s" stroke-width="2"/>'
        % (잉크, 주황, 잉크))),

    # ★ 전유동 (2026-09-30 주인 지시 — 「유동채비도 만들어줘」)
    #   반유동 아이콘과 한눈에 갈리게 그립니다.
    #     · 찌가 **아래쪽**에 있습니다 — 원줄을 타고 내려가는 채비입니다
    #     · 옆에 **내려가는 화살표**를 둡니다
    #     · 면사매듭이 없으므로 윗줄에 매듭 표시를 넣지 않습니다
    'float_free': ('전유동 채비', (
        '<path d="M24 6 V26" stroke="%s" stroke-width="2"/>'
        '<path d="M24 26 C29 30 29 37 24 41 C19 37 19 30 24 26Z" fill="%s"/>'
        '<path d="M14 13 V21 M11 18 l3 3 l3 -3" stroke="%s" '
        'stroke-width="1.8" fill="none" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
        % (잉크, 주황, 바다))),

    # ★ 막대찌 (2026-09-30 주인 지시 — 「막대찌부터 모두 만들어」)
    #   구멍찌 아이콘과 갈리게 **가늘고 긴 막대**로 그립니다.
    #   윗머리가 주황이라 물 위에서 잘 보입니다.
    'float_rod': ('막대찌 채비', (
        '<path d="M24 4 V13" stroke="%s" stroke-width="2"/>'
        '<rect x="21" y="13" width="6" height="12" rx="3" fill="%s"/>'
        '<rect x="21" y="23" width="6" height="16" rx="3" fill="%s"/>'
        '<path d="M24 39 V44" stroke="%s" stroke-width="2"/>'
        % (잉크, 주황, 바다, 잉크))),

    'bottom': ('바닥 채비', (
        '<path d="M24 6 V26" stroke="%s" stroke-width="2"/>'
        '<path d="M18 26 H30 L27 34 H21Z" fill="%s"/>'
        '<path d="M24 34 C24 40 30 40 30 36" stroke="%s" '
        'stroke-width="2.4" fill="none" stroke-linecap="round"/>'
        '<path d="M6 42 H42" stroke="%s" stroke-width="2.4" '
        'stroke-linecap="round"/>'
        % (잉크, 잉크, 주황, 진한모래))),

    'jighead': ('지그헤드', (
        '<circle cx="18" cy="18" r="7" fill="%s"/>'
        '<path d="M18 25 C18 34 28 36 30 30" stroke="%s" '
        'stroke-width="2.6" fill="none" stroke-linecap="round"/>'
        '<path d="M18 11 V5" stroke="%s" stroke-width="2"/>'
        % (잉크, 주황, 잉크))),

    'egi': ('에기', (
        '<path d="M14 34 L30 12 C34 16 35 24 30 30 L18 38Z" fill="%s"/>'
        '<path d="M14 34 L8 40 M18 38 L12 42" stroke="%s" '
        'stroke-width="2.2" stroke-linecap="round"/>'
        '<circle cx="28" cy="18" r="2" fill="#fff"/>'
        % (주황, 주황))),

    # ★ 주꾸미·갑오징어용 — **봉돌이 아래**에 달립니다 (2026-09-30)
    #   무늬오징어 에깅(egi)과 채비가 달라 아이콘도 갈랐습니다.
    'egi_sinker': ('에기 채비 (봉돌)', (
        '<path d="M24 4 V20" stroke="%s" stroke-width="2"/>'
        '<path d="M12 26 L26 14 C29 17 30 23 26 27 L16 32Z" fill="%s"/>'
        '<path d="M12 26 L6 31 M16 32 L10 36" stroke="%s" '
        'stroke-width="2" stroke-linecap="round"/>'
        '<circle cx="24" cy="18" r="1.8" fill="#fff"/>'
        '<path d="M24 20 V34" stroke="%s" stroke-width="2"/>'
        '<path d="M21 34 h6 l-3 9Z" fill="%s"/>'
        % (잉크, 주황, 주황, 잉크, 잉크))),

    'sabiki': ('카드 채비', (
        '<path d="M24 5 V43" stroke="%s" stroke-width="2"/>'
        '<path d="M24 13 C30 13 31 18 27 19 M24 23 C30 23 31 28 27 29 '
        'M24 33 C30 33 31 38 27 39" stroke="%s" stroke-width="2.2" '
        'fill="none" stroke-linecap="round"/>'
        % (잉크, 주황))),

    # ★ **민장대** — 릴이 없는 긴 대 (2026-10-01 주인 안내도)
    #   릴을 안 그리는 것이 핵심입니다. 다른 채비는 모두
    #   릴이 있어야 하는데 이것만 없습니다.
    'minjangdae': ('민장대 채비', (
        # 대 — 비스듬히, 손잡이 쪽이 굵습니다
        '<path d="M7 41 L33 12" stroke="%s" stroke-width="4" '
        'stroke-linecap="round"/>'
        '<path d="M22 25 L33 12" stroke="%s" stroke-width="2.4" '
        'stroke-linecap="round"/>'
        # 줄 — 대 끝에서 아래로
        '<path d="M33 12 V38" stroke="%s" stroke-width="1.4" '
        'stroke-linecap="round"/>'
        # 찌 — 주황 머리
        '<rect x="31" y="20" width="4.4" height="9" rx="2.2" '
        'fill="%s"/>'
        % (잉크, 바다, 잉크, 주황))),

    # ★ **처넣기(맥낚시)** — 방파제 구멍으로 내립니다
    #   (2026-10-01 주인 안내도). 던지지 않고 **발밑으로
    #   곧게 내리는** 것이 이 채비의 특징입니다.
    'maknak': ('처넣기 채비', (
        # 방파제 블록 둘 — 그 사이가 구멍입니다
        '<path d="M6 20 h13 v22 h-13 z" fill="%s" opacity=".3"/>'
        '<path d="M29 20 h13 v22 h-13 z" fill="%s" opacity=".3"/>'
        # 줄 — 구멍 사이로 곧게
        '<path d="M24 6 V33" stroke="%s" stroke-width="1.6"/>'
        # 봉돌
        '<circle cx="24" cy="29" r="3" fill="%s"/>'
        # 바늘 — 아래 끝
        '<path d="M24 33 v4 a3 3 0 1 0 6 0 v-2" fill="none" '
        'stroke="%s" stroke-width="2" stroke-linecap="round"/>'
        % (잉크, 잉크, 바다, 잉크, 주황))),

    # ★ **갈치 채비** — 케미가 표시입니다 (2026-10-01 주인 안내도)
    #   갈치는 **밤에만** 잡습니다. 빛을 내는 케미가 다른
    #   채비에는 없는 이 채비만의 부품입니다.
    'galchi': ('갈치 채비', (
        # 케미 — 초록 발광 막대
        '<rect x="21" y="7" width="6" height="13" rx="3" '
        'fill="#7BD34A"/>'
        '<rect x="22.4" y="9" width="1.6" height="8" rx=".8" '
        'fill="#FFFFFF" opacity=".6"/>'
        # 줄
        '<path d="M24 20 V34" stroke="%s" stroke-width="1.6"/>'
        # 와이어 — 굵은 구간 (갈치 이빨을 막습니다)
        '<path d="M24 24 V30" stroke="%s" stroke-width="3" '
        'stroke-linecap="round"/>'
        # 갈치바늘
        '<path d="M24 34 v3 a3.2 3.2 0 1 0 6.4 0 v-2" fill="none" '
        'stroke="%s" stroke-width="2" stroke-linecap="round"/>'
        # 봉돌
        '<path d="M18 38 q3 -5 6 0 q-3 6 -6 0 z" fill="%s"/>'
        % (바다, 잉크, 주황, 잉크))),

    # ★ **메탈지그** — 물고기꼴 쇳덩이 (2026-10-01 주인 안내도)
    #   「멀리 던져야 하는 상황에서 가장 효과적인 채비」
    'metal': ('메탈지그 채비', (
        '<path d="M14 24 q10 -11 20 0 q-10 11 -20 0 z" fill="%s"/>'
        '<path d="M14 24 q10 -11 20 0" fill="none" stroke="%s" '
        'stroke-width="1.6" opacity=".5"/>'
        '<circle cx="29" cy="21" r="1.8" fill="#fff"/>'
        # 줄 — 위로
        '<path d="M34 24 L40 14" stroke="%s" stroke-width="1.5"/>'
        # 삼중 바늘 — 아래
        '<path d="M18 28 v5 M22 29 v5 M14 29 v5" stroke="%s" '
        'stroke-width="2" stroke-linecap="round"/>'
        % (바다, 주황, 잉크, 주황))),

    # ★ **다운샷** — 봉돌이 맨 아래, 바늘이 그 위
    #   (2026-10-01 주인 안내도). 보통 채비와 **거꾸로**인 것이
    #   이 채비의 핵심입니다 — 그래서 바닥 걸림이 적습니다.
    'downshot': ('다운샷 채비', (
        # 줄
        '<path d="M24 6 V38" stroke="%s" stroke-width="1.6"/>'
        # 바늘 — **봉돌보다 위**
        '<path d="M24 20 h5 a3.4 3.4 0 1 1 0 6 h-1" fill="none" '
        'stroke="%s" stroke-width="2" stroke-linecap="round"/>'
        # 웜 — 바늘에 꿰임
        '<path d="M30 26 q5 2 3 6 q-2 4 3 5" fill="none" '
        'stroke="#C0522B" stroke-width="3" stroke-linecap="round"/>'
        # 봉돌 — **맨 아래**
        '<path d="M20 38 q4 -7 8 0 q-4 7 -8 0 z" fill="%s"/>'
        % (바다, 주황, 잉크))),

    # ★ **문어 에기** — 문어 전용 에기 (2026-10-01 주인 안내도)
    #   「일반 에기보다 크고 튼튼한 바늘이 달려 있으며,
    #    문어가 잘 붙잡을 수 있는 발판(갈고리)이 있습니다」
    'octopus': ('문어 에기 채비', (
        # 문어 머리
        '<path d="M14 16 q10 -9 20 0 q0 9 -10 11 q-10 -2 -10 -11 z" '
        'fill="%s"/>'
        '<circle cx="19" cy="16" r="1.8" fill="#fff"/>'
        '<circle cx="29" cy="16" r="1.8" fill="#fff"/>'
        # 다리 넷
        '<path d="M18 27 q-3 7 1 12 M23 28 q-1 8 1 12 '
        'M27 28 q2 8 0 12 M31 26 q4 7 1 12" fill="none" '
        'stroke="%s" stroke-width="2.2" stroke-linecap="round"/>'
        % (주황, 주황))),

    # ★ **플로팅 미노우** — **수면에 뜨는** 루어
    #   (2026-10-01 주인 안내도). 물결 위에 떠 있는 것이
    #   이 채비의 핵심입니다.
    'minnow': ('플로팅 미노우 채비', (
        # 물결 — 수면
        '<path d="M4 28 q6 -4 12 0 t12 0 t12 0" fill="none" '
        'stroke="%s" stroke-width="2" opacity=".5"/>'
        # 미노우 — 물결 위
        '<path d="M13 20 q11 -8 22 0 q-11 8 -22 0 z" fill="%s"/>'
        '<circle cx="30" cy="18" r="1.7" fill="#fff"/>'
        # 립 — 앞쪽 아래
        '<path d="M35 20 l5 4" stroke="%s" stroke-width="2" '
        'stroke-linecap="round"/>'
        # 트레블 훅 둘
        '<path d="M18 24 v5 M27 24 v5" stroke="%s" '
        'stroke-width="2" stroke-linecap="round"/>'
        % (바다, 바다, 잉크, 주황))),

    # ★ **뜰채·가프** — 잡은 고기를 올리는 장비
    #   (2026-10-01 주인 안내도). 매는 채비가 아닙니다.
    'landing': ('뜰채·가프', (
        # 그물 테두리
        '<ellipse cx="18" cy="17" rx="11" ry="9" fill="none" '
        'stroke="%s" stroke-width="2.4"/>'
        # 그물코
        '<path d="M11 15 q7 10 14 0 M18 8 v18" fill="none" '
        'stroke="%s" stroke-width="1.2" opacity=".55"/>'
        # 손잡이
        '<path d="M26 24 L40 40" stroke="%s" stroke-width="3.4" '
        'stroke-linecap="round"/>'
        % (바다, 잉크, 잉크))),

    'lure': ('루어', (
        '<ellipse cx="22" cy="22" rx="12" ry="7" '
        'transform="rotate(-25 22 22)" fill="%s"/>'
        '<circle cx="15" cy="17" r="1.8" fill="#fff"/>'
        '<path d="M30 28 C30 35 36 35 36 31 M22 32 C22 39 28 39 28 35" '
        'stroke="%s" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
        % (바다, 주황))),
}


def main():
    쓰기 = '--write' in sys.argv
    칸 = os.path.join(ASSETS, 'icon')
    print('어종·해루질 아이콘을 그립니다 (주인 규칙 6-1)')
    print('  자리: %s' % os.path.relpath(칸, ROOT))
    print('')
    for 이름 in sorted(그림들):
        대체글, 속 = 그림들[이름]
        s = 틀 % (대체글, 속)
        print('  · %-10s %-12s %4d바이트' % (이름, 대체글, len(s)))
        if 쓰기:
            io.write(os.path.join(칸, '%s.svg' % 이름), s)
    print('')
    if not 쓰기:
        print('  보여만 준 것입니다. 그리려면 --write 를 붙이세요.')
        return 0
    print('아이콘 %d개를 그렸습니다.' % len(그림들))
    return 0


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
