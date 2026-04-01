# 통합 데이터 상세 설명 (Data Description)

이 폴더는 영화 분석 프로젝트의 결과물로 생성된 통합 데이터들을 포함하고 있습니다. 팀원들이 각 데이터의 구성을 이해하고 분석에 활용할 수 있도록 각 파일의 명세와 컬럼 정보를 정리하였습니다.

## 파일 목록 및 설명

### 1. [all_movies_processed_integrated.csv](all_movies_processed_integrated.csv)
- **설명**: 영화별 일별 박스오피스 데이터를 가공하여 추가 지표(상영횟수 당 관객수 등)를 포함한 통합 데이터.
- **주요 컬럼**:
    - `movieCd`: KOBIS 영화 코드
    - `movieNm`: 영화 이름 (국문)
    - `targetDt`: 기준 일자
    - `audiCnt`: 당일 관객수
    - `showCnt`: 당일 상영횟수
    - `aud_per_show`: 상영횟수 당 관객수 (가공 지표)

### 2. [boxoffice_daily_integrated.csv](boxoffice_daily_integrated.csv)
- **설명**: 영화별 개봉 이후 일별 박스오피스 성적 통합본.
- **주요 컬럼**:
    - `show_dt`: 일자
    - `rank`: 당일 순위
    - `audi_cnt`: 당일 관객수
    - `sales_amt`: 당일 매출액
    - `scrn_cnt`: 당일 스크린수
    - `show_cnt`: 당일 상영횟수
    - `movie_id`: 영화 식별자 (영문)

### 3. [boxoffice_timeseries_integrated.csv](boxoffice_timeseries_integrated.csv)
- **설명**: 시계열 분석 및 시각화를 위해 가공된 누적 관객수 및 순위 변동 데이터.
- **주요 컬럼**:
    - `target_dt`: 기준 일자
    - `audi_acc`: 누적 관객수
    - `rank`: 당일 순위
    - `movie_id`: 영화 식별자 (영문)

### 4. [movie_details_integrated.csv](movie_details_integrated.csv)
- **설명**: 영화의 상세 프로필(줄거리, 예산, 수익 등) 통합본 (KOBIS 및 TMDB 데이터 병합).
- **주요 컬럼**:
    - `movie_id`: 영화 식별자 (영문)
    - `overview`: 줄거리 (TMDB)
    - `budget`: 제작비
    - `revenue`: 수익
    - `popularity`: 인기도 지수
    - `vote_average`: 평균 평점

### 5. [naver_datalab_integrated.csv](naver_datalab_integrated.csv)
- **설명**: 영화별 네이버 데이터랩 검색어 트렌드 통합 데이터.
- **주요 컬럼**:
    - `period`: 날짜
    - `ratio`: 검색 상대 수치
    - `movie_id`: 영화 식별자 (영문)

### 6. [naver_news_integrated.csv](naver_news_integrated.csv)
- **설명**: 네이버 뉴스 API를 통해 수집된 영화 관련 주요 기사 데이터.
- **주요 컬럼**:
    - `pub_date`: 발행 일시
    - `media_name`: 언론사명
    - `title`: 기사 제목
    - `description`: 기사 요약
    - `movie_id`: 영화 식별자 (영문)

### 7. [news_sentiment_integrated.csv](news_sentiment_integrated.csv)
- **설명**: 수집된 뉴스 기사 제목에 대한 감성 분석 결과 통합본.
- **주요 컬럼**:
    - `movie_name`: 영화 이름 (영문/ID)
    - `부정`: 부정적인 어조의 비율 (%)
    - `중립`: 중립적인 어조의 비율 (%)

### 8. [watcha_reviews_popular_integrated.csv](watcha_reviews_popular_integrated.csv)
- **설명**: 왓챠(Watcha)에서 수집된 사용자 리뷰 통합본 (**좋아요순** 정렬).
- **주요 컬럼**:
    - `user_name`: 작성자 닉네임
    - `rating`: 평점 (0.5~5.0)
    - `review_text`: 리뷰 내용
    - `likes_count`: 좋아요 수
    - `replies_count`: 댓글 수
    - `created_at`: 작성 시간
    - `movie_id`: 영화 식별자 (영문)

### 9. [watcha_reviews_low_integrated.csv](watcha_reviews_low_integrated.csv)
- **설명**: 왓챠(Watcha)에서 수집된 사용자 리뷰 통합본 (**평점 낮은순** 정렬).
- **주요 컬럼**: (위 좋아요순 데이터와 동일한 양식)
    - `user_name`, `rating`, `review_text`, `likes_count`, `replies_count`, `created_at`, `movie_id`

---
**비고 (Notes)**:
- 모든 CSV 파일은 `utf-8-sig` 인코딩으로 저장되어 엑셀(Excel)에서 한글 깨짐 없이 열람 가능합니다.
- 영화 식별자(`movie_id`)와 한글 명칭 매핑은 다음과 같습니다:
    - `myeongryang`: 명량
    - `parasite`: 기생충
    - `sado`: 사도
    - `the_kings_garden`: 왕과 사는 남자
    - `the_night_owl`: 올빼미
    - `the_man_standing_next`: 남산의 부장들
    - `decision_to_leave`: 헤어질 결심
