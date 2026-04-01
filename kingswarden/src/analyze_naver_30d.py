import pandas as pd
import numpy as np
from konlpy.tag import Okt
from datetime import datetime, timedelta
import os
import re
import matplotlib.pyplot as plt
import koreanize_matplotlib

okt = Okt()

def clean_html(text):
    if not isinstance(text, str): return ""
    # HTML 태그 제거 (<b>, </b>, &quot; 등)
    clean = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    text = re.sub(clean, '', text)
    # URL 및 특수문자 제거
    text = re.sub(r'http\S+|www\S+', '', text)
    text = re.sub(r'[^가-힣0-9\s]', '', text)
    return text.strip()

def run_naver_30d_analysis():
    # 1. 데이터 로드
    file_path = '../data/naver_review_proxy.csv'
    if not os.path.exists(file_path):
        print(f"파일 없음: {file_path}")
        return

    df = pd.read_csv(file_path)
    
    # 2. 시간 필터링 (KST 기준)
    # postdate 포맷: YYYYMMDD
    current_date = datetime(2026, 3, 21)
    start_date_str = (current_date - timedelta(days=30)).strftime('%Y%m%d')
    
    df['postdate'] = df['postdate'].astype(str)
    df_30d = df[df['postdate'] >= start_date_str].copy()
    
    print(f"최근 30일 네이버 문서: {len(df_30d)}건 (전체 {len(df)}건 중)")
    df_30d.to_csv('../data/naver_proxy_30d.csv', index=False, encoding='utf-8-sig')

    # 3. 영화별 KPI 산출
    kpi_list = []
    for movie in df['movie_title'].unique():
        m_df = df_30d[df_30d['movie_title'] == movie]
        
        blog_cnt = len(m_df[m_df['channel'] == 'blog'])
        cafe_cnt = len(m_df[m_df['channel'] == 'cafe'])
        unique_links = m_df['link'].nunique()
        
        kpi_list.append({
            'movie_title': movie,
            'blog_docs_30d': blog_cnt,
            'cafe_docs_30d': cafe_cnt,
            'total_docs_30d': blog_cnt + cafe_cnt,
            'unique_links_30d': unique_links
        })
        
    df_kpi = pd.DataFrame(kpi_list)
    df_kpi.to_csv('../data/naver_movie_kpis_30d.csv', index=False, encoding='utf-8-sig')

    # 4. 키워드 추출
    user_stopwords = {'오늘','정말','너무','영화','진짜','보고','보다','하다','있다','되다','쇼박스','배급사','개봉','관객'}
    query_blacklist = {'리뷰','관람평','후기','감상','평점','결말','스포','쿠키','예고편','출연진','정보','내용','줄거리'}
    
    keyword_results = []
    
    for movie in df_kpi['movie_title'].unique():
        m_df = df_30d[df_30d['movie_title'] == movie]
        if m_df.empty: continue
        
        # 합산 및 채널별 분석
        channels = [('combined', m_df), ('blog', m_df[m_df['channel'] == 'blog']), ('cafe', m_df[m_df['channel'] == 'cafe'])]
        
        for ch_label, ch_df in channels:
            if ch_df.empty: continue
            
            # 블랙리스트
            movie_blacklist = set(okt.nouns(movie))
            total_blacklist = user_stopwords | query_blacklist | movie_blacklist
            
            all_nouns = []
            for _, row in ch_df.iterrows():
                text = clean_html(str(row['title']) + " " + str(row['description']))
                nouns = okt.nouns(text)
                all_nouns.extend([n for n in nouns if n not in total_blacklist and len(n) > 1])
                
            counts = pd.Series(all_nouns).value_counts().head(30)
            for rank, (word, count) in enumerate(counts.items(), 1):
                keyword_results.append({
                    'movie_title': movie,
                    'channel': ch_label,
                    'keyword': word,
                    'count': count,
                    'rank': rank
                })
                
    df_keywords = pd.DataFrame(keyword_results)
    df_keywords.to_csv('../data/naver_keywords_top_30d.csv', index=False, encoding='utf-8-sig')

    # 5. 시각화 (천만 vs 비교군)
    hit_movies = ['명량', '극한직업', '파묘', '서울의 봄', '범죄도시2', '신과함께-죄와 벌', '국제시장', '왕과 사는 남자']
    df_kpi['group'] = df_kpi['movie_title'].apply(lambda x: 'Hit' if x in hit_movies else 'Compare')
    
    # [Visual 1] 블로그 vs 카페 비중 (Average)
    avg_shares = df_kpi.groupby('group')[['blog_docs_30d', 'cafe_docs_30d']].mean()
    plt.figure(figsize=(10, 6))
    avg_shares.plot(kind='bar', stacked=True, color=['#2ecc71', '#f39c12'])
    plt.title('블로그 vs 카페 문서 발생 비중 (30일 평균)')
    plt.ylabel('평균 문서 수')
    plt.savefig('../images/eda/naver_30d_channel_share.png')
    plt.close()
    
    # [Visual 2] 전체 문서 발생량 TOP 10
    top_10 = df_kpi.sort_values('total_docs_30d', ascending=False).head(10)
    plt.figure(figsize=(12, 6))
    plt.bar(top_10['movie_title'], top_10['total_docs_30d'], color='#8e44ad')
    plt.xticks(rotation=45)
    plt.title('최근 30일 네이버 문서 발생 화력 TOP 10')
    plt.savefig('../images/eda/naver_30d_top_volume.png')
    plt.close()
    
    print("네이버 분석 및 시각화 완료.")

if __name__ == "__main__":
    run_naver_30d_analysis()
