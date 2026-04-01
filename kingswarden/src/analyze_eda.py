import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import re
from collections import Counter

def load_all_data():
    """
    모든 수집된 데이터를 로드합니다.
    """
    data_dir = "../data/"
    data = {
        'naver': pd.read_csv(os.path.join(data_dir, "naver_review_proxy.csv")),
        'yt_metrics': pd.read_csv(os.path.join(data_dir, "youtube_metrics.csv")),
        'yt_comments': pd.read_csv(os.path.join(data_dir, "youtube_comments.csv")),
        'kobis': pd.read_csv(os.path.join(data_dir, "kobis_audience.csv"))
    }
    return data

def extract_keywords(text_list, top_n=30):
    """
    단순 정규표현식을 사용하여 명사 형태의 키워드를 추출합니다 (2글자 이상).
    """
    words = []
    # 한글만 추출
    regex = re.compile('[가-힣]{2,}')
    
    for text in text_list:
        if pd.isna(text): continue
        found = regex.findall(str(text))
        words.extend(found)
        
    # 불용어 처리 (예시)
    stopwords = ['영화', '정말', '진짜', '너무', '보고', '오늘', '그냥', '거기', '하나', '생각', '우리']
    words = [w for w in words if w not in stopwords]
    
    return Counter(words).most_common(top_n)

def analyze_naver(data):
    """
    네이버 언급량 및 키워드를 분석합니다.
    """
    df = data['naver']
    # 영화별/채널별 언급량
    volume = df.groupby(['movie_title', 'channel']).size().unstack(fill_value=0)
    print("\n[네이버 채널별 언급량]")
    print(volume)
    
    # 영화별 키워드 Top 30
    keywords_results = {}
    for movie in df['movie_title'].unique():
        m_df = df[df['movie_title'] == movie]
        # 제목과 설명을 합쳐서 분석
        texts = m_df['title'].tolist() + m_df['description'].tolist()
        keywords_results[movie] = extract_keywords(texts)
        
    return volume, keywords_results

def analyze_youtube(data):
    """
    유튜브 참여도 및 댓글 키워드를 분석합니다.
    """
    m_df = data['yt_metrics']
    c_df = data['yt_comments']
    
    # Engagement Rate 계산 (좋아요+댓글 / 조회수)
    m_df['engagement_rate'] = ((m_df['like_count'] + m_df['comment_count']) / m_df['view_count']) * 100
    avg_eng = m_df.groupby('movie_title')['engagement_rate'].mean()
    
    print("\n[유튜브 평균 참여율(Engagement Rate)]")
    print(avg_eng)
    
    # 댓글 키워드
    keywords_results = {}
    for movie in c_df['movie_title'].unique():
        movie_comments = c_df[c_df['movie_title'] == movie]['text'].tolist()
        keywords_results[movie] = extract_keywords(movie_comments)
        
    return avg_eng, keywords_results

def calculate_kpis(data, naver_vol, yt_eng):
    """
    천만 성공 신호 후보 KPI 5종을 산출합니다.
    """
    k_df = data['kobis']
    
    kpis = []
    movies = naver_vol.index.get_level_values(0).unique()
    
    for movie in movies:
        # 1. Cafe-to-Blog Ratio
        vol = naver_vol.loc[movie]
        cafe_blog_ratio = vol.get('cafe', 0) / vol.get('blog', 1) if vol.get('blog', 0) > 0 else 0
        
        # 2. Engagement Rate (YouTube)
        eng_rate = yt_eng.get(movie, 0)
        
        # 3. KOBIS Initial Audi (개봉 첫날 관객수)
        m_kobis = k_df[k_df['movie_title'] == movie].sort_values('target_date')
        first_day_audi = int(m_kobis.iloc[0]['audi_cnt']) if not m_kobis.empty else 0
        
        # 4. Comment-to-View Ratio (YouTube)
        yt_m = data['yt_metrics'][data['yt_metrics']['movie_title'] == movie]
        comment_view_ratio = (yt_m['comment_count'].sum() / yt_m['view_count'].sum()) * 100 if yt_m['view_count'].sum() > 0 else 0
        
        # 5. Daily Audi Stability (상위권 유지일수 - Top 3 기준)
        top3_days = len(m_kobis[m_kobis['rank'].astype(int) <= 3])
        
        kpis.append({
            "movie": movie,
            "Cafe/Blog Ratio": cafe_blog_ratio,
            "Engagement Rate": eng_rate,
            "First Day Audi": first_day_audi,
            "Comment/View Ratio": comment_view_ratio,
            "Top 3 Maintain Days": top3_days
        })
        
    return pd.DataFrame(kpis)

def plot_final_eda(kpi_df, na_kw, yt_kw):
    """
    분석 결과를 시각화합니다.
    """
    os.makedirs("../images/eda", exist_ok=True)
    
    # 1. KPI 비교 (Spider Chart 대용 Bar Chart)
    kpi_norm = kpi_df.copy()
    for col in kpi_df.columns[1:]:
        kpi_norm[col] = kpi_df[col] / kpi_df[col].max() # 정규화
        
    kpi_norm.set_index('movie').plot(kind='bar', figsize=(12, 6))
    plt.title("천만(왕사남) vs 비교군 KPI 상대 비교 (정규화)")
    plt.xticks(rotation=0)
    plt.savefig("../images/eda/kpi_comparison.png")
    
    # 2. 키워드 시각화 (왕사남 기준)
    mv = "왕과 사는 남자"
    if mv in na_kw:
        kws = na_kw[mv][:15]
        words, counts = zip(*kws)
        plt.figure(figsize=(10, 5))
        plt.barh(words, counts, color='skyblue')
        plt.title(f"[{mv}] 네이버 핵심 키워드 Top 15")
        plt.gca().invert_yaxis()
        plt.savefig("../images/eda/king_naver_keywords.png")
        
    print("\nEDA 시각화 완료: images/eda/ 폴더를 확인하세요.")

def run_full_eda():
    data = load_all_data()
    
    na_vol, na_kw = analyze_naver(data)
    yt_eng, yt_kw = analyze_youtube(data)
    kpi_df = calculate_kpis(data, na_vol, yt_eng)
    
    print("\n[최종 산출된 KPI 데이터프레임]")
    print(kpi_df)
    
    plot_final_eda(kpi_df, na_kw, yt_kw)
    
    # KPI 파일 저장
    kpi_df.to_csv("../data/success_kpi_pilot.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    run_full_eda()
