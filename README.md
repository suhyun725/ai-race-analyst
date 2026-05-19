# 🏎️ AI Race Analyst

> LLM과 정량 시뮬레이션을 결합한 F1 포스트 레이스 분석 시스템

경기가 끝난 후, 데이터로 **"왜 그랬을까"** 와 **"만약 다른 전략이었다면?"** 을 자동으로 답하는 시스템입니다.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastF1](https://img.shields.io/badge/FastF1-3.8+-red.svg)](https://github.com/theOehrly/Fast-F1)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-In%20Development-yellow.svg)]()

---

## 📌 프로젝트 개요

F1 경기 데이터를 활용해 **드라이버·차량 분석**과 **What-if 전략 시뮬레이션**을 수행하고, 그 결과를 **LLM이 자연어 인사이트로 변환**하는 시스템입니다.

### 핵심 가치

| 가치 | 설명 |
|------|------|
| 🔬 **정량 + 정성** | 수학적 시뮬레이션과 LLM 자연어 해석의 결합 |
| ✅ **검증 가능성** | 실제 경기 데이터와 비교한 모델 정확도 측정 |
| 🚀 **확장 가능성** | 타이어 전략 → 전체 레이스 → 시즌 단위로 확장 |

---

## 🏗️ 시스템 아키텍처

```
[FastF1 API]
     ↓
[데이터 수집 & 전처리]
     ↓
┌────┴────┐
↓         ↓
[정량 분석]  [시뮬레이션]
↓         ↓
└────┬────┘
     ↓
[LLM 자연어 해석]
     ↓
[종합 리포트]
```

**설계 원칙: "계산은 Python, 해석은 LLM"**

- **Python**: 데이터 수집, 회귀 분석, 몬테카를로 시뮬레이션
- **LLM**: 결과 해석, 인사이트 추출, 자연어 리포트 생성

---

## 🛠️ 기술 스택

### 데이터 수집
- **FastF1** — F1 공식 데이터 + Jolpica API 통합 (Pandas 친화적)

### 분석 & 시뮬레이션
- **Pandas / NumPy** — 데이터 처리
- **SciPy** — 회귀분석, 통계
- **Monte Carlo** — TUM Heilmeier et al. (2020) 방법론 기반

### LLM 통합
- **Claude API** — 자연어 인사이트 생성

### 시각화
- **Matplotlib / Plotly** — 데이터 시각화

---

## 🔬 핵심 기술: What-if 시뮬레이션

학계 검증 방법론 ([TUM Heilmeier et al., 2020](https://www.mdpi.com/2076-3417/10/12/4229)) 기반:

- **랩타임 모델**: `기본 페이스 + 타이어 디그라데이션 + 연료 효과 + 피트 손실 + 트래픽`
- **확률적 이벤트**: 사고·세이프티카·변동성을 몬테카를로로 수천 회 시뮬레이션
- **Ghost Car 기법**: 가상 차량으로 세이프티카 페이스 재현
- **검증**: 2022–2024 시즌 학습, 2025 시즌 테스트로 정량 평가

### 시나리오 예시

1. **피트스톱 전략**: 1스톱 vs 2스톱, 어느 쪽이 더 빨랐을까?
2. **세이프티카 대응**: 갑작스러운 SC 발생 시 피트인 vs 유지, 어느 쪽이 유리했나?

---

## 📦 설치 및 실행

### 사전 요구사항
- Python 3.11+
- macOS / Linux / Windows

### 설치

```bash
# 1. 저장소 클론
git clone https://github.com/suhyun725/ai-race-analyst.git
cd ai-race-analyst

# 2. 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# 3. 의존성 설치
pip install -r requirements.txt
```

### 실행

```bash
# Step 1: 데이터 수집 테스트
python step1_fetch_data.py
```

---

## 🗺️ 로드맵

### Phase 1: 데이터 파이프라인 (Week 1)
- [x] FastF1 환경 설정 및 데이터 수집
- [ ] 캐싱 시스템 구축
- [ ] 데이터 전처리 모듈

### Phase 2: 분석 모듈 (Week 2)
- [ ] 드라이버 페이스 분석
- [ ] 타이어 디그라데이션 회귀
- [ ] 섹터별 강약점 분석

### Phase 3: 시뮬레이션 엔진 (Week 3)
- [ ] 랩타임 모델 구현
- [ ] 몬테카를로 시뮬레이션
- [ ] What-if 시나리오 모듈

### Phase 4: LLM 통합 (Week 4)
- [ ] 프롬프트 설계
- [ ] 자연어 리포트 생성
- [ ] 검증 및 마무리

---

## 📊 검증 방법

| 지표 | 목표 |
|------|------|
| 랩타임 예측 오차 (MAE) | < 0.5초 / 랩 |
| 전략 분류 정확도 | > 70% |
| 베이스라인 대비 개선 | 오차 30%+ 감소 |

---

## 📂 프로젝트 구조

```
ai-race-analyst/
├── README.md
├── .gitignore
├── requirements.txt
├── LICENSE
│
├── src/                    # 소스 코드
│   ├── data/              # 데이터 수집/전처리
│   ├── analysis/          # 정량 분석
│   ├── simulation/        # 시뮬레이션 엔진
│   └── llm/              # LLM 통합
│
├── notebooks/             # Jupyter 분석 노트북
├── tests/                 # 테스트 코드
└── docs/                  # 문서
```

---

## 🤝 참고 자료

- [FastF1 공식 문서](https://docs.fastf1.dev/)
- Heilmeier, A., et al. (2020). [*Application of Monte Carlo Methods to Consider Probabilistic Effects in a Race Simulation for Circuit Motorsport*](https://www.mdpi.com/2076-3417/10/12/4229). Applied Sciences.
- [TUMFTM/race-simulation](https://github.com/TUMFTM/race-simulation) (오픈소스 레퍼런스)

---

## 📝 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

## 👤 만든 사람

**Suhyun Ko**
- GitHub: [suhyun725](https://github.com/suhyun725)
- 프로젝트 기간: 2026.05 ~ 2026.06

---

*🏁 "Data tells you what happened. AI tells you what it means."*
