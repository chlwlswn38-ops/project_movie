import pandas as pd
import numpy as np
from konlpy.tag import Okt
from collections import Counter
import re
import os

# 1. 초기 설정 (초보자용 가이드: Okt 형태소 분석기 생성)
okt = Okt()

def clean_text(text):
    """
    특수문자 및 이모지 정제 (예외 처리: 빈 텍스트)
    """
    if not isinstance(text, str) or len(text.strip()) == 0:
        return ""
    # 한글, 숫자, 공백만 남기기
    text = re.sub(r'[^가-힣0-9\s]', '', text)
    return text.strip()

def get_weighted_keywords(comments_df, movie_title, video_title_tokens, user_stopwords):
    """
    영화별 키워드 추출 및 가중치(weighted_count) 산출
    """
    # [예외 처리 1] 데이터 중복 제거 (도배 댓글 방지)
    comments_df = comments_df.drop_duplicates(subset=['author', 'text'])
    
    # [예외 처리 2] 빈 댓글 제거
    comments_df = comments_df[comments_df['text'].apply(lambda x: len(str(x).strip()) > 0)]
    
    # 블랙리스트 정의 (영화 제목 + 영상 제목 토큰 + 사용자 불용어)
    movie_tokens = set(okt.nouns(movie_title))
    blacklist = movie_tokens | set(video_title_tokens) | set(user_stopwords)
    
    keyword_data = [] # (word, likes) 쌍을 저장
    
    for _, row in comments_df.iterrows():
        text = clean_text(row['text'])
        likes = row.get('like_count', 0)
        
        # [토큰화] 명사 추출
        nouns = okt.nouns(text)
        
        # [필터링] 블랙리스트 제외 및 1글자 제거
        valid_nouns = [n for n in nouns if n not in blacklist and len(n) > 1]
        
        for word in valid_nouns:
            keyword_data.append((word, likes))
    
    if not keyword_data:
        return pd.DataFrame()
    
    # [통계 산출]
    temp_df = pd.DataFrame(keyword_data, columns=['keyword', 'likes'])
    
    # 가중치 산출 로직: 빈도 * (1 + ln(평균 좋아요 + 1))
    agg = temp_df.groupby('keyword').agg(
        count=('keyword', 'count'),
        avg_likes=('likes', 'mean')
    ).reset_index()
    
    agg['weighted_count'] = agg['count'] * (1 + np.log1p(agg['avg_likes']))
    
    return agg.sort_values('weighted_count', ascending=False)

def run_pipeline():
    # 데이터 로드
    comments_path = '../data/youtube_comments.csv'
    metrics_path = '../data/youtube_metrics.csv'
    
    if not os.path.exists(comments_path):
        print("데이터 파일이 없습니다.")
        return

    df_comments = pd.read_csv(comments_path)
    df_metrics = pd.read_csv(metrics_path)
    
    # 사용자 정의 불용어
    user_stopwords = ['사는', '하다', '되다', '있다', '영화', '정말', '너무', '보고', '진짜', '오늘']
    
    final_results = []
    
    for movie in df_comments['movie_title'].unique():
        print(f"[{movie}] 분석 중...")
        m_comments = df_comments[df_comments['movie_title'] == movie]
        
        # 해당 영화의 영상 제목 토큰 수집
        m_videos = df_metrics[df_metrics['movie_title'] == movie]
        all_title_tokens = []
        for v_title in m_videos['title']:
            all_title_tokens.extend(okt.nouns(v_title))
            
        # 키워드 산출
        kpi_df = get_weighted_keywords(m_comments, movie, all_title_tokens, user_stopwords)
        
        if not kpi_df.empty:
            kpi_df['movie_title'] = movie # movie_id 대신 title 사용 (가독성)
            kpi_df = kpi_df.head(30)
            kpi_df['rank'] = range(1, len(kpi_df) + 1)
            final_results.append(kpi_df)
            
    if final_results:
        final_df = pd.concat(final_results)
        # 컬럼 순서 조정
        final_df = final_df[['movie_title', 'keyword', 'count', 'weighted_count', 'rank']]
        final_df.to_csv('../data/youtube_keywords_top_v2.csv', index=False, encoding='utf-8-sig')
        print(f"최종 산출물 저장 완료: ../data/youtube_keywords_top_v2.csv (총 {len(final_df)}행)")
    else:
        print("분석 결과가 비어있습니다. (final_results is empty)")

if __name__ == "__main__":
    run_pipeline()
