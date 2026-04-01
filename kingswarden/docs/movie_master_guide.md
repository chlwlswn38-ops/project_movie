# KOBIS 분석의 기준: movie_master(정답표) 구축 가이드

KOBIS API 수집 전, 데이터의 '기준점'이 되는 `movie_master` 테이블을 정확하게 구축하는 것이 가장 중요합니다.

## 1. movie_master 구성 컬럼
| 컬럼명 | 타입 | 설명 | 예시 |
| :--- | :--- | :--- | :--- |
| movie_title | string | 영화 제목 (KOBIS 대표명) | 서울의 봄 |
| movie_cd | string | KOBIS 영화코드 (8자리) | 20228555 |
| release_date | string | 개봉일 (YYYY-MM-DD) | 2023-11-22 |
| group | string | 분석 그룹 (Hit / Compare) | Hit |
| is_10m | boolean | 천만 관객 달성 여부 | True |

## 2. 구축 단계별 절차

### [1단계] 수작업 검증 (천만 8편 우선)
- [ ] [KOBIS 영화관람객 통합전산망](http://www.kobis.or.kr/kobis/business/main/main.do) 접속.
- [ ] '서울의 봄' 등 제목 검색 후 상세 페이지의 **영화코드(movieCd)**와 **개봉일** 확인.
- [ ] `data/movie_master.csv`에 직접 입력.

### [2단계] API 확장 방식 (비교군 40편)
- [ ] `searchMovieList.json` API를 사용하여 비교군 영화 제목 검색.
- [ ] 반환된 리스트 중 `openDt`가 비교군 샘플링 기준(2021~2026)에 부합하는지 확인.
- [ ] 제작사/배급사 정보를 대조하여 동명이작 여부 필터링 후 자동 매핑.

## 3. 데이터 오염 방지 체크리스트 (Mistake Prevention)
- [ ] **동명이작 확인**: "범죄도시" vs "범죄도시2" vs "범죄도시3" 등 시리즈물이나 동명 영화의 `movieCd`가 섞이지 않았는가?
- [ ] **재개봉 데이터 제외**: `openDt`가 최초 개봉일이 아닌 재개봉일로 찍힌 경우, 분석의 시작점이 뒤로 밀리므로 반드시 **최초 개봉일**을 기준으로 한다.
- [ ] **개봉전 시사회(Premiere)**: KOBIS는 시사회 관객도 일별 데이터에 포함하므로, `openDt` 이전 1~2일 데이터가 존재하는지 확인하고 필요 시 포함 여부를 결정한다.

## 4. 작업 계획

### Phase 1: 천만 8편 완성 (우선 순위: 상)
- 대상: 명량, 극한직업, 파묘, 서울의 봄, 범죄도시2, 신과함께-죄와 벌, 국제시장, 왕과 사는 남자
- 목표: 모든 `movie_cd`와 `release_date` 입력 완료.

### Phase 2: 비교군 40편 확장 (우선 순위: 중)
- 대상: 누적 관객 100만~900만 사이 영화 40편 (장르/시즌별 고루 안배).
- 목표: 수집 파이프라인 자동 연동을 위한 CSV 리스트 확보.

## 5. 완료 기준 (Success Criteria)
1. `data/movie_master.csv` 파일이 생성됨.
2. 천만 영화 8편의 `movie_cd`와 `release_date`가 누락 없이 채워짐.
3. KOBIS 사이트와 교차 검증 결과 오차가 없음.
