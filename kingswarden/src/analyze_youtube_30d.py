import pandas as pd
import numpy as np
from konlpy.tag import Okt
from datetime import datetime, timedelta
import os
import re

# 한글 폰트 설정
import matplotlib.pyplot as plt
import koreanize_matplotlib

# Okt 초기화
okt = Okt()

def run_30d_analysis():
    # 1. 데이터 로드
    comments_path = '../data/youtube_comments.csv'
    metrics_path = '../data/youtube_metrics.csv'
    
    if not os.path.exists(comments_path) or not os.path.exists(metrics_path):
        print("데이터 파일이 없습니다.")
        return

    df_comments = pd.read_csv(comments_path)
    df_metrics = pd.read_csv(metrics_path)
    
    # 2. 시간 필터링 (KST 기준)
    # 현재 날짜 2026-03-21 기준 30일 전: 2026-02-19
    current_date = datetime(2026, 3, 21)
    start_date = current_date - timedelta(days=30)
    
    # published_at 변환 (타임존 제거하여 비교 가능하게 처리)
    df_comments['published_at'] = pd.to_datetime(df_comments['published_at']).dt.tz_localize(None)
    df_30d = df_comments[df_comments['published_at'] >= start_date].copy()
    
    print(f"최근 30일 댓글 수: {len(df_30d)}건 (전체 {len(df_comments)}건 중)")
    
    # 3. 영화별 KPI 산출
    kpis = []
    for movie in df_metrics['movie_title'].unique():
        m_metrics = df_metrics[df_metrics['movie_title'] == movie]
        m_30d_comments = df_30d[df_30d['movie_title'] == movie]
        
        v_sum = m_metrics['view_count'].sum()
        l_sum = m_metrics['like_count'].sum()
        c_sum = m_metrics['comment_count'].sum()
        c_30d = len(m_30d_comments)
        
        er = 0
        if v_sum > 0:
            er = (l_sum + c_sum) / v_sum * 100
            
        kpis.append({
            'movie_title': movie,
            'views_sum': int(v_sum),
            'likes_sum': int(l_sum),
            'comments_sum': int(c_sum),
            'comment_30d_count': c_30d,
            'engagement_rate': round(er, 4)
        })
        
    df_kpi_30d = pd.DataFrame(kpis)
    df_kpi_30d.to_csv('../data/youtube_movie_kpis_30d.csv', index=False, encoding='utf-8-sig')
    
    # 4. 키워드 추출 (30일 댓글 기반)
    user_stopwords = {'오늘','정말','너무','영화','진짜','보고','보다','하다','있다','되다','쇼박스','배급사','개봉','관객'}
    keyword_results = []
    
    # 라벨링용 매핑 (Heuristic)
    video_labels = {}
    for _, row in df_metrics.iterrows():
        v_id = row['video_id']
        v_title = row['title']
        label = 'clip'
        if '메인' in v_title and '예고' in v_title: label = 'trailer'
        elif '티저' in v_title or '런칭' in v_title: label = 'teaser'
        video_labels[v_id] = label

    for movie in df_kpi_30d['movie_title'].unique():
        m_comments = df_30d[df_30d['movie_title'] == movie]
        if m_comments.empty: continue
        
        m_metrics = df_metrics[df_metrics['movie_title'] == movie]
        blacklist = set(okt.nouns(movie)) | user_stopwords
        for title in m_metrics['title']:
            blacklist |= set(okt.nouns(title))
            
        all_nouns = []
        for v_id in m_comments['video_id'].unique():
            v_comments = m_comments[m_comments['video_id'] == v_id]
            for text in v_comments['text']:
                if not isinstance(text, str): continue
                nouns = okt.nouns(text)
                all_nouns.extend([n for n in nouns if n not in blacklist and len(n) > 1])
            
        counts = pd.Series(all_nouns).value_counts().head(30)
        for rank, (word, count) in enumerate(counts.items(), 1):
            keyword_results.append({
                'movie_title': movie,
                'keyword': word,
                'count': count,
                'rank': rank
            })
            
    df_keywords_30d = pd.DataFrame(keyword_results)
    df_keywords_30d.to_csv('../data/youtube_keywords_top_30d.csv', index=False, encoding='utf-8-sig')
    
    # 5. 시각화 (천만 vs 비교군)
    hit_movies = ['명량', '극한직업', '파묘', '서울의 봄', '범죄도시2', '신과함께-죄와 벌', '국제시장', '왕과 사는 남자']
    df_kpi_30d['group'] = df_kpi_30d['movie_title'].apply(lambda x: 'Hit' if x in hit_movies else 'Compare')
    
    # [Visual 1] 30일 댓글수 분포
    plt.figure(figsize=(10, 6))
    groups = df_kpi_30d.groupby('group')['comment_30d_count'].mean()
    groups.plot(kind='bar', color=['#3498db', '#e74c3c'])
    plt.title('최근 30일 평균 댓글수 (천만 그룹 vs 비교군)')
    plt.ylabel('평균 댓글수')
    plt.savefig('../images/eda/youtube_30d_comment_comparison.png')
    plt.close()
    
    # [Visual 2] Engagement Rate 비교
    plt.figure(figsize=(10, 6))
    plt.scatter(df_kpi_30d['views_sum'], df_kpi_30d['engagement_rate'], 
                c=df_kpi_30d['group'].map({'Hit': '#e74c3c', 'Compare': '#3498db'}), alpha=0.6)
    plt.xscale('log')
    plt.title('조회수 대비 참여율 (Engagement Rate)')
    plt.xlabel('누적 조회수 (log)')
    plt.ylabel('Engagement Rate (%)')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig('../images/eda/youtube_30d_engagement_scatter.png')
    plt.close()

    # [Visual 3] 전체 상위 키워드 빈도 (Hit Group 선별)
    hit_keywords = df_keywords_30d[df_keywords_30d['movie_title'].isin(hit_movies)]
    top_hit_k = hit_keywords.groupby('keyword')['count'].sum().sort_values(ascending=False).head(15)
    plt.figure(figsize=(10, 6))
    top_hit_k.plot(kind='barh', color='#f1c40f')
    plt.title('천만 영화 최근 30일 핵심 키워드 Top 15')
    plt.gca().invert_yaxis()
    plt.savefig('../images/eda/youtube_30d_hit_keywords.png')
    plt.close()

    # [Visual 4] 영상 라벨별 댓글 비중 (전체)
    df_30d['label'] = df_30d['video_id'].map(video_labels)
    label_counts = df_30d['label'].value_counts()
    plt.figure(figsize=(8, 8))
    label_counts.plot(kind='pie', autopct='%1.1f%%', colors=['#1abc9c','#9b59b6','#34495e'])
    plt.title('영상 라벨별 최근 30일 댓글 분포')
    plt.ylabel('')
    plt.savefig('../images/eda/youtube_30d_label_pie.png')
    plt.close()
    
    print("분석 및 시각화 완료.")
    
    print("분석 및 시각화 완료.")

if __name__ == "__main__":
    run_30d_analysis()
