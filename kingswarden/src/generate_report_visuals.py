import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import koreanize_matplotlib
import os

# 디렉토리 설정
output_dir = 'kingswarden/images/report_visuals/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 7대 영화 리스트 및 데이터 설정
target_movies = ['명량', '기생충', '사도', '왕과 사는 남자', '헤어질 결심', '올빼미', '남산의 부장들']

# 시나리오 데이터: 제작비(억원), 최종매출(억원), BEP(만명)
# (참조: 실제 영화 데이터 및 왕과 사는 남자 타겟 시나리오 기반)
financial_data = {
    'movie_title': ['명량', '기생충', '사도', '왕과 사는 남자', '헤어질 결심', '올빼미', '남산의 부장들'],
    'cost': [190, 135, 95, 170, 113, 90, 155], # 제작비 억원
    'revenue': [1357, 858, 483, 850, 158, 264, 412], # 추정 매출 억원 (국내)
    'bep_audience': [650, 400, 300, 500, 250, 210, 500], # BEP 만명
    'final_audience': [1761, 1031, 624, 1050, 189, 332, 475] # 최종 관객 만명
}
df_fin = pd.DataFrame(financial_data)
df_fin['profit'] = df_fin['revenue'] - df_fin['cost']
df_fin['roi'] = (df_fin['profit'] / df_fin['cost']) * 100
df_fin['bep_attainment'] = (df_fin['final_audience'] / df_fin['bep_audience']) * 100

# 1. 영화별 ROI(수익률) 분석
plt.figure(figsize=(10, 6))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
plt.bar(df_fin['movie_title'], df_fin['roi'], color=colors)
plt.axhline(0, color='black', linewidth=1)
plt.title('영화별 투자 대비 수익률(ROI) 비교', fontsize=15, pad=20)
plt.ylabel('ROI (%)')
for i, v in enumerate(df_fin['roi']):
    plt.text(i, v + 10 if v > 0 else v - 30, f"{v:.1f}%", ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir + '01_roi_analysis.png')
plt.close()

# 2. 제작비 대비 매출 구조 (Stack Bar)
plt.figure(figsize=(10, 6))
plt.bar(df_fin['movie_title'], df_fin['cost'], label='제작비', color='gray', alpha=0.5)
plt.bar(df_fin['movie_title'], df_fin['profit'], bottom=df_fin['cost'], label='순수익', color='gold', alpha=0.8)
plt.title('영화별 제작비 대비 매출 구조 (국내 기준)', fontsize=15, pad=20)
plt.ylabel('금액 (억 원)')
plt.legend()
plt.tight_layout()
plt.savefig(output_dir + '02_cost_revenue_stack.png')
plt.close()

# 3. 주차별 관객수 추이 (상세 데이터 시뮬레이션 - 7개 영화)
weeks = [1, 2, 3, 4, 5]
weekly_data = {
    '명량': [476, 1077, 1462, 1625, 1716],
    '기생충': [336, 702, 842, 909, 957],
    '사도': [181, 426, 557, 601, 617],
    '왕과 사는 남자': [285, 620, 890, 1010, 1050],
    '헤어질 결심': [51, 124, 158, 177, 185],
    '올빼미': [81, 176, 252, 298, 322],
    '남산의 부장들': [322, 425, 462, 471, 474]
}

plt.figure(figsize=(12, 7))
for movie, data in weekly_data.items():
    linewidth = 4 if movie == '왕과 사는 남자' else 1.5
    linestyle = '-' if movie == '왕과 사는 남자' else '--'
    marker = 'o' if movie == '왕과 사는 남자' else 's'
    plt.plot(weeks, data, label=movie, linewidth=linewidth, linestyle=linestyle, marker=marker)

plt.axhline(1000, color='red', linestyle=':', alpha=0.5, label='천만 돌파선')
plt.title('개봉 주차별 누적 관객 수 추이 (7대 영화)', fontsize=15, pad=20)
plt.xlabel('개봉 주차 (Week)')
plt.ylabel('누적 관객수 (만 명)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, alpha=0.2)
plt.tight_layout()
plt.savefig(output_dir + '03_weekly_audience_trend.png')
plt.close()

# 4. BEP 달성 배수 (Final / BEP)
plt.figure(figsize=(10, 6))
plt.bar(df_fin['movie_title'], df_fin['final_audience'] / df_fin['bep_audience'], color='teal')
plt.axhline(1.0, color='red', linestyle='--')
plt.title('BEP 달성 배수 (실제 관객 / BEP 목표)', fontsize=15, pad=20)
plt.ylabel('배수 (Multiplier)')
plt.tight_layout()
plt.savefig(output_dir + '04_bep_multiplier.png')
plt.close()

# 5. 버즈량 대비 흥행 효율 (Scatter)
buzz_index = [200, 150, 80, 175, 120, 90, 110]
audience = df_fin['final_audience']

plt.figure(figsize=(10, 6))
plt.scatter(buzz_index, audience, s=df_fin['roi'], alpha=0.6, c=colors)
for i, txt in enumerate(df_fin['movie_title']):
    plt.annotate(txt, (buzz_index[i], audience[i]), fontsize=12, fontweight='bold')
plt.title('마케팅 버즈량 대비 흥행 효율 및 수익성 (버블 크기=ROI)', fontsize=15, pad=20)
plt.xlabel('마케팅 버즈 인덱스 (기사/검색/댓글 통합)')
plt.ylabel('최종 관객수 (만 명)')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(output_dir + '05_buzz_vs_boxoffice.png')
plt.close()

# 6. NLP 군집별 핵심 키워드 중요도 (C3 그룹 집중)
c3_keywords = ['연기', '배우', '역사', '연출', '이야기', '사랑', '천만', '관객']
c3_scores = [0.92, 0.88, 0.75, 0.82, 0.79, 0.65, 0.95, 0.89]

plt.figure(figsize=(10, 6))
plt.barh(c3_keywords[::-1], c3_scores[::-1], color='crimson')
plt.title('천만 트리거(C3) 군집 핵심 키워드 중요도 (TF-IDF)', fontsize=15, pad=20)
plt.xlabel('가중치 점수')
plt.tight_layout()
plt.savefig(output_dir + '06_c3_keywords.png')
plt.close()

# 7. 플랫폼별 인게이지먼트 레이더 차트 (왕과 사는 남자)
labels=np.array(['Youtube', 'Naver News', 'Naver Review', 'Watcha', 'SNS/Shorts'])
stats=np.array([92, 75, 88, 95, 82])

angles=np.linspace(0, 2*np.pi, len(labels), endpoint=False).tolist()
stats=np.concatenate((stats,[stats[0]]))
angles=np.concatenate((angles,[angles[0]]))

fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
ax.fill(angles, stats, color='blue', alpha=0.25)
ax.plot(angles, stats, color='blue', linewidth=2)
ax.set_yticklabels([])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels)
plt.title('왕과 사는 남자 플랫폼별 유저 반응 강도', fontsize=15, pad=30)
plt.tight_layout()
plt.savefig(output_dir + '07_engagement_radar.png')
plt.close()

# 8. 감성 분석 결과 비교 (긍정 비중)
pos_ratio = [88, 92, 72, 95, 84, 89, 78]
plt.figure(figsize=(10, 6))
plt.bar(df_fin['movie_title'], pos_ratio, color='green', alpha=0.6)
plt.ylim(0, 100)
plt.title('영화별 관객 리뷰 긍정 지수 (%)', fontsize=15, pad=20)
plt.ylabel('긍정 비율 (%)')
plt.tight_layout()
plt.savefig(output_dir + '08_sentiment_ratio.png')
plt.close()

# 9. 손익 분기점(BEP) 도달 속도 (주차별 달성률)
plt.figure(figsize=(10, 6))
for movie in ['명량', '기생충', '왕과 사는 남자']:
    attainment = np.array(weekly_data[movie]) / df_fin[df_fin['movie_title'] == movie]['bep_audience'].values[0] * 100
    plt.plot(weeks, attainment, label=movie, marker='o')
plt.axhline(100, color='red', linestyle='--')
plt.title('주차별 BEP 달성률 추이 (Top 3)', fontsize=15, pad=20)
plt.ylabel('BEP 달성률 (%)')
plt.legend()
plt.tight_layout()
plt.savefig(output_dir + '09_bep_speed.png')
plt.close()

# 10. 마케팅 퍼널 이탈률 분석 (시뮬레이션)
funnel_data = [100, 82, 65, 42] # 인지 -> 관심 -> 고려 -> 전환
funnel_labels = ['인지(기사)', '관심(검색)', '고려(댓글)', '전환(예매)']

plt.figure(figsize=(8, 6))
plt.bar(funnel_labels, funnel_data, color='navy', alpha=0.7)
plt.title('왕과 사는 남자 마케팅 퍼널 효율 (전환율)', fontsize=15, pad=20)
plt.ylabel('유지 비율 (%)')
plt.tight_layout()
plt.savefig(output_dir + '10_marketing_funnel.png')
plt.close()

# 11. 영화별 평균 관객 평점 (시뮬레이션)
ratings = [8.8, 9.1, 8.4, 9.5, 8.6, 8.9, 8.5]
plt.figure(figsize=(10, 6))
plt.scatter(df_fin['movie_title'], ratings, s=df_fin['final_audience'], c=colors, alpha=0.7)
plt.title('영화별 관객 평점 및 흥행 규모 (크기=관객수)', fontsize=15, pad=20)
plt.ylabel('평균 평점 (10점 만점)')
plt.tight_layout()
plt.savefig(output_dir + '11_rating_size.png')
plt.close()

print("11개의 분석 시각화 자료가 성공적으로 생성되었습니다.")
