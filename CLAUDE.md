# CLAUDE.md

> 이 파일은 Claude Code가 프로젝트를 일관되게 이해하고 작업할 수 있도록 작성된 컨텍스트 파일입니다.
> Claude Code는 매 세션 시작 시 이 파일을 자동으로 읽습니다.

---

## 📌 프로젝트 개요

**프로젝트명**: AI Race Analyst

**한 줄 설명**: LLM과 정량 시뮬레이션을 결합한 F1 포스트 레이스 분석 시스템

**목표**: F1 경기 데이터를 활용해 (1) 드라이버·차량 분석, (2) What-if 전략 시뮬레이션을 수행하고, (3) LLM이 그 결과를 자연어 인사이트로 변환하는 시스템 구축

**설계 원칙**: "계산은 Python, 해석은 LLM"
- Python: 데이터 수집, 회귀 분석, 몬테카를로 시뮬레이션
- LLM: 결과 해석, 인사이트 추출, 자연어 리포트 생성

**예상 기간**: 4주 (Phase 1 ~ Phase 4)

---

## 🛠️ 기술 스택

### 환경
- **OS**: macOS
- **Python**: 3.13+
- **가상환경**: `venv` (프로젝트 루트의 `venv/` 폴더)

### 핵심 라이브러리
- **FastF1** (3.8+): F1 데이터 수집
- **Pandas / NumPy**: 데이터 처리
- **SciPy**: 회귀 분석, 통계
- **Matplotlib / Plotly**: 시각화
- **Anthropic SDK** (예정): LLM 통합

### 개발 도구
- **Black**: 코드 포매터 (라인 길이 88자)
- **Ruff**: 린터
- **pytest**: 테스트 프레임워크

---

## 📂 프로젝트 구조

```
ai-race-analyst/
├── README.md              # 프로젝트 소개
├── CLAUDE.md              # 이 파일 (Claude Code용 컨텍스트)
├── .gitignore             # Git 제외 목록
├── requirements.txt       # 의존성 목록
├── pyproject.toml         # Black/Ruff 설정
├── LICENSE                # 라이선스
│
├── src/                   # 소스 코드
│   ├── __init__.py
│   ├── data/             # 데이터 수집/전처리 (Phase 1)
│   │   ├── __init__.py
│   │   ├── session_loader.py   # FastF1 세션 로딩
│   │   └── lap_data.py         # 랩 데이터 처리 (작업 중)
│   │
│   ├── analysis/         # 정량 분석 (Phase 2)
│   │   └── __init__.py
│   │
│   ├── simulation/       # 시뮬레이션 엔진 (Phase 3)
│   │   └── __init__.py
│   │
│   └── llm/              # LLM 통합 (Phase 4)
│       └── __init__.py
│
├── notebooks/            # Jupyter 분석 노트북 (탐색용)
├── tests/                # pytest 테스트 코드
├── docs/                 # 문서
│
├── step1_fetch_data.py   # 실행 스크립트 (Step 1)
├── step2_explore_data.py # 실행 스크립트 (Step 2)
│
├── venv/                 # 가상환경 (Git 제외)
└── f1_cache/             # FastF1 캐시 (Git 제외)
```

### 모듈 역할

- **`src/data/`**: FastF1 API와의 모든 상호작용을 담당. 원시 데이터를 받아 분석 가능한 형태로 가공.
- **`src/analysis/`**: 정량 분석 함수들. 페이스, 디그라데이션, 섹터 분석 등.
- **`src/simulation/`**: What-if 시뮬레이션 엔진. 랩타임 모델 + 몬테카를로.
- **`src/llm/`**: LLM 프롬프트 설계 및 자연어 리포트 생성.

---

## 📝 코딩 컨벤션

### 언어 정책
- **변수, 함수, 클래스명**: 영어 (snake_case)
- **주석, docstring**: 한국어 (학습 목적)
- **에러 메시지, 로그**: 한국어 OK
- **PR/커밋 메시지**: 영어 (Conventional Commits)

### Python 스타일

```python
# 좋은 예시
def get_drivers_laps(
    session: fastf1.core.Session,
    drivers: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    여러 드라이버의 랩 데이터를 한 번에 받아온다.
    
    Args:
        session: 로드된 FastF1 세션 객체
        drivers: 드라이버 약자 리스트 (None이면 전체)
    
    Returns:
        랩 데이터가 담긴 DataFrame
    
    Example:
        >>> laps = get_drivers_laps(session, ['NOR', 'VER'])
    """
    if drivers is None:
        return session.laps.copy()
    
    return session.laps.pick_drivers(drivers).copy()
```

### 필수 규칙
1. **타입 힌트**: 모든 함수 인자와 반환값에 타입 명시
2. **Docstring**: 모든 public 함수에 작성 (Args, Returns, Example 포함)
3. **함수 이름**: 동사로 시작 (`get_`, `clean_`, `filter_`, `calculate_`)
4. **상수**: UPPER_SNAKE_CASE
5. **들여쓰기**: 스페이스 4칸 (Black 기본값)
6. **라인 길이**: 최대 88자 (Black 기본값)

### Import 순서
```python
# 1. 표준 라이브러리
from pathlib import Path
from typing import List, Optional

# 2. 서드파티
import fastf1
import pandas as pd
import numpy as np

# 3. 프로젝트 내부
from src.data.session_loader import load_session
```

---

## 🔧 개발 도구 사용법

### Black (코드 포매터)

코드 자동 정리. 일관된 스타일 유지.

```bash
# 전체 프로젝트 포매팅
black src/ tests/ *.py

# 특정 파일만
black src/data/lap_data.py

# 변경 없이 확인만 (CI용)
black --check src/
```

### Ruff (린터)

코드 스타일/품질 체크.

```bash
# 전체 프로젝트 검사
ruff check src/ tests/ *.py

# 자동 수정 가능한 것 수정
ruff check --fix src/

# 특정 파일
ruff check src/data/lap_data.py
```

### pytest (테스트)

```bash
# 모든 테스트 실행
pytest

# 특정 파일
pytest tests/test_lap_data.py

# 상세 출력
pytest -v

# 커버리지 포함
pytest --cov=src
```

### 작업 후 표준 체크
새 코드 작성 후 항상 이 순서로:
```bash
black src/                  # 1. 포매팅
ruff check --fix src/       # 2. 린트 수정
pytest                      # 3. 테스트 실행
```

---

## 🌿 Git 워크플로우

### 브랜치 전략 (GitHub Flow)

```
main                           ← 항상 안정적인 코드
 ├─ feature/multi-driver-data  ← 새 기능
 ├─ fix/cache-error            ← 버그 수정
 ├─ refactor/data-loader       ← 리팩토링
 ├─ docs/api-reference         ← 문서 작업
 └─ test/session-loader        ← 테스트 추가
```

### 작업 단위
**1 모듈 = 1 PR** (작은 단위 유지)

너무 큰 PR은 만들지 않음. 한 PR에 너무 많은 파일이 변경되면 분리.

### 브랜치 네이밍
- `feature/<기능명>`: 새 기능 추가
- `fix/<문제>`: 버그 수정
- `refactor/<대상>`: 리팩토링 (기능 변경 없음)
- `docs/<주제>`: 문서 작업
- `test/<대상>`: 테스트 추가

### 커밋 메시지 컨벤션 (Conventional Commits)

```
<타입>: <한 줄 요약 (영어)>

[선택: 본문 - 상세 설명]
```

#### 타입 종류
- `feat`: 새 기능 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `style`: 코드 스타일 변경 (기능 X)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정, 잡일

#### 예시
```bash
# 좋은 예시
git commit -m "feat: add lap data processing module"
git commit -m "fix: handle empty stint data in pace analysis"
git commit -m "refactor: split session_loader into smaller functions"
git commit -m "docs: update README with installation guide"

# 본문 포함 예시
git commit -m "feat: modularize FastF1 session loader

- Move session loading logic to src/data/session_loader.py
- Add reusable functions: setup_cache, load_session
- Refactor step1_fetch_data.py to use the new module"
```

### 표준 작업 흐름

```bash
# 1. main 최신화
git checkout main
git pull origin main

# 2. 새 브랜치 생성
git checkout -b feature/<기능명>

# 3. 작업 진행 (코드 작성, 테스트)
# ...

# 4. 코드 정리
black src/
ruff check --fix src/
pytest

# 5. 커밋
git add .
git commit -m "feat: <설명>"

# 6. 푸시
git push -u origin feature/<기능명>

# 7. GitHub에서 PR 생성
# 제목: feat: <설명>
# 본문: 변경사항, 테스트 결과, 다음 작업

# 8. 머지 후 정리
git checkout main
git pull origin main
git branch -d feature/<기능명>
```

### PR 작성 가이드

PR 본문에 항상 포함:
1. **변경 사항** (체크리스트)
2. **테스트 결과** (어떻게 검증했는지)
3. **변경된 파일** (주요 파일 목록)
4. **다음 작업** (이어지는 작업이 있다면)

---

## 🧪 테스트 정책

**원칙**: 핵심 함수에만 단위 테스트 작성

### 테스트 대상
- ✅ 시뮬레이션 로직 (정확성이 중요)
- ✅ 데이터 변환 함수 (입출력 형식이 명확)
- ✅ 통계 계산 함수
- ❌ 단순 wrapper 함수
- ❌ 단순 출력 함수

### 테스트 파일 구조
```
tests/
├── __init__.py
├── test_session_loader.py
├── test_lap_data.py
├── test_pace_analysis.py
└── test_simulation.py
```

### pytest 스타일
```python
# tests/test_lap_data.py
import pytest
import pandas as pd
from src.data.lap_data import clean_lap_data

def test_clean_lap_data_removes_nan_laptimes():
    """LapTime이 NaN인 행이 제거되는지 확인"""
    df = pd.DataFrame({
        'LapTime': [pd.Timedelta('1:30'), pd.NaT, pd.Timedelta('1:31')],
        'Driver': ['NOR', 'VER', 'LEC'],
    })
    result = clean_lap_data(df)
    assert len(result) == 2
    assert 'VER' not in result['Driver'].values
```

---

## ⚠️ 작업 시 주의사항

### 가상환경
**모든 명령은 가상환경 활성화 상태에서 실행**
```bash
source venv/bin/activate
# 프롬프트에 (venv) 표시 확인
```

### 캐시 관리
- `f1_cache/`는 `.gitignore`에 포함됨 (커밋되지 않음)
- 캐시 크기가 수 GB까지 커질 수 있으니 주기적으로 확인
- 캐시 위치: 프로젝트 루트의 `f1_cache/`

### 비밀 정보 (절대 커밋 X)
- API 키, 토큰은 `.env` 파일에 저장
- `.env`는 `.gitignore`에 포함됨
- API 키 필요한 모듈은 `python-dotenv`로 환경 변수 로드
- 코드에 API 키 하드코딩 절대 금지

### FastF1 사용 시
- `session.load()` 후에야 데이터 접근 가능
- `pick_drivers()`, `pick_fastest()` 등은 새 DataFrame 반환 (원본 유지)
- 랩타임은 `Timedelta` 객체이므로 분석 시 `.total_seconds()` 변환 필요

---

## 📊 현재 진행 상황

### ✅ 완료
- [x] 프로젝트 초기 설정 (Git, venv, 의존성)
- [x] README, .gitignore, requirements.txt 작성
- [x] `src/data/session_loader.py` 모듈 (PR #1 머지)

### 🚧 진행 중
- [ ] `src/data/lap_data.py` 모듈 (브랜치: `feature/multi-driver-data`)
  - 여러 드라이버 데이터 수집
  - 랩 데이터 전처리
  - 필터링 헬퍼 함수들
  - 페이스 요약 통계

### 📋 다음 작업 (Phase 1 마무리)
- [ ] `feature/data-models`: 데이터 클래스 정의 (Lap, Stint, Driver)

### 🎯 Phase 2 (분석 모듈)
- [ ] `feature/pace-analysis`: 페이스 비교 분석
- [ ] `feature/tire-degradation`: 타이어 디그라데이션 회귀
- [ ] `feature/stint-analysis`: 스틴트별 분석

### 🎯 Phase 3 (시뮬레이션)
- [ ] `feature/laptime-model`: 랩타임 모델
- [ ] `feature/monte-carlo`: 몬테카를로 시뮬레이션
- [ ] `feature/whatif-scenarios`: What-if 시나리오

### 🎯 Phase 4 (LLM 통합)
- [ ] `feature/llm-prompts`: 프롬프트 설계
- [ ] `feature/llm-integration`: Claude API 연동
- [ ] `feature/report-generation`: 리포트 생성

---

## 💡 Claude Code에게

### 작업 시 따라야 할 원칙
1. **이 문서의 컨벤션을 항상 준수**
2. 새 모듈 작성 시 **타입 힌트 + docstring 필수**
3. 코드 작성 후 **black + ruff** 실행
4. 핵심 함수는 **pytest 테스트** 함께 작성
5. 작업 완료 시 **의미 있는 커밋 메시지** 작성
6. PR 본문은 **체크리스트 형식**으로 작성

### 자주 사용하는 패턴

**모듈 생성 시:**
```python
"""
<모듈명>.py
==========
<모듈 설명 한 줄>

<모듈 상세 설명>
"""

from typing import List, Optional
# ... imports

# 상수 정의
DEFAULT_VALUE = ...

# 함수 정의 (타입 힌트 + docstring)
def function_name(arg: Type) -> ReturnType:
    """함수 설명."""
    ...
```

**실행 스크립트 생성 시:**
```python
"""
=============================================================
AI Race Analyst - Step N: <작업 내용>
=============================================================

목표: <한 줄>
실행: python3 step_N_xxx.py
=============================================================
"""

from src.module import function

def main():
    # 실행 로직
    pass

if __name__ == '__main__':
    main()
```

### 우선순위
- **명확성 > 간결성**: 짧은 코드보다 읽기 쉬운 코드
- **검증 가능성 > 추측**: 결과는 항상 정량적으로 검증 가능해야 함
- **모듈성 > 중복**: 같은 로직 반복 시 함수로 추출

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*
