import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os

def load_pilot_data():
    """
    수집된 CSV 데이터들을 로드합니다.
    """
    data_dir = "../data/"
    naver_path = os.path.join(data_dir, "naver_review_proxy.csv")
    yt_metrics_path = os.path.join(data_dir, "youtube_metrics.csv")
    yt_comments_path = os.path.join(data_dir, "youtube_comments.csv")
    kobis_path = os.path.join(data_dir, "kobis_audience.csv")
    
    data = {}
    if os.path.exists(naver_path):
        data['naver'] = pd.read_csv(naver_path)
    if os.path.exists(yt_metrics_path):
        data['yt_metrics'] = pd.read_csv(yt_metrics_path)
    if os.path.exists(yt_comments_path):
        data['yt_comments'] = pd.read_csv(yt_comments_path)
    if os.path.exists(kobis_path):
        data['kobis'] = pd.read_csv(kobis_path)
        
    return data

def analyze_youtube_engagement(data):
    """
    유튜브 영상의 참여도(Engagement)를 분석합니다.
    """
    if 'yt_metrics' not in data:
        print("유튜브 메트릭 데이터가 없습니다.")
        return
    
    df = data['yt_metrics']
    # 조회수 대비 좋아요/댓글 비율 계산
    df['like_engagement'] = (df['like_count'] / df['view_count']) * 100
    df['comment_engagement'] = (df['comment_count'] / df['view_count']) * 100
    
    print("\n[유튜브 참여도 분석 결과]")
    print(df[['movie_title', 'title', 'view_count', 'like_engagement', 'comment_engagement']])

def plot_audience_vs_youtube(data):
    """
    관객수 추이와 유튜브 댓글/조회수 반응 추이를 시각화합니다.
    """
    if 'kobis' not in data or 'yt_comments' not in data:
        print("시각화에 필요한 데이터(KOBIS 또는 유튜브 댓글)가 부족합니다.")
        return
    
    kobis_df = data['kobis']
    yt_df = data['yt_comments']
    
    # 날짜 형식 변환
    kobis_df['date'] = pd.to_datetime(kobis_df['target_date'], format='%Y%m%d')
    # 유튜브 날짜(UTC)에서 타임존을 제거하여 naive datetime으로 변환
    yt_df['date'] = pd.to_datetime(yt_df['published_at']).dt.tz_localize(None).dt.normalize()
    
    movies = kobis_df['movie_title'].unique()
    
    for movie in movies:
        m_kobis = kobis_df[kobis_df['movie_title'] == movie].sort_values('date')
        # 일별 댓글 수 집계
        m_yt = yt_df[yt_df['movie_title'] == movie].groupby('date').size().reset_index(name='comment_cnt')
        
        # 데이터 병합 (날짜 기준)
        merged = pd.merge(m_kobis, m_yt, on='date', how='left').fillna(0)
        
        # 시각화
        fig, ax1 = plt.subplots(figsize=(12, 6))
        
        # 왼쪽 축: 관객수
        ax1.set_xlabel('날짜')
        ax1.set_ylabel('일별 관객수', color='tab:blue')
        ax1.plot(merged['date'], merged['audi_cnt'], color='tab:blue', marker='o', label='관객수')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        
        # 오른쪽 축: 유튜브 댓글 수
        ax2 = ax1.twinx()
        ax2.set_ylabel('유튜브 댓글수', color='tab:red')
        ax2.plot(merged['date'], merged['comment_cnt'], color='tab:red', linestyle='--', label='유튜브 댓글')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        
        plt.title(f"[{movie}] 관객수 vs 유튜브 반응 추이")
        fig.tight_layout()
        
        # 이미지 저장
        save_path = f"../images/{movie}_trend_comparison.png"
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path)
        print(f"시각화 결과 저장됨: {save_path}")
        plt.close()

def run_pilot_analysis():
    data = load_pilot_data()
    if not data:
        print("분석할 파일이 없습니다. 수집 스크립트를 먼저 실행하세요.")
        return
        
    analyze_youtube_engagement(data)
    plot_audience_vs_youtube(data)

if __name__ == "__main__":
    run_pilot_analysis()
