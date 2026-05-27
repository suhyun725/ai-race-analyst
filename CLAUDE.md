# CLAUDE.md

> 이 파일은 Claude Code가 프로젝트를 일관되게 이해하고 작업할 수 있도록 작성된 컨텍스트 파일입니다.
> Claude Code는 매 세션 시작 시 이 파일을 자동으로 읽습니다.

---

## 📌 프로젝트 개요

**프로젝트명**: AI Race Analyst

**한 줄 설명**: LLM과 정량 시뮬레이션을 결합한 F1 포스트 레이스 분석 시스템

**설계 원칙**: "계산은 Python, 해석은 LLM"

---

## 🛠️ 기술 스택

- **Python**: 3.13+ / venv
- **데이터**: FastF1 3.8+, Pandas, NumPy, SciPy
- **시각화**: Matplotlib
- **개발 도구**: Black, Ruff, pytest

---

## 📂 프로젝트 구조

```
ai-race-analyst/
├── README.md / CLAUDE.md / .gitignore
├── requirements.txt / pyproject.toml
│
├── src/
│   ├── data/
│   │   ├── session_loader.py      ✅
│   │   └── lap_data.py            ✅
│   │
│   └── analysis/
│       ├── pace.py                ✅
│       ├── position.py            ✅
│       │   └── degradation.py         ✅
    │   └── sector.py              ✅
│
├── step1_fetch_data.py            # 데이터 수집
├── step2_explore_data.py          # 데이터 탐색
├── step3_pace_analysis.py         # 페이스 분석 (Brazil 2024)
├── step4_degradation_analysis.py  # 디그라데이션 분석 (Bahrain 2025)
│
├── outputs/                       # 생성 그래프
├── venv/ / f1_cache/              # .gitignore
```

---

## 📊 모듈별 함수

### `src/data/`
- **session_loader.py**: `setup_cache`, `load_session`
- **lap_data.py**: `get_drivers_laps`, `clean_lap_data`, `filter_by_compound`, `filter_quick_laps`, `filter_lap_range`, `get_pace_summary`

### `src/analysis/`
- **pace.py**: `compare_drivers_pace`, `calculate_pace_delta`, `plot_pace_evolution`, `plot_pace_delta`, `plot_pace_evolution_styled`, `plot_race_pace_overview`
- **position.py**: `get_position_history`, `get_pit_stops`, `get_track_events`, `plot_race_trace`
- **degradation.py**: `apply_fuel_correction`, `get_stints`, `calculate_stint_degradation`, `get_degradation_summary`, `plot_driver_degradation`, `plot_degradation_comparison`, `plot_stint_degradation_overview`

---

## 🎨 시각화 표준

### 팀 컬러
```python
TEAM_COLORS = {
    'VER': '#3671C6', 'NOR': '#FF8000', 'PIA': '#FF8000',
    'LEC': '#E80020', 'HAM': '#E80020', 'RUS': '#27F4D2',
    'ANT': '#27F4D2', 'GAS': '#FF87BC', 'STR': '#229971',
    'ALO': '#229971', 'TSU': '#6692FF', 'LAW': '#6692FF',
    'BOT': '#52E252', 'HUL': '#B6BABD', 'ALB': '#64C4FF',
}
```

### 컴파운드 컬러
```python
COMPOUND_COLORS = {'SOFT': '#FF3333', 'MEDIUM': '#FFD700', 'HARD': '#FFFFFF'}
```

### 그래프 스타일
- 다크 모드: `plt.style.use('dark_background')`
- Race Trace: figsize=(20,10), dpi=200
- 일반 그래프: figsize=(14,7), dpi=150
- 레이블: 영어 (한글 폰트 이슈 회피)

### 맥라렌 두 명 구분
같은 팀 컬러(#FF8000)인 NOR/PIA는 라인스타일로 구분:
- PIA: 실선
- NOR: 점선 (`--`)

---

## 📝 코딩 컨벤션

### 언어 정책
- 변수/함수/클래스명: 영어 snake_case
- 주석/docstring: 한국어
- PR/커밋 메시지: 영어 Conventional Commits

### 필수 규칙
- 타입 힌트, docstring (Args/Returns/Example)
- 함수명 동사 시작: `get_`, `clean_`, `filter_`, `calculate_`, `plot_`
- 함수 패턴: DataFrame → DataFrame (재사용성)
- 작업 후: `black src/` + `ruff check --fix src/`

### Pace vs Lap Time 용어
- **Lap Time**: raw 랩타임 (피트랩, 트래픽 등 외부 요인 포함)
- **Pace**: 연료 효과 등 보정한 페이스. 시각화 y축 라벨은 "Pace (s)" 사용

---

## 🌿 Git 워크플로우

GitHub Flow. 1 모듈 = 1 PR.

```bash
git checkout main && git pull origin main
git checkout -b feature/<기능명>
# 작업
black src/ && ruff check --fix src/
git add . && git commit -m "feat: <설명>"
git push -u origin feature/<기능명>
# GitHub에서 PR 생성 → 머지
```

### 브랜치 네이밍
- `feature/<기능명>` / `fix/<문제>` / `docs/<주제>` / `refactor/<대상>`

### 커밋 타입
- `feat:` / `fix:` / `docs:` / `style:` / `refactor:` / `test:` / `chore:`

---

## 📊 현재 진행 상황

### ✅ Phase 1: 데이터 파이프라인 (완료)
- session_loader, lap_data
- FastF1 캐시 시스템

### ✅ Phase 2: 분석 모듈 (2/3 완료)
- **페이스 분석** (PR #3): Brazil 2024
- **타이어 디그라데이션** (현재 PR): Bahrain 2025, 연료 보정 0.03s/lap
- **섹터 분석** (PR #6): Bahrain 2025, 전체 드라이버 섹터 베스트/얼티밋랩/스피드트랩 ✅

### 🎯 Phase 3: 시뮬레이션 엔진
- 랩타임 모델 (TUM Heilmeier 2020 기반)
- 몬테카를로 시뮬레이션
- What-if 시나리오

### 🎯 Phase 4: LLM 통합
- 프롬프트 설계
- Claude API 연동
- 자연어 리포트

### 🎯 Phase 5: 검증 + 문서화

---

## ⚠️ 작업 시 주의사항

### 가상환경
모든 명령은 `source venv/bin/activate` 후 실행

### 캐시
- `f1_cache/`는 `.gitignore` 포함
- 크기가 수 GB까지 커질 수 있음

### FastF1 사용
- `session.load()` 후에야 데이터 접근 가능
- 랩타임은 `Timedelta` → `.total_seconds()` 변환

### 디그라데이션 분석의 함정
랩타임의 시간적 변화만으로 디그라데이션을 측정하면 안 됨.
연료 감소 효과(랩당 -0.03s)가 디그라데이션을 상쇄하므로,
반드시 `apply_fuel_correction()` 적용 후 측정.

---

## 💡 Claude Code에게

### 작업 원칙
1. 이 문서의 컨벤션을 항상 준수
2. 새 모듈은 타입 힌트 + docstring 필수
3. 작업 후 black + ruff 실행
4. 의미 있는 커밋 메시지 작성

### 우선순위
- 명확성 > 간결성
- 검증 가능성 > 추측
- 모듈성 > 중복

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다. 최종 업데이트: Phase 2 디그라데이션 완료 시점.*
