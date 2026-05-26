# 🏎️ Tire Degradation Analysis — Module Spec

> 이 문서는 `feature/tire-degradation` 브랜치 작업용 명세서입니다.
> Claude Code에 그대로 전달하여 코드 작성에 사용하세요.

---

## 📋 작업 개요

**브랜치**: `feature/tire-degradation`
**분석 대상**: 2025 Spain GP (Barcelona)
**분석 드라이버**: PIA, NOR, VER, RUS, LEC (상위 포디움 + 추적자)
**핵심 인사이트**: 연료 효과를 보정해야 진짜 디그라데이션이 보인다 (학계 표준: 0.03s/lap)

---

## 🎯 분석 목표

1. 5명의 드라이버가 같은 컴파운드(MEDIUM, HARD)에서 보이는 디그라데이션 차이를 정량 측정
2. 연료 보정 효과를 명시적으로 보여 분석 방법론의 깊이를 드러냄
3. Phase 3 시뮬레이션 엔진의 입력값으로 쓸 수 있는 회귀 계수 추출

---

## ⚠️ Spain 2025 특수 사항

이 경기는 다음과 같은 데이터 노이즈가 있음. 코드에서 명시적으로 처리할 것:

1. **막판 Safety Car (L55/66)** — 마지막 ~10랩은 회귀에서 제외 가능성 검토
2. **VER의 3-stop 전략** — 짧은 스틴트가 섞여 있음, `min_stint_length` 필터 필요
3. **고온 + 거친 노면** — 트래픽이나 손상 시 랩타임이 크게 튐, 110% 컷오프 필수

---

## 📂 파일 구조

```
src/analysis/
└── degradation.py       # 6개 함수 (아래 명세)

step4_degradation_analysis.py  # 실행 스크립트

outputs/
├── degradation_comparison_MEDIUM_spain_2025.png
└── degradation_comparison_HARD_spain_2025.png
```

---

## 🔧 함수 명세 (6개)

### 공통 규칙
- 변수/함수명: 영어 snake_case
- docstring: 한국어, Args/Returns/Example 포함
- 타입 힌트 필수
- 함수 패턴: DataFrame → DataFrame (가능한 곳마다)
- 작업 후 `black src/` + `ruff check --fix src/`

---

### 1. `apply_fuel_correction`

```python
def apply_fuel_correction(
    laps: pd.DataFrame,
    fuel_effect_per_lap: float = 0.03,
) -> pd.DataFrame:
    """
    연료 효과를 제거한 보정 랩타임 컬럼을 추가한다.

    원리:
        F1 차는 레이스 동안 연료가 줄어 가벼워지며 랩당 약 0.03초씩 빨라진다
        (TUM Heilmeier 2020 학계 표준). 디그라데이션을 정확히 측정하려면
        이 효과를 먼저 제거해야 한다.

        보정 공식:
            LapTimeFuelCorrected = LapTime - (TotalLaps - LapNumber) * fuel_effect_per_lap

        의미: "만약 차가 처음부터 끝까지 동일한 연료량이었다면"의 랩타임.
        스틴트 시작 시점(연료 많음)의 무거움 효과가 사라지므로,
        남는 랩타임 증가는 순수한 타이어 디그라데이션이다.

    Args:
        laps: clean_lap_data()를 거친 DataFrame.
            필수 컬럼: 'LapTime' (초 단위), 'LapNumber'
        fuel_effect_per_lap: 연료 1랩당 시간 효과(초). 기본 0.03 (학계 표준).

    Returns:
        원본 DataFrame + 'LapTimeFuelCorrected' 컬럼 (초)

    Example:
        >>> corrected = apply_fuel_correction(clean_laps)
        >>> corrected[['LapNumber', 'LapTime', 'LapTimeFuelCorrected']].head()
    """
```

---

### 2. `get_stints`

```python
def get_stints(
    laps: pd.DataFrame,
    driver: str,
    min_stint_length: int = 5,
) -> List[Dict]:
    """
    한 드라이버의 랩을 피트스톱 기준으로 스틴트별로 분할한다.

    FastF1의 'Stint' 컬럼을 활용. 스틴트가 너무 짧으면(min_stint_length 미만)
    회귀 분석이 의미 없으므로 제외한다.

    ⚠️ Spain 2025: VER이 3-stop을 했으므로 짧은 스틴트가 섞여 있음.
       기본값 5랩이 적절. (VER 마지막 스틴트가 SC 직후 짧을 가능성)

    Args:
        laps: clean_lap_data()를 거친 DataFrame
        driver: 드라이버 약자 ('VER', 'NOR', ...)
        min_stint_length: 최소 스틴트 길이. 이보다 짧으면 결과에서 제외.

    Returns:
        스틴트 정보 리스트. 각 원소:
        {
            'stint_num': int,        # 1, 2, 3, ...
            'compound': str,         # 'SOFT' / 'MEDIUM' / 'HARD'
            'laps': pd.DataFrame,    # 해당 스틴트의 랩 데이터
            'length': int,           # 랩 수
            'start_lap': int,        # 절대 랩 번호 (전체 레이스 기준)
            'end_lap': int,
        }

    Example:
        >>> stints = get_stints(laps, 'VER')
        >>> for s in stints:
        ...     print(f"Stint {s['stint_num']}: {s['compound']}, {s['length']} laps")
        Stint 1: MEDIUM, 18 laps
        Stint 2: HARD, 25 laps
        Stint 3: HARD, 15 laps
    """
```

---

### 3. `calculate_stint_degradation`

```python
def calculate_stint_degradation(
    stint_laps: pd.DataFrame,
    use_fuel_corrected: bool = True,
    outlier_threshold: float = 1.10,
    skip_first_n_laps: int = 2,
) -> Dict:
    """
    한 스틴트의 디그라데이션을 선형 회귀로 계산한다.

    회귀 방법:
        x: 스틴트 내 랩 번호 (1, 2, 3, ... — 절대 랩 아님)
        y: LapTimeFuelCorrected (또는 LapTime if use_fuel_corrected=False)

        scipy.stats.linregress 사용:
            slope    = 디그라데이션 (초/lap, 양수일수록 빠르게 느려짐)
            intercept = 스틴트 시작 시점 랩타임
            r_squared = 회귀 신뢰도 (1에 가까울수록 선형성 좋음)

    ⚠️ 아웃라이어 제거 (Spain 2025 노이즈 대응):
        1. 스틴트 시작 skip_first_n_laps 랩 제외 (아웃랩 + 워밍업)
        2. 스틴트 마지막 랩이 PitInLap이면 제외
        3. outlier_threshold (110%) 이상의 랩타임 제외
           기준: 스틴트 내 최소 랩타임 * threshold

    Args:
        stint_laps: get_stints()의 한 원소의 'laps' DataFrame
        use_fuel_corrected: True면 'LapTimeFuelCorrected', False면 'LapTime' 사용
        outlier_threshold: 컷오프 비율. 1.10 = 110%
        skip_first_n_laps: 스틴트 시작부터 제외할 랩 수

    Returns:
        {
            'slope': float,            # 초/lap (디그라데이션)
            'intercept': float,        # 초
            'r_squared': float,        # 0~1
            'n_laps_used': int,        # 회귀에 사용된 랩 수
            'n_laps_excluded': int,    # 제외된 랩 수
            'compound': str,
            'stint_num': int,
            'excluded_laps': List[int],  # 제외된 절대 랩 번호 (디버깅용)
        }

    Example:
        >>> result = calculate_stint_degradation(stints[1]['laps'])
        >>> print(f"Degradation: {result['slope']:.3f}s/lap (R²={result['r_squared']:.2f})")
        Degradation: 0.084s/lap (R²=0.91)
    """
```

---

### 4. `get_degradation_summary`

```python
def get_degradation_summary(
    laps: pd.DataFrame,
    drivers: List[str],
) -> pd.DataFrame:
    """
    드라이버 × 스틴트별 디그라데이션 요약 테이블을 생성한다.

    내부적으로 각 드라이버에 대해:
        1. get_stints() 호출
        2. 각 스틴트에 대해 calculate_stint_degradation() 호출
        3. 결과를 long-format DataFrame으로 정리

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        drivers: 분석할 드라이버 약자 리스트

    Returns:
        DataFrame with columns:
            Driver | Stint | Compound | Slope | Intercept | R² | LapsUsed | LapsExcluded
            VER    | 1     | MEDIUM   | 0.082 | 78.5     | 0.88 | 16     | 2
            VER    | 2     | HARD     | 0.045 | 79.2     | 0.92 | 22     | 1
            NOR    | 1     | MEDIUM   | 0.095 | 78.1     | 0.94 | 18     | 2
            ...

    Example:
        >>> summary = get_degradation_summary(corrected_laps, ['VER', 'NOR', 'PIA'])
        >>> print(summary.groupby('Compound')['Slope'].mean())
    """
```

---

### 5. `plot_driver_degradation` (모듈에 남기되 step4에선 호출 안 함)

```python
def plot_driver_degradation(
    laps: pd.DataFrame,
    driver: str,
    save_path: str,
) -> None:
    """
    한 드라이버의 모든 스틴트를 한 그래프에 표시 (디버깅/검증용).

    레이아웃:
        - x축: 스틴트 내 랩 번호 (1, 2, 3, ...)
        - y축: 연료 보정 랩타임 (초)
        - 각 스틴트마다 다른 색 + 컴파운드 라벨
        - 각 스틴트에 회귀선 + slope 텍스트
        - 제외된 랩은 회색 X 마커로 표시 (분석 투명성)

    스타일:
        - figsize=(14, 7), dpi=150
        - plt.style.use('dark_background')
        - 영어 레이블

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        driver: 드라이버 약자
        save_path: 저장 경로 (e.g., 'outputs/degradation_VER_spain_2025.png')
    """
```

---

### 6. `plot_degradation_comparison` ⭐ (메인 시각화)

```python
def plot_degradation_comparison(
    laps: pd.DataFrame,
    drivers: List[str],
    compound: str,
    save_path: str,
) -> None:
    """
    같은 컴파운드에서 여러 드라이버의 디그라데이션을 비교한다.

    규칙:
        - 각 드라이버의 해당 컴파운드 스틴트 중 가장 긴 것 사용 (공정한 비교)
        - 만약 어떤 드라이버가 해당 컴파운드를 안 썼으면 자동 제외 + 경고 출력

    레이아웃:
        - x축: 스틴트 내 랩 번호 (1, 2, 3, ...)
        - y축: 연료 보정 랩타임 (초)
        - 드라이버별:
            * raw 데이터: 흐릿한 산점도 (alpha=0.3)
            * 회귀선: 진한 실선/점선
            * 범례에 slope 값 표시: "VER: 0.082 s/lap"

    드라이버별 스타일 (TEAM_COLORS 기반):
        VER: '#3671C6', 실선
        NOR: '#FF8000', 점선 ('--')  ← 맥라렌 PIA와 구분
        PIA: '#FF8000', 실선          ← 맥라렌 NOR과 구분
        RUS: '#27F4D2', 실선
        LEC: '#E80020', 실선

    스타일:
        - figsize=(14, 7), dpi=150
        - plt.style.use('dark_background')
        - 영어 레이블, 깔끔한 그리드
        - 타이틀: "Tire Degradation Comparison — {compound} — 2025 Spanish GP"

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        drivers: ['PIA', 'NOR', 'VER', 'RUS', 'LEC']
        compound: 'MEDIUM' or 'HARD' (Spain은 SOFT 거의 안 씀)
        save_path: 저장 경로
    """
```

---

## 🚀 실행 스크립트: `step4_degradation_analysis.py`

```python
"""
2025 Spain GP — Tire Degradation Analysis
"""

from src.data.session_loader import load_session
from src.data.lap_data import (
    get_drivers_laps, clean_lap_data, filter_quick_laps
)
from src.analysis.degradation import (
    apply_fuel_correction,
    get_degradation_summary,
    plot_degradation_comparison,
)

# 1. 세션 로드
session = load_session(year=2025, gp='Spain', session_type='R')

# 2. 분석 대상 드라이버
DRIVERS = ['PIA', 'NOR', 'VER', 'RUS', 'LEC']

# 3. 랩 데이터 준비
laps = get_drivers_laps(session, drivers=DRIVERS)
clean = clean_lap_data(laps)
quick = filter_quick_laps(clean, threshold=1.07)  # 107% 컷오프

# 4. 연료 보정
corrected = apply_fuel_correction(quick, fuel_effect_per_lap=0.03)

# 5. 요약 테이블 출력
summary = get_degradation_summary(corrected, drivers=DRIVERS)
print("\n=== Degradation Summary ===")
print(summary.to_string(index=False))

# 평균 디그라데이션 (컴파운드별)
print("\n=== Average Degradation by Compound ===")
print(summary.groupby('Compound')['Slope'].agg(['mean', 'std', 'count']))

# 6. 시각화 (그래프 2장)
plot_degradation_comparison(
    corrected,
    drivers=DRIVERS,
    compound='MEDIUM',
    save_path='outputs/degradation_comparison_MEDIUM_spain_2025.png',
)
plot_degradation_comparison(
    corrected,
    drivers=DRIVERS,
    compound='HARD',
    save_path='outputs/degradation_comparison_HARD_spain_2025.png',
)

print("\n✅ 분석 완료. outputs/ 폴더 확인.")
```

---

## ✅ 완료 기준 (Definition of Done)

- [ ] `src/analysis/degradation.py` 6개 함수 모두 구현
- [ ] 모든 함수에 한국어 docstring + 타입 힌트
- [ ] `step4_degradation_analysis.py` 실행 시 에러 없음
- [ ] `outputs/degradation_comparison_MEDIUM_spain_2025.png` 생성
- [ ] `outputs/degradation_comparison_HARD_spain_2025.png` 생성
- [ ] 요약 테이블이 콘솔에 깔끔하게 출력됨
- [ ] `black src/` + `ruff check --fix src/` 통과

---

## 💡 구현 시 주의사항

1. **`apply_fuel_correction`의 TotalLaps**: 세션 전체 랩 수가 아니라 해당 드라이버가 완주한 마지막 랩 번호 기준일 수 있음. FastF1에서 `session.total_laps` 사용 권장.

2. **`get_stints`의 PitInLap/PitOutLap**: 피트인/아웃 랩은 매우 느림. 회귀에서 반드시 제외해야 함. `calculate_stint_degradation`에서 명시적으로 처리.

3. **`plot_degradation_comparison`의 raw 산점도**: alpha를 낮게(0.3) 해야 회귀선이 잘 보임. 데이터 포인트가 너무 진하면 회귀선이 묻힘.

4. **컴파운드 약자**: FastF1은 'SOFT'/'MEDIUM'/'HARD' (대문자) 사용. Spain 2025는 MEDIUM과 HARD 위주, SOFT는 거의 사용 안 됨.

5. **에러 핸들링**: 어떤 드라이버가 특정 컴파운드를 안 썼을 경우 `plot_degradation_comparison`은 그 드라이버를 자동 스킵하고 콘솔에 경고 출력.

---

*이 명세서는 2026-05-27 작성. AI Race Analyst Phase 2 / 타이어 디그라데이션 분석.*
