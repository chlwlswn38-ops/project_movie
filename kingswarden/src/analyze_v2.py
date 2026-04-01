import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import koreanize_matplotlib

# 경로 설정
DATA_DIR = "/Users/me/icb6/antigravity_project/project_s_movie/kingswarden/king_all/data/"
SAVE_DIR = "/Users/me/icb6/antigravity_project/project_s_movie/king_summary_v2/images/"
os.makedirs(SAVE_DIR, exist_ok=True)

# 1. 데이터 로드
master = pd.read_csv(DATA_DIR + "movie_master.csv")
audience = pd.read_csv(DATA_DIR + "kobis_audience.csv")
yt_metrics = pd.read_csv(DATA_DIR + "youtube_metrics.csv")
naver_kpis = pd.read_csv(DATA_DIR + "naver_movie_kpis_30d.csv")
yt_keywords = pd.read_csv(DATA_DIR + "youtube_keywords_top_30d.csv")

# 2. 데이터 전처리 및 KPI 계산
# 인코딩 등 문제로 인해 컬럼명 앞의 BOM 제거 (필요할 경우)
yt_metrics.columns = yt_metrics.columns.str.replace('^\ufeff', '', regex=True)
audience.columns = audience.columns.str.replace('^\ufeff', '', regex=True)
naver_kpis.columns = naver_kpis.columns.str.replace('^\ufeff', '', regex=True)

# 유튜브 인게이지먼트 계산 (합계 기준)
yt_agg = yt_metrics.groupby('movie_title').agg({'view_count':'sum', 'like_count':'sum', 'comment_count':'sum'}).reset_index()
yt_agg['engagement_rate'] = (yt_agg['like_count'] + yt_agg['comment_count']) / yt_agg['view_count'].replace(0, 1) * 100
yt_agg['comment_view_ratio'] = yt_agg['comment_count'] / yt_agg['view_count'].replace(0, 1) * 100

# 박스오피스 주차별 주간 관객수 계산
audience['target_date'] = pd.to_datetime(audience['target_date'])
audience = audience.sort_values(['movie_title', 'target_date'])
audience['day_num'] = audience.groupby('movie_title').cumcount() + 1

w1 = audience[audience['day_num'] <= 7].groupby('movie_title')['audi_cnt'].sum().reset_index().rename(columns={'audi_cnt': 'w1_audi'})
w2 = audience[(audience['day_num'] > 7) & (audience['day_num'] <= 14)].groupby('movie_title')['audi_cnt'].sum().reset_index().rename(columns={'audi_cnt': 'w2_audi'})
total_audi = audience.groupby('movie_title')['audi_cnt'].sum().reset_index().rename(columns={'audi_cnt': 'total_audi'})

bo_metrics = total_audi.merge(w1, on='movie_title', how='left').merge(w2, on='movie_title', how='left')
bo_metrics['reverse_run_idx'] = bo_metrics['w2_audi'] / bo_metrics['w1_audi'].replace(0, 1)

# 네이버 버즈량
naver_agg = naver_kpis[['movie_title', 'total_docs_30d']]

# 데이터 통합
df = master.merge(yt_agg, on='movie_title', how='left') \
           .merge(bo_metrics, on='movie_title', how='left') \
           .merge(naver_agg, on='movie_title', how='left')

# 3. 시각화 함수
def plot_1_engagement(df):
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='group', y='engagement_rate', palette='Set2')
    sns.stripplot(data=df, x='group', y='engagement_rate', color='black', alpha=0.3)
    plt.title('유튜브 인게이지먼트 비율 (좋아요+댓글 / 조회수)', fontsize=15)
    plt.savefig(SAVE_DIR + "01_engagement_rate.png")
    plt.close()

def plot_2_comment_scatter(df):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='engagement_rate', y='comment_view_ratio', hue='group', size='total_audi', sizes=(50, 500), alpha=0.7)
    plt.title('인게이지먼트 vs 댓글 비중 (버블 크기: 총 관객수)', fontsize=15)
    plt.savefig(SAVE_DIR + "02_comment_view_scatter.png")
    plt.close()

def plot_3_reverse_run(df):
    plt.figure(figsize=(10, 6))
    top_15 = df.sort_values('reverse_run_idx', ascending=False).head(15)
    sns.barplot(data=top_15, x='reverse_run_idx', y='movie_title', palette='viridis')
    plt.axvline(x=1.0, color='red', linestyle='--')
    plt.title('역주행 지수 상위 15개 영화', fontsize=15)
    plt.savefig(SAVE_DIR + "03_reverse_run_index.png")
    plt.close()

def plot_4_funnel(df):
    hit_avg = df[df['group'] == 'Hit'].mean(numeric_only=True)
    funnel_data = [
        hit_avg['view_count'] / 10, 
        hit_avg['total_docs_30d'] * 100, 
        hit_avg['w1_audi'], 
        hit_avg['total_audi']
    ]
    labels = ["상진적 인지도(YT View/10)", "관심도(Naver Buzz*100)", "전환(W1 Audi)", "누적 성과(Total Audi)"]
    plt.figure(figsize=(8, 8))
    plt.barh(labels, funnel_data, color='lightgreen')
    plt.gca().invert_yaxis()
    plt.title('천만 영화 표준 비즈니스 퍼널 (Hit 평균)', fontsize=15)
    plt.savefig(SAVE_DIR + "04_business_funnel.png")
    plt.close()

def plot_5_keywords(yt_keywords, df):
    hit_titles = df[df['group'] == 'Hit']['movie_title'].tolist()
    hit_keywords = yt_keywords[yt_keywords['movie_title'].isin(hit_titles)]
    # '영화', '관객' 등 일반 단어 제외 필터링 (필요 시)
    top_hit = hit_keywords.groupby('keyword')['count'].sum().sort_values(ascending=False).head(15)
    plt.figure(figsize=(10, 6))
    top_hit.plot(kind='bar', color='gold')
    plt.title('천만 영화(Hit 그룹) 주요 감성 및 속성 키워드', fontsize=15)
    plt.savefig(SAVE_DIR + "05_top_keywords.png")
    plt.close()

def plot_6_trajectory(audience, df):
    plt.figure(figsize=(10, 6))
    top_5 = df.nlargest(5, 'total_audi')['movie_title'].tolist()
    for movie in top_5:
        m_data = audience[audience['movie_title'] == movie].sort_values('day_num')
        plt.plot(m_data['day_num'], m_data['audi_acc'], label=movie)
    plt.title('누적 관객수 성장 트래젝토리 (D+30)', fontsize=15)
    plt.legend()
    plt.savefig(SAVE_DIR + "06_audience_trajectory.png")
    plt.close()

def plot_7_correlation(df):
    plt.figure(figsize=(10, 8))
    corr = df[['engagement_rate', 'comment_view_ratio', 'reverse_run_idx', 'total_docs_30d', 'total_audi']].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm')
    plt.title('핵심 KPI 상관관계 분석', fontsize=15)
    plt.savefig(SAVE_DIR + "07_correlation_matrix.png")
    plt.close()

def plot_8_efficiency(df):
    df['efficiency'] = df['total_audi'] / df['total_docs_30d'].replace(0, 1)
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=df, x='group', y='efficiency', palette='pastel')
    plt.title('마케팅 효율성 (버즈 1건당 총 관객수)', fontsize=15)
    plt.savefig(SAVE_DIR + "08_buzz_efficiency.png")
    plt.close()

def plot_9_radar(df):
    hit_avg = df[df['group'] == 'Hit'].mean(numeric_only=True)
    target = df[df['movie_title'] == '왕과 사는 남자'].iloc[0]
    metrics = ['engagement_rate', 'comment_view_ratio', 'reverse_run_idx', 'total_docs_30d']
    stats = hit_avg[metrics].values
    target_stats = target[metrics].values
    target_norm = target_stats / np.where(stats==0, 1, stats)
    
    angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
    stats_norm = [1.0] * len(metrics)
    target_norm = target_norm.tolist()
    stats_norm += stats_norm[:1]; target_norm += target_norm[:1]; angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.fill(angles, stats_norm, color='gray', alpha=0.1, label='Hit Group Avg')
    ax.fill(angles, target_norm, color='red', alpha=0.2, label='왕과 사는 남자')
    ax.set_thetagrids(np.degrees(angles[:-1]), metrics)
    plt.title('핵심 지표 벤치마킹 (Hit=1.0 기준)', fontsize=15)
    plt.legend(loc='upper right')
    plt.savefig(SAVE_DIR + "09_radar_chart.png")
    plt.close()

def plot_10_bubble(df):
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='total_docs_30d', y='total_audi', size='view_count', hue='group', sizes=(50, 1000), alpha=0.5)
    plt.title('버즈량 vs 총 관객수 (버블 크기: 유튜브 조회수)', fontsize=15)
    plt.savefig(SAVE_DIR + "10_bubble_chart.png")
    plt.close()

# 실행
print("Generating visualizations...")
plot_1_engagement(df)
plot_2_comment_scatter(df)
plot_3_reverse_run(df)
plot_4_funnel(df)
plot_5_keywords(yt_keywords, df)
plot_6_trajectory(audience, df)
plot_7_correlation(df)
plot_8_efficiency(df)
plot_9_radar(df)
plot_10_bubble(df)
print(f"10 visualizations saved to {SAVE_DIR}")

# 요약 출력
target = df[df['movie_title'] == '왕과 사는 남자'].iloc[0]
hit_avg = df[df['group'] == 'Hit'].mean(numeric_only=True)
print("\n=== Data Summary for Report ===")
print(f"Target Engagement: {target['engagement_rate']:.2f}% (Hit Avg: {hit_avg['engagement_rate']:.2f}%)")
print(f"Target Reverse Index: {target['reverse_run_idx']:.2f} (Hit Avg: {hit_avg['reverse_run_idx']:.2f})")
print(f"Target Total Audience: {target['total_audi']:,} (D+30)")
