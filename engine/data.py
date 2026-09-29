# -*- coding: utf-8 -*-
"""자료를 읽어 하나로 합칩니다.  (계약-20)

    data/raw/        옮기는 도구가 만듭니다 — 덮어씁니다
    data/overrides/  사람이 고친 것 — 절대 안 덮습니다
            ↓ 합침
        여기서 돌려주는 값 (파일로 남기지 않습니다)

합치는 규칙
    같은 아이디가 양쪽에 있으면 overrides 가 이깁니다.
    항목 하나만 고쳐도 됩니다 — 나머지는 raw 에서 옵니다.

★ 숫자는 여기서 셉니다 (계약-04·06)
    쪽이나 자료에 「110곳」을 적지 않습니다. 물어보면 세어 줍니다.
"""
import os
import sys
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))


class 자료오류(Exception):
    pass


def _합치기(바탕, 덧):
    """덧이 바탕을 이깁니다. 사전은 파고들며, 목록은 통째로 바꿉니다."""
    나옴 = dict(바탕)
    for k, v in (덧 or {}).items():
        if isinstance(v, dict) and isinstance(나옴.get(k), dict):
            나옴[k] = _합치기(나옴[k], v)
        else:
            나옴[k] = v
    return 나옴


def _읽기(상대길, default=None):
    바탕 = io.read_json(os.path.join(DATA, 'raw', 상대길), default=None)
    덧 = io.read_json(os.path.join(DATA, 'overrides', 상대길), default=None)
    if 바탕 is None and 덧 is None:
        if default is None:
            raise 자료오류('자료가 없습니다: %s' % 상대길)
        return default
    return _합치기(바탕 or {}, 덧 or {})


class 자료:
    """사이트의 모든 자료. 한 번 만들어 두고 씁니다."""

    def __init__(self):
        self.사이트 = _읽기('site.json')
        self.색인 = _읽기('index.json')
        self.어종 = _읽기('species.json')
        # 중국어 낱말표. 없어도 됩니다 — 그때는 한국어로 떨어집니다
        self.중국어낱말 = _읽기('zh.json', default={})
        # 사진. 없어도 돌아갑니다 — 그때는 사진 없는 쪽이 나옵니다
        self._사진자료 = _읽기('photos.json', default={})
        # 옛 첫 화면의 전국 바다지도 (2026-09-27 주인 지시)
        self._지도자료 = _읽기('map.json', default={})
        self._히어로 = None
        self._명소사진 = None
        self._거른사진 = None
        self._채비 = None
        self._새사진 = None
        self._포인트 = None
        self._권역 = None
        self._여행 = None
        self._축제 = None
        self._안내 = None

    @property
    def 지도(self):
        """옛 첫 화면의 전국 바다지도. 없으면 빈 것 — 쪽은 그대로 돕니다."""
        return self._지도자료 or {}

    # ── 사진 ─────────────────────────────────────────────
    #
    # ★ 2026-09-27 주인 지시 「사진 넣어야해」
    #   새 틀 416쪽에 사진이 한 장도 없었습니다. 게다가 build.py 가
    #   대표 사진 주소를 **자료를 안 보고 지어내** 공유 미리보기
    #   52갈래가 깨져 있었습니다.
    #
    #       지어낸 것   img/taean/hero.jpg        ← 없는 파일
    #       실제 파일   img/coast/taean-hero.jpg  ← 있는 파일
    #
    #   이제 자료에서만 읽습니다. 주소를 짐작하지 않습니다.
    @property
    def 사진들(self):
        # ★ **명소와 다른 사진을 걸러 냅니다** (2026-09-29 주인 지시)
        #
        #   「명소들이 이미지 잘못들어간게 많아 … 사진검수해」
        #
        #   옛 사이트에서 옮겨 온 위키미디어 계열 사진 가운데
        #   **다대포해수욕장 자리에 지하철역 승강장**, 오이도 빨간등대
        #   자리에 무덤 비석이 들어 있었습니다. 사진을 하나씩 눈으로
        #   보고 골라 `data/raw/photo-reject.json` 에 적었습니다.
        #
        #   ★ photos.json 은 migrate_photos.py 가 만드는 **생성물**이라
        #     손대지 않습니다. 고치면 다음 이사 때 되돌아갑니다 (규칙 26).
        #     거를 것만 따로 두고 **읽을 때** 걸러 냅니다.
        if self._거른사진 is None:
            거를것 = _읽기('photo-reject.json', default={}) or {}
            self._거른사진 = set(x.get('파일') for x in 거를것.get('거를것', [])
                                 if x.get('파일'))
        # ★ **관광공사에서 새로 받은 명소 사진을 함께 봅니다** (2026-09-29)
        #
        #   주인 지시 — 「사진검수해 실제 사진으로 지역 광관안내 잘
        #   살펴보면 사진 많을꺼야」
        #
        #   명소 393곳 가운데 사진이 있는 곳이 125곳(32%)뿐이라
        #   명소 격자에 빈자리가 크게 났습니다.
        #   engine/fetch_spot_photos.py 가 찾고 download_spot_photos.py 가
        #   받아 둔 것을 여기서 합칩니다.
        #
        #   ★ 받을 때 이미 두 가지를 걸렀습니다.
        #     · **이용허락을 안 주면 버립니다** (주인 규칙 5)
        #     · **명소 좌표에서 1km 밖이면 버립니다** (주인 제안)
        if self._새사진 is None:
            새 = _읽기('spot-photos-new.json', default={}) or {}
            self._새사진 = []
            for x in (새.get('사진') or []):
                if not (x.get('파일') and x.get('이용허락')):
                    continue
                self._새사진.append({
                    '파일': x['파일'], '권역': x['권역'], '명소': x['명소'],
                    '제목': x.get('제목') or x['명소'],
                    '촬영자': x.get('촬영자') or '한국관광공사',
                    '이용허락': x['이용허락'], '쓰임': 'spot',
                    '출처주소': x.get('사진주소') or '',
                    '찍은곳': x.get('주소') or '',
                    '거리km': x.get('거리km'),
                })
        return [x for x in ((self._사진자료.get('사진') or []) + self._새사진)
                if x.get('파일') not in self._거른사진]

    @property
    def 거른사진(self):
        """검사기가 「걸러 놓은 것이 쪽에 남았나」를 볼 때 씁니다."""
        self.사진들            # 채워 넣기
        return self._거른사진

    def 히어로(self, 권역):
        """그 권역의 대표 사진. 없으면 None — **지어내지 않습니다.**"""
        if self._히어로 is None:
            self._히어로 = {}
            for x in self.사진들:
                if str(x.get('쓰임', '')).startswith('hero') and x.get('권역'):
                    # 한 권역에 여럿이면 파일 이름 차례로 첫째를 씁니다
                    앞것 = self._히어로.get(x['권역'])
                    if 앞것 is None or x.get('파일', '') < 앞것.get('파일', ''):
                        self._히어로[x['권역']] = x
        return self._히어로.get(권역)

    @property
    def 채비자료(self):
        """채비도가 읽는 자료 — data/raw/rigs.json

        ★ 호수·간격을 **자료에서 읽습니다** (주인 규칙 29).
          값이 바뀌면 자료만 고치면 모든 어종 쪽이 함께 바뀝니다.
        """
        if self._채비 is None:
            self._채비 = _읽기('rigs.json', default={}) or {}
        return self._채비

    def 명소사진(self, 권역):
        """그 권역의 명소 사진들. 차례를 못 박아 돌려줍니다."""
        if self._명소사진 is None:
            self._명소사진 = {}
            for x in self.사진들:
                if str(x.get('쓰임', '')).startswith('hero'):
                    continue
                if not x.get('권역'):
                    continue
                self._명소사진.setdefault(x['권역'], []).append(x)
            for k in self._명소사진:
                self._명소사진[k].sort(key=lambda v: v.get('파일', ''))
        return self._명소사진.get(권역) or []

    def 어종사진(self, 아이디):
        """그 어종의 사진. 없으면 None — 지어내지 않습니다."""
        for x in self.사진들:
            if x.get('명소') == 아이디 and 'species' in str(x.get('파일', '')):
                return x
        return None

    # ── 권역 ─────────────────────────────────────────────
    @property
    def 권역들(self):
        return self.색인['권역']

    def 권역(self, 아이디):
        if self._권역 is None:
            self._권역 = dict((x['id'], x) for x in self.권역들)
        if 아이디 not in self._권역:
            raise 자료오류('모르는 권역입니다: %s (index.json 에 없습니다)' % 아이디)
        return self._권역[아이디]

    # ── 포인트 ───────────────────────────────────────────
    @property
    def 포인트들(self):
        """모든 포인트. 아이디 차례로 — 늘 같은 차례여야 합니다 (계약-07)"""
        if self._포인트 is None:
            나옴 = []
            for p in sorted(glob.glob(os.path.join(DATA, 'raw', 'points', '*.json'))):
                묶음 = os.path.splitext(os.path.basename(p))[0]
                덧 = io.read_json(
                    os.path.join(DATA, 'overrides', 'points', '%s.json' % 묶음),
                    default={})
                덧표 = dict((x['id'], x) for x in 덧.get('포인트', []))
                for x in io.read_json(p, default={}).get('포인트', []):
                    나옴.append(_합치기(x, 덧표.get(x['id'])))
            나옴.sort(key=lambda x: x['id'])
            self._포인트 = 나옴
        return self._포인트

    def 포인트(self, 권역, 갈래=None):
        """한 권역의 포인트. 갈래를 주면 그것만"""
        return [x for x in self.포인트들
                if x['권역'] == 권역 and (갈래 is None or x['갈래'] == 갈래)]

    # ── 셈 (계약-04·06) ──────────────────────────────────
    def 셈(self, 권역=None, 갈래=None, 묶음=None):
        """포인트 수. **쪽에 적힌 숫자는 전부 여기서 나옵니다.**"""
        n = 0
        묶음표 = None
        if 묶음:
            묶음표 = set(x['id'] for x in self.권역들 if x['묶음'] == 묶음)
        for x in self.포인트들:
            if 권역 and x['권역'] != 권역:
                continue
            if 갈래 and x['갈래'] != 갈래:
                continue
            if 묶음표 is not None and x['권역'] not in 묶음표:
                continue
            n += 1
        return n

    def 묶음별셈(self):
        """묶음 → 포인트 수. 합이 전국 수와 같아야 합니다 (계약-05)"""
        권역묶음 = dict((x['id'], x['묶음']) for x in self.권역들)
        나옴 = collections.Counter()
        for x in self.포인트들:
            나옴[권역묶음.get(x['권역'], '?')] += 1
        return dict(나옴)

    # ── 여행 (명소·먹거리·축제·어종·코스·마을·통제) ─────
    @property
    def 여행들(self):
        if getattr(self, '_여행', None) is None:
            나옴 = {}
            for p in sorted(glob.glob(os.path.join(DATA, 'raw', 'travel',
                                                   '*.json'))):
                묶음 = os.path.splitext(os.path.basename(p))[0]
                덧 = io.read_json(
                    os.path.join(DATA, 'overrides', 'travel', '%s.json' % 묶음),
                    default={})
                덧표 = dict((x['id'], x) for x in 덧.get('권역', []))
                for x in io.read_json(p, default={}).get('권역', []):
                    나옴[x['id']] = _합치기(x, 덧표.get(x['id']))
            self._여행 = 나옴
        return self._여행

    def 여행(self, 권역):
        """한 권역의 여행 자료. 없으면 빈 것을 돌려줍니다"""
        빈것 = {'id': 권역, '명소': [], '먹거리': [], '축제': [], '어종': [],
                '코스': [], '마을': [], '통제': [], '관광안내': None}
        나온것 = self.여행들.get(권역)
        if not 나온것:
            return 빈것
        빈것.update(나온것)
        return 빈것

    # ── 축제 ─────────────────────────────────────────────
    @property
    def 축제들(self):
        """모든 축제. 아이디 차례로 (계약-07)"""
        if self._축제 is None:
            나옴 = []
            for p in sorted(glob.glob(os.path.join(DATA, 'raw', 'festivals',
                                                   '*.json'))):
                묶음 = os.path.splitext(os.path.basename(p))[0]
                덧 = io.read_json(
                    os.path.join(DATA, 'overrides', 'festivals',
                                 '%s.json' % 묶음), default={})
                덧표 = dict((x['id'], x) for x in 덧.get('축제', []))
                for x in io.read_json(p, default={}).get('축제', []):
                    나옴.append(_합치기(x, 덧표.get(x['id'])))
            나옴.sort(key=lambda x: x['id'])
            self._축제 = 나옴
        return self._축제

    def 축제(self, 권역=None, 달=None):
        """권역·달로 고릅니다"""
        return [x for x in self.축제들
                if (권역 is None or x['권역'] == 권역)
                and (달 is None or x.get('달') == 달)]

    # ── 어종 안내 (낚시 어종·해루질 대상) ───────────────
    @property
    def 안내들(self):
        if self._안내 is None:
            바탕 = _읽기('guide.json', default={}).get('어종', [])
            self._안내 = sorted(바탕, key=lambda x: (x['갈래'], x['id']))
        return self._안내

    def 안내(self, 갈래=None):
        return [x for x in self.안내들
                if 갈래 is None or x['갈래'] == 갈래]

    # ── 배우는 차례 (그림 넉 장으로 가르치는 것) ─────────
    @property
    def 배우는차례(self):
        """대상별 단계 그림. 옛 쪽에 있던 35갈래 141단계입니다.

        ★ 2026-09-29 — 옛 쪽과 견주다 이것이 통째로 빠진 것을
          찾았습니다. 손으로 그린 것이라 옛 생성기를 그대로
          돌려 뽑아 자료로 두었습니다.
        """
        if getattr(self, '_차례', None) is None:
            self._차례 = _읽기('lessons.json', default={}).get('차례', {})
        return self._차례

    # ── 어종 ─────────────────────────────────────────────
    def 어종이름(self, 아이디, 언어='ko'):
        if not hasattr(self, '_어종표'):
            self._어종표 = dict((x['id'], x) for x in self.어종['어종'])
        x = self._어종표.get(아이디)
        if x is None:
            raise 자료오류('모르는 어종입니다: %s' % 아이디)
        return (x['이름'].get(언어) or x['이름']['ko'])

    # ── 바다 ─────────────────────────────────────────────
    def 바다안내(self, 권역아이디, 언어='ko'):
        """권역이 닿는 바다의 안내글. 어느 바다인지는 **자료가 정합니다**"""
        바다 = self.권역(권역아이디).get('바다')
        안내 = (self.사이트.get('바다안내') or {}).get(바다)
        if not 안내:
            raise 자료오류('바다 안내글이 없습니다: %s (권역 %s)' % (바다, 권역아이디))

        def 글(칸):
            v = 안내[칸]
            return v.get(언어) or v['ko']
        return {'제목': 글('제목'), '글': 글('글'), '조심': 글('조심')}
