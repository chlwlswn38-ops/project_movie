import pandas as pd
import numpy as np
import os

def calculate_kpis():
    # 1. 일별 박스오피스 데이터 로드
    daily_path = '../data/kobis_boxoffice_daily.csv' # V2 스크립트 결과물
    if not os.path.exists(daily_path):
        print("kobis_boxoffice_daily.csv 파일이 없습니다. 수집을 먼저 완료하세요.")
        return
    
    df = pd.read_csv(daily_path)
    
    kpi_results = []
    
    for movie in df['movie_title'].unique():
        m_df = df[df['movie_title'] == movie].sort_values('days_since_open')
        
        # [KPI 1] 1주차(W1) 누적 관객 (D+0 ~ D+6)
        w1_df = m_df[m_df['days_since_open'] <= 6]
        w1_audi_acc = w1_df['audi_cnt'].sum()
        
        # [KPI 2] 주차별 관객수 집계 (W1~W5)
        # 0-6: W1, 7-13: W2, 14-20: W3, 21-27: W4, 28-34: W5
        weekly_audi = []
        for w in range(5):
            w_start = w * 7
            w_end = (w + 1) * 7 - 1
            w_cnt = m_df[(m_df['days_since_open'] >= w_start) & (m_df['days_since_open'] <= w_end)]['audi_cnt'].sum()
            weekly_audi.append(w_cnt)
            
        # [KPI 3] 3~5주차 성장률 (W3 대비 W5 비율)
        growth_rate = 0
        if weekly_audi[2] > 0: # W3가 0이 아닐 때
            growth_rate = round((weekly_audi[4] / weekly_audi[2]) * 100, 2)
            
        # [KPI 4] Peak 시점 (일일 관객수가 가장 높은 날)
        peak_row = m_df.loc[m_df['audi_cnt'].idxmax()]
        peak_date = peak_row['target_date']
        peak_days = peak_row['days_since_open']
        
        # [KPI 5] 곡선 타입(Curve Type) 정의 (Heuristic)
        # W1 비중이 50% 이상이면 Front-loaded, 성장률 100% 이상이면 Sleeper-hit
        total_35d = sum(weekly_audi)
        curve_type = "Steady-seller"
        if w1_audi_acc / total_35d > 0.5:
            curve_type = "Front-loaded (초반집중형)"
        elif growth_rate > 100:
            curve_type = "Sleeper-hit (역주행형)"
        elif weekly_audi[0] < weekly_audi[1]:
            curve_type = "Mouth-fire (입소문형)"
            
        kpi_results.append({
            'movie_title': movie,
            'w1_audience': w1_audi_acc,
            'w3_audience': weekly_audi[2],
            'w5_audience': weekly_audi[4],
            'growth_rate_w3_w5': growth_rate,
            'peak_date': peak_date,
            'peak_days_since_open': peak_days,
            'curve_type': curve_type
        })
        
    # 최종 결과 저장
    df_kpi = pd.DataFrame(kpi_results)
    df_kpi.to_csv('../data/boxoffice_kpis.csv', index=False, encoding='utf-8-sig')
    print(f"[완료] boxoffice_kpis.csv 저장 완료 (총 {len(df_kpi)}건)")

if __name__ == "__main__":
    # calculate_kpis() # 수집 완료 후 실행
    pass
