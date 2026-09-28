# -*- coding: utf-8 -*-
"""어종 이름을 아이디로 바꾸고, 같은 것을 하나로 모읍니다.

왜
    옛 사이트는 어종을 **한글 이름으로만** 적었습니다. 그래서
      · 같은 것이 여러 이름으로 흩어졌습니다 (망둥어 / 망둑어)
      · 어종이 아닌 것이 섞였습니다 ("체험", "갯벌 생물 관찰")
      · 이름이 바뀌면 이어진 것이 모두 끊깁니다

    아이디로 바꾸면 이름이 바뀌어도 안 끊깁니다 (계약-03 정신).

무엇을 하나
    1. 같은 것으로 보이는 이름을 하나로 모읍니다
    2. 어종이 아닌 것은 걸러 냅니다
    3. data/raw/species.json 을 만듭니다
    4. 포인트의 '대상' 을 아이디로 바꿉니다

몇 번을 돌려도 안전합니다 (계약-26)
    ★ 2026-09-26 — 처음 판은 두 번 돌리면 자료가 망가졌습니다.
      이미 바뀐 `gamseongdom` 을 **새 어종 이름**으로 읽고 `etc-001` 을 덧씌웠습니다.
      그래서 이제 species.json 을 먼저 읽어, 이미 아이디인 값은 본디 이름으로
      되돌린 뒤에 일합니다. 시험: tests/test_fix_species.py

영문 이름표에 없는 이름이 나오면 **쓰지 않고 멈춥니다.**
    순번(etc-001)을 저절로 붙이면 쓰임 횟수에 따라 번호가 흔들립니다.
    아이디는 한 번 정하면 안 바뀌어야 하므로(계약-03), 사람이 이름을 줍니다.

쓰는 법
    python engine/fix_species.py            보여만 줍니다
    python engine/fix_species.py --write    씁니다
"""
import os
import re
import sys
import glob
import collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from engine import io   # noqa: E402

# 자료가 있는 자리. 시험은 여기를 딴 데로 돌려 **진짜 자료를 안 건드립니다**
DATA = os.environ.get('BADAGAJA_DATA', os.path.join(ROOT, 'data'))

# 같은 것을 가리키는 다른 이름 — 왼쪽으로 모읍니다
같은것 = {
    '망둑어': '망둥어',
    '문어(현장 확인)': '문어',
    '세발낙지': '낙지',
    '참꼬막': '꼬막',
    '왕우럭조개': '우럭조개',
    '개불(현장 확인)': '개불',
    '쭈꾸미': '주꾸미',
    # 2026-09-26 — 순번(etc-)이 붙은 것 가운데 이미 있는 이름과 같은 것
    '학공치': '학꽁치',
    '볼낙': '볼락',
    '홍합류': '홍합',
    '고둥류': '고둥',
    '게류': '게',
    '새우류': '새우',
    '해조류': '미역',
    '가리비류': '가리비',
    '대합': '백합',
    '왕게': '털게',
    # 남은 것을 마저 — 별칭·괄호 붙은 것을 본디 이름으로
    '놀래미': '노래미',
    '장대': '양태',              # 장대는 양태의 딴이름
    '보구치': '백조기',          # 같은 물고기
    '돌문어': '문어',
    '살오징어': '오징어',
    '풀치(갈치)': '갈치',
    '갈치(풀치)': '갈치',
    '짱뚱어(관찰)': '짱뚱어',
    '백합(둔장어촌체험마을 체험장)': '백합',
    '참가자미': '가자미',
    '대맛': '맛조개',
    '비단조개': '명주조개',
    '조개': '조개류',
}

# 어종·해산물이 아닌 것 — 자료에서 뺍니다
어종아님 = re.compile(
    r'^(체험|갯벌\s*생물\s*관찰|관찰|산책|해루질|낚시|기타|각종|여러|다양|잡어|개막이)'
)

# 이름 → 영문 아이디. 사람이 주소나 파일 이름에서 알아볼 수 있게
영문 = {
    '감성돔': 'gamseongdom', '농어': 'nongeo', '우럭': 'ureok', '광어': 'gwangeo',
    '참돔': 'chamdom', '벵에돔': 'bengedom', '볼락': 'bollak', '노래미': 'noraemi',
    '숭어': 'sungeo', '붕장어': 'bungjangeo', '도다리': 'dodari', '가자미': 'gajami',
    '학꽁치': 'hakkongchi', '전어': 'jeoneo', '갈치': 'galchi', '고등어': 'godeungeo',
    '삼치': 'samchi', '망둥어': 'mangdungeo', '무늬오징어': 'muniojingeo',
    '갑오징어': 'gabojingeo', '주꾸미': 'jukkumi', '문어': 'muneo', '낙지': 'nakji',
    '민어': 'mineo', '쥐노래미': 'jwinoraemi', '보리멸': 'borimyeol',
    '바지락': 'bajirak', '맛조개': 'matjogae', '동죽': 'dongjuk', '백합': 'baekhap',
    '꼬막': 'kkomak', '개불': 'gaebul', '해삼': 'haesam', '전복': 'jeonbok',
    '소라': 'sora', '고둥': 'godung', '게': 'ge', '새우': 'saeu',
    '멍게': 'meongge', '성게': 'seonggae', '굴': 'gul', '홍합': 'honghap',
    '톳': 'tot', '미역': 'miyeok', '짱뚱어': 'jjangttungeo', '갯지렁이': 'gaetjireongi',
    '우럭조개': 'ureokjogae', '가리비': 'garibi', '키조개': 'kijogae',
    # 2026-09-26 — 쓰임이 많은 것부터 이름을 줍니다.
    # 순번(etc-001)보다 뜻이 보이는 이름이 주소·파일 이름에서 알아보기 쉽습니다
    '돌돔': 'doldom', '전갱이': 'jeongaengi', '꽃게': 'kkotge', '박하지': 'bakhaji',
    '보말': 'bomal', '한치': 'hanchi', '부시리': 'busiri', '넙치': 'neopchi',
    '방어': 'bangeo', '농게': 'nongge', '칠게': 'chilge', '갯가재': 'gaetgajae',
    '가무락': 'gamurak', '모시조개': 'mosijogae', '새조개': 'saejogae',
    '피조개': 'pijogae', '다슬기': 'daseulgi', '군소': 'gunso', '미더덕': 'mideodeok',
    '대하': 'daeha', '보리새우': 'borisaeu', '쭈꾸미': 'jukkumi',   # 주꾸미와 같은 것
    '열기': 'yeolgi', '쏨뱅이': 'ssombaengi', '우럭볼락': 'ureokbollak',
    '삼세기': 'samsegi', '아귀': 'agwi', '임연수어': 'imyeonsueo',
    '도루묵': 'dorumuk', '양태': 'yangtae', '숭대': 'sungdae', '밴댕이': 'baendaengi',
    '청어': 'cheongeo', '멸치': 'myeolchi', '정어리': 'jeongeori',
    '참게': 'chamge', '털게': 'teolge', '대게': 'daege', '홍게': 'hongge',
    '성대': 'seongdae', '가오리': 'gaori', '홍어': 'hongeo', '간재미': 'ganjaemi',
    '서대': 'seodae', '민꽃게': 'minkkotge', '쥐치': 'jwichi', '독가시치': 'dokgasichi',
    '고랑치': 'gorangchi', '용치놀래기': 'yongchi', '황놀래기': 'hwangnolraegi',
    '호래기': 'horaegi', '골뱅이': 'golbaengi', '자리돔': 'jaridom', '황어': 'hwangeo',
    '벤자리': 'benjari', '망상어': 'mangsangeo', '백조기': 'baekjogi',
    '조개류': 'jogae', '따개비': 'ttagaebi', '거북손': 'geobuksol',
    '군부': 'gunbu', '배말': 'baemal', '삿갓조개': 'satgatjogae',
    '뿔소라': 'ppulsora', '피뿔고둥': 'pippulgodung', '총알고둥': 'chongalgodung',
    '맛살': 'matsal', '개조개': 'gaejogae', '떡조개': 'tteokjogae',
    '민들조개': 'mindeuljogae', '명주조개': 'myeongjujogae',
    '쏠종개': 'ssoljonggae',
    # 마지막 남은 것들 — 순번(etc-)이 하나도 안 남게 합니다
    '부세': 'buse', '돌게': 'dolge', '다금바리': 'dageumbari', '쏙': 'ssok',
    '망농어': 'mangnongeo', '방게': 'bangge', '갯고둥': 'gaetgodung',
    '갯벌장어': 'gaetbeoljangeo', '은어': 'euneo', '복어': 'bogeo',
    '붉바리': 'bukbari', '소라게': 'sorage', '새꼬막': 'saekkomak',
    '강도다리': 'gangdodari', '오징어': 'ojingeo',
}


def 아이디(이름):
    """한글 이름 → 아이디. 영문 표가 있으면 쓰고, 없으면 순번을 붙입니다."""
    이름 = 같은것.get(이름, 이름)
    if 이름 in 영문:
        return 영문[이름], 이름
    return None, 이름


def 되돌리기표():
    """대상에 적힌 값 → 본디 한글 이름.

    두 가지를 되돌립니다
      · sp-001   — 옮기는 도구가 붙인 임시 아이디 (species-map.json)
      · gamseongdom — 이 도구가 이미 붙인 아이디 (species.json)

    둘째를 빠뜨려 두 번째 실행이 자료를 망가뜨렸습니다 (2026-09-26).
    """
    표 = {}
    옛 = io.read_json(os.path.join(DATA, 'raw', 'species-map.json'),
                      default={}).get('이름표', {})
    for 이름, 아 in 옛.items():
        표[아] = 이름
    이미 = io.read_json(os.path.join(DATA, 'raw', 'species.json'), default={})
    for x in 이미.get('어종', []):
        표[x['id']] = (x.get('이름') or {}).get('ko') or x['id']
    return 표


def main():
    쓰기 = '--write' in sys.argv

    # 모든 포인트에서 어종 이름을 모읍니다
    파일들 = sorted(glob.glob(os.path.join(DATA, 'raw', 'points', '*.json')))
    쓰인이름 = collections.Counter()
    거꾸로 = 되돌리기표()

    for p in 파일들:
        d = io.read_json(p, default={})
        for x in d.get('포인트', []):
            for s in (x.get('대상') or []):
                쓰인이름[거꾸로.get(s, s)] += 1

    # 정리
    표 = {}          # 원래 이름 → 아이디
    어종 = {}        # 아이디 → {이름, 쓰인 횟수}
    버림 = []
    이름없음 = []
    for 이름, 횟수 in 쓰인이름.most_common():
        이름 = (이름 or '').strip()
        if not 이름 or 어종아님.match(이름):
            버림.append((이름, 횟수))
            continue
        아, 모은이름 = 아이디(이름)
        if 아 is None:
            이름없음.append((이름, 횟수))
            continue
        표[이름] = 아
        if 아 in 어종:
            어종[아]['쓰임'] += 횟수
        else:
            어종[아] = {'id': 아, '이름': {'ko': 모은이름, 'zh': None}, '쓰임': 횟수}

    print('어종 이름 정리')
    print('  쓰인 이름 %d가지 → 어종 %d가지' % (len(쓰인이름), len(어종)))
    print('')
    print('  많이 쓰인 것')
    for x in sorted(어종.values(), key=lambda v: -v['쓰임'])[:10]:
        print('    %-16s %-14s %4d곳' % (x['이름']['ko'], x['id'], x['쓰임']))
    print('')

    모음 = [(k, v) for k, v in 같은것.items() if k in 쓰인이름]
    if 모음:
        print('  같은 것으로 모은 이름 %d가지' % len(모음))
        for a, b in 모음:
            print('    %s → %s' % (a, b))
        print('')

    if 버림:
        print('  어종이 아니라 뺀 것 %d가지' % len(버림))
        for 이름, 횟수 in 버림[:6]:
            print('    %-20s %d곳' % (이름, 횟수))
        print('')

    if 이름없음:
        print('★ 영문 이름표에 없는 이름 %d가지 — 쓰지 않고 멈춥니다' % len(이름없음))
        for 이름, 횟수 in 이름없음:
            print('    %-20s %4d곳' % (이름, 횟수))
        print('')
        print('  engine/fix_species.py 의 영문 표(또는 같은것)에 더해 주세요.')
        print('  순번을 저절로 붙이면 쓰임 횟수에 따라 아이디가 흔들립니다 (계약-03)')
        return 1

    if not 쓰기:
        print('보여만 준 것입니다. 쓰려면 --write 를 붙이세요.')
        return 0

    # 어종 자료
    io.write_json(os.path.join(DATA, 'raw', 'species.json'), {
        '_설명': '어종·해루질 대상. 포인트가 이 아이디를 가리킵니다',
        '어종': sorted(({'id': v['id'], '이름': v['이름']} for v in 어종.values()),
                       key=lambda x: x['id']),
    })

    # 포인트의 대상을 아이디로
    바꾼수 = 0
    for p in 파일들:
        d = io.read_json(p, default={})
        for x in d.get('포인트', []):
            새대상 = []
            for s in (x.get('대상') or []):
                # ★ 여기서도 되돌리기 표를 써야 합니다 — 이미 아이디인 값을
                #   못 알아보면 대상이 통째로 비어 버립니다 (2026-09-26)
                아 = 표.get((거꾸로.get(s, s) or '').strip())
                if 아 and 아 not in 새대상:
                    새대상.append(아)
                    바꾼수 += 1
            x['대상'] = 새대상
        io.write_json(p, d)

    # 옛 이름표는 더 쓰지 않습니다.
    #
    # ★ 계약-17(삭제는 만드는 일보다 어려워야 한다)의 **밝힌 예외**입니다
    #   지우는 것은 이 도구가 방금 대신한 중간 파일입니다.
    #   migrate.py 가 만들고 여기가 다 쓰면 없앱니다 — 사람이 모은
    #   자료가 아닙니다. 남겨 두면 오히려 check_stale.py 가
    #   「앞 도구만 돌렸다」고 잡습니다.
    #   --write 다짐을 이미 받았으므로 여기서 또 묻지 않습니다.
    옛 = os.path.join(DATA, 'raw', 'species-map.json')
    if os.path.exists(옛):
        os.remove(옛)   # 계약-17 예외 — 제가 대신한 중간 파일

    print('자료에 썼습니다.')
    print('  data/raw/species.json — 어종 %d가지' % len(어종))
    print('  포인트의 대상 %d건을 아이디로 바꿨습니다' % 바꾼수)
    return 0


if __name__ == '__main__':
    sys.exit(main())
