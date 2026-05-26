"""
degradation.py
==============
타이어 디그라데이션 분석 모듈

연료 보정을 거쳐 스틴트별 타이어 디그라데이션을 선형 회귀로 계산하고,
드라이버 간 디그라데이션을 비교·시각화하는 함수들을 제공한다.
"""

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from src.analysis.pace import TEAM_COLORS

# 드라이버별 선 스타일 (같은 팀 맥라렌 NOR/PIA 구분용)
DRIVER_LINESTYLES: dict[str, str] = {
    "VER": "-",
    "NOR": "--",
    "PIA": "-",
    "RUS": "-",
    "LEC": "-",
}

# 컴파운드별 색상
COMPOUND_COLORS: dict[str, str] = {
    "SOFT": "#FF3333",
    "MEDIUM": "#FFD700",
    "HARD": "#FFFFFF",
    "INTERMEDIATE": "#39B54A",
    "WET": "#0067FF",
}

# 컴파운드별 마커 모양
COMPOUND_MARKERS: dict[str, str] = {
    "SOFT": "o",
    "MEDIUM": "^",
    "HARD": "s",
    "INTERMEDIATE": "D",
    "WET": "D",
}


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
            LapTimeFuelCorrected = LapTimeSeconds - (TotalLaps - LapNumber) * fuel_effect_per_lap

        의미: "만약 차가 처음부터 끝까지 동일한 연료량이었다면"의 랩타임.
        스틴트 시작 시점(연료 많음)의 무거움 효과가 사라지므로,
        남는 랩타임 증가는 순수한 타이어 디그라데이션이다.

    Args:
        laps: clean_lap_data()를 거친 DataFrame.
            필수 컬럼: 'LapTimeSeconds' (초 단위), 'LapNumber', 'Driver'
        fuel_effect_per_lap: 연료 1랩당 시간 효과(초). 기본 0.03 (학계 표준).

    Returns:
        원본 DataFrame + 'LapTimeFuelCorrected' 컬럼 (초)

    Example:
        >>> corrected = apply_fuel_correction(clean_laps)
        >>> corrected[['LapNumber', 'LapTimeSeconds', 'LapTimeFuelCorrected']].head()
    """
    df = laps.copy()
    total_laps_per_driver = df.groupby("Driver")["LapNumber"].transform("max")
    df["LapTimeFuelCorrected"] = (
        df["LapTimeSeconds"]
        - (total_laps_per_driver - df["LapNumber"]) * fuel_effect_per_lap
    )
    return df


def get_stints(
    laps: pd.DataFrame,
    driver: str,
    min_stint_length: int = 5,
) -> list[dict]:
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
    driver_laps = laps[laps["Driver"] == driver].copy()
    stints = []

    for stint_num, stint_df in driver_laps.groupby("Stint"):
        if len(stint_df) < min_stint_length:
            continue
        compound = (
            stint_df["Compound"].mode()[0]
            if "Compound" in stint_df.columns
            else "UNKNOWN"
        )
        stints.append(
            {
                "stint_num": int(stint_num),
                "compound": compound,
                "laps": stint_df.reset_index(drop=True),
                "length": len(stint_df),
                "start_lap": int(stint_df["LapNumber"].min()),
                "end_lap": int(stint_df["LapNumber"].max()),
            }
        )

    return sorted(stints, key=lambda s: s["stint_num"])


def calculate_stint_degradation(
    stint_laps: pd.DataFrame,
    use_fuel_corrected: bool = True,
    outlier_threshold: float = 1.10,
    skip_first_n_laps: int = 2,
) -> dict:
    """
    한 스틴트의 디그라데이션을 선형 회귀로 계산한다.

    회귀 방법:
        x: 스틴트 내 랩 번호 (1, 2, 3, ... — 절대 랩 아님)
        y: LapTimeFuelCorrected (또는 LapTimeSeconds if use_fuel_corrected=False)

        scipy.stats.linregress 사용:
            slope    = 디그라데이션 (초/lap, 양수일수록 빠르게 느려짐)
            intercept = 스틴트 시작 시점 랩타임 (x=0 외삽)
            r_squared = 회귀 신뢰도 (1에 가까울수록 선형성 좋음)

    ⚠️ 아웃라이어 제거 (Spain 2025 노이즈 대응):
        1. 스틴트 시작 skip_first_n_laps 랩 제외 (아웃랩 + 워밍업)
        2. PitInTime이 있는 랩(피트인랩) 제외
        3. outlier_threshold (110%) 이상의 랩타임 제외
           기준: 남은 유효 랩 중 최소 랩타임 * threshold

    Args:
        stint_laps: get_stints()의 한 원소의 'laps' DataFrame
        use_fuel_corrected: True면 'LapTimeFuelCorrected', False면 'LapTimeSeconds' 사용
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
    df = stint_laps.copy().sort_values("LapNumber").reset_index(drop=True)
    df["StintLap"] = range(1, len(df) + 1)

    lap_time_col = "LapTimeFuelCorrected" if use_fuel_corrected else "LapTimeSeconds"
    compound = df["Compound"].mode()[0] if "Compound" in df.columns else "UNKNOWN"
    stint_num = int(df["Stint"].iloc[0]) if "Stint" in df.columns else 0

    excluded_laps: set = set()

    # 1. 초반 N랩 제외 (아웃랩 + 타이어 워밍업)
    first_n = df[df["StintLap"] <= skip_first_n_laps]
    excluded_laps.update(first_n["LapNumber"].tolist())

    # 2. 피트인랩 제외 (PitInTime이 존재하는 랩)
    if "PitInTime" in df.columns:
        pit_in_rows = df[df["PitInTime"].notna()]
        excluded_laps.update(pit_in_rows["LapNumber"].tolist())

    df_work = df[~df["LapNumber"].isin(excluded_laps)].copy()

    # 3. 아웃라이어 제외 (스틴트 내 최속 랩타임의 threshold 초과)
    if not df_work.empty and lap_time_col in df_work.columns:
        min_time = df_work[lap_time_col].min()
        cutoff = min_time * outlier_threshold
        outliers = df_work[df_work[lap_time_col] > cutoff]
        excluded_laps.update(outliers["LapNumber"].tolist())

    df_final = df[(~df["LapNumber"].isin(excluded_laps)) & (df[lap_time_col].notna())]

    n_used = len(df_final)
    n_excluded = len(df) - n_used

    if n_used < 2:
        return {
            "slope": float("nan"),
            "intercept": float("nan"),
            "r_squared": float("nan"),
            "n_laps_used": n_used,
            "n_laps_excluded": n_excluded,
            "compound": compound,
            "stint_num": stint_num,
            "excluded_laps": sorted(int(lap) for lap in excluded_laps),
        }

    x = df_final["StintLap"].values.astype(float)
    y = df_final[lap_time_col].values.astype(float)

    slope, intercept, r_value, _p, _se = stats.linregress(x, y)

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_value**2),
        "n_laps_used": n_used,
        "n_laps_excluded": n_excluded,
        "compound": compound,
        "stint_num": stint_num,
        "excluded_laps": sorted(int(lap) for lap in excluded_laps),
    }


def get_degradation_summary(
    laps: pd.DataFrame,
    drivers: list[str],
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
            Driver | Stint | Compound | Slope | Intercept | R2 | LapsUsed | LapsExcluded
            (Slope 단위: 초/lap)

    Example:
        >>> summary = get_degradation_summary(corrected_laps, ['VER', 'NOR', 'PIA'])
        >>> print(summary.groupby('Compound')['Slope'].mean())
    """
    rows = []
    for driver in drivers:
        stints = get_stints(laps, driver)
        for stint in stints:
            result = calculate_stint_degradation(stint["laps"])
            rows.append(
                {
                    "Driver": driver,
                    "Stint": stint["stint_num"],
                    "Compound": stint["compound"],
                    "Slope": round(result["slope"], 4),
                    "Intercept": round(result["intercept"], 3),
                    "R2": round(result["r_squared"], 3),
                    "LapsUsed": result["n_laps_used"],
                    "LapsExcluded": result["n_laps_excluded"],
                }
            )
    return pd.DataFrame(rows)


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

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        driver: 드라이버 약자
        save_path: 저장 경로 (e.g., 'outputs/degradation_VER_spain_2025.png')
    """
    stints = get_stints(laps, driver)

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(14, 7), dpi=150)
        colors = plt.cm.Set1.colors

        for i, stint in enumerate(stints):
            color = colors[i % len(colors)]
            stint_df = (
                stint["laps"].copy().sort_values("LapNumber").reset_index(drop=True)
            )
            stint_df["StintLap"] = range(1, len(stint_df) + 1)

            result = calculate_stint_degradation(stint["laps"])
            excluded_set = set(result["excluded_laps"])

            included = stint_df[~stint_df["LapNumber"].isin(excluded_set)]
            excluded = stint_df[stint_df["LapNumber"].isin(excluded_set)]

            ax.scatter(
                included["StintLap"],
                included["LapTimeFuelCorrected"],
                color=color,
                alpha=0.7,
                s=40,
                label=f"Stint {stint['stint_num']} ({stint['compound']})",
            )

            if not excluded.empty:
                ax.scatter(
                    excluded["StintLap"],
                    excluded["LapTimeFuelCorrected"],
                    color="gray",
                    marker="x",
                    s=60,
                    alpha=0.8,
                    zorder=3,
                )

            if not np.isnan(result["slope"]):
                x_fit = np.linspace(1, stint["length"], 100)
                y_fit = result["slope"] * x_fit + result["intercept"]
                ax.plot(
                    x_fit,
                    y_fit,
                    color=color,
                    linewidth=2,
                    linestyle="--",
                    label=f"  → {result['slope']:.3f} s/lap (R²={result['r_squared']:.2f})",
                )

        ax.set_xlabel("Stint Lap", fontsize=12)
        ax.set_ylabel("Fuel-Corrected Lap Time (s)", fontsize=12)
        ax.set_title(
            f"Tire Degradation — {driver} — 2025 Spanish GP",
            fontsize=14,
            fontweight="bold",
        )
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
        plt.close(fig)


def plot_degradation_comparison(
    laps: pd.DataFrame,
    drivers: list[str],
    compound: str,
    save_path: str,
) -> None:
    """
    같은 컴파운드에서 여러 드라이버의 디그라데이션을 비교한다.

    규칙:
        - 각 드라이버의 해당 컴파운드 스틴트 중 가장 긴 것 사용 (공정한 비교)
        - 어떤 드라이버가 해당 컴파운드를 안 썼으면 자동 제외 + 경고 출력

    레이아웃:
        - x축: 스틴트 내 랩 번호 (1, 2, 3, ...)
        - y축: 연료 보정 랩타임 (초)
        - 드라이버별:
            * raw 데이터: 흐릿한 산점도 (alpha=0.3)
            * 회귀선: 진한 실선/점선
            * 범례에 slope 값 표시: "VER: 0.082 s/lap"

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        drivers: ['PIA', 'NOR', 'VER', 'RUS', 'LEC']
        compound: 'MEDIUM' or 'HARD'
        save_path: 저장 경로
    """
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(14, 7), dpi=150)

        for driver in drivers:
            stints = get_stints(laps, driver)
            compound_stints = [s for s in stints if s["compound"] == compound]

            if not compound_stints:
                print(f"⚠️  {driver}: {compound} 스틴트 없음, 제외")
                continue

            longest = max(compound_stints, key=lambda s: s["length"])
            result = calculate_stint_degradation(longest["laps"])

            if np.isnan(result["slope"]):
                print(f"⚠️  {driver}: 회귀 계산 불가 ({compound}), 제외")
                continue

            stint_df = (
                longest["laps"].copy().sort_values("LapNumber").reset_index(drop=True)
            )
            stint_df["StintLap"] = range(1, len(stint_df) + 1)

            color = TEAM_COLORS.get(driver, "#888888")
            linestyle = DRIVER_LINESTYLES.get(driver, "-")

            ax.scatter(
                stint_df["StintLap"],
                stint_df["LapTimeFuelCorrected"],
                color=color,
                alpha=0.3,
                s=40,
            )

            x_fit = np.linspace(1, longest["length"], 100)
            y_fit = result["slope"] * x_fit + result["intercept"]
            ax.plot(
                x_fit,
                y_fit,
                color=color,
                linewidth=2,
                linestyle=linestyle,
                label=f"{driver}: {result['slope']:.3f} s/lap",
            )

        ax.set_xlabel("Stint Lap", fontsize=12)
        ax.set_ylabel("Fuel-Corrected Lap Time (s)", fontsize=12)
        ax.set_title(
            f"Tire Degradation Comparison — {compound} — 2025 Spanish GP",
            fontsize=14,
            fontweight="bold",
        )
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
        plt.close(fig)


def plot_degradation_with_laptimes(
    laps: pd.DataFrame,
    drivers: list[str],
    save_path: str,
    title: str | None = None,
) -> None:
    """
    상위 5명의 디그라데이션을 전체 레이스 랩 번호 기준으로 한 그래프에 시각화한다.

    plot_degradation_comparison과 달리 x축을 스틴트 내 랩이 아닌 전체 레이스
    랩 번호로 표시해 피트스톱 타이밍과 스틴트 길이를 한눈에 파악할 수 있다.

    레이아웃:
        - x축: 전체 레이스 랩 번호
        - y축: 연료 보정 랩타임 (초)
        - 컴파운드별 색: SOFT=빨강, MEDIUM=노랑, HARD=흰색
        - 각 스틴트에 회귀선 (드라이버 linestyle 적용) + slope 텍스트
        - PIA 실선, NOR 점선, 나머지 실선

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        drivers: 분석할 드라이버 약자 리스트 (최대 5명 권장)
        save_path: 저장 경로 (e.g., 'outputs/degradation_all_bahrain_2025.png')
        title: 그래프 제목. None이면 기본값 사용.

    Example:
        >>> plot_degradation_with_laptimes(
        ...     corrected, ['PIA', 'NOR', 'VER', 'RUS', 'LEC'], 'out.png'
        ... )
    """
    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(16, 8), dpi=150)

        for driver in drivers:
            stints = get_stints(laps, driver)
            linestyle = DRIVER_LINESTYLES.get(driver, "-")

            for stint in stints:
                compound = stint["compound"]
                color = COMPOUND_COLORS.get(compound, "#888888")
                stint_df = (
                    stint["laps"].copy().sort_values("LapNumber").reset_index(drop=True)
                )
                stint_df["StintLap"] = range(1, len(stint_df) + 1)

                result = calculate_stint_degradation(stint["laps"])
                excluded_set = set(result["excluded_laps"])

                # 포함된 랩만 산점도 (컴파운드 색, 낮은 투명도)
                included = stint_df[~stint_df["LapNumber"].isin(excluded_set)]
                if not included.empty and "LapTimeFuelCorrected" in included.columns:
                    ax.scatter(
                        included["LapNumber"],
                        included["LapTimeFuelCorrected"],
                        color=color,
                        alpha=0.30,
                        s=25,
                        zorder=2,
                    )

                # 회귀선: StintLap = LapNumber - start_lap + 1 로 변환
                if not np.isnan(result["slope"]):
                    start_lap = stint["start_lap"]
                    end_lap = stint["end_lap"]
                    x_abs = np.linspace(start_lap, end_lap, 100)
                    x_stint = x_abs - start_lap + 1
                    y_fit = result["slope"] * x_stint + result["intercept"]

                    ax.plot(
                        x_abs,
                        y_fit,
                        color=color,
                        linewidth=2,
                        linestyle=linestyle,
                        alpha=0.9,
                        zorder=3,
                    )

                    # slope 텍스트: 스틴트 중간 지점 바로 위에 표시
                    mid_x = (start_lap + end_lap) / 2
                    mid_stint_lap = mid_x - start_lap + 1
                    mid_y = result["slope"] * mid_stint_lap + result["intercept"]
                    ax.text(
                        mid_x,
                        mid_y + 0.25,
                        f"{driver}: {result['slope']:+.3f}s/lap",
                        color=color,
                        fontsize=7,
                        fontweight="bold",
                        ha="center",
                        va="bottom",
                        zorder=4,
                    )

        # 범례: 컴파운드 색상 패치 + 드라이버 선 스타일
        compound_handles = [
            mpatches.Patch(color=COMPOUND_COLORS["SOFT"], label="Soft"),
            mpatches.Patch(color=COMPOUND_COLORS["MEDIUM"], label="Medium"),
            mpatches.Patch(color=COMPOUND_COLORS["HARD"], label="Hard"),
        ]
        driver_handles = [
            mlines.Line2D(
                [],
                [],
                color="#AAAAAA",
                linestyle=DRIVER_LINESTYLES.get(d, "-"),
                linewidth=1.5,
                label=d,
            )
            for d in drivers
        ]

        legend_compound = ax.legend(
            handles=compound_handles,
            loc="upper left",
            fontsize=9,
            title="Compound",
            title_fontsize=9,
        )
        ax.add_artist(legend_compound)
        ax.legend(
            handles=driver_handles,
            loc="upper right",
            fontsize=9,
            title="Driver",
            title_fontsize=9,
        )

        ax.set_xlabel("Lap Number", fontsize=12)
        ax.set_ylabel("Fuel-Corrected Lap Time (s)", fontsize=12)
        ax.set_title(
            title or "Tire Degradation — All Stints",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
        plt.close(fig)


def plot_stint_degradation_overview(
    laps: pd.DataFrame,
    drivers: list[str],
    save_path: str,
    title: str | None = None,
) -> None:
    """
    레이스 전체 랩 번호를 x축으로 드라이버별 스틴트 회귀선을 한 그래프에 시각화한다.

    드라이버는 팀 컬러로, 컴파운드는 마커 모양으로 구분한다. raw 데이터는 매우
    흐리게(alpha=0.15) 표시하고 회귀선이 주요 시각 요소다. 범례에 드라이버별
    평균 디그라데이션 속도를 표시해 slope 텍스트 없이 비교 가능하다.

    레이아웃:
        - x축: 전체 레이스 랩 번호
        - y축: 연료 보정 랩타임 (회귀선 범위 자동 설정)
        - 드라이버 구분: 팀 컬러 + NOR 점선/나머지 실선
        - 컴파운드 구분: 마커 모양 (SOFT=원, MEDIUM=세모, HARD=네모)
        - raw 데이터: alpha=0.15 스캐터
        - 회귀선: alpha=0.95, linewidth=2.5
        - 범례: 드라이버+평균 slope (우측), 컴파운드 마커 (좌측)

    Args:
        laps: apply_fuel_correction()을 거친 DataFrame
        drivers: 분석할 드라이버 약자 리스트
        save_path: 저장 경로
        title: 그래프 제목. None이면 기본값 사용.

    Example:
        >>> plot_stint_degradation_overview(
        ...     corrected, ['PIA', 'NOR', 'VER', 'RUS', 'LEC'], 'out.png'
        ... )
    """
    # 사전 계산: 드라이버별 평균 slope + y축 범위용 회귀선 끝점 수집
    avg_slopes: dict[str, float] = {}
    all_regression_y: list[float] = []

    for driver in drivers:
        stints = get_stints(laps, driver)
        slopes: list[float] = []
        for stint in stints:
            result = calculate_stint_degradation(stint["laps"])
            if not np.isnan(result["slope"]):
                slopes.append(result["slope"])
                n_laps = stint["end_lap"] - stint["start_lap"] + 1
                all_regression_y.append(result["intercept"] + result["slope"] * 1)
                all_regression_y.append(result["intercept"] + result["slope"] * n_laps)
        avg_slopes[driver] = float(np.mean(slopes)) if slopes else float("nan")

    with plt.style.context("dark_background"):
        fig, ax = plt.subplots(figsize=(16, 8), dpi=150)

        for driver in drivers:
            stints = get_stints(laps, driver)
            linestyle = DRIVER_LINESTYLES.get(driver, "-")
            color = TEAM_COLORS.get(driver, "#888888")

            for stint in stints:
                compound = stint["compound"]
                marker = COMPOUND_MARKERS.get(compound, "o")
                stint_df = stint["laps"].copy().sort_values("LapNumber")
                valid = stint_df[stint_df["LapTimeFuelCorrected"].notna()]

                if valid.empty:
                    continue

                # raw 데이터: 컴파운드 마커, 매우 흐리게
                ax.scatter(
                    valid["LapNumber"],
                    valid["LapTimeFuelCorrected"],
                    color=color,
                    alpha=0.15,
                    s=30,
                    marker=marker,
                    zorder=2,
                )

                # 회귀선 (팀 컬러 + 드라이버 linestyle)
                result = calculate_stint_degradation(stint["laps"])
                if not np.isnan(result["slope"]):
                    start_lap = stint["start_lap"]
                    end_lap = stint["end_lap"]
                    x_abs = np.linspace(start_lap, end_lap, 100)
                    x_stint = x_abs - start_lap + 1
                    y_fit = result["slope"] * x_stint + result["intercept"]

                    ax.plot(
                        x_abs,
                        y_fit,
                        color=color,
                        linewidth=2.5,
                        linestyle=linestyle,
                        alpha=0.95,
                        zorder=3,
                    )

        # y축: 회귀선 끝점 범위 기준 자동 설정
        if all_regression_y:
            span = max(all_regression_y) - min(all_regression_y)
            margin = max(span * 0.15, 0.3)
            ax.set_ylim(min(all_regression_y) - margin, max(all_regression_y) + margin)

        # 범례: 드라이버 (팀 컬러 + avg slope) + 컴파운드 마커
        driver_handles = [
            mlines.Line2D(
                [],
                [],
                color=TEAM_COLORS.get(d, "#888888"),
                linestyle=DRIVER_LINESTYLES.get(d, "-"),
                linewidth=2,
                label=(
                    f"{d}: {avg_slopes[d]:+.3f} s/lap"
                    if not np.isnan(avg_slopes.get(d, float("nan")))
                    else d
                ),
            )
            for d in drivers
        ]
        compound_handles = [
            mlines.Line2D(
                [],
                [],
                color="#AAAAAA",
                marker=COMPOUND_MARKERS["SOFT"],
                linestyle="none",
                markersize=7,
                label="Soft",
            ),
            mlines.Line2D(
                [],
                [],
                color="#AAAAAA",
                marker=COMPOUND_MARKERS["MEDIUM"],
                linestyle="none",
                markersize=7,
                label="Medium",
            ),
            mlines.Line2D(
                [],
                [],
                color="#AAAAAA",
                marker=COMPOUND_MARKERS["HARD"],
                linestyle="none",
                markersize=7,
                label="Hard",
            ),
        ]

        legend_compound = ax.legend(
            handles=compound_handles,
            loc="upper left",
            fontsize=9,
            title="Compound",
            title_fontsize=9,
        )
        ax.add_artist(legend_compound)
        ax.legend(
            handles=driver_handles,
            loc="upper right",
            fontsize=9,
            title="Driver (avg degradation)",
            title_fontsize=9,
        )

        ax.set_xlabel("Lap Number", fontsize=12)
        ax.set_ylabel("Pace (s)", fontsize=12)
        ax.set_title(
            title or "Stint Degradation Overview",
            fontsize=14,
            fontweight="bold",
        )
        ax.grid(True, alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(save_path, bbox_inches="tight")
        print(f"Saved: {save_path}")
        plt.close(fig)
