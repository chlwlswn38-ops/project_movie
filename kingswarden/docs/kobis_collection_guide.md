# KOBIS 일별 박스오피스 데이터 수집 가이드

이 가이드는 KOBIS(영화관입장권통합전산망) OpenAPI를 사용하여 특정 영화의 개봉 후 35일간의 데이터를 수집하는 절차를 설명합니다.

## 1. 수집 개요
- **목표**: 영화별 개봉일(D+0)부터 D+35일까지의 관객수, 스크린수, 매출액 점유율 수집.
- **주요 지표**: 1주차 누적 관객, 3~5주차 성장률, Peak 시점 산출.
- **기술 스택**: Python, Pandas, Requests.

## 2. 데이터 구조 및 파일명
- **Raw Data**: `data/raw/kobis_daily/{movieCd}_{date}.json` (API 결과 원본)
- **Processed Data**: `data/kobis_boxoffice_daily.csv` (정제된 테이블)
- **Master Data**: `data/movie_master.csv` (영화별 `movieCd` 및 `openDt` 매핑)

## 3. 단계별 체크리스트

### STEP 1: KOBIS API 키 발급 및 환경 설정
- [ ] [KOBIS 오픈 API 페이지](http://www.kobis.or.kr/kobisopenapi/home/main/main.do)에서 키 발급.
- [ ] `.env` 파일 또는 스크립트에 키 저장.

### STEP 2: movie_master 생성
- [ ] 수집 대상 영화 리스트 작성.
- [ ] `searchMovieList.json` API를 호출하여 영화별 `movieCd`와 `openDt`(개봉일) 확보.
- [ ] `data/movie_master.csv`로 저장.

### STEP 3: 일별 데이터 수집 실행 (V2: 안정성 강화)
- [ ] `collect_kobis_daily_v2.py` 실행.
- [ ] **체크포인트**: 이미 `data/raw/` 폴더에 해당 날짜의 JSON 파일이 있다면 API 호출을 건너뛰고 다음 날짜로 진행 (서버 부하 감소 및 중단 시 재개 가능).
- [ ] **재시도 로직**: 네트워크 오류 발생 시 최대 3회 재시도 후 로그 기록.

### STEP 4: 데이터 품질 관리 및 누락 대응
- [ ] **이슈**: 일별 박스오피스 API는 해당 일자 **TOP 10**만 반환함.
- [ ] **대응**: 
  - 영화가 흥행 순위권 밖으로 밀려나 데이터가 누락된 경우, `rank=0`, `audi_cnt=0` 등으로 기본값을 채워 데이터프레임의 연속성 유지.
  - Raw JSON 파일에는 빈 결과라도 저장하여 수집 완료 여부를 표시.

## 4. 수집 로직 흐름도 (Flowchart)
1. `movie_master.csv` 읽기
2. 영화별 `release_date` 기준 날짜 리스트(35일) 생성
3. 각 날짜별:
   - `if raw_file_exists`: PASS (이미 수집됨)
   - `else`: API 호출 -> `try-except` (재시도 3회) -> JSON 저장
4. JSON 파일들을 순회하며 `kobis_boxoffice_daily.csv`로 통합
| 컬럼명 | 설명 | 예시 |
| :--- | :--- | :--- |
| movie_title | 영화 제목 | 왕과 사는 남자 |
| movie_cd | KOBIS 영화코드 | 20241234 |
| target_date | 조회 일자 | 20260204 |
| days_since_open | 개봉 후 경과일 | 0 |
| rank | 해당 일자 순위 | 1 |
| audi_cnt | 해당 일자 관객수 | 117783 |
| audi_acc | 누적 관객수 | 147538 |
| scrn_cnt | 스크린수 | 1658 |
- **W1 Audience**: 개봉일(D+0)부터 D+6일까지의 누적 관객수.
- **Growth Rate (W3-W5)**: 3주차 대비 5주차 관객수 유지/상승 비율 (역주행 판별).
- **Peak**: 일별 관객수가 가장 높았던 날짜 및 개봉 후 경과일.
- **Curve Type**: '개봉일 집중형(Front-loaded)', '역주행형(Sleeper-hit)', '안정 유지형(Steady-seller)' 중 판별.

## 5. 단계별 실행 체크리스트 (Summary)

### Phase A: 데이터 수집 (Collection)
1. [ ] `movie_master.csv` (8편) 준비 및 `movieCd` 확인.
2. [ ] API 키 등록 후 `collect_kobis_daily_v2.py` 실행.
3. [ ] `data/raw/` 폴더에 280개(8편 * 35일)의 JSON 파일 생성 확인.

### Phase B: KPI 정산 (Calculation)
1. [ ] `calculate_boxoffice_kpis.py` 실행.
2. [ ] 일별 데이터를 주차별(W1~W5)로 집계.
3. [ ] 성장률 및 Peak 지점 산출 후 `boxoffice_kpis.csv` 저장.
4. [ ] **완료 기준**: 천만 영화 8편의 곡선 타입이 논리적으로 도출되었는지 검증.
