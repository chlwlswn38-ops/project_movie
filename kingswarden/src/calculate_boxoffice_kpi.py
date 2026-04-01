import pandas as pd
import numpy as np
import os

def calculate_boxoffice_kpis(csv_path):
    df = pd.read_csv(csv_path)
    df['target_date'] = pd.to_datetime(df['target_date'], format='%Y%m%d')
    df = df.sort_values(['movie_title', 'target_date'])
    
    kpi_list = []
    
    for movie in df['movie_title'].unique():
        m_df = df[df['movie_title'] == movie].copy()
        m_df = m_df.reset_index(drop=True)
        
        # 개봉일(데이터상 첫 날) 기준 주차 계산
        start_date = m_df['target_date'].min()
        m_df['week'] = ((m_df['target_date'] - start_date).dt.days // 7) + 1
        
        # 주차별 관객수 (W1~W5)
        weekly_audi = m_df.groupby('week')['audi_cnt'].sum()
        w1 = weekly_audi.get(1, 0)
        w2 = weekly_audi.get(2, 0)
        w3 = weekly_audi.get(3, 0)
        w4 = weekly_audi.get(4, 0)
        w5 = weekly_audi.get(5, 0)
        
        # 성장률 (3~5주차) -> (W5 - W3) / W3 * 100
        growth_3_5 = 0
        if w3 > 0:
            growth_3_5 = ((w5 - w3) / w3) * 100
            
        # Peak 시점 (일일 관객수 기준)
        peak_idx = m_df['audi_cnt'].idxmax()
        peak_row = m_df.loc[peak_idx]
        peak_date = peak_row['target_date'].strftime('%Y-%m-%d')
        peak_week = int(peak_row['week'])
        
        # 스크린수 (최대값)
        max_screens = int(m_df['scrn_cnt'].max())
        
        # 결과 저장
        kpi_list.append({
            'movie': movie,
            'w1_audi': int(w1),
            'w2_audi': int(w2),
            'w3_audi': int(w3),
            'w4_audi': int(w4),
            'w5_audi': int(w5),
            'growth_w3_w5': round(growth_3_5, 2),
            'peak_date': peak_date,
            'peak_week': peak_week,
            'max_screens': max_screens
        })
        
    kpi_df = pd.DataFrame(kpi_list)
    return kpi_df

# 실행
data_path = '../data/kobis_audience.csv'
if os.path.exists(data_path):
    kpis = calculate_boxoffice_kpis(data_path)
    
    # 저장
    output_path = '../data/boxoffice_kpis.csv'
    kpis.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print("--- boxoffice_kpis 테이블 스키마 ---")
    print(kpis.head(10))
    print(f"\n총 {len(kpis)}편 분석 완료 및 {output_path} 저장 성공.")
else:
    print(f"데이터 파일 없음: {data_path}")
